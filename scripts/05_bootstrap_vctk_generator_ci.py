#!/usr/bin/env python3
"""
Script 05: Bootstrap 95% CIs for VCTK Generator Comparison (Entry 6)
=====================================================================
Reads the already-scored VCTK Phase 2 predictions and computes 95%
bootstrap confidence intervals on EER for each generator subset
(xtts_v2, openvoice_v2), so the Entry 5 point estimates can be
reported with defensible uncertainty bounds.

Method:
  - Load results/vctk/detector_predictions.csv (from
    `python scripts/03_run_detectors.py --manifest data/generated_spoofs_vctk/manifest.jsonl
       --output-dir results/vctk --corpus vctk_english_control`).
  - Restrict to detector_name == aasist.
  - Bonafide pool: ALL bonafide rows in that CSV (120 unique originals,
    per Entry 5's overlap check).
  - For each generator in [xtts_v2, openvoice_v2]:
      - spoofs = rows with generator_name == <gen> AND label == 0
      - compute EER + AUC + accuracy + FAR + FRR via metrics.compute_metrics
      - 95% CI on EER via 1000 non-parametric bootstrap resamples
        (bonafide + spoof resampled independently with replacement,
        same-sized draws each iteration, seed 42 base with per-gen offset).

Output:
  - results/vctk/vctk_generator_bootstrap_ci.csv (one row per generator)
  - clean summary printed to terminal

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/05_bootstrap_vctk_generator_ci.py

Does NOT: rescore audio, touch data/, manifests, checkpoints, or
generated audio. Only reads predictions CSV and writes to results/.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.metrics import compute_metrics, compute_eer


GENERATORS = ("xtts_v2", "openvoice_v2")


def bootstrap_eer_ci(
    bonafide: np.ndarray,
    spoof: np.ndarray,
    n_iters: int = 1000,
    seed: int = 42,
    ci_level: float = 0.95,
) -> tuple[float, float, float]:
    """Non-parametric bootstrap CI on EER.

    Resamples bonafide and spoof arrays independently with replacement
    (each at its original size), computes EER per iteration, returns
    (median, lo, hi) at the requested confidence level.
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
        description="Bootstrap 95% CIs on EER for VCTK xtts_v2 vs openvoice_v2"
    )
    parser.add_argument(
        "--predictions", type=str,
        default="results/vctk/detector_predictions.csv",
    )
    parser.add_argument(
        "--output", type=str,
        default="results/vctk/vctk_generator_bootstrap_ci.csv",
    )
    parser.add_argument("--detector-name", type=str, default="aasist")
    parser.add_argument("--bootstrap-iters", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        print(f"ERROR: predictions file not found: {pred_path}")
        print("Run the VCTK Phase 2 evaluation first:")
        print("  python scripts/03_run_detectors.py \\")
        print("    --manifest data/generated_spoofs_vctk/manifest.jsonl \\")
        print("    --output-dir results/vctk \\")
        print("    --corpus vctk_english_control")
        sys.exit(1)

    df = pd.read_csv(pred_path)
    df = df.dropna(subset=["score"])
    if "detector_name" in df.columns:
        df = df[df["detector_name"] == args.detector_name]

    bonafide = df[df["label"] == 1]["score"].to_numpy()
    gen_spoofs = {
        gen: df[(df["generator_name"] == gen) & (df["label"] == 0)]["score"].to_numpy()
        for gen in GENERATORS
    }

    if len(bonafide) == 0:
        print("ERROR: no bonafide rows in predictions.")
        sys.exit(1)
    missing = [g for g, s in gen_spoofs.items() if len(s) == 0]
    if missing:
        print(f"ERROR: no spoof rows for generator(s): {missing}")
        sys.exit(1)

    print("=" * 60)
    print("VCTK GENERATOR BOOTSTRAP CI")
    print("=" * 60)
    print(f"Predictions file : {pred_path}")
    print(f"Detector         : {args.detector_name}")
    print(f"Bonafide rows    : {len(bonafide)}")
    for gen in GENERATORS:
        print(f"{gen:<14} spoof rows: {len(gen_spoofs[gen])}")
    print(f"Bootstrap iters  : {args.bootstrap_iters} (base seed={args.seed})")

    rows = []
    for offset, gen in enumerate(GENERATORS):
        rows.append(evaluate_generator(
            gen, bonafide, gen_spoofs[gen],
            bootstrap_iters=args.bootstrap_iters,
            # Per-generator seed offset avoids identical bootstrap index
            # sequences across generators.
            seed=args.seed + offset,
        ))
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
