#!/usr/bin/env python3
"""
Script 13: LFCC + LR OpenVoice Corpus-Gap Replication (Entry 10)
=================================================================
Gives the OpenVoice reversal claim (Entry 9, AASIST-only) the same
cross-detector support the XTTS gap claim already has (Entry 6 AASIST
+ Entry 8 LFCC+LR).

Does NOT retrain -- loads the already-fitted LFCC+LR pipeline from
Entry 8 (results/second_detector_lfcc_lr/lfcc_lr_model.joblib) and
scores the OpenVoice arms of both corpora with it.

Files scored are chosen by reading `audio_path` values out of the
existing AASIST prediction CSVs, so the LR eval slice matches the
AASIST eval slice exactly file-for-file. This makes the Entry 10
LFCC+LR numbers directly comparable to Entry 9's AASIST numbers.

Method
------
  - Load fitted pipeline from Entry 8:
        results/second_detector_lfcc_lr/lfcc_lr_model.joblib
  - For each corpus (DECTE, VCTK):
      - Read the AASIST predictions CSV.
      - Collect unique bonafide audio_paths and unique openvoice_v2
        spoof audio_paths.
      - Extract 120-dim LFCC features per file (using the identical
        preprocessing + LFCC extractor from scripts/11).
      - Score through the loaded pipeline (StandardScaler -> LR),
        take P(bonafide) so higher = more real.
  - compute_metrics on each corpus (EER + AUC + accuracy + FAR + FRR).
  - Joint bootstrap (1000 iters, seed 42, independent resampling per
    arm) for per-corpus EER CIs and the DECTE-minus-VCTK gap CI.
  - Verdict:
      gap_hi < 0  -> LR replicates AASIST OpenVoice reversal (VCTK harder)
      gap_lo > 0  -> LR CONFLICTS with AASIST -- investigate
      CI includes 0 -> UNCONFIRMED cross-architecture

Output
------
  - results/lfcc_lr_openvoice_corpus_gap/lfcc_lr_openvoice_corpus_gap_bootstrap_ci.csv
    (three rows: DECTE, VCTK, GAP; same schema as scripts/12)

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/13_lfcc_lr_openvoice_corpus_gap.py

Does NOT modify: data, manifests, checkpoints, the fitted LR model,
existing results in other subdirectories, or any config/detector code.
"""

import argparse
import os
import sys
from pathlib import Path

import joblib
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
from scipy.fftpack import dct
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.evaluation.metrics import compute_metrics, compute_eer


# ---------- fixed inputs / outputs ----------

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / "results" / "second_detector_lfcc_lr" / "lfcc_lr_model.joblib"
DECTE_PREDICTIONS = REPO_ROOT / "results" / "detector_predictions.csv"
VCTK_PREDICTIONS = REPO_ROOT / "results" / "vctk" / "detector_predictions.csv"

RESULTS_DIR = REPO_ROOT / "results" / "lfcc_lr_openvoice_corpus_gap"
RESULTS_CSV = RESULTS_DIR / "lfcc_lr_openvoice_corpus_gap_bootstrap_ci.csv"

GENERATOR = "openvoice_v2"


# ---------- LFCC + preprocessing constants (KEEP IN SYNC with scripts/11) ----------

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


# ---------- audio + feature extraction (COPIED FROM scripts/11 for isolation) ----------
# Keep this block byte-for-byte in sync with scripts/11_lfcc_lr_second_detector.py.
# We intentionally duplicate (not import) because Python cannot import a module
# whose name starts with a digit without importlib gymnastics.

def load_audio_fixed(path: str) -> np.ndarray:
    """Match src/evaluation/detectors.py::AASISTDetector._load_audio exactly."""
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
    stft = librosa.stft(
        wav, n_fft=N_FFT, hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH, window="hann",
    )
    power = (np.abs(stft) ** 2).astype(np.float32)
    filt = _FB @ power
    log_e = np.log(np.maximum(filt, 1e-10)).astype(np.float32)
    cepstral = dct(log_e, axis=0, type=2, norm="ortho")[:N_LFCC]
    return cepstral.astype(np.float32)


