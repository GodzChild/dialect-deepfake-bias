#!/usr/bin/env python3
"""
Script 01: Prepare DECTE Data
===============================
Run this FIRST to inspect your DECTE download and prepare it for the pipeline.

This script:
  1. Scans your DECTE audio directory
  2. Matches audio files with your existing Whisper transcripts
  3. Reports what you have vs. what you need
  4. Creates the speaker_info.json template if it doesn't exist

Usage:
    python scripts/01_prepare_decte.py \
        --audio-dir data/decte/audio \
        --transcripts-dir data/decte/transcripts \
        --output-metadata data/decte/metadata/speaker_info.json
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torchaudio


def scan_audio(audio_dir: Path) -> dict:
    """Scan audio directory and report what's there."""
    extensions = {".wav", ".flac", ".mp3", ".ogg"}
    files = []

    for f in sorted(audio_dir.rglob("*")):
        if f.suffix.lower() in extensions:
            files.append(f)

    print(f"\n📁 Audio Directory: {audio_dir}")
    print(f"   Total audio files found: {len(files)}")

    if not files:
        print("   ⚠️  No audio files found! Check the path.")
        return {"files": [], "speakers": {}}

    # Show file naming pattern
    print(f"   Sample filenames:")
    for f in files[:5]:
        print(f"     {f.name}")
    if len(files) > 5:
        print(f"     ... and {len(files) - 5} more")

    # Try to extract speaker IDs from filenames
    # ADAPT THIS PATTERN to match your DECTE naming
    speaker_files = defaultdict(list)
    for f in files:
        stem = f.stem
        # Common patterns:
        # "INT001_speaker1" -> speaker = "INT001_speaker1" or parts[0]
        # "PVC_001_utt01" -> speaker = "PVC_001"
        # Adapt based on what you see in the output above
        parts = stem.split("_")
        if len(parts) >= 2:
            spk_id = parts[0]  # CHANGE THIS based on your naming
        else:
            spk_id = stem
        speaker_files[spk_id].append(f)

    print(f"\n   Detected speaker groups (from filename parsing): {len(speaker_files)}")
    print(f"   ⚠️  If this looks wrong, edit the speaker ID extraction logic above!")

    # Audio stats
    total_duration = 0
    durations = []
    sample_rates = Counter()

    print(f"\n   Scanning audio properties (this may take a moment)...")
    for f in files[:100]:  # Sample first 100 for speed
        try:
            info = torchaudio.info(str(f))
            dur = info.num_frames / info.sample_rate
            durations.append(dur)
            total_duration += dur
            sample_rates[info.sample_rate] += 1
        except Exception as e:
            print(f"   ⚠️  Error reading {f.name}: {e}")

    if durations:
        print(f"   Sample rates found: {dict(sample_rates)}")
        print(f"   Duration stats (first 100 files):")
        print(f"     Min: {min(durations):.1f}s")
        print(f"     Max: {max(durations):.1f}s")
        print(f"     Mean: {sum(durations)/len(durations):.1f}s")
        print(f"     Total sampled: {total_duration/60:.1f} min")

    return {"files": files, "speakers": dict(speaker_files)}


def scan_transcripts(transcripts_dir: Path, audio_files: list) -> dict:
    """Check which audio files have matching transcripts."""
    print(f"\n📝 Transcripts Directory: {transcripts_dir}")

    if not transcripts_dir.exists():
        print(f"   ⚠️  Directory not found!")
        return {"matched": 0, "unmatched": 0}

    transcript_files = list(transcripts_dir.rglob("*.txt")) + list(transcripts_dir.rglob("*.json"))
    print(f"   Total transcript files found: {len(transcript_files)}")

    # Show samples
    if transcript_files:
        print(f"   Sample filenames:")
        for f in transcript_files[:5]:
            print(f"     {f.name}")

    # Match audio to transcripts
    transcript_stems = {f.stem for f in transcript_files}
    audio_stems = {f.stem for f in audio_files}

    matched = audio_stems & transcript_stems
    audio_only = audio_stems - transcript_stems
    transcript_only = transcript_stems - audio_stems

    print(f"\n   ✅ Audio files WITH transcripts: {len(matched)}")
    print(f"   ❌ Audio files WITHOUT transcripts: {len(audio_only)}")
    print(f"   ❓ Transcripts without audio match: {len(transcript_only)}")

    if audio_only and len(audio_only) <= 10:
        print(f"   Missing transcripts for: {sorted(audio_only)}")

    return {"matched": len(matched), "unmatched": len(audio_only)}


def create_metadata_template(
    speaker_ids: list, output_path: Path
):
    """Create a speaker_info.json template to fill in."""
    if output_path.exists():
        print(f"\n📋 Metadata file already exists: {output_path}")
        with open(output_path) as f:
            existing = json.load(f)
        print(f"   Contains {len(existing)} speakers")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    template = {}
    for spk_id in sorted(speaker_ids):
        template[spk_id] = {
            "gender": "FILL_IN",        # "M" or "F"
            "age_group": "FILL_IN",      # "young", "middle", "old"
            "ses_class": "FILL_IN",      # e.g., "working", "middle"
            "recording_era": "FILL_IN",  # "1960s-70s", "1990s", "2007-2010"
        }

    with open(output_path, "w") as f:
        json.dump(template, f, indent=2)

    print(f"\n📋 Created metadata template: {output_path}")
    print(f"   Contains {len(template)} speaker entries to fill in.")
    print(f"   ⚠️  FILL THIS IN using DECTE documentation before running generation!")
    print(f"   Social variables needed (from Serditova & Tang 2025/2026):")
    print(f"     - gender: M/F")
    print(f"     - age_group: young/middle/old")
    print(f"     - ses_class: working/middle (socioeconomic status)")
    print(f"     - recording_era: 1960s-70s / 1990s / 2007-2010")


def main():
    parser = argparse.ArgumentParser(description="Prepare DECTE data")
    parser.add_argument("--audio-dir", type=str, default="data/decte/audio")
    parser.add_argument("--transcripts-dir", type=str, default="data/decte/transcripts")
    parser.add_argument(
        "--output-metadata",
        type=str,
        default="data/decte/metadata/speaker_info.json",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("DIALECT DEEPFAKE BIAS — DATA PREPARATION")
    print("=" * 60)

    # Scan audio
    audio_result = scan_audio(Path(args.audio_dir))

    # Scan transcripts
    if audio_result["files"]:
        scan_transcripts(Path(args.transcripts_dir), audio_result["files"])

    # Create metadata template
    if audio_result["speakers"]:
        create_metadata_template(
            list(audio_result["speakers"].keys()),
            Path(args.output_metadata),
        )

    print(f"\n{'=' * 60}")
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Check the file counts and naming patterns above")
    print("2. Edit decte_loader.py speaker ID extraction if needed")
    print("3. Fill in data/decte/metadata/speaker_info.json")
    print("4. If transcripts are missing, run Whisper on remaining audio")
    print("5. Run: python scripts/02_generate_spoofs.py")


if __name__ == "__main__":
    main()
