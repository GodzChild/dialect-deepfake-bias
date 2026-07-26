#!/usr/bin/env python3
"""
Script 00b: Verify VCTK Layout for Entry 4 Control Set
=======================================================
Filesystem-only inspection of a downloaded VCTK corpus. Confirms the
expected folder tree exists, counts usable utterances per speaker,
parses speaker-info.txt, prints the accent/region distribution, and
reports whether Southern British English alone has enough eligible
speakers (>= 20 with >= 8 usable utterances) for the planned Entry 4
control set (20 speakers x 5 target + 3 reference utterances).

Does not:
  - read any audio content
  - touch data/generated_spoofs/ or data/decte/ or existing configs
  - create or modify any pipeline / loader / detector code
  - download anything
  - commit anything

Expected layout after you extract VCTK 0.92 into data/vctk/:

  data/vctk/
    wav48_silence_trimmed/
      p225/
        p225_001_mic1.flac
        p225_001_mic2.flac
        ...
      p226/
      ...
    txt/
      p225/
        p225_001.txt
        ...
    speaker-info.txt

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/00b_verify_vctk_layout.py
"""

import re
import sys
from collections import Counter
from pathlib import Path


VCTK_ROOT = Path("data/vctk")
AUDIO_DIR = VCTK_ROOT / "wav48_silence_trimmed"
TXT_DIR = VCTK_ROOT / "txt"
INFO_FILE = VCTK_ROOT / "speaker-info.txt"

# Entry 4 protocol constants (match the Phase 1 spoof-gen defaults).
N_REFERENCE = 3
MAX_UTTS_PER_SPEAKER = 5
MIN_USABLE_UTTS = N_REFERENCE + MAX_UTTS_PER_SPEAKER   # -> 8
TARGET_SPEAKER_COUNT = 20

# ---------------------------------------------------------------------------
# Strict Southern British English region list.
# VCTK's REGION column is free-form; these are exact case-insensitive matches
# after whitespace collapse. Bare "England" is INTENTIONALLY EXCLUDED because
# it can include northern speakers (e.g. Newcastle) -- add it here only if
# the printed distribution below shows the "England"-only rows are all
# clearly southern.
# ---------------------------------------------------------------------------
STRICT_SBE_REGIONS = [
    # South East England
    "southern england",
    "london",
    "surrey",
    "kent",
    "sussex", "east sussex", "west sussex",
    "berkshire", "reading",
    "hampshire", "southampton",
    "essex",
    "hertfordshire",
    "middlesex",
    "buckinghamshire",
    "oxfordshire", "oxford",
    "isle of wight",
    # South West England
    "somerset", "devon", "wiltshire", "cornwall", "dorset", "gloucestershire",
]


def normalize(s: str) -> str:
    """Lowercase + collapse whitespace + strip. For robust matching."""
    return " ".join(str(s).strip().split()).lower()


STRICT_SBE_SET = {normalize(r) for r in STRICT_SBE_REGIONS}


def check_paths() -> bool:
    """Verify base tree exists. Prints per-path OK/MISSING and returns
    True only when all four required paths exist."""
    all_ok = True
    for label, p in [
        ("data/vctk/", VCTK_ROOT),
        ("data/vctk/wav48_silence_trimmed/", AUDIO_DIR),
        ("data/vctk/txt/", TXT_DIR),
        ("data/vctk/speaker-info.txt", INFO_FILE),
    ]:
        exists = p.exists()
        status = "OK     " if exists else "MISSING"
        print(f"  {status}  {label}")
        if not exists:
            all_ok = False
    return all_ok


def detect_audio_pattern(sample_speaker_dir: Path) -> tuple[str, str]:
    """Return (glob_pattern, human_label) for how utterance files are named.
    Prefers _mic1.flac (VCTK 0.92), falls back to any .flac, then .wav."""
    if any(sample_speaker_dir.glob("*_mic1.flac")):
        return ("*_mic1.flac", "_mic1.flac (VCTK 0.92)")
    if any(sample_speaker_dir.glob("*.flac")):
        return ("*.flac", ".flac (unknown VCTK variant)")
    if any(sample_speaker_dir.glob("*.wav")):
        return ("*.wav", ".wav (older VCTK)")
    return ("", "UNKNOWN (no audio files found)")


