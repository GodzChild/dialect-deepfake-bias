from pathlib import Path
import json
import re

TRANSCRIPT_ROOT = Path("data/decte/transcripts/Original")
OUT_PATH = Path("data/decte/metadata/speaker_info.json")


def clean_stem(path: Path) -> str:
    stem = path.stem.lower()
    if stem.endswith("audio"):
        stem = stem[:-5]
    return stem


def get_value(line: str, field: str):
    pattern = rf"<\s*{field}\s*:\s*(.*?)\s*>"
    match = re.search(pattern, line, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_file(path: Path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    file_id = clean_stem(path)
    recording_era = "unknown"
    speakers = []

    # Get recording era
    for i, line in enumerate(lines):
        if "TIME PERIOD OF INTERVIEW" in line.upper():
            if i + 1 < len(lines):
                recording_era = lines[i + 1].replace("<", "").replace(">", "").strip()
            break

    current = None

    for line in lines:
        line = line.strip()

        # Start a new speaker when we see Informant code
        if "Informant" in line and ("Primary Speaker" in line or "Secondary Speaker" in line):
            if current:
                speakers.append(current)

            match = re.search(r"Informant\s+([A-Za-z0-9]+)", line, re.IGNORECASE)
            speaker_id = match.group(1).lower() if match else "unknown"

            role = "primary" if "Primary Speaker" in line else "secondary"

            current = {
                "file_id": file_id,
                "speaker_id": speaker_id,
                "role": role,
                "gender": "unknown",
                "age_group": "unknown",
                "education": "unknown",
                "occupation": "unknown",
                "residence": "unknown",
                "recording_era": recording_era,
            }

            continue

        if current:
            value = get_value(line, "Gender")
            if value:
                current["gender"] = value.lower()
                continue

            value = get_value(line, "Age")
            if value:
                current["age_group"] = value
                continue

            value = get_value(line, "Education")
            if value:
                current["education"] = value
                continue

            value = get_value(line, "Occupation")
            if value:
                current["occupation"] = value
                continue

            value = get_value(line, "Residence")
            if value:
                current["residence"] = value
                continue

    if current:
        speakers.append(current)

    return speakers


def main():
    all_speakers = {}

    txt_files = sorted(TRANSCRIPT_ROOT.rglob("*.txt"))

    for path in txt_files:
        for speaker in parse_file(path):
            sid = speaker["speaker_id"]
            if sid not in {"unknown", "code"}:
                all_speakers[sid] = speaker

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(all_speakers, indent=2), encoding="utf-8")

    print("Found transcript files:", len(txt_files))
    print("Extracted speakers:", len(all_speakers))
    print("Saved to:", OUT_PATH)

    for test_id in ["pvc01a", "pvc03a", "pvc03b"]:
        if test_id in all_speakers:
            print(f"\nExample {test_id}:")
            print(json.dumps(all_speakers[test_id], indent=2))


if __name__ == "__main__":
    main()