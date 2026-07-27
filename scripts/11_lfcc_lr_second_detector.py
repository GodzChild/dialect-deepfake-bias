#!/usr/bin/env python3
"""
Script 11: LFCC + Logistic Regression Second-Detector Replication (Entry 8)
============================================================================
Trains a lightweight, hand-crafted-feature detector (LFCC + delta + delta-
delta, mean+std pooling, StandardScaler + LogisticRegression) on the same
AuralGuard training distribution AASIST uses, minus the 16 held-out DECTE
mitigation test speakers, then evaluates on the exact same DECTE mitigation
test manifest and VCTK XTTS control that AASIST was scored on.

Purpose: test whether the DECTE-vs-VCTK XTTS gap (Entry 6, +12.8pp for
AASIST) also appears in a fundamentally different detector family
(hand-crafted spectral features + convex linear classifier). If yes, the
gap is detector-invariant and much more defensible as a thesis claim.

Method
------
Features:
  - 20 LFCC coefficients per frame + delta + delta-delta = 60-dim per frame
  - Mean + std over time -> 120-dim utterance vector
  - Extracted via librosa STFT + a linear-scale triangular filter bank
    + log + type-2 orthonormal DCT (standard ASVspoof LFCC).
  - Audio preprocessing MIRRORS the AASIST detector's _load_audio:
    soundfile read, mono, resample to 16 kHz, deterministic 4-second
    zero-padded crop from position 0. Both detectors therefore see the
    same 4-s audio window per file -- a fair architecture-only comparison.

Classifier:
  - StandardScaler + LogisticRegression(class_weight="balanced", C=1.0,
    max_iter=1000, random_state=42).
  - Score = predict_proba(...)[:, class 0] = P(bonafide). Higher = more
    real, matching src/evaluation/metrics.py convention.

Training data:
  - AuralGuard train CSV (~35k rows), with the 16 DECTE mitigation-test
    speakers removed to avoid leakage into the held-out DECTE evaluation.

Bootstrap:
  - 1000 iterations, seed 42, stratified independent resampling of
    bonafide and spoof arrays per corpus. Joint bootstrap per iteration
    computes DECTE EER, VCTK EER, and their difference in one pass, so
    the gap CI is on the difference directly.

Outputs (all under results/second_detector_lfcc_lr/, gitignored):
  - train_features.npz             (feature cache, skips extraction on re-runs)
  - lfcc_lr_model.joblib           (fitted pipeline: scaler + LR)
  - lfcc_lr_results.csv            (per-corpus rows + gap row with CIs)

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/11_lfcc_lr_second_detector.py

Force re-extraction of training features (skip cache):
    python scripts/11_lfcc_lr_second_detector.py --refresh-features
"""

import argparse
import json
import os
import sys
from pathlib import Path

import joblib
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
from scipy.fftpack import dct
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.evaluation.metrics import compute_metrics, compute_eer


# ---------- fixed inputs / outputs ----------

REPO_ROOT = Path(__file__).resolve().parents[1]
AURALGUARD_ROOT = Path(
    r"C:\Users\AYO\Desktop\JKU\Extra Semester\THESIS AND PRACTICAL\auralguard-aasistpp"
)
AURALGUARD_TRAIN_CSV = AURALGUARD_ROOT / "data" / "metadata" / "train_final_accent_globe_wavefake_balanced.csv"
DECTE_TEST_CSV = REPO_ROOT / "data" / "decte" / "metadata" / "decte_mitigation_test.csv"
DECTE_TEST_MANIFEST = REPO_ROOT / "data" / "generated_spoofs" / "manifest_mitigation_test.jsonl"
VCTK_MANIFEST = REPO_ROOT / "data" / "generated_spoofs_vctk" / "manifest.jsonl"

RESULTS_DIR = REPO_ROOT / "results" / "second_detector_lfcc_lr"
TRAIN_FEATURES_CACHE = RESULTS_DIR / "train_features.npz"
MODEL_PATH = RESULTS_DIR / "lfcc_lr_model.joblib"
RESULTS_CSV = RESULTS_DIR / "lfcc_lr_results.csv"