def utterance_features(wav: np.ndarray) -> np.ndarray:
    lfcc = compute_lfcc(wav)
    delta1 = librosa.feature.delta(lfcc, order=1)
    delta2 = librosa.feature.delta(lfcc, order=2)
    feats = np.concatenate([lfcc, delta1, delta2], axis=0)
    return np.concatenate([feats.mean(axis=1), feats.std(axis=1)]).astype(np.float32)


def extract_features_from_paths(paths: list[str], desc: str) -> np.ndarray:
    X = np.full((len(paths), 120), np.nan, dtype=np.float32)
    for i, path in enumerate(tqdm(paths, desc=desc)):
        try:
            wav = load_audio_fixed(path)
            X[i] = utterance_features(wav)
        except Exception as e:
            tqdm.write(f"  ERROR {path}: {e}")
    return X


# ---------- path collection (from existing AASIST prediction CSVs) ----------

def collect_paths_from_predictions(
    pred_csv: Path, generator_name: str, detector_name: str = "aasist",
) -> tuple[list[str], list[str]]:
    """From an existing AASIST predictions CSV, return:
      - unique bonafide audio_paths (label==1), preserving first-seen order
      - unique spoof audio_paths (label==0 AND generator_name==<generator>)
    So the LR eval slice matches the AASIST eval slice file-for-file.
    """
    df = pd.read_csv(pred_csv).dropna(subset=["score"])
    if "detector_name" in df.columns:
        df = df[df["detector_name"] == detector_name]
    bon = list(dict.fromkeys(df[df["label"] == 1]["audio_path"].astype(str).tolist()))
    spf = list(dict.fromkeys(
        df[(df["label"] == 0) & (df["generator_name"] == generator_name)]
        ["audio_path"].astype(str).tolist()
    ))
    return bon, spf


def score_paths(paths: list[str], model, desc: str) -> np.ndarray:
    """Extract LFCC features and score through the loaded pipeline.
    Returns P(bonafide) as float64. Drops rows that fail extraction."""
    Xf = extract_features_from_paths(paths, desc=desc)
    Xf = Xf[~np.isnan(Xf).any(axis=1)]
    bon_col = int(list(model.classes_).index(0))
    return model.predict_proba(Xf)[:, bon_col].astype(np.float64)


# ---------- joint bootstrap (mirror of scripts/12) ----------

