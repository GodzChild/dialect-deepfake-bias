#!/usr/bin/env python3
"""
Script 08: Backfill source_audio_path (+ corpus) into an existing manifest
==========================================================================
One-shot utility that rewrites a spoof-generation manifest in place,
adding the `source_audio_path` and `corpus` fields introduced in Phase 2
so pre-schema-change manifests work with the updated eval script's
matched-original bonafide pairing.

Reconstruction rule per corpus:
  - vctk : source_utterance_id -> pXXX_YYY -> data/vctk/wav48_silence_trimmed/pXXX/pXXX_YYY*.flac
           (prefers _mic1.flac, falls back to any .flac, then .wav)
  - decte: source_utterance_id -> <chunk stem> -> data/01_chunks/**/{stem}.wav

Safety:
  - Aborts BEFORE writing if any row's source_audio_path cannot be
    resolved on disk. Prints the unresolved rows so you can diagnose.
  - Always writes a timestamped backup (manifest.jsonl.bak_YYYYMMDD_HHMMSS)
    before rewriting.
  - Skips rows that already carry a non-empty source_audio_path (idempotent).
  - Never touches audio files, checkpoints, or any other manifest.

Usage:
    python scripts/08_backfill_source_audio_path.py \\
        --manifest data/generated_spoofs_vctk/manifest.jsonl \\
        --corpus vctk

    python scripts/08_backfill_source_audio_path.py \\
        --manifest data/generated_spoofs/manifest.jsonl \\
        --corpus decte
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


VCTK_AUDIO_ROOT = Path("data/vctk/wav48_silence_trimmed")
DECTE_CHUNKS_ROOT = Path("data/01_chunks")


def strip_spoofed_suffix(utt_id: str) -> str:
    """Turn 'p225_046_spoofed' -> 'p225_046'."""
    if utt_id.endswith("_spoofed"):
        return utt_id[: -len("_spoofed")]
    return utt_id


def resolve_vctk(source_utterance_id: str) -> Path | None:
    """VCTK: pXXX_YYY -> data/vctk/wav48_silence_trimmed/pXXX/pXXX_YYY*.flac."""
    stem = strip_spoofed_suffix(source_utterance_id)
    speaker = stem.split("_")[0]  # 'p225' from 'p225_046'
    speaker_dir = VCTK_AUDIO_ROOT / speaker
    if not speaker_dir.exists():
        return None

    # Prefer the mic1 recording, then any flac, then any wav
    for candidate in (
        speaker_dir / f"{stem}_mic1.flac",
        speaker_dir / f"{stem}.flac",
        speaker_dir / f"{stem}.wav",
    ):
        if candidate.exists():
            return candidate

    # Last resort: any file starting with the stem
    matches = sorted(speaker_dir.glob(f"{stem}*"))
    return matches[0] if matches else None


def resolve_decte(source_utterance_id: str) -> Path | None:
    """DECTE: <chunk stem> -> data/01_chunks/**/<chunk stem>.wav."""
    stem = strip_spoofed_suffix(source_utterance_id)
    matches = list(DECTE_CHUNKS_ROOT.rglob(f"{stem}.wav"))
    if not matches:
        return None
    return matches[0]


RESOLVERS = {
    "vctk": resolve_vctk,
    "decte": resolve_decte,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill source_audio_path + corpus into an existing manifest."
    )
    parser.add_argument("--manifest", type=str, required=True)
    parser.add_argument(
        "--corpus", type=str, required=True, choices=sorted(RESOLVERS),
        help="Which corpus this manifest belongs to (drives reconstruction).",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        return 1
    resolver = RESOLVERS[args.corpus]

    print(f"Manifest : {manifest_path}")
    print(f"Corpus   : {args.corpus}")

    # ---- read rows ----
    with manifest_path.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    print(f"Rows read: {len(rows)}")

    # ---- resolve each row ----
    already = 0
    to_fill = []
    unresolved = []

    for i, row in enumerate(rows):
        existing = row.get("source_audio_path", "")
        if existing:
            already += 1
            continue

        source_utt_id = row.get("source_utterance_id", "")
        if not source_utt_id:
            unresolved.append((i, row, "missing source_utterance_id"))
            continue

        resolved = resolver(source_utt_id)
        if resolved is None or not resolved.exists():
            unresolved.append((i, row, f"no file found for {source_utt_id!r}"))
            continue

        to_fill.append((i, row, str(resolved)))

    print(f"  already had source_audio_path : {already}")
    print(f"  to fill                       : {len(to_fill)}")
    print(f"  unresolved                    : {len(unresolved)}")

    # ---- abort on unresolved ----
    if unresolved:
        print()
        print("ABORT: some rows could not be resolved. Manifest NOT modified.")
        print("First 10 unresolved:")
        for i, row, reason in unresolved[:10]:
            print(f"  row {i}: {reason} | speaker={row.get('source_speaker_id')} | out={row.get('output_path')}")
        return 2

    if not to_fill:
        print("Nothing to do (every row already has source_audio_path). Exiting.")
        return 0

    # ---- backup ----
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = manifest_path.with_suffix(manifest_path.suffix + f".bak_{ts}")
    shutil.copy2(manifest_path, backup_path)
    print(f"Backup written: {backup_path}")

    # ---- fill + rewrite ----
    for i, _, resolved_str in to_fill:
        rows[i]["source_audio_path"] = resolved_str
        # Set corpus if absent; don't overwrite a manifest-provided value.
        if not rows[i].get("corpus"):
            rows[i]["corpus"] = args.corpus

    with manifest_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    print(f"Rewrote {manifest_path} with {len(to_fill)} rows updated.")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