# ---------- audio / feature constants (match AASIST 4-s window) ----------

TARGET_SR = 16000
DURATION_SEC = 4.0
NUM_SAMPLES = int(TARGET_SR * DURATION_SEC)
N_FFT = 512
HOP_LENGTH = 160
WIN_LENGTH = 400
N_LFCC = 20
N_FILTERS = 20
BOOTSTRAP_ITERS = 1000
SEED = 42


# ---------- audio + feature extraction ----------

def load_audio_fixed(path: str) -> np.ndarray:
    """Mirror src/evaluation/detectors.py::AASISTDetector._load_audio.
    soundfile read, mono-average, resample to 16k, deterministic 4-s
    zero-padded crop from position 0. Returns np.float32 of shape [NUM_SAMPLES]."""
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    wav = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    if sr != TARGET_SR:
        wav = librosa.resample(wav, orig_sr=sr, target_sr=TARGET_SR)
    if wav.shape[0] < NUM_SAMPLES:
        wav = np.pad(wav, (0, NUM_SAMPLES - wav.shape[0]))
    else:
        wav = wav[:NUM_SAMPLES]
    return wav.astype(np.float32)


def _linear_filterbank(sr: int, n_fft: int, n_filters: int = N_FILTERS,
                       f_min: float = 0.0, f_max: float | None = None) -> np.ndarray:
    """Triangular filter bank linearly spaced on Hz (LFCC front end)."""
    if f_max is None:
        f_max = sr / 2.0
    edges = np.linspace(f_min, f_max, n_filters + 2)
    fft_freqs = np.linspace(0.0, sr / 2.0, n_fft // 2 + 1)
    fb = np.zeros((n_filters, n_fft // 2 + 1), dtype=np.float32)
    for i in range(n_filters):
        left, center, right = edges[i], edges[i + 1], edges[i + 2]
        rising = (fft_freqs >= left) & (fft_freqs <= center)
        fb[i, rising] = (fft_freqs[rising] - left) / max(center - left, 1e-9)
        falling = (fft_freqs >= center) & (fft_freqs <= right)
        fb[i, falling] = (right - fft_freqs[falling]) / max(right - center, 1e-9)
    return fb


_FB = _linear_filterbank(TARGET_SR, N_FFT, N_FILTERS)


def compute_lfcc(wav: np.ndarray) -> np.ndarray:
    """20 LFCC per frame. Returns [N_LFCC, n_frames]."""
    stft = librosa.stft(
        wav, n_fft=N_FFT, hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH, window="hann",
    )
    power = (np.abs(stft) ** 2).astype(np.float32)
    filt = _FB @ power                                  # (n_filters, n_frames)
    log_e = np.log(np.maximum(filt, 1e-10)).astype(np.float32)
    cepstral = dct(log_e, axis=0, type=2, norm="ortho")[:N_LFCC]
    return cepstral.astype(np.float32)


def utterance_features(wav: np.ndarray) -> np.ndarray:
    """LFCC + delta + delta-delta, mean+std over time -> 120-dim."""
    lfcc = compute_lfcc(wav)
    delta1 = librosa.feature.delta(lfcc, order=1)
    delta2 = librosa.feature.delta(lfcc, order=2)
    feats = np.concatenate([lfcc, delta1, delta2], axis=0)  # (60, n_frames)
    return np.concatenate([feats.mean(axis=1), feats.std(axis=1)]).astype(np.float32)


def extract_features_from_paths(paths: list[str], desc: str) -> np.ndarray:
    """Extract 120-dim features for a list of audio paths. Skips (and warns
    about) unreadable files with a NaN row so the caller can drop them."""
    X = np.full((len(paths), 120), np.nan, dtype=np.float32)
    for i, path in enumerate(tqdm(paths, desc=desc)):
        try:
            wav = load_audio_fixed(path)
            X[i] = utterance_features(wav)
        except Exception as e:
            tqdm.write(f"  ERROR {path}: {e}")
    return X


# ---------- training-data prep ----------

def resolve_train_path(path_str: str) -> str:
    """Resolve a file_path from the AuralGuard train CSV to an absolute path.
    Absolute paths pass through. Relative paths are resolved against
    AURALGUARD_ROOT (that's the CWD they were written relative to)."""
    p = Path(path_str.replace("\\", "/"))
    if p.is_absolute():
        return str(p)
    return str(AURALGUARD_ROOT / p)


def speaker_from_path(path_str: str) -> str:
    """Best-effort speaker-ID extraction from an audio path, primarily for
    DECTE chunk audio filenames:
      data/01_chunks/PVC/decten1pvc03audio/decten1pvc03audio_chunk_00043.wav
      -> 'decten1pvc03'
    Rules: lowercase the filename stem; drop suffix from '_chunk_' onward;
    strip trailing 'audio'. Non-DECTE paths return their lowercased stem
    (which will not collide with the DECTE test speaker IDs, so filtering
    is safe)."""
    stem = Path(path_str.replace("\\", "/")).stem.lower()
    if "_chunk_" in stem:
        stem = stem.split("_chunk_")[0]
    if stem.endswith("audio"):
        stem = stem[: -len("audio")]
    return stem


def load_test_speaker_set() -> set[str]:
    """The 16 held-out DECTE test speakers, from the mitigation test CSV."""
    df = pd.read_csv(DECTE_TEST_CSV)
    speakers = set(df["speaker"].dropna().astype(str).str.strip().str.lower().unique())
    return speakers


def build_training_features(refresh: bool) -> tuple[np.ndarray, np.ndarray]:
    """Extract or load cached LFCC features for the leakage-filtered
    AuralGuard training set. Returns (X, y) with AuralGuard's convention
    y=0 bonafide / y=1 spoof.

    Fixes vs the first (bad) run:
      - Resolves relative auralguard file_paths against AURALGUARD_ROOT.
      - Speaker-column-first + file_path-derived leakage filter.
      - Aborts if 0 rows filtered (leakage protection has silently failed).
      - Path existence precheck; aborts if >5% of paths are missing.
    """
    if TRAIN_FEATURES_CACHE.exists() and not refresh:
        cached = np.load(TRAIN_FEATURES_CACHE, allow_pickle=False)
        print(f"Loaded cached training features from {TRAIN_FEATURES_CACHE} "
              f"({cached['X'].shape[0]} rows, {cached['X'].shape[1]} feats)")
        return cached["X"], cached["y"]

    print(f"Reading AuralGuard train CSV: {AURALGUARD_TRAIN_CSV}")
    df = pd.read_csv(AURALGUARD_TRAIN_CSV)
    n_before = len(df)

    # ---- Resolve per-row speaker: prefer speaker column, else derive from file_path ----
    def _row_speaker(row):
        s = str(row.get("speaker", "")).strip().lower()
        if s and s != "nan":
            return s
        return speaker_from_path(str(row.get("file_path", "")))

    df["train_speaker_resolved"] = df.apply(_row_speaker, axis=1)

    # ---- Leakage filter ----
    test_speakers = load_test_speaker_set()
    print()
    print(f"Held-out DECTE test speakers ({len(test_speakers)}):")
    for s in sorted(test_speakers):
        print(f"  {s}")

    mask_drop = df["train_speaker_resolved"].isin(test_speakers)
    dec_before = (
        int((df["dataset"].astype(str).str.upper() == "DECTE").sum())
        if "dataset" in df.columns else -1
    )
    removed_counts = df.loc[mask_drop, "train_speaker_resolved"].value_counts()
    df = df[~mask_drop].reset_index(drop=True)
    matched_rows = int(mask_drop.sum())
    dec_after = (
        int((df["dataset"].astype(str).str.upper() == "DECTE").sum())
        if "dataset" in df.columns else -1
    )

    print()
    print(f"Rows in AuralGuard train CSV     : {n_before}")
    print(f"Rows removed (leakage protection): {matched_rows}")
    if matched_rows:
        print("Per-speaker removal counts:")
        for spk, cnt in removed_counts.items():
            print(f"  {spk:<25} {cnt}")
    if dec_before >= 0:
        print(f"DECTE rows before filter         : {dec_before}")
        print(f"DECTE rows after filter          : {dec_after}")
    print(f"Rows kept for training           : {len(df)}")

    if matched_rows == 0:
        print()
        print("ABORT: leakage filter matched 0 rows. Inspect the "
              "train_speaker_resolved column vs the test speaker set "
              "above. No training will happen and no cache will be written.")
        sys.exit(2)

    # ---- Resolve absolute audio paths ----
    df["abs_path"] = df["file_path"].astype(str).apply(resolve_train_path)

    # ---- Existence precheck ----
    print()
    print("Checking training audio path existence ...")
    exists_mask = df["abs_path"].apply(lambda p: Path(p).exists())
    n_exists = int(exists_mask.sum())
    n_missing = int((~exists_mask).sum())
    frac_missing = n_missing / max(len(df), 1)
    print(f"Training audio files existing    : {n_exists}")
    print(f"Training audio files MISSING     : {n_missing}  ({100*frac_missing:.2f}%)")
    if n_missing:
        missing_sample = df.loc[~exists_mask, "abs_path"].head(10).tolist()
        print("First 10 missing paths:")
        for m in missing_sample:
            print(f"  {m}")
    if frac_missing > 0.05:
        print()
        print(f"ABORT: {100*frac_missing:.2f}% of training audio paths are missing "
              "(> 5%). Fix AURALGUARD_ROOT or path resolution before continuing. "
              "No feature extraction attempted; no cache written.")
        sys.exit(3)
    df = df[exists_mask].reset_index(drop=True)

    # ---- Extract features ----
    paths = df["abs_path"].tolist()
    y = df["binary_label"].astype(int).to_numpy()

    X = extract_features_from_paths(paths, desc="train LFCC")
    good = ~np.isnan(X).any(axis=1)
    dropped = int((~good).sum())
    if dropped:
        print(f"Dropped {dropped} rows with unreadable audio during extraction.")
    X, y = X[good], y[good]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(TRAIN_FEATURES_CACHE, X=X, y=y)
    print(f"Cached training features to {TRAIN_FEATURES_CACHE}")
    return X, y


# ---------- eval-set feature extraction ----------

def collect_decte_paths() -> tuple[list[str], list[str]]:
    """Bonafide = source_audio_path, spoof = output_path, from every
    successful xtts_v2 row in the DECTE mitigation test manifest.
    Deduplicated, order preserved."""
    rows = [json.loads(l) for l in DECTE_TEST_MANIFEST.open(encoding="utf-8")]
    bon = [
        r["source_audio_path"] for r in rows
        if r.get("generator_name") == "xtts_v2" and r.get("success", False)
        and r.get("source_audio_path") and Path(r["source_audio_path"]).exists()
    ]
    spf = [
        r["output_path"] for r in rows
        if r.get("generator_name") == "xtts_v2" and r.get("success", False)
    ]
    return list(dict.fromkeys(bon)), list(dict.fromkeys(spf))


def collect_vctk_xtts_paths() -> tuple[list[str], list[str]]:
    """VCTK bonafide pool (all unique source_audio_paths across the whole
    VCTK manifest -- matches Entry 5/6 methodology) vs XTTS spoofs only."""
    rows = [json.loads(l) for l in VCTK_MANIFEST.open(encoding="utf-8")]
    bon = [
        r["source_audio_path"] for r in rows
        if r.get("success", False)
        and r.get("source_audio_path") and Path(r["source_audio_path"]).exists()
    ]
    spf = [
        r["output_path"] for r in rows
        if r.get("generator_name") == "xtts_v2" and r.get("success", False)
    ]
    return list(dict.fromkeys(bon)), list(dict.fromkeys(spf))


def score_paths(paths: list[str], model: Pipeline, desc: str) -> np.ndarray:
    """Extract raw LFCC features for `paths`, drop unreadables, then
    pipeline-score (scaler + LR) and return P(bonafide) as float64."""
    Xf = extract_features_from_paths(paths, desc=desc)
    Xf = Xf[~np.isnan(Xf).any(axis=1)]
    bon_col = int(list(model.classes_).index(0))
    return model.predict_proba(Xf)[:, bon_col].astype(np.float64)


# ---------- bootstrap ----------

def bootstrap_gap(
    dec_bon: np.ndarray, dec_spf: np.ndarray,
    vctk_bon: np.ndarray, vctk_spf: np.ndarray,
    n_iters: int, seed: int, ci_level: float = 0.95,
) -> dict:
    """Joint bootstrap: on each iteration, resample all four arrays
    independently with replacement (each at its original size). Records
    per-corpus EER and their difference. Same design as scripts/06."""
    rng = np.random.default_rng(seed)
    dec_eers = np.empty(n_iters); vctk_eers = np.empty(n_iters); gaps = np.empty(n_iters)
    for i in range(n_iters):
        db = rng.choice(dec_bon, size=len(dec_bon), replace=True)
        ds = rng.choice(dec_spf, size=len(dec_spf), replace=True)
        vb = rng.choice(vctk_bon, size=len(vctk_bon), replace=True)
        vs = rng.choice(vctk_spf, size=len(vctk_spf), replace=True)
        dec, _ = compute_eer(db, ds)
        vc, _ = compute_eer(vb, vs)
        dec_eers[i], vctk_eers[i], gaps[i] = dec, vc, dec - vc

    alpha = (1.0 - ci_level) / 2.0
    def pct(a):
        return (float(np.percentile(a, alpha * 100)),
                float(np.percentile(a, (1.0 - alpha) * 100)),
                float(np.percentile(a, 50)))
    return {"dec": pct(dec_eers), "vctk": pct(vctk_eers), "gap": pct(gaps)}


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="LFCC + LR second-detector replication.")
    parser.add_argument("--refresh-features", action="store_true",
                        help="Re-extract training features even if cache exists.")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("LFCC + LR SECOND-DETECTOR REPLICATION (Entry 8)")
    print("=" * 60)

    # 1. Build (or load cached) training features
    X_train, y_train = build_training_features(refresh=args.refresh_features)
    print(f"Training matrix                  : X={X_train.shape}, y bincount={np.bincount(y_train)}")

    # 2. Fit StandardScaler + LogisticRegression
    print("\nFitting StandardScaler + LogisticRegression(class_weight='balanced')...")
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(
            class_weight="balanced", C=1.0, max_iter=1000,
            solver="lbfgs", random_state=SEED,
        )),
    ])
    model.fit(X_train, y_train)
    print(f"model.named_steps['lr'].classes_ = {model.named_steps['lr'].classes_}")
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

    # 3. Score DECTE + VCTK eval sets (through the full scaler+LR pipeline)
    print("\nCollecting eval paths ...")
    dec_bon_paths, dec_spf_paths = collect_decte_paths()
    vctk_bon_paths, vctk_spf_paths = collect_vctk_xtts_paths()
    print(f"  DECTE : {len(dec_bon_paths)} bon paths, {len(dec_spf_paths)} spf paths")
    print(f"  VCTK  : {len(vctk_bon_paths)} bon paths, {len(vctk_spf_paths)} spf paths")

    print("\nExtracting features and scoring (scaler + LR) ...")
    dec_bon = score_paths(dec_bon_paths, model, desc="DECTE bonafide")
    dec_spf = score_paths(dec_spf_paths, model, desc="DECTE xtts")
    vctk_bon = score_paths(vctk_bon_paths, model, desc="VCTK  bonafide")
    vctk_spf = score_paths(vctk_spf_paths, model, desc="VCTK  xtts")
    print(f"  DECTE scores : {len(dec_bon)} bon, {len(dec_spf)} spf")
    print(f"  VCTK  scores : {len(vctk_bon)} bon, {len(vctk_spf)} spf")

    # 4. Point metrics
    dec_m = compute_metrics(dec_bon, dec_spf)
    vctk_m = compute_metrics(vctk_bon, vctk_spf)
    point_gap = dec_m.eer - vctk_m.eer

    # 5. Bootstrap CIs
    print(f"\nBootstrap ({BOOTSTRAP_ITERS} iters, seed {SEED}) ...")
    ci = bootstrap_gap(dec_bon, dec_spf, vctk_bon, vctk_spf, BOOTSTRAP_ITERS, SEED)

    # 6. Save CSV
    rows_out = [
        {"row": "LR_DECTE_XTTS",
         "n_bonafide": int(dec_m.n_bonafide), "n_spoof": int(dec_m.n_spoof),
         "eer_percent": round(dec_m.eer, 3),
         "eer_ci95_lo": round(ci["dec"][0], 3), "eer_ci95_hi": round(ci["dec"][1], 3),
         "eer_boot_median": round(ci["dec"][2], 3),
         "auc": round(dec_m.auc, 4),
         "accuracy": round(dec_m.accuracy, 4),
         "far_percent": round(dec_m.false_accept_rate, 3),
         "frr_percent": round(dec_m.false_reject_rate, 3)},
        {"row": "LR_VCTK_XTTS",
         "n_bonafide": int(vctk_m.n_bonafide), "n_spoof": int(vctk_m.n_spoof),
         "eer_percent": round(vctk_m.eer, 3),
         "eer_ci95_lo": round(ci["vctk"][0], 3), "eer_ci95_hi": round(ci["vctk"][1], 3),
         "eer_boot_median": round(ci["vctk"][2], 3),
         "auc": round(vctk_m.auc, 4),
         "accuracy": round(vctk_m.accuracy, 4),
         "far_percent": round(vctk_m.false_accept_rate, 3),
         "frr_percent": round(vctk_m.false_reject_rate, 3)},
        {"row": "LR_GAP_DECTE_minus_VCTK_pp",
         "n_bonafide": None, "n_spoof": None,
         "eer_percent": round(point_gap, 3),
         "eer_ci95_lo": round(ci["gap"][0], 3), "eer_ci95_hi": round(ci["gap"][1], 3),
         "eer_boot_median": round(ci["gap"][2], 3),
         "auc": None, "accuracy": None,
         "far_percent": None, "frr_percent": None},
    ]
    out_df = pd.DataFrame(rows_out)
    out_df.to_csv(RESULTS_CSV, index=False)

    # 7. Print + verdict
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(out_df.to_string(index=False))

    print()
    dlo, dhi, _ = ci["gap"]
    print(f"LR DECTE-vs-VCTK XTTS gap : {point_gap:+.3f}pp  95% CI [{dlo:+.3f}, {dhi:+.3f}]pp")
    if dlo > 0:
        print("VERDICT: gap CI entirely POSITIVE (DECTE > VCTK).")
        print("  The DECTE-vs-VCTK XTTS gap REPLICATES on an LFCC+LR detector")
        print("  at 95% -- the gap is not specific to the AASIST architecture.")
    elif dhi < 0:
        print("VERDICT: gap CI entirely NEGATIVE (VCTK > DECTE for LR).")
        print("  Opposite direction from AASIST -- unexpected; investigate.")
    else:
        print("VERDICT: gap CI includes 0.")
        print("  LR cannot statistically confirm the DECTE-vs-VCTK gap at 95%.")
        print("  Report cautiously; may indicate LR is too weak to resolve the effect.")
    print(f"\nSaved to {RESULTS_CSV} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
