"""Build an audio-stem-keyed metadata JSON from the per-speaker extractor
output, so the Phase 1 DECTELoader can match audio files to metadata.

Bridge rule (same collapse logic as scripts/03_run_detectors.py):
  - If all speakers in an interview share the same value -> keep it.
  - If they disagree -> "mixed".
  - If no metadata for that interview -> "unknown".

Read : data/decte/metadata/speaker_info.json          (per-speaker, e.g. pvc03a)
       data/01_chunks/**/*.wav                        (audio-stem IDs)
Write: data/decte/metadata/speaker_info_by_audio.json (audio-stem keyed)
"""

import json
import re
from collections import defaultdict
from pathlib import Path

FIELDS = (
    "gender", "age_group", "ses_class", "recording_era",
    "education", "occupation", "residence",
)

# Keys the DECTELoader looks up directly:
CORE_FIELDS = ("gender", "age_group", "ses_class", "recording_era")


def audio_stem(p: Path) -> str:
    """Normalize a chunk filename to its interview-level audio stem.

    Mirrors src/data/decte_loader.normalize_decte_stem so keys line up
    with what discover_audio_files() derives.
    """
    stem = p.stem.lower()
    if "_chunk_" in stem:
        stem = stem.split("_chunk_")[0]
    if stem.endswith("audio"):
        stem = stem[:-5]
    return stem


def audio_interview_code(audio_stem_id: str) -> str:
    """decten1pvc03 -> pvc03,  decten2y07i001 -> y07i001"""
    m = re.match(r"decten\d(.+)", audio_stem_id)
    return m.group(1) if m else audio_stem_id


def speaker_interview_code(spk_key: str) -> str:
    """pvc03a -> pvc03,  y07i001a -> y07i001,  pvc03 -> pvc03"""
    m = re.match(r"^(.+\d)[a-z]$", spk_key)
    return m.group(1) if m else spk_key


def collapse(values):
    values = [v for v in values if v and v != "unknown"]
    if not values:
        return "unknown"
    uniq = set(values)
    return uniq.pop() if len(uniq) == 1 else "mixed"


def main():
    per_speaker_path = Path("data/decte/metadata/speaker_info.json")
    per_speaker = json.loads(per_speaker_path.read_text(encoding="utf-8"))

    audio_stems = sorted({audio_stem(p) for p in Path("data/01_chunks").rglob("*.wav")})

    # Bucket per-speaker entries by interview code
    by_code: dict[str, list[dict]] = defaultdict(list)
    by_code_keys: dict[str, list[str]] = defaultdict(list)
    for spk_key, meta in per_speaker.items():
        code = speaker_interview_code(spk_key)
        by_code[code].append(meta)
        by_code_keys[code].append(spk_key)

    out: dict[str, dict] = {}
    for stem in audio_stems:
        code = audio_interview_code(stem)
        speakers = by_code.get(code, [])
        entry = {f: collapse(s.get(f) for s in speakers) for f in FIELDS}
        entry["source_speaker_keys"] = sorted(by_code_keys.get(code, []))
        out[stem] = entry

    out_path = Path("data/decte/metadata/speaker_info_by_audio.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    with_meta = sum(1 for v in out.values() if v["gender"] != "unknown")
    core_complete = sum(
        1 for v in out.values()
        if all(v[f] not in ("unknown", "") for f in CORE_FIELDS)
    )

    print(f"Wrote {len(out)} audio-stem entries -> {out_path}")
    print(f"  audio stems with any metadata (gender != unknown): {with_meta}")
    print(f"  audio stems complete on core fields              : {core_complete}")
    print(f"  per-speaker input entries                        : {len(per_speaker)}")


if __name__ == "__main__":
    main()
