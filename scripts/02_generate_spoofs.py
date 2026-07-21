#!/usr/bin/env python3
"""
Script 02: Generate Spoofed Audio
==================================
Run this after preparing your DECTE data (Script 01).

Usage:
    python scripts/02_generate_spoofs.py --config configs/spoof_gen.yaml

This will:
  1. Load DECTE audio + metadata + your Whisper transcripts
  2. For each speaker, select reference utterances (voice identity)
  3. Generate spoofed versions of target utterances using XTTS v2
  4. Save everything + a manifest.jsonl for evaluation
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.spoof_gen.pipeline import SpoofPipeline


def main():
    parser = argparse.ArgumentParser(description="Generate spoofed audio from DECTE")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/spoof_gen.yaml",
        help="Path to spoof generation config",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("DIALECT DEEPFAKE BIAS — SPOOF GENERATION")
    print("=" * 60)

    pipeline = SpoofPipeline(config_path=args.config)
    pipeline.run()

    print("\nDone! Next step: run detectors with scripts/03_run_detectors.py")


if __name__ == "__main__":
    main()
