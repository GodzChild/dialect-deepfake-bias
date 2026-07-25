#!/usr/bin/env python3
"""
Script 06: In-Domain Sanity Check for the Fixed AuralGuard-AASIST Detector
===========================================================================
Runs the AASISTDetector (as used by scripts/03_run_detectors.py) on the
validation set the checkpoint was trained against:

  auralguard-aasistpp/data/metadata/val_final_accent_globe_wavefake_balanced.csv

Purpose: confirm the detector-loader fix is complete. If in-domain EER is
close to the training-time val_metrics.eer (~1.7% for this checkpoint),
the high DECTE EER (35-48%) can be attributed to domain-transfer
difficulty rather than a remaining pipeline bug. Discharges the first
box on Entry 1's verification checklist in docs/THESIS_FINDINGS_LOG.md.

Usage (in the `dialectbias` env):
    conda activate dialectbias

    # Default: stratified 500 bonafide + 500 spoof (~1 min on GPU)
    python scripts/06_indomain_sanity_check.py

    # Full validation set (9,514 files, ~8 min on GPU)
    python scripts/06_indomain_sanity_check.py --full

Does not modify any code or checkpoint. Writes results to
results/indomain_sanity_metrics.csv (gitignored via results/ rule).

Label convention note: the AuralGuard CSV uses binary_label 0=bonafide,
1=spoof -- OPPOSITE of our metrics.py convention. This script translates:
rows with binary_label==0 go into the bonafide array; ==1 into the spoof
array. compute_metrics(bonafide_scores, spoof_scores) then behaves as
documented.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.detectors import AASISTDetector
from src.evaluation.metrics import compute_metrics


AURALGUARD_ROOT = Path(
    r"C:/Users/AYO/Desktop/JKU/Extra Semester/THESIS AND PRACTICAL/auralguard-aasistpp"
)
DEFAULT_VAL_CSV = AURALGUARD_ROOT / "data" / "metadata" / "val_final_accent_globe_wavefake_balanced.csv"
DEFAULT_DETECTOR_CFG = Path("configs/detectors.yaml")


def resolve_path(p) -> Path | None:
    """Resolve a file_path from the val CSV to an existing file on disk.

    Three formats occur in the CSV:
      1. Absolute Windows path (may use backslashes)
      2. Absolute path into a sibling DECTE_ASR_PROJECT folder
      3. Path relative to the auralguard-aasistpp project root
    Returns Path if it exists, else None.
    """
    p_str = str(p).replace("\\", "/")
    pp = Path(p_str)
    if pp.is_absolute():
        return pp if pp.exists() else None
    cand = AURALGUARD_ROOT / p_str
    return cand if cand.exists() else None


def stratified_class_sample(
    df: pd.DataFrame, n_per_class: int, stratify_col: str, seed: int
) -> pd.DataFrame:
    """Sample n_per_class rows from each binary_label class, stratified by
    `stratify_col` in proportion to the class's per-stratum sizes."""
    rng = np.random.default_rng(seed)
    parts = []
    for label_value in sorted(df["binary_label"].unique()):
        class_rows = df[df["binary_label"] == label_value]
        counts = class_rows[stratify_col].value_counts()
        total = counts.sum()
        picks = []
        for stratum, s_count in counts.items():
            take = max(1, int(round(s_count / total * n_per_class)))
            take = min(take, s_count)
            s_rows = class_rows[class_rows[stratify_col] == stratum]
            idx = rng.choice(len(s_rows), size=take, replace=False)
            picks.append(s_rows.iloc[idx])
        merged = pd.concat(picks, ignore_index=True)
        # Trim / top up to hit n_per_class exactly
        if len(merged) > n_per_class:
            merged = merged.sample(n=n_per_class, random_state=seed)
        elif len(merged) < n_per_class:
            extras = class_rows.drop(index=merged.index, errors="ignore")
            need = n_per_class - len(merged)
            if len(extras) >= need:
                merged = pd.concat(
                    [merged, extras.sample(n=need, random_state=seed)],
                    ignore_index=True,
                )
        parts.append(merged)
    return pd.concat(parts, ignore_index=True)


def compute_row(dataset_name: str, bonafide: np.ndarray, spoof: np.ndarray) -> dict:
    """Compute a metric row for a dataset subset. If either class is
    absent we still record counts + score stats but leave metric fields
    as NaN (so per-dataset rows for bonafide-only sources still appear)."""
    row = {
        "dataset": dataset_name,
        "n_bonafide": int(len(bonafide)),
        "n_spoof": int(len(spoof)),
        "mean_score_bonafide": float(bonafide.mean()) if len(bonafide) else float("nan"),
        "mean_score_spoof": float(spoof.mean()) if len(spoof) else float("nan"),
    }
    if len(bonafide) >= 5 and len(spoof) >= 5:
        m = compute_metrics(bonafide, spoof)
        row.update({
            "eer_percent": round(m.eer, 3),
            "auc": round(m.auc, 4),
            "accuracy": round(m.accuracy, 4),
            "far_percent": round(m.false_accept_rate, 3),
            "frr_percent": round(m.false_reject_rate, 3),
        })
    else:
        row.update({
            "eer_percent": float("nan"),
            "auc": float("nan"),
            "accuracy": float("nan"),
            "far_percent": float("nan"),
            "frr_percent": float("nan"),
        })
    return row


def verdict_for(eer_pct: float) -> str:
    if np.isnan(eer_pct):
        return "N/A"
    if eer_pct <= 5.0:
        return "PASS"
    if eer_pct <= 15.0:
        return "PARTIAL"
    return "FAIL"