def utterance_id(audio_path: Path, pattern_label: str) -> str:
    """Turn 'p225_001_mic1.flac' -> 'p225_001'. For .wav it's just the stem."""
    stem = audio_path.stem
    if stem.endswith("_mic1") or stem.endswith("_mic2"):
        stem = stem.rsplit("_mic", 1)[0]
    return stem


def count_usable_utts(speaker_dir: Path, audio_pattern: str) -> int:
    """Number of utterances with BOTH audio and matching .txt on disk."""
    txt_speaker_dir = TXT_DIR / speaker_dir.name
    if not txt_speaker_dir.exists():
        return 0
    audio_ids = {
        utterance_id(f, audio_pattern) for f in speaker_dir.glob(audio_pattern)
    }
    txt_ids = {f.stem for f in txt_speaker_dir.glob("*.txt")}
    return len(audio_ids & txt_ids)


def parse_speaker_info() -> tuple[list[dict], list[str]]:
    """Parse speaker-info.txt into a list of dicts. Also returns the raw
    first 3 lines so the caller can eyeball the format."""
    raw = INFO_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    first_three = raw[:3]

    rows = []
    for line in raw[1:]:  # skip the ID/AGE/... header
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Split on whitespace: ID AGE GENDER ACCENTS [REGION ...] [COMMENTS]
        tokens = line.split()
        if len(tokens) < 4:
            continue
        speaker_id_raw = tokens[0]
        age = tokens[1]
        gender = tokens[2]
        accents = tokens[3]
        # Everything after col 4 is REGION [+ COMMENTS]. Strip trailing
        # parenthesised comments like "(?)".
        rest = " ".join(tokens[4:]).strip()
        rest = re.sub(r"\s*\([^)]*\)\s*$", "", rest).strip()
        rows.append({
            "id_raw": speaker_id_raw,
            "age": age,
            "gender": gender,
            "accents": accents,
            "region": rest,
        })
    return rows, first_three


def normalize_speaker_id(raw: str) -> str:
    """Canonicalize VCTK speaker IDs so folder names and speaker-info.txt IDs
    hash to the same key. Applied on BOTH sides:

      '225'   -> 'p225'
      'p225'  -> 'p225'
      'P225'  -> 'p225'
      's5'    -> 's5'
      'S5'    -> 's5'

    Some VCTK releases store the ID as a bare number, others already prefix
    it with 'p'. Older speaker-info files also occasionally use uppercase
    for the sXXX (Scottish) IDs. This makes both sides match.
    """
    s = str(raw).strip().lower()
    if s.isdigit():
        return f"p{s}"
    return s


def match_sbe_strict(region: str) -> bool:
    return normalize(region) in STRICT_SBE_SET


def match_sbe_loose(accents: str) -> bool:
    return normalize(accents) == "english"


