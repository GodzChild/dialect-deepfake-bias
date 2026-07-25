#!/usr/bin/env python3
"""
Script 04: Balanced Generator Comparison (xtts_v2 vs openvoice_v2)
===================================================================
Reads the already-scored Phase 2 predictions and computes matched-N
detector metrics for each generator, plus bootstrap 95% confidence
intervals on EER. Does NOT rescore any audio and does NOT touch the
detector code.

Method:
  - Uses all bonafide rows in results/detector_predictions.csv
  - Uses all openvoice_v2 spoof rows (target: 100 after the large run)
  - Randomly downsamples xtts_v2 spoof rows (without replacement, seed 42)
    to match the openvoice_v2 count -> matched-N comparison
  - Metrics via src/evaluation/metrics.compute_metrics
  - 95% CI on EER via non-parametric bootstrap (resample bonafide and
    spoof arrays with replacement, 1000 iterations, seed 42)

Output:
  - results/balanced_generator_comparison.csv (one row per generator,
    gitignored via existing results/ rule)
  - clean table printed to terminal

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/04_balanced_generator_comparison.py

Optional args: --predictions, --output, --bootstrap-iters, --seed.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.metrics import compute_metrics, compute_eer


def bootstrap_eer_ci(
    bonafide: np.ndarray,
    spoof: np.ndarray,
    n_iters: int = 1000,
    seed: int = 42,
    ci_level: float = 0.95,
) -> tuple[float, float, float]:
    """Non-parametric bootstrap 95% CI on EER.

    Resamples bonafide and spoof arrays independently with replacement
    (same original sizes) each iteration; returns (median, lo, hi).
    """
    rng = np.random.default_rng(seed)
    n_bon = len(bonafide)
    n_spf = len(spoof)
    eers = np.empty(n_iters, dtype=np.float64)
    for i in range(n_iters):
        bon = rng.choice(bonafide, size=n_bon, replace=True)
        spf = rng.choice(spoof, size=n_spf, replace=True)
        eer_pct, _ = compute_eer(bon, spf)
        eers[i] = eer_pct

    alpha = (1.0 - ci_level) / 2.0
    lo = float(np.percentile(eers, alpha * 100))
    hi = float(np.percentile(eers, (1.0 - alpha) * 100))
    med = float(np.percentile(eers, 50))
    return med, lo, hi


def evaluate_generator(
    name: str,
    bonafide: np.ndarray,
    spoof: np.ndarray,
    bootstrap_iters: int,
    seed: int,
) -> dict:
    m = compute_metrics(bonafide, spoof)
    med, lo, hi = bootstrap_eer_ci(
        bonafide, spoof, n_iters=bootstrap_iters, seed=seed
    )
    return {
        "generator": name,
        "n_bonafide": int(m.n_bonafide),
        "n_spoof": int(m.n_spoof),
        "eer_percent": round(m.eer, 3),
        "eer_ci95_lo": round(lo, 3),
        "eer_ci95_hi": round(hi, 3),
        "eer_boot_median": round(med, 3),
        "auc": round(m.auc, 4),
        "accuracy": round(m.accuracy, 4),
        "far_percent": round(m.false_accept_rate, 3),
        "frr_percent": round(m.false_reject_rate, 3),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Balanced xtts_v2 vs openvoice_v2 comparison from existing predictions"
    )
    parser.add_argument("--predictions", type=str,
                        default="results/detector_predictions.csv")
    parser.add_argument("--output", type=str,
                        default="results/balanced_generator_comparison.csv")
    parser.add_argument("--bootstrap-iters", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        print(f"ERROR: predictions file not found: {pred_path}")
        print("Run scripts/03_run_detectors.py first to generate it.")
        sys.exit(1)

    df = pd.read_csv(pred_path)
    # Drop any NaN scores from failed inference (should already be filtered
    # by run_detection, but guard against stale CSVs).
    df = df.dropna(subset=["score"])

    bonafide = df[df["label"] == 1]["score"].to_numpy()
    xtts_pool = df[(df["generator_name"] == "xtts_v2") & (df["label"] == 0)]["score"].to_numpy()
    openvoice = df[(df["generator_name"] == "openvoice_v2") & (df["label"] == 0)]["score"].to_numpy()

    if len(openvoice) == 0:
        print("ERROR: no openvoice_v2 spoof rows in predictions.")
        print(f"       Rows found: bonafide={len(bonafide)}, xtts_pool={len(xtts_pool)}, openvoice=0")
        sys.exit(1)

    n = len(openvoice)
    if len(xtts_pool) < n:
        print(f"ERROR: xtts_v2 pool ({len(xtts_pool)}) smaller than openvoice_v2 ({n}); "
              "cannot match-N via downsampling.")
        sys.exit(1)

    print("=" * 60)
    print("BALANCED GENERATOR COMPARISON (matched N)")
    print("=" * 60)
    print(f"Predictions file : {pred_path}")
    print(f"Bonafide rows    : {len(bonafide)}")
    print(f"XTTS pool        : {len(xtts_pool)}")
    print(f"OpenVoice rows   : {len(openvoice)}  <- target N")
    print(f"Downsampling XTTS to {n} (without replacement, seed={args.seed})")
    print(f"Bootstrap iters  : {args.bootstrap_iters} (seed={args.seed})")

    rng = np.random.default_rng(args.seed)
    xtts_sample = rng.choice(xtts_pool, size=n, replace=False)

    rows = [
        evaluate_generator("xtts_v2", bonafide, xtts_sample,
                           bootstrap_iters=args.bootstrap_iters,
                           seed=args.seed),
        evaluate_generator("openvoice_v2", bonafide, openvoice,
                           bootstrap_iters=args.bootstrap_iters,
                           # Different seed offset to avoid identical
                           # bootstrap index sequences across generators.
                           seed=args.seed + 1),
    ]
    out_df = pd.DataFrame(rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    display_cols = [
        "generator", "n_bonafide", "n_spoof",
        "eer_percent", "eer_ci95_lo", "eer_ci95_hi",
        "auc", "accuracy", "far_percent", "frr_percent",
    ]
    print(out_df[display_cols].to_string(index=False))

    print()
    print(f"Saved to {out_path} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