def load_detector(cfg_path: Path) -> AASISTDetector:
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    a = cfg["detectors"]["aasist"]
    det = AASISTDetector(
        checkpoint_path=a["checkpoint_path"],
        model_module_path=a.get("model_module_path"),
        device=a.get("device", "cuda"),
        target_sr=a.get("target_sr", 16000),
    )
    det.load()
    return det


def main():
    parser = argparse.ArgumentParser(
        description="In-domain sanity check for the fixed AuralGuard-AASIST detector"
    )
    parser.add_argument("--val-csv", type=str, default=str(DEFAULT_VAL_CSV))
    parser.add_argument("--detector-config", type=str, default=str(DEFAULT_DETECTOR_CFG))
    parser.add_argument("--n-per-class", type=int, default=500,
                        help="Rows sampled per class in sanity mode (default 500)")
    parser.add_argument("--stratify", type=str, default="dataset",
                        help="Column to stratify the per-class sample by")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--full", action="store_true",
                        help="Score every row in the val CSV (~9,514 files)")
    parser.add_argument("--output", type=str,
                        default="results/indomain_sanity_metrics.csv")
    args = parser.parse_args()

    print("=" * 60)
    print("IN-DOMAIN SANITY CHECK")
    print("=" * 60)
    print(f"Val CSV        : {args.val_csv}")
    print(f"Detector config: {args.detector_config}")

    val_path = Path(args.val_csv)
    if not val_path.exists():
        print(f"ERROR: val CSV not found: {val_path}")
        sys.exit(1)

    val = pd.read_csv(val_path)
    print(f"Loaded {len(val)} rows")
    print(f"  by binary_label: {val['binary_label'].value_counts().to_dict()}")
    print(f"  by dataset     : {val['dataset'].value_counts().to_dict()}")

    if args.full:
        sample = val
        print(f"\nMode: FULL ({len(sample)} rows)")
    else:
        sample = stratified_class_sample(
            val, n_per_class=args.n_per_class,
            stratify_col=args.stratify, seed=args.seed,
        )
        print(f"\nMode: sanity ({args.n_per_class} per class, "
              f"stratified by '{args.stratify}', seed={args.seed})")
        print(f"  sampled by binary_label: "
              f"{sample['binary_label'].value_counts().to_dict()}")

    # Resolve paths and drop unresolvable rows
    resolved = sample["file_path"].apply(resolve_path)
    unresolved = int(resolved.isna().sum())
    if unresolved:
        print(f"WARNING: {unresolved} rows have unresolvable paths and will be skipped")
    sample = sample.assign(resolved_path=resolved).dropna(subset=["resolved_path"])
    print(f"Scoring {len(sample)} files ({(sample['binary_label']==0).sum()} bonafide, "
          f"{(sample['binary_label']==1).sum()} spoof)")

    # Load detector once
    detector = load_detector(Path(args.detector_config))

    # Score every file (single-file inference to match the existing detector API)
    scores = []
    errors = 0
    for _, row in tqdm(sample.iterrows(), total=len(sample), desc="scoring"):
        try:
            s = detector.score(str(row["resolved_path"]))
        except Exception as e:
            tqdm.write(f"  ERROR scoring {row['resolved_path']}: {e}")
            s = float("nan")
            errors += 1
        scores.append(s)

    sample = sample.copy()
    sample["score"] = scores
    sample = sample.dropna(subset=["score"])
    if errors:
        print(f"WARNING: {errors} files failed to score (dropped from metrics)")

    # Translate label convention: AuralGuard 0=bonafide -> our bonafide array;
    # AuralGuard 1=spoof -> our spoof array.
    bonafide_all = sample.loc[sample["binary_label"] == 0, "score"].to_numpy()
    spoof_all = sample.loc[sample["binary_label"] == 1, "score"].to_numpy()

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    rows = [compute_row("ALL", bonafide_all, spoof_all)]
    for ds in sorted(sample["dataset"].unique()):
        sub = sample[sample["dataset"] == ds]
        bon = sub.loc[sub["binary_label"] == 0, "score"].to_numpy()
        spf = sub.loc[sub["binary_label"] == 1, "score"].to_numpy()
        rows.append(compute_row(ds, bon, spf))

    out_df = pd.DataFrame(rows)

    display_cols = [
        "dataset", "n_bonafide", "n_spoof",
        "eer_percent", "auc", "accuracy",
        "far_percent", "frr_percent",
        "mean_score_bonafide", "mean_score_spoof",
    ]
    with pd.option_context("display.width", 200,
                           "display.max_columns", None,
                           "display.float_format", lambda x: f"{x:.4f}"):
        print(out_df[display_cols].to_string(index=False))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path} (gitignored via results/ rule)")

    overall_eer = out_df.iloc[0]["eer_percent"]
    v = verdict_for(overall_eer)
    print()
    print("=" * 60)
    print(f"VERDICT: {v}  (overall EER = {overall_eer:.3f}%)")
    print("=" * 60)
    if v == "PASS":
        print("Detector performs as expected on its in-domain val set.")
        print("The high DECTE EER (35-48%) can be attributed to domain")
        print("transfer difficulty, not a remaining pipeline bug.")
    elif v == "PARTIAL":
        print("Detector discriminates but not as well as its training-time")
        print("val_metrics suggest (~1.7% EER). Some drift remains -- worth")
        print("checking preprocessing / audio decoding before writing this up.")
    else:
        print("Detector fails on its own in-domain val set. The DECTE numbers")
        print("cannot yet be interpreted as domain-transfer difficulty -- fix")
        print("the pipeline before publishing any Phase 2 result.")


if __name__ == "__main__":
    main()