def main() -> int:
    print("=" * 60)
    print("VCTK LAYOUT VERIFICATION")
    print("=" * 60)

    if not check_paths():
        print()
        print("ERROR: one or more expected paths are missing.")
        print("Download VCTK 0.92 from Edinburgh DataShare (10283/3443)")
        print("and extract it so the tree above exists, then rerun.")
        return 1

    # --- audio file pattern detection ---
    speaker_dirs = sorted(d for d in AUDIO_DIR.iterdir() if d.is_dir())
    if not speaker_dirs:
        print(f"\nERROR: no speaker subfolders under {AUDIO_DIR}")
        return 1
    pattern, pattern_label = detect_audio_pattern(speaker_dirs[0])
    if not pattern:
        print(f"\nERROR: cannot detect an audio file pattern in {speaker_dirs[0]}")
        return 1
    print(f"\nDetected audio suffix               : {pattern_label}")
    print(f"Speakers on disk                    : {len(speaker_dirs)}")

    # --- per-speaker usable-utterance counts ---
    per_speaker_counts = {}
    for d in speaker_dirs:
        per_speaker_counts[d.name] = count_usable_utts(d, pattern)

    total_utts = sum(per_speaker_counts.values())
    counts_vals = sorted(per_speaker_counts.values())
    median = counts_vals[len(counts_vals) // 2] if counts_vals else 0
    n_ge_min = sum(1 for c in counts_vals if c >= MIN_USABLE_UTTS)
    print(f"Usable utterances (audio+txt) total : {total_utts}")
    print(f"  min per speaker                   : {min(counts_vals) if counts_vals else 0}")
    print(f"  median per speaker                : {median}")
    print(f"  max per speaker                   : {max(counts_vals) if counts_vals else 0}")
    print(f"  with >= {MIN_USABLE_UTTS} usable utterances       : "
          f"{n_ge_min}/{len(speaker_dirs)}")

    # --- speaker-info.txt parse ---
    metadata_rows, first_three = parse_speaker_info()
    print("\nspeaker-info.txt first 3 lines:")
    for line in first_three:
        print(f"  {line}")

    by_id = {normalize_speaker_id(r["id_raw"]): r for r in metadata_rows}
    print(f"\nMetadata rows                       : {len(metadata_rows)}")
    missing_meta = [
        d.name for d in speaker_dirs
        if normalize_speaker_id(d.name) not in by_id
    ]
    print(f"Speakers on disk, missing metadata  : {len(missing_meta)}"
          + (f"  {missing_meta[:10]}" if missing_meta else ""))

    # --- accent + region distributions ---
    def meta_for(folder_name):
        return by_id.get(normalize_speaker_id(folder_name))

    accent_counter = Counter(
        (meta_for(d.name) or {}).get("accents", "MISSING") for d in speaker_dirs
    )
    print("\nAccent distribution (top 10):")
    for a, c in accent_counter.most_common(10):
        print(f"  {a:<15} : {c}")

    english_regions = Counter(
        (meta_for(d.name) or {}).get("region", "")
        for d in speaker_dirs
        if match_sbe_loose((meta_for(d.name) or {}).get("accents", ""))
    )
    print("\nRegion distribution for ACCENTS=English speakers (top 15):")
    for r, c in english_regions.most_common(15):
        label = r if r else "(blank)"
        marker = "  <SBE>" if normalize(r) in STRICT_SBE_SET else ""
        print(f"  {label:<30} : {c}{marker}")

    # --- SBE eligibility ---
    strict = []
    loose = []
    for d in speaker_dirs:
        meta = meta_for(d.name)
        if not meta:
            continue
        if match_sbe_strict(meta["region"]):
            strict.append((d.name, meta, per_speaker_counts[d.name]))
        if match_sbe_loose(meta["accents"]):
            loose.append((d.name, meta, per_speaker_counts[d.name]))

    def summarise(name, group):
        eligible = [(spk, m, n) for spk, m, n in group if n >= MIN_USABLE_UTTS]
        genders = Counter(m["gender"] for _, m, _ in eligible)
        print(f"\n{name}:")
        print(f"  matching speakers                 : {len(group)}")
        print(f"  with >= {MIN_USABLE_UTTS} usable utterances       : {len(eligible)}")
        print(f"  gender balance                    : "
              f"{genders.get('F', 0)}F / {genders.get('M', 0)}M")
        return len(eligible)

    print("\n--- SBE eligibility ---")
    n_strict = summarise("Strict SBE (English + southern region list)", strict)
    n_loose = summarise("Loose SBE (ACCENTS==English, any region)", loose)

    n_all_eligible = n_ge_min

    print()
    print("=" * 60)
    if n_strict >= TARGET_SPEAKER_COUNT:
        print(f"VERDICT: SBE-STRICT-OK  "
              f"({n_strict} strict-SBE eligible, need {TARGET_SPEAKER_COUNT})")
        print("Proceed with strict Southern British English for Entry 4.")
    elif n_loose >= TARGET_SPEAKER_COUNT:
        print(f"VERDICT: SBE-LOOSE-OK  "
              f"(strict={n_strict}, loose={n_loose}, need {TARGET_SPEAKER_COUNT})")
        print("Strict SBE is too small. Recommend loose SBE (all English-accent")
        print("VCTK speakers). Record each speaker's region label alongside.")
    elif n_all_eligible >= TARGET_SPEAKER_COUNT:
        print(f"VERDICT: SBE-INSUFFICIENT  "
              f"(strict={n_strict}, loose={n_loose}, "
              f"all-VCTK={n_all_eligible}, need {TARGET_SPEAKER_COUNT})")
        print("Even loose SBE is too small. Fall back to all-VCTK; preserve")
        print("accent labels so the accent mix can be reported in Entry 4.")
    else:
        print(f"VERDICT: TOTAL-INSUFFICIENT  "
              f"(only {n_all_eligible} speakers overall have >= {MIN_USABLE_UTTS} "
              f"usable utterances, need {TARGET_SPEAKER_COUNT})")
        print("Check the VCTK download -- something is likely incomplete.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
