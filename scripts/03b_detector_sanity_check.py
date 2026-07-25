#!/usr/bin/env python3
"""
Script 03b: Detector Sanity Check
==================================
Diagnostic run for the AASIST detector: score a handful of KNOWN bonafide
and spoof files, print raw scores, and report the max-min gap. Use this
before trusting any Phase 2 group metrics.

If the gap across bonafide + spoof scores is < 0.01, the detector is
almost certainly not loading correctly (untrained weights, checkpoint
mismatch, or preprocessing mismatch) -- fix that first, ignore any
downstream EER/AUC numbers until this passes.

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/03b_detector_sanity_check.py

Does not modify any files. Does not touch generation, manifest, or metrics.
"""

import argparse
import os
import sys
from pathlib import Path

import jsonlines
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.detectors import AASISTDetector


N_PER_CLASS = 3   # 3 bonafide, up to 3 per generator on the spoof side


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def pick_samples(manifest_path: str):
    """Pick a small stratified sample from the manifest:
      - up to N_PER_CLASS unique bonafide (reference) audio paths
      - up to N_PER_CLASS spoof paths per successful generator
    """
    bonafide = []
    seen_bonafide = set()
    spoof_by_gen: dict[str, list] = {}

    with jsonlines.open(manifest_path) as reader:
        for entry in reader:
            if not entry.get("success", False):
                continue

            gen = entry.get("generator_name", "unknown")
            spoof_by_gen.setdefault(gen, [])
            if len(spoof_by_gen[gen]) < N_PER_CLASS:
                spoof_by_gen[gen].append({
                    "path": entry["output_path"],
                    "label": 0,
                    "generator_name": gen,
                    "source_speaker_id": entry.get("source_speaker_id", ""),
                })

            for ref_path in entry.get("reference_audio_paths", []):
                if ref_path in seen_bonafide:
                    continue
                seen_bonafide.add(ref_path)
                if len(bonafide) < N_PER_CLASS:
                    bonafide.append({
                        "path": ref_path,
                        "label": 1,
                        "generator_name": "bonafide",
                        "source_speaker_id": entry.get("source_speaker_id", ""),
                    })

    samples = list(bonafide)
    for gen in sorted(spoof_by_gen):
        samples.extend(spoof_by_gen[gen])
    return samples


def main():
    parser = argparse.ArgumentParser(description="AASIST detector sanity check")
    parser.add_argument("--config", type=str, default="configs/detectors.yaml")
    parser.add_argument("--manifest", type=str,
                        default="data/generated_spoofs/manifest.jsonl")
    args = parser.parse_args()

    print("=" * 60)
    print("AASIST DETECTOR SANITY CHECK")
    print("=" * 60)

    config = load_config(args.config)
    aasist_cfg = config["detectors"]["aasist"]

    print(f"\nCheckpoint : {aasist_cfg['checkpoint_path']}")
    print(f"Device     : {aasist_cfg.get('device', 'cuda')}")
    print(f"Target SR  : {aasist_cfg.get('target_sr', 16000)}")

    ckpt_path = Path(aasist_cfg["checkpoint_path"])
    if not ckpt_path.exists():
        print(f"\nERROR: checkpoint file not found on disk: {ckpt_path}")
        return
    print(f"Checkpoint size on disk: {ckpt_path.stat().st_size / (1024*1024):.2f} MB")

    detector = AASISTDetector(
        checkpoint_path=str(aasist_cfg["checkpoint_path"]),
        model_module_path=aasist_cfg.get("model_module_path"),
        device=aasist_cfg.get("device", "cuda"),
        target_sr=aasist_cfg.get("target_sr", 16000),
    )
    detector.load()

    # Cheap "did weights actually load?" sniff: a randomly-init model would
    # have parameter norms very close to their kaiming-init scale; a trained
    # model usually diverges. Not conclusive, but informative.
    import torch
    total_params = sum(p.numel() for p in detector.model.parameters())
    total_norm = float(sum(p.detach().float().norm().item()
                           for p in detector.model.parameters()))
    print(f"Model params: {total_params:,} | sum of param L2 norms: {total_norm:.2f}")

    print(f"\nPicking sample files from {args.manifest}...")
    samples = pick_samples(args.manifest)
    if not samples:
        print("ERROR: no samples found in manifest.")
        return

    print(f"Selected {len(samples)} files.")
    print("-" * 60)
    print(f"{'label':>6}  {'generator':<14}  score      path")
    print("-" * 60)

    scores = []
    for s in samples:
        try:
            score = detector.score(s["path"])
        except Exception as e:
            print(f"  ERROR scoring {s['path']}: {e}")
            continue
        scores.append(score)
        label_str = "bonafide" if s["label"] == 1 else "spoof"
        print(f"{label_str:>8}  {s['generator_name']:<14}  {score:.6f}  {s['path']}")

    print("-" * 60)

    if not scores:
        print("No scores produced. Cannot compute gap.")
        return

    smin = min(scores)
    smax = max(scores)
    smean = sum(scores) / len(scores)
    gap = smax - smin

    print(f"\nScore stats over {len(scores)} files:")
    print(f"  min  : {smin:.6f}")
    print(f"  max  : {smax:.6f}")
    print(f"  mean : {smean:.6f}")
    print(f"  gap  : {gap:.6f}")

    print()
    if gap < 0.01:
        print("WARNING: max - min gap is below 0.01.")
        print("The detector is producing near-constant output for every input.")
        print("Do NOT trust downstream Phase 2 metrics until this is fixed.")
        print("Likely causes:")
        print("  - AASIST checkpoint failed to load (weights are untrained)")
        print("  - Preprocessing mismatch between this pipeline and the")
        print("    original training pipeline in auralguard-aasistpp")
        print("  - Audio decoded as silence / zeros")
    elif gap < 0.1:
        print("NOTE: score gap is small (< 0.1). Detector is discriminating")
        print("slightly but may still be miscalibrated. Investigate further.")
    else:
        print("OK: score gap looks healthy. Detector appears to be loading")
        print("and discriminating. Downstream metrics should be meaningful.")


if __name__ == "__main__":
    main()
