#!/usr/bin/env python3
"""
Script 06: Bootstrap 95% CI for the XTTS DECTE-vs-VCTK Corpus Gap
==================================================================
Load-bearing statistical test for the *thesis headline* claim:

  Same detector (AuralGuard-AASIST), same generator (XTTS v2),
  different speech domain (DECTE dialectal interview-style speech vs
  VCTK English-control studio-read speech). Does the DECTE EER exceed
  the VCTK EER by a statistically supported margin?

Point estimates already in the log:
  DECTE XTTS v2 EER = 34.63% (Entry 2, balanced 100-vs-100 subsample)
  VCTK  XTTS v2 EER = 21.83% (Entry 5, full 100 XTTS samples)
  Naive gap         = +12.8pp (DECTE harder)

This script attaches 95% bootstrap CIs to both cells and to their gap.

Method
------
  - Reuses two existing prediction CSVs (no rescoring, no regeneration):
      results/detector_predictions.csv        (DECTE, from Entry 2 run)
      results/vctk/detector_predictions.csv   (VCTK, from Entry 5 run)
  - Filters to detector_name == "aasist" and generator_name == "xtts_v2".
  - DECTE arm: downsamples XTTS spoofs to n=100 using seed 42 to
    reproduce the exact balanced sample used in Entry 2 (bonafide pool
    is DECTE's full 216).
  - VCTK arm: uses all 100 XTTS spoofs (Entry 5 slate) and the full VCTK
    bonafide pool (120 unique matched originals per Entry 5).
  - 1000 bootstrap iterations, base seed 42. Each iteration
    independently resamples each corpus's bonafide + spoof arrays with
    replacement (same original sizes), computes EER per corpus, and
    records the gap. Independent resampling is appropriate because the
    two corpora share zero speakers and zero files.
  - Reports for each corpus: n_bonafide, n_spoof, EER, AUC, 95% CI on
    EER. Reports for the gap: point estimate, 95% CI, whether 0 is
    inside the CI (i.e. whether the gap is statistically supported).

Output
------
  - results/xtts_corpus_gap_bootstrap_ci.csv (three rows: DECTE, VCTK, GAP)
  - clean terminal summary + verdict line

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/06_bootstrap_xtts_corpus_gap.py

Does not modify data, manifests, checkpoints, existing configs, or
detector code.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.metrics import compute_metrics, compute_eer


DECTE_XTTS_N = 100  # matches Entry 2's balanced downsample size


def load_corpus_arrays(
    predictions_path: Path,
    detector_name: str,
    generator_name: str,
    downsample_spoof_n: int | None,
    downsample_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (bonafide_scores, spoof_scores) arrays for one corpus.

    If `downsample_spoof_n` is not None and the spoof pool is larger,
    downsamples to that size WITHOUT replacement using
    `numpy.random.default_rng(downsample_seed).choice`. This reproduces
    Entry 2's balanced XTTS sample when applied to the DECTE arm.
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"predictions file not found: {predictions_path}")

    df = pd.read_csv(predictions_path).dropna(subset=["score"])
    if "detector_name" in df.columns:
        df = df[df["detector_name"] == detector_name]

    bonafide = df[df["label"] == 1]["score"].to_numpy()
    spoof = df[
        (df["generator_name"] == generator_name) & (df["label"] == 0)
    ]["score"].to_numpy()

    if downsample_spoof_n is not None and len(spoof) > downsample_spoof_n:
        rng = np.random.default_rng(downsample_seed)
        spoof = rng.choice(spoof, size=downsample_spoof_n, replace=False)

    return bonafide, spoof


def bootstrap_gap(
    dec_bon: np.ndarray, dec_spf: np.ndarray,
    vctk_bon: np.ndarray, vctk_spf: np.ndarray,
    n_iters: int = 1000, seed: int = 42, ci_level: float = 0.95,
) -> dict:
    """Joint bootstrap: on each iteration, resample all four arrays
    independently with replacement, compute EER per corpus, record the
    gap (DECTE - VCTK). Returns dict with per-corpus and gap CIs.
    """
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
        return (
            float(np.percentile(a, alpha * 100)),
            float(np.percentile(a, (1.0 - alpha) * 100)),
            float(np.percentile(a, 50)),
        )
    dec_lo, dec_hi, dec_med = pct(dec_eers)
    vctk_lo, vctk_hi, vctk_med = pct(vctk_eers)
    gap_lo, gap_hi, gap_med = pct(gaps)
    return {
        "dec": (dec_lo, dec_hi, dec_med),
        "vctk": (vctk_lo, vctk_hi, vctk_med),
        "gap": (gap_lo, gap_hi, gap_med),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap 95% CI for the XTTS DECTE-vs-VCTK corpus gap"
    )
    parser.add_argument(
        "--decte-predictions", type=str,
        default="results/detector_predictions.csv",
        help="Predictions CSV from the DECTE Phase 2 run.",
    )
    parser.add_argument(
        "--vctk-predictions", type=str,
        default="results/vctk/detector_predictions.csv",
        help="Predictions CSV from the VCTK Phase 2 run.",
    )
    parser.add_argument(
        "--output", type=str,
        default="results/xtts_corpus_gap_bootstrap_ci.csv",
    )
    parser.add_argument("--detector-name", type=str, default="aasist")
    parser.add_argument("--generator-name", type=str, default="xtts_v2")
    parser.add_argument(
        "--decte-downsample", type=int, default=DECTE_XTTS_N,
        help="Downsample DECTE XTTS spoofs to this N to match Entry 2's "
             "balanced comparison (default 100).",
    )
    parser.add_argument("--bootstrap-iters", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dec_path = Path(args.decte_predictions)
    vctk_path = Path(args.vctk_predictions)

    print("=" * 60)
    print("XTTS DECTE-vs-VCTK CORPUS GAP — BOOTSTRAP 95% CI")
    print("=" * 60)
    print(f"DECTE predictions : {dec_path}")
    print(f"VCTK predictions  : {vctk_path}")
    print(f"Detector          : {args.detector_name}")
    print(f"Generator         : {args.generator_name}")
    print(f"DECTE downsample  : {args.decte_downsample} spoofs (seed {args.seed})")
    print(f"Bootstrap iters   : {args.bootstrap_iters} (seed {args.seed})")

    try:
        dec_bon, dec_spf = load_corpus_arrays(
            dec_path, args.detector_name, args.generator_name,
            downsample_spoof_n=args.decte_downsample,
            downsample_seed=args.seed,
        )
        vctk_bon, vctk_spf = load_corpus_arrays(
            vctk_path, args.detector_name, args.generator_name,
            downsample_spoof_n=None,       # VCTK is already 100
            downsample_seed=args.seed,
        )
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Both DECTE and VCTK Phase 2 runs must have been executed first.")
        sys.exit(1)

    for label, bon, spf in (
        ("DECTE", dec_bon, dec_spf), ("VCTK", vctk_bon, vctk_spf),
    ):
        if len(bon) < 5 or len(spf) < 5:
            print(f"\nERROR: {label} arm has too few samples "
                  f"(bonafide={len(bon)}, spoof={len(spf)}).")
            sys.exit(1)

    # ---- point estimates ----
    dec_metrics = compute_metrics(dec_bon, dec_spf)
    vctk_metrics = compute_metrics(vctk_bon, vctk_spf)
    point_gap = dec_metrics.eer - vctk_metrics.eer

    # ---- joint bootstrap ----
    ci = bootstrap_gap(
        dec_bon, dec_spf, vctk_bon, vctk_spf,
        n_iters=args.bootstrap_iters, seed=args.seed,
    )
    (dec_lo, dec_hi, dec_med) = ci["dec"]
    (vctk_lo, vctk_hi, vctk_med) = ci["vctk"]
    (gap_lo, gap_hi, gap_med) = ci["gap"]

    rows = [
        {
            "row": "DECTE_XTTS",
            "n_bonafide": int(dec_metrics.n_bonafide),
            "n_spoof": int(dec_metrics.n_spoof),
            "eer_percent": round(dec_metrics.eer, 3),
            "eer_ci95_lo": round(dec_lo, 3),
            "eer_ci95_hi": round(dec_hi, 3),
            "eer_boot_median": round(dec_med, 3),
            "auc": round(dec_metrics.auc, 4),
        },
        {
            "row": "VCTK_XTTS",
            "n_bonafide": int(vctk_metrics.n_bonafide),
            "n_spoof": int(vctk_metrics.n_spoof),
            "eer_percent": round(vctk_metrics.eer, 3),
            "eer_ci95_lo": round(vctk_lo, 3),
            "eer_ci95_hi": round(vctk_hi, 3),
            "eer_boot_median": round(vctk_med, 3),
            "auc": round(vctk_metrics.auc, 4),
        },
        {
            "row": "GAP_DECTE_minus_VCTK",
            "n_bonafide": None,
            "n_spoof": None,
            "eer_percent": round(point_gap, 3),      # point-estimate gap
            "eer_ci95_lo": round(gap_lo, 3),
            "eer_ci95_hi": round(gap_hi, 3),
            "eer_boot_median": round(gap_med, 3),
            "auc": None,
        },
    ]
    out_df = pd.DataFrame(rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(out_df.to_string(index=False))

    # ---- verdict ----
    print()
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)
    print(f"DECTE XTTS 95% CI : [{dec_lo:.2f}, {dec_hi:.2f}] %")
    print(f"VCTK  XTTS 95% CI : [{vctk_lo:.2f}, {vctk_hi:.2f}] %")
    print(f"Corpus-gap 95% CI : [{gap_lo:.2f}, {gap_hi:.2f}] pp "
          f"(point estimate {point_gap:+.2f} pp)")
    if gap_lo > 0:
        print("VERDICT: DECTE-vs-VCTK XTTS gap is POSITIVE across the full CI.")
        print("  The dialect/domain gap for XTTS is statistically supported")
        print("  at 95% (0 is outside the interval).")
    elif gap_hi < 0:
        print("VERDICT: gap CI is entirely NEGATIVE (VCTK is harder).")
        print("  Unexpected direction — investigate before publishing.")
    else:
        print("VERDICT: gap CI includes 0.")
        print("  DECTE-vs-VCTK XTTS gap is NOT statistically supported at 95%.")
        print("  Report cautiously; consider larger sample sizes.")

    print()
    print(f"Saved to {out_path} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
