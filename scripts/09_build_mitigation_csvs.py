#!/usr/bin/env python3
"""
Script 09: Build DECTE Mitigation Train/Val/Test CSVs + Held-Out Test Manifest
================================================================================
Prepares the data artefacts for Phase 4 v1 (dialect-aware fine-tuning of
AuralGuardAASISTPP). Does NOT train, does NOT touch checkpoints, does NOT
modify the existing 516-row DECTE manifest or the 200-row VCTK manifest.

Eligibility rule: a speaker is used only if they have BOTH valid DECTE
bonafide utterances (post-filter, via DECTELoader) AND at least one
successful XTTS v2 spoof in the manifest. On the current data that
intersection is 82 speakers (out of 96 with bonafide and 82 with XTTS).

Speaker-level 52 / 14 / 16 split (roughly 65% / 17% / 18%) of the 82
eligible speakers, seeded at 42.

Outputs (all under data/, hence gitignored):
  data/decte/metadata/decte_mitigation_train.csv
  data/decte/metadata/decte_mitigation_val.csv
  data/decte/metadata/decte_mitigation_test.csv
  data/generated_spoofs/manifest_mitigation_test.jsonl

CSV format matches auralguard-aasistpp/src/train.py's expectations:
  file_path, binary_label, attack_type, start_fake, end_fake,
  dataset, split, accent, gender, config, text, speaker

Label convention here is AuralGuard's (opposite of our metrics.py):
  binary_label = 0  ->  bonafide
  binary_label = 1  ->  spoof

Safety:
- Refuses to overwrite any of the four output files if they already exist.
- Runs leakage checks BEFORE writing anything (speaker disjointness and
  file disjointness across the three splits). Aborts on failure.

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/09_build_mitigation_csvs.py

Force overwrite (only if you know what you're doing):
    python scripts/09_build_mitigation_csvs.py --force
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.decte_loader import DECTELoader


# ---- fixed paths (mirror configs/spoof_gen.yaml) ----
REPO_ROOT = Path(__file__).resolve().parents[1]
DECTE_AUDIO_DIR = REPO_ROOT / "data" / "01_chunks"
DECTE_METADATA = REPO_ROOT / "data" / "decte" / "metadata" / "speaker_info_by_audio.json"
DECTE_TRANSCRIPTS = REPO_ROOT / "data" / "01_chunk_transcripts"
DECTE_MANIFEST = REPO_ROOT / "data" / "generated_spoofs" / "manifest.jsonl"

# ---- outputs ----
OUT_TRAIN_CSV = REPO_ROOT / "data" / "decte" / "metadata" / "decte_mitigation_train.csv"
OUT_VAL_CSV = REPO_ROOT / "data" / "decte" / "metadata" / "decte_mitigation_val.csv"
OUT_TEST_CSV = REPO_ROOT / "data" / "decte" / "metadata" / "decte_mitigation_test.csv"
OUT_TEST_MANIFEST = REPO_ROOT / "data" / "generated_spoofs" / "manifest_mitigation_test.jsonl"

# ---- split sizing (must sum to the eligible speaker count, currently 82) ----
N_TRAIN, N_VAL, N_TEST = 52, 14, 16

# ---- CSV columns in AuralGuard order ----
CSV_COLUMNS = [
    "file_path", "binary_label", "attack_type",
    "start_fake", "end_fake",
    "dataset", "split", "accent", "gender", "config", "text", "speaker",
]

# ---- AuralGuard label + attack_type constants ----
BINARY_BONAFIDE = 0
BINARY_SPOOF = 1
ATTACK_BONAFIDE = "bonafide"
ATTACK_SPOOF = "tts_vc"


def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"DECTE manifest not found: {path}")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_xtts_speakers(manifest: list[dict]) -> set[str]:
    """Speakers that have at least one successful XTTS v2 spoof."""
    return {
        r["source_speaker_id"] for r in manifest
        if r.get("generator_name") == "xtts_v2" and r.get("success", False)
    }


def deterministic_split(
    speakers: list[str], n_train: int, n_val: int, n_test: int, seed: int,
) -> tuple[set[str], set[str], set[str]]:
    """Sort -> shuffle with numpy default_rng(seed) -> slice."""
    import numpy as np
    if len(speakers) < n_train + n_val + n_test:
        raise ValueError(
            f"Only {len(speakers)} speakers available; need at least "
            f"{n_train + n_val + n_test}."
        )
    ordered = sorted(speakers)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(ordered))
    permuted = [ordered[i] for i in idx]
    train = set(permuted[:n_train])
    val = set(permuted[n_train:n_train + n_val])
    test = set(permuted[n_train + n_val:n_train + n_val + n_test])
    return train, val, test


def build_bonafide_rows(
    loader: DECTELoader, speakers: set[str], split_name: str,
) -> tuple[list[dict], set[str]]:
    """Bonafide CSV rows + the set of audio paths used (for leakage check)."""
    rows = []
    files_used = set()
    for utt in loader.utterances:
        if utt.speaker_id not in speakers:
            continue
        abs_path = str(Path(utt.audio_path).resolve())
        spk = loader.speakers.get(utt.speaker_id)
        gender = ""
        if spk is not None:
            g = (spk.gender or "").strip().lower()
            gender = "F" if g in ("female", "f") else ("M" if g in ("male", "m") else "")
        rows.append({
            "file_path": abs_path,
            "binary_label": BINARY_BONAFIDE,
            "attack_type": ATTACK_BONAFIDE,
            "start_fake": -1.0,
            "end_fake": -1,
            "dataset": "DECTE",
            "split": split_name,
            "accent": "Tyneside English",
            "gender": gender,
            "config": "",
            "text": utt.transcript.replace("\n", " ").replace("\r", " ").strip(),
            "speaker": utt.speaker_id,
        })
        files_used.add(abs_path)
    return rows, files_used


def build_spoof_rows(
    manifest: list[dict], speakers: set[str], split_name: str,
    loader: DECTELoader,
) -> tuple[list[dict], set[str]]:
    """XTTS spoof CSV rows + the set of output_paths used."""
    rows = []
    files_used = set()
    for entry in manifest:
        if entry.get("generator_name") != "xtts_v2":
            continue
        if not entry.get("success", False):
            continue
        spk_id = entry.get("source_speaker_id")
        if spk_id not in speakers:
            continue
        abs_path = str(Path(entry["output_path"]).resolve())
        spk = loader.speakers.get(spk_id)
        gender = ""
        if spk is not None:
            g = (spk.gender or "").strip().lower()
            gender = "F" if g in ("female", "f") else ("M" if g in ("male", "m") else "")
        rows.append({
            "file_path": abs_path,
            "binary_label": BINARY_SPOOF,
            "attack_type": ATTACK_SPOOF,
            "start_fake": 0.0,
            "end_fake": "full",
            "dataset": "DECTE",
            "split": split_name,
            "accent": "Tyneside English",
            "gender": gender,
            "config": "xtts_v2",
            "text": entry.get("input_transcript", "").replace("\n", " ").strip(),
            "speaker": spk_id,
        })
        files_used.add(abs_path)
    return rows, files_used


def leakage_check(
    train_speakers: set[str], val_speakers: set[str], test_speakers: set[str],
    train_files: set[str], val_files: set[str], test_files: set[str],
) -> list[str]:
    """Return a list of leakage errors (empty list = OK)."""
    errors = []
    for a_name, a, b_name, b in [
        ("train", train_speakers, "val", val_speakers),
        ("train", train_speakers, "test", test_speakers),
        ("val", val_speakers, "test", test_speakers),
    ]:
        overlap = a & b
        if overlap:
            errors.append(f"speaker overlap {a_name}<->{b_name}: {sorted(overlap)[:10]}")
    for a_name, a, b_name, b in [
        ("train", train_files, "val", val_files),
        ("train", train_files, "test", test_files),
        ("val", val_files, "test", test_files),
    ]:
        overlap = a & b
        if overlap:
            errors.append(f"file overlap {a_name}<->{b_name}: {len(overlap)} files")
    return errors


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _strip_spoofed_suffix(utt_id: str) -> str:
    return utt_id[: -len("_spoofed")] if utt_id.endswith("_spoofed") else utt_id


def resolve_decte_source_audio(
    source_utterance_id: str, audio_by_utt_id: dict[str, str],
) -> Path | None:
    """Resolve a DECTE spoof's source_utterance_id -> original bonafide audio.

    Fast path: exact lookup in DECTELoader's utterances index.
    Fallback: rglob under data/01_chunks/ for the chunk stem.
    Returns None if neither works.
    """
    stem = _strip_spoofed_suffix(source_utterance_id)
    if stem in audio_by_utt_id:
        p = Path(audio_by_utt_id[stem])
        if p.exists():
            return p
    matches = list(DECTE_AUDIO_DIR.rglob(f"{stem}.wav"))
    return matches[0] if matches else None


def build_test_manifest_rows(
    manifest: list[dict],
    test_speakers: set[str],
    loader: DECTELoader,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """Filter DECTE manifest to (xtts_v2, success, in-test-speakers) rows
    and ensure each carries a valid source_audio_path.

    Returns (rows_ready_to_write, unresolved_list). Any row where the
    matched original audio cannot be located is added to unresolved.
    Rows that already have a valid source_audio_path pass through
    unchanged (idempotent for post-Entry-4 manifests).
    """
    audio_by_utt_id = {u.utterance_id: u.audio_path for u in loader.utterances}

    rows_out: list[dict] = []
    unresolved: list[tuple[str, str]] = []

    for entry in manifest:
        if entry.get("generator_name") != "xtts_v2":
            continue
        if not entry.get("success", False):
            continue
        if entry.get("source_speaker_id") not in test_speakers:
            continue

        existing = entry.get("source_audio_path", "")
        if existing and Path(existing).exists():
            rows_out.append(entry)
            continue

        resolved = resolve_decte_source_audio(
            entry.get("source_utterance_id", ""), audio_by_utt_id
        )
        if resolved is None:
            unresolved.append((
                entry.get("source_utterance_id", "<missing>"),
                entry.get("source_speaker_id", "<missing>"),
            ))
            continue

        new_entry = dict(entry)
        new_entry["source_audio_path"] = str(resolved)
        rows_out.append(new_entry)

    return rows_out, unresolved


def write_test_manifest(rows: list[dict], path: Path) -> int:
    """Write the pre-validated rows list to a JSONL manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Build DECTE mitigation CSVs + test manifest.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing output files (default: refuse).")
    args = parser.parse_args()

    print("=" * 60)
    print("BUILD DECTE MITIGATION CSVs + TEST MANIFEST")
    print("=" * 60)

    # --- refuse to overwrite ---
    for out in (OUT_TRAIN_CSV, OUT_VAL_CSV, OUT_TEST_CSV, OUT_TEST_MANIFEST):
        if out.exists() and not args.force:
            print(f"ERROR: output file already exists: {out}")
            print("Refusing to overwrite. Re-run with --force if intentional.")
            sys.exit(1)

    # --- load manifest + DECTE loader (uses same paths as configs/spoof_gen.yaml) ---
    manifest = load_manifest(DECTE_MANIFEST)
    print(f"DECTE manifest rows loaded : {len(manifest)}")

    loader = DECTELoader(
        audio_dir=str(DECTE_AUDIO_DIR),
        metadata_path=str(DECTE_METADATA),
        transcripts_dir=str(DECTE_TRANSCRIPTS),
        target_sr=16000, min_duration=2.0, max_duration=15.0,
    )
    loader.load_speaker_metadata()
    loader.discover_audio_files()
    loader.build_utterance_list()

    bonafide_speakers = {u.speaker_id for u in loader.utterances}
    xtts_speakers = get_xtts_speakers(manifest)
    eligible = bonafide_speakers & xtts_speakers
    excluded_no_xtts = sorted(bonafide_speakers - xtts_speakers)
    excluded_no_bonafide = sorted(xtts_speakers - bonafide_speakers)

    print()
    print(f"Speakers with valid DECTE bonafide utterances : {len(bonafide_speakers)}")
    print(f"Speakers with successful xtts_v2 spoofs       : {len(xtts_speakers)}")
    print(f"Eligible intersection (bonafide AND XTTS)     : {len(eligible)}")
    print(f"Excluded (bonafide present but no XTTS spoof) : {len(excluded_no_xtts)}"
          + (f"  e.g. {excluded_no_xtts[:5]}" if excluded_no_xtts else ""))
    if excluded_no_bonafide:
        print(f"Excluded (XTTS spoof but no valid bonafide)   : {len(excluded_no_bonafide)}"
              f"  e.g. {excluded_no_bonafide[:5]}")

    if len(eligible) < N_TRAIN + N_VAL + N_TEST:
        print(f"\nERROR: only {len(eligible)} eligible speakers, need "
              f"{N_TRAIN + N_VAL + N_TEST}.")
        sys.exit(1)
    if len(eligible) != N_TRAIN + N_VAL + N_TEST:
        print(f"\nNOTE: eligible pool ({len(eligible)}) larger than split total "
              f"({N_TRAIN + N_VAL + N_TEST}); {len(eligible) - N_TRAIN - N_VAL - N_TEST} "
              f"speakers will be dropped from the alphabetical tail.")

    # --- deterministic 52/14/16 speaker split on the eligible pool ---
    train_spk, val_spk, test_spk = deterministic_split(
        sorted(eligible), N_TRAIN, N_VAL, N_TEST, seed=args.seed,
    )
    print()
    print(f"Final split sizes                             : "
          f"train={len(train_spk)}  val={len(val_spk)}  test={len(test_spk)}  "
          f"total={len(train_spk) + len(val_spk) + len(test_spk)}")

    # --- build per-split rows ---
    split_data = {}
    for name, speakers in (
        ("mitigation_train", train_spk),
        ("mitigation_val", val_spk),
        ("mitigation_test", test_spk),
    ):
        bon_rows, bon_files = build_bonafide_rows(loader, speakers, name)
        spf_rows, spf_files = build_spoof_rows(manifest, speakers, name, loader)
        split_data[name] = {
            "speakers": speakers,
            "rows": bon_rows + spf_rows,
            "files": bon_files | spf_files,
            "n_bon": len(bon_rows),
            "n_spf": len(spf_rows),
        }

    print()
    print(f"{'split':<20} {'speakers':>9} {'bonafide':>9} {'spoof':>7} {'total':>7}")
    print("-" * 55)
    for name in ("mitigation_train", "mitigation_val", "mitigation_test"):
        d = split_data[name]
        print(f"{name:<20} {len(d['speakers']):>9} "
              f"{d['n_bon']:>9} {d['n_spf']:>7} {d['n_bon']+d['n_spf']:>7}")
    total_xtts = sum(d["n_spf"] for d in split_data.values())
    print()
    print(f"Total XTTS spoof rows selected across all splits: {total_xtts} "
          f"(manifest has {sum(1 for r in manifest if r['generator_name']=='xtts_v2' and r['success'])})")

    # --- leakage checks BEFORE writing anything ---
    errors = leakage_check(
        split_data["mitigation_train"]["speakers"],
        split_data["mitigation_val"]["speakers"],
        split_data["mitigation_test"]["speakers"],
        split_data["mitigation_train"]["files"],
        split_data["mitigation_val"]["files"],
        split_data["mitigation_test"]["files"],
    )
    print()
    if errors:
        print("LEAKAGE CHECK: FAILED")
        for e in errors:
            print(f"  {e}")
        print("Refusing to write outputs. Investigate the split logic.")
        sys.exit(2)
    print("LEAKAGE CHECK: OK (speakers and files disjoint across all three splits)")

    # --- pre-validate held-out test manifest rows (must have source_audio_path) ---
    test_manifest_rows, unresolved = build_test_manifest_rows(
        manifest, split_data["mitigation_test"]["speakers"], loader,
    )
    print()
    print(f"Test-manifest rows to write         : {len(test_manifest_rows)}")
    print(f"Unresolved source_audio_path rows   : {len(unresolved)}")
    if unresolved:
        print("ABORT: cannot resolve original bonafide audio for these test-manifest rows:")
        for utt, spk in unresolved[:10]:
            print(f"  {utt}  (speaker {spk})")
        if len(unresolved) > 10:
            print(f"  ... and {len(unresolved) - 10} more")
        print("No files written. Investigate the manifest / DECTELoader before rerunning.")
        sys.exit(3)

    # --- write outputs ---
    write_csv(OUT_TRAIN_CSV, split_data["mitigation_train"]["rows"])
    write_csv(OUT_VAL_CSV, split_data["mitigation_val"]["rows"])
    write_csv(OUT_TEST_CSV, split_data["mitigation_test"]["rows"])
    n_test_manifest = write_test_manifest(test_manifest_rows, OUT_TEST_MANIFEST)

    print()
    print("Wrote outputs:")
    print(f"  {OUT_TRAIN_CSV}  ({split_data['mitigation_train']['n_bon']} bonafide + "
          f"{split_data['mitigation_train']['n_spf']} spoof)")
    print(f"  {OUT_VAL_CSV}  ({split_data['mitigation_val']['n_bon']} bonafide + "
          f"{split_data['mitigation_val']['n_spf']} spoof)")
    print(f"  {OUT_TEST_CSV}  ({split_data['mitigation_test']['n_bon']} bonafide + "
          f"{split_data['mitigation_test']['n_spf']} spoof)")
    print(f"  {OUT_TEST_MANIFEST}  ({n_test_manifest} XTTS entries for held-out DECTE eval)")

    print()
    print("Done. No training run, no checkpoint touched, no existing manifest modified.")


if __name__ == "__main__":
    main()
