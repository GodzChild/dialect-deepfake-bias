#!/usr/bin/env python3
"""
Build per-chunk transcript .txt files from FairFix input CSVs.

Input:
    data/03_fairfix_inputs/*_chunks_for_fairfix.csv

Output:
    data/01_chunk_transcripts/*.txt

Each output .txt matches one chunk .wav filename.
"""

from pathlib import Path
import pandas as pd


FAIRFIX_DIR = Path("data/03_fairfix_inputs")
OUT_DIR = Path("data/01_chunk_transcripts")


def safe_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(FAIRFIX_DIR.rglob("*_chunks_for_fairfix.csv"))

    if not csv_files:
        print(f"No CSV files found recursively in {FAIRFIX_DIR}")
        return

    print(f"Found {len(csv_files)} FairFix CSV files")

    written = 0
    skipped_empty = 0

    for csv_path in csv_files:
        print(f"Reading {csv_path.name}")

        df = pd.read_csv(csv_path)

        required_cols = {"chunk_audio_file", "raw_whisper_text"}
        missing = required_cols - set(df.columns)

        if missing:
            print(f"  Skipping {csv_path.name}: missing columns {missing}")
            continue

        for _, row in df.iterrows():
            chunk_audio_file = safe_text(row["chunk_audio_file"])
            raw_text = safe_text(row["raw_whisper_text"])
            fairfix_text = safe_text(row.get("fairfix_corrected_text", ""))

            # Prefer FairFix corrected text if it exists, otherwise use raw Whisper text
            text = fairfix_text if fairfix_text else raw_text

            if not chunk_audio_file:
                continue

            if not text:
                skipped_empty += 1
                continue

            chunk_stem = Path(chunk_audio_file).stem

            out_path = OUT_DIR / f"{chunk_stem}.txt"
            out_path.write_text(text, encoding="utf-8")

            written += 1

    print("=" * 60)
    print(f"Created chunk transcript files: {written}")
    print(f"Skipped empty transcript rows: {skipped_empty}")
    print(f"Output folder: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()