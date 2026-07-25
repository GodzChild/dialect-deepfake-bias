#!/usr/bin/env python3
"""
Script 03: Run Detectors
==========================
Phase 2 main script. Loads the spoof manifest from Phase 1, runs the
detector on both bonafide and spoofed audio, computes metrics overall
and per social-variable group, saves results.

Usage:
    python scripts/03_run_detectors.py --config configs/detectors.yaml

Outputs:
    results/detector_predictions.csv   — raw per-file scores (gitignored, large)
    results/detector_metrics.csv       — overall metrics (small, commit this)
    results/group_bias_summary.csv     — per-group breakdown (small, commit this)
"""

import argparse
import sys
import os
from pathlib import Path

import jsonlines
import pandas as pd
import yaml
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.detectors import AASISTDetector
from src.evaluation.bias_analysis import compute_grouped_metrics, compute_dialect_vs_standard_gap
from src.evaluation.metrics import compute_metrics, metrics_to_dict


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def create_detector(config: dict):
    """Instantiate the detector(s) specified in config. Extend this as you
    add more detectors (Wav2Vec2-based, Whisper-feature-based, etc.)."""
    detectors = []
    det_configs = config["detectors"]

    if det_configs.get("aasist", {}).get("enabled", False):
        cfg = det_configs["aasist"]
        detectors.append(AASISTDetector(
            checkpoint_path=cfg["checkpoint_path"],
            model_module_path=cfg.get("model_module_path"),
            device=cfg.get("device", "cuda"),
            target_sr=cfg.get("target_sr", 16000),
        ))

    return detectors


def build_evaluation_pairs(manifest_path: str, config: dict) -> pd.DataFrame:
    """
    Build the full list of (audio_path, label, metadata) pairs to evaluate:
      - Every successfully generated spoof file -> label 0
      - The corresponding bonafide source file -> label 1

    Reads directly from the Phase 1 manifest.jsonl.
    """
    records = []

    with jsonlines.open(manifest_path) as reader:
        for entry in reader:
            if not entry.get("success", False):
                continue

            spoof_path = entry["output_path"]
            # The bonafide reference is the FIRST reference audio used
            # (the clip that provided voice identity for cloning)
            bonafide_paths = entry.get("reference_audio_paths", [])

            metadata = {
                "speaker_gender": entry.get("speaker_gender", "unknown"),
                "speaker_age_group": entry.get("speaker_age_group", "unknown"),
                "speaker_ses_class": entry.get("speaker_ses_class", "unknown"),
                "speaker_recording_era": entry.get("speaker_recording_era", "unknown"),
                "generator_name": entry.get("generator_name", "unknown"),
                "speaker_id": entry.get("source_speaker_id", "unknown"),
                "dialect_group": "decte",  # set to "vctk" for the control set later
            }

            # Spoof record
            records.append({
                "audio_path": spoof_path,
                "label": 0,
                **metadata,
            })

            # Bonafide record(s) — dedupe since multiple spoofs share the
            # same reference audio
            for bp in bonafide_paths:
                records.append({
                    "audio_path": bp,
                    "label": 1,
                    **metadata,
                })

    df = pd.DataFrame(records)
    # Drop duplicate bonafide entries (same file referenced by multiple spoofs)
    df = df.drop_duplicates(subset=["audio_path", "label"])
    return df


def run_detection(detector, eval_df: pd.DataFrame) -> pd.DataFrame:
    """Run the detector on every audio file, return df with scores added."""
    print(f"\nRunning {detector.name} on {len(eval_df)} files...")
    detector.load()

    scores = []
    errors = 0
    for _, row in tqdm(eval_df.iterrows(), total=len(eval_df), desc=detector.name):
        try:
            score = detector.score(row["audio_path"])
        except Exception as e:
            tqdm.write(f"  ERROR scoring {row['audio_path']}: {e}")
            score = float("nan")
            errors += 1
        scores.append(score)

    eval_df = eval_df.copy()
    eval_df["score"] = scores
    eval_df["detector_name"] = detector.name

    if errors:
        print(f"  ⚠️  {errors}/{len(eval_df)} files failed to score — check errors above")

    return eval_df.dropna(subset=["score"])