def bootstrap_gap(
    dec_bon: np.ndarray, dec_spf: np.ndarray,
    vctk_bon: np.ndarray, vctk_spf: np.ndarray,
    n_iters: int = BOOTSTRAP_ITERS, seed: int = SEED, ci_level: float = 0.95,
) -> dict:
    rng = np.random.default_rng(seed)
    dec_eers = np.empty(n_iters, dtype=np.float64)
    vctk_eers = np.empty(n_iters, dtype=np.float64)
    gaps = np.empty(n_iters, dtype=np.float64)

    for i in range(n_iters):
        db = rng.choice(dec_bon, size=len(dec_bon), replace=True)
        ds = rng.choice(dec_spf, size=len(dec_spf), replace=True)
        vb = rng.choice(vctk_bon, size=len(vctk_bon), replace=True)
        vs = rng.choice(vctk_spf, size=len(vctk_spf), replace=True)
        dec_eer, _ = compute_eer(db, ds)
        vctk_eer, _ = compute_eer(vb, vs)
        dec_eers[i] = dec_eer
        vctk_eers[i] = vctk_eer
        gaps[i] = dec_eer - vctk_eer

    alpha = (1.0 - ci_level) / 2.0
    def pct(a):
        return (float(np.percentile(a, alpha * 100)),
                float(np.percentile(a, (1.0 - alpha) * 100)),
                float(np.percentile(a, 50)))
    return {"dec": pct(dec_eers), "vctk": pct(vctk_eers), "gap": pct(gaps)}


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(
        description="LFCC+LR OpenVoice corpus-gap replication (Entry 10)."
    )
    parser.add_argument("--model", type=str, default=str(MODEL_PATH))
    parser.add_argument("--decte-predictions", type=str, default=str(DECTE_PREDICTIONS))
    parser.add_argument("--vctk-predictions", type=str, default=str(VCTK_PREDICTIONS))
    parser.add_argument("--output", type=str, default=str(RESULTS_CSV))
    parser.add_argument("--bootstrap-iters", type=int, default=BOOTSTRAP_ITERS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    print("=" * 60)
    print("LFCC+LR OPENVOICE CORPUS-GAP REPLICATION (Entry 10)")
    print("=" * 60)

    model_path = Path(args.model)
    dec_path = Path(args.decte_predictions)
    vctk_path = Path(args.vctk_predictions)
    for label, p_ in [("LR model", model_path),
                      ("DECTE predictions", dec_path),
                      ("VCTK predictions", vctk_path)]:
        if not p_.exists():
            print(f"ERROR: {label} not found: {p_}")
            sys.exit(1)
    print(f"LR model         : {model_path}")
    print(f"DECTE predictions: {dec_path}")
    print(f"VCTK predictions : {vctk_path}")
    print(f"Bootstrap iters  : {args.bootstrap_iters} (seed {args.seed})")

    # Load LR pipeline
    model = joblib.load(model_path)
    print(f"model.classes_   : {list(model.classes_)}")
    if list(model.classes_) != [0, 1]:
        print("ERROR: model.classes_ is not [0, 1]; bonafide column would be wrong.")
        sys.exit(2)

    # Collect audio paths from existing AASIST predictions
    dec_bon_paths, dec_spf_paths = collect_paths_from_predictions(dec_path, GENERATOR)
    vctk_bon_paths, vctk_spf_paths = collect_paths_from_predictions(vctk_path, GENERATOR)

    print()
    print(f"DECTE paths: {len(dec_bon_paths)} bonafide, {len(dec_spf_paths)} openvoice spoof")
    print(f"VCTK  paths: {len(vctk_bon_paths)} bonafide, {len(vctk_spf_paths)} openvoice spoof")

    for label, bon, spf in (
        ("DECTE", dec_bon_paths, dec_spf_paths),
        ("VCTK",  vctk_bon_paths, vctk_spf_paths),
    ):
        if len(bon) < 5 or len(spf) < 5:
            print(f"ERROR: {label} has too few files "
                  f"(bonafide={len(bon)}, spoof={len(spf)}).")
            sys.exit(3)

    # Extract features + score through pipeline
    print("\nExtracting features + scoring (scaler + LR) ...")
    dec_bon = score_paths(dec_bon_paths, model, desc="DECTE bonafide")
    dec_spf = score_paths(dec_spf_paths, model, desc="DECTE openvoice")
    vctk_bon = score_paths(vctk_bon_paths, model, desc="VCTK  bonafide")
    vctk_spf = score_paths(vctk_spf_paths, model, desc="VCTK  openvoice")
    print(f"  DECTE scores : {len(dec_bon)} bon, {len(dec_spf)} spf")
    print(f"  VCTK  scores : {len(vctk_bon)} bon, {len(vctk_spf)} spf")

    for label, bon, spf in (
        ("DECTE", dec_bon, dec_spf),
        ("VCTK",  vctk_bon, vctk_spf),
    ):
        if len(bon) < 5 or len(spf) < 5:
            print(f"ERROR: {label} has too few scores after feature-extraction failures "
                  f"(bonafide={len(bon)}, spoof={len(spf)}).")
            sys.exit(4)

    # Point metrics
    dec_m = compute_metrics(dec_bon, dec_spf)
    vctk_m = compute_metrics(vctk_bon, vctk_spf)
    point_gap = dec_m.eer - vctk_m.eer

    # Joint bootstrap
    print(f"\nBootstrap ({args.bootstrap_iters} iters, seed {args.seed}) ...")
    ci = bootstrap_gap(
        dec_bon, dec_spf, vctk_bon, vctk_spf,
        n_iters=args.bootstrap_iters, seed=args.seed,
    )
    (dec_lo, dec_hi, dec_med) = ci["dec"]
    (vctk_lo, vctk_hi, vctk_med) = ci["vctk"]
    (gap_lo, gap_hi, gap_med) = ci["gap"]

    # Save CSV
    rows = [
        {"row": "LR_DECTE_OPENVOICE",
         "n_bonafide": int(dec_m.n_bonafide), "n_spoof": int(dec_m.n_spoof),
         "eer_percent": round(dec_m.eer, 3),
         "eer_ci95_lo": round(dec_lo, 3), "eer_ci95_hi": round(dec_hi, 3),
         "eer_boot_median": round(dec_med, 3),
         "auc": round(dec_m.auc, 4),
         "accuracy": round(dec_m.accuracy, 4),
         "far_percent": round(dec_m.false_accept_rate, 3),
         "frr_percent": round(dec_m.false_reject_rate, 3)},
        {"row": "LR_VCTK_OPENVOICE",
         "n_bonafide": int(vctk_m.n_bonafide), "n_spoof": int(vctk_m.n_spoof),
         "eer_percent": round(vctk_m.eer, 3),
         "eer_ci95_lo": round(vctk_lo, 3), "eer_ci95_hi": round(vctk_hi, 3),
         "eer_boot_median": round(vctk_med, 3),
         "auc": round(vctk_m.auc, 4),
         "accuracy": round(vctk_m.accuracy, 4),
         "far_percent": round(vctk_m.false_accept_rate, 3),
         "frr_percent": round(vctk_m.false_reject_rate, 3)},
        {"row": "LR_GAP_DECTE_minus_VCTK_pp",
         "n_bonafide": None, "n_spoof": None,
         "eer_percent": round(point_gap, 3),
         "eer_ci95_lo": round(gap_lo, 3), "eer_ci95_hi": round(gap_hi, 3),
         "eer_boot_median": round(gap_med, 3),
         "auc": None, "accuracy": None,
         "far_percent": None, "frr_percent": None},
    ]
    out_df = pd.DataFrame(rows)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    # Print + verdict
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(out_df.to_string(index=False))
    print()
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)
    print(f"LR DECTE OpenVoice 95% CI : [{dec_lo:.2f}, {dec_hi:.2f}] %")
    print(f"LR VCTK  OpenVoice 95% CI : [{vctk_lo:.2f}, {vctk_hi:.2f}] %")
    print(f"LR corpus-gap     95% CI  : [{gap_lo:+.2f}, {gap_hi:+.2f}] pp "
          f"(point estimate {point_gap:+.2f} pp)")
    if gap_hi < 0:
        print("VERDICT: gap CI entirely NEGATIVE (VCTK > DECTE for LFCC+LR OpenVoice).")
        print("  The Entry 9 OpenVoice reversal REPLICATES on the LFCC+LR detector")
        print("  at 95% -- the reversal is not specific to AASIST.")
    elif gap_lo > 0:
        print("VERDICT: gap CI entirely POSITIVE (DECTE > VCTK for LFCC+LR OpenVoice).")
        print("  CONFLICT with AASIST Entry 9 -- investigate before publishing Entry 10.")
    else:
        print("VERDICT: gap CI includes 0.")
        print("  UNCONFIRMED: LFCC+LR cannot statistically resolve the OpenVoice reversal")
        print("  at 95%. Entry 9's reversal remains AASIST-only in the thesis.")
    print(f"\nSaved to {out_path} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
