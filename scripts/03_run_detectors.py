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


def normalize_file_id(value: str) -> str:
    """Normalize DECTE file/chunk names to transcript file_id style."""
    value = str(value).replace("\\", "/").lower()
    stem = Path(value).stem

    if "_chunk_" in stem:
        stem = stem.split("_chunk_")[0]

    if stem.endswith("audio"):
        stem = stem[:-5]

    return stem


def load_speaker_metadata(path: str = "data/decte/metadata/speaker_info.json") -> dict:
    """Load speaker metadata and also build file-level lookup."""
    import json

    metadata_path = Path(path)
    if not metadata_path.exists():
        print(f"WARNING: speaker metadata not found: {metadata_path}")
        return {"by_speaker": {}, "by_file": {}}

    by_speaker = json.loads(metadata_path.read_text(encoding="utf-8"))
    by_file = {}

    for speaker_id, info in by_speaker.items():
        file_id = info.get("file_id", "unknown")
        by_file.setdefault(file_id, []).append(info)

    return {
        "by_speaker": by_speaker,
        "by_file": by_file,
    }


def combine_file_metadata(speakers: list[dict]) -> dict:
    """
    If an interview file has multiple speakers, combine safely.
    If all speakers share the same value, keep it.
    If values differ, mark as mixed.
    """
    fields = ["gender", "age_group", "education", "occupation", "residence", "recording_era"]
    combined = {}

    for field in fields:
        values = sorted({
            spk.get(field, "unknown")
            for spk in speakers
            if spk.get(field, "unknown") != "unknown"
        })

        if len(values) == 0:
            combined[field] = "unknown"
        elif len(values) == 1:
            combined[field] = values[0]
        else:
            combined[field] = "mixed"

    return combined


def lookup_metadata(entry: dict, audio_path: str, speaker_meta: dict) -> dict:
    by_speaker = speaker_meta["by_speaker"]
    by_file = speaker_meta["by_file"]

    source_speaker_id = str(entry.get("source_speaker_id", "unknown")).lower()
    file_id = normalize_file_id(audio_path)

    # 1. Exact speaker match, e.g. pvc03a
    if source_speaker_id in by_speaker:
        info = by_speaker[source_speaker_id]
    # 2. File/interview match, e.g. decten1pvc03
    elif file_id in by_file:
        info = combine_file_metadata(by_file[file_id])
    else:
        info = {
            "gender": "unknown",
            "age_group": "unknown",
            "education": "unknown",
            "occupation": "unknown",
            "residence": "unknown",
            "recording_era": "unknown",
        }

    return {
        "speaker_gender": info.get("gender", "unknown"),
        "speaker_age_group": info.get("age_group", "unknown"),
        "speaker_education": info.get("education", "unknown"),
        "speaker_occupation": info.get("occupation", "unknown"),
        "speaker_residence": info.get("residence", "unknown"),
        "speaker_recording_era": info.get("recording_era", "unknown"),
    }


def build_evaluation_pairs(manifest_path: str, config: dict) -> pd.DataFrame:
    """
    Build the full list of audio files to evaluate:
      - spoof file -> label 0
      - matching bonafide source file -> label 1

    Also attaches speaker metadata from data/decte/metadata/speaker_info.json.
    """
    records = []
    speaker_meta = load_speaker_metadata()

    with jsonlines.open(manifest_path) as reader:
        for entry in reader:
            if not entry.get("success", False):
                continue

            spoof_path = entry["output_path"]
            bonafide_paths = entry.get("reference_audio_paths", [])

            base_metadata = {
                "generator_name": entry.get("generator_name", "unknown"),
                "speaker_id": entry.get("source_speaker_id", "unknown"),
                "dialect_group": "decte",
            }

            spoof_metadata = lookup_metadata(entry, spoof_path, speaker_meta)

            records.append({
                "audio_path": spoof_path,
                "label": 0,
                **base_metadata,
                **spoof_metadata,
            })

            for bp in bonafide_paths:
                bonafide_metadata = lookup_metadata(entry, bp, speaker_meta)

                records.append({
                    "audio_path": bp,
                    "label": 1,
                    # Bonafide files are shared across generators (the same
                    # DECTE reference wav feeds both XTTS and OpenVoice).
                    # Tag them "bonafide" so per-generator grouping in
                    # bias_analysis pools the same real files against each
                    # generator's spoofs, instead of first-writer-wins.
                    "generator_name": "bonafide",
                    "speaker_id": entry.get("source_speaker_id", "unknown"),
                    "dialect_group": "decte",
                    **bonafide_metadata,
                })

    df = pd.DataFrame(records)
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

        # --- Diagnostic: score/label distributions (catches broken detector
        # loading, direction flips, and per-generator bonafide dropouts) ---
        print(f"\n{detector.name} - score/label diagnostics")
        print("-" * 60)
        print("counts by (generator_name, label):")
        print(result_df.groupby(["generator_name", "label"])
              .size().unstack(fill_value=0).to_string())
        print("\nmean score by label:")
        print(result_df.groupby("label")["score"]
              .agg(["count", "mean", "std", "min", "max"]).to_string())
        print("\nmean score by (generator_name, label):")
        print(result_df.groupby(["generator_name", "label"])["score"]
              .agg(["count", "mean", "std"]).to_string())
        print("\nfirst 10 rows:")
        print(result_df[["audio_path", "label", "score",
                         "generator_name", "speaker_id"]]
              .head(10).to_string(index=False))
        # Warn on a near-constant score distribution (broken checkpoint /
        # preprocessing mismatch signature: everything clusters within ~1e-3).
        score_span = float(result_df["score"].max() - result_df["score"].min())
        if score_span < 1e-3:
            print(f"\nWARNING: {detector.name} score span is {score_span:.6f} - "
                  "detector may not be loading correctly. Verify the "
                  "checkpoint and preprocessing before trusting metrics.")
        print("-" * 60)

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
    print("\nNote: speaker metadata is loaded from")
    print("  data/decte/metadata/speaker_info.json (per-speaker)")
    print("and collapsed to file level in-script via combine_file_metadata.")
    print("Some groups may be reported as 'mixed' or 'unknown' when an")
    print("interview contains multiple speakers or has incomplete metadata.")


if __name__ == "__main__":
    main()