def main():
    parser = argparse.ArgumentParser(description="Run deepfake detectors on generated spoofs")
    parser.add_argument("--config", type=str, default="configs/detectors.yaml")
    parser.add_argument(
        "--manifest", type=str, default="data/generated_spoofs/manifest.jsonl"
    )
    parser.add_argument("--output-dir", type=str, default="results")
    args = parser.parse_args()

    print("=" * 60)
    print("PHASE 2 — DETECTOR EVALUATION")
    print("=" * 60)

    config = load_config(args.config)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build evaluation pairs from Phase 1 manifest
    print(f"\nLoading manifest from {args.manifest}...")
    eval_df = build_evaluation_pairs(args.manifest, config)
    print(f"Built {len(eval_df)} evaluation pairs "
          f"({(eval_df['label']==1).sum()} bonafide, "
          f"{(eval_df['label']==0).sum()} spoof)")

    if eval_df.empty:
        print("ERROR: No evaluation pairs found. Check manifest path and content.")
        return

    # Load detectors
    detectors = create_detector(config)
    if not detectors:
        print("ERROR: No detectors enabled in config. Edit configs/detectors.yaml.")
        return

    all_predictions = []

    for detector in detectors:
        result_df = run_detection(detector, eval_df)
        all_predictions.append(result_df)

        # --- Overall metrics for this detector ---
        bonafide_scores = result_df[result_df["label"] == 1]["score"].values
        spoof_scores = result_df[result_df["label"] == 0]["score"].values

        if len(bonafide_scores) == 0 or len(spoof_scores) == 0:
            print(f"  ⚠️  Not enough data to compute metrics for {detector.name}")
            continue

        overall_metrics = compute_metrics(bonafide_scores, spoof_scores)
        print(f"\n{detector.name} — Overall Results:")
        print(f"  EER: {overall_metrics.eer:.2f}%")
        print(f"  AUC: {overall_metrics.auc:.4f}")
        print(f"  Accuracy: {overall_metrics.accuracy:.4f}")
        print(f"  False Accept Rate: {overall_metrics.false_accept_rate:.2f}%")
        print(f"  False Reject Rate: {overall_metrics.false_reject_rate:.2f}%")

        # --- Grouped bias analysis (the actual thesis result) ---
        grouped = compute_grouped_metrics(result_df)
        grouped["detector_name"] = detector.name

        grouped_path = output_dir / f"group_bias_summary_{detector.name}.csv"
        grouped.to_csv(grouped_path, index=False)
        print(f"\n  Group breakdown saved to {grouped_path}")
        if not grouped.empty:
            print(grouped.to_string(index=False))

        # --- Dialect vs standard gap (once VCTK control exists) ---
        gap_result = compute_dialect_vs_standard_gap(result_df)
        print(f"\n  Dialect vs standard gap: {gap_result}")

    # Save all raw predictions (gitignored — large file, keep locally)
    predictions_df = pd.concat(all_predictions, ignore_index=True)
    predictions_path = output_dir / "detector_predictions.csv"
    predictions_df.to_csv(predictions_path, index=False)
    print(f"\nRaw predictions saved to {predictions_path} (not committed to git)")

    # Save overall metrics summary across all detectors (small — commit this)
    summary_rows = []
    for detector_name in predictions_df["detector_name"].unique():
        sub = predictions_df[predictions_df["detector_name"] == detector_name]
        bonafide = sub[sub["label"] == 1]["score"].values
        spoof = sub[sub["label"] == 0]["score"].values
        if len(bonafide) and len(spoof):
            m = compute_metrics(bonafide, spoof)
            row = metrics_to_dict(m, group_name=detector_name)
            summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "detector_metrics.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"Overall metrics summary saved to {summary_path}")

    print("\n" + "=" * 60)
    print("PHASE 2 COMPLETE")
    print("=" * 60)
    print("\nNote: speaker_info.json still has FILL_IN placeholders for most")
    print("fields — group breakdowns for gender/age/SES will be empty or")
    print("meaningless until you fill in real values from DECTE documentation.")


if __name__ == "__main__":
    main()
