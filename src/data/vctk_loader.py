"""
VCTK Corpus Loader (Entry 4 control set)
=========================================
Standard-accent control set for the dialect-deepfake-bias thesis. Loads
VCTK 0.92 audio + transcripts + speaker metadata and exposes the same
interface as DECTELoader so SpoofPipeline can consume either loader
without knowing which corpus produced the utterances.

Interface contract shared with src.data.decte_loader:
  - load_speaker_metadata()
  - discover_audio_files()
  - build_utterance_list()
  - get_reference_and_target_utterances(speaker_id, n_reference)
  - .speakers        : dict[str, VCTKSpeaker]
  - .utterances      : list[Utterance]

VCTKSpeaker keeps the same attribute names (`gender`, `age_group`,
`ses_class`, `recording_era`) as DECTESpeaker so pipeline._save_manifest
can attach speaker metadata to each manifest record without any change.
VCTK-specific fields (`accent`, `region`) are stored alongside for
future manifest extension.

Does NOT modify DECTELoader, SpoofPipeline, or anything else.
"""

import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import soundfile as sf


# ---------------------------------------------------------------------------
# Data classes — Utterance shape matches src/data/decte_loader.py::Utterance
# ---------------------------------------------------------------------------

@dataclass
class VCTKSpeaker:
    """Metadata for a single VCTK speaker.

    Attribute names match DECTESpeaker so downstream code (notably
    pipeline._save_manifest) can attach them uniformly.
    """
    speaker_id: str
    gender: str              # 'female' / 'male'
    age_group: str           # '16-20', '21-30', ... (matches DECTE convention)
    ses_class: str           # 'unknown' — VCTK has no SES field
    recording_era: str       # 'vctk_2012_2019' (VCTK recording period)
    accent: str              # VCTK ACCENTS column value, e.g. 'English'
    region: str              # VCTK REGION value, e.g. 'Surrey'
    audio_files: list[str] = field(default_factory=list)
    transcript_files: list[str] = field(default_factory=list)


@dataclass
class Utterance:
    """Same shape as src.data.decte_loader.Utterance — downstream code
    doesn't need to know which corpus produced it."""
    utterance_id: str
    speaker_id: str
    audio_path: str
    transcript: str
    duration_sec: float
    sample_rate: int
    speaker_metadata: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_speaker_id(raw: str) -> str:
    """VCTK folders are 'pXXX' or 'sX'; speaker-info.txt IDs can be 'pXXX',
    'XXX', 'sXXX'. Canonicalize both sides to lowercase 'pXXX' / 'sX'."""
    s = str(raw).strip().lower()
    return f"p{s}" if s.isdigit() else s


def _age_to_group(age_str: str) -> str:
    """Bucket a numeric age to a DECTE-style decade band."""
    try:
        age = int(str(age_str).strip())
    except (ValueError, TypeError):
        return "unknown"
    if age <= 15: return "0-15"
    if age <= 20: return "16-20"
    if age <= 30: return "21-30"
    if age <= 40: return "31-40"
    if age <= 50: return "41-50"
    if age <= 60: return "51-60"
    if age <= 70: return "61-70"
    if age <= 80: return "71-80"
    return "81-90"


def _utterance_stem(audio_path: str) -> str:
    """'p225_001_mic1.flac' -> 'p225_001'."""
    stem = Path(audio_path).stem
    if stem.endswith("_mic1") or stem.endswith("_mic2"):
        stem = stem.rsplit("_mic", 1)[0]
    return stem


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

class VCTKLoader:
    """Load and organize the VCTK 0.92 corpus for spoof generation.

    Only reads data. Reproduces DECTELoader's public surface exactly so
    the existing SpoofPipeline can consume it once a small dispatch is
    added (see this session's notes; not applied here).
    """

    def __init__(
        self,
        audio_dir: str,               # data/vctk/wav48_silence_trimmed
        transcripts_dir: str,         # data/vctk/txt
        speaker_info_path: str,       # data/vctk/speaker-info.txt
        accent_filter: Optional[str] = "English",  # None => keep all accents
        target_sr: int = 16000,
        min_duration: float = 2.0,
        max_duration: float = 15.0,
    ):
        self.audio_dir = Path(audio_dir)
        self.transcripts_dir = Path(transcripts_dir)
        self.speaker_info_path = Path(speaker_info_path)
        self.accent_filter = accent_filter
        self.target_sr = target_sr
        self.min_duration = min_duration
        self.max_duration = max_duration

        self.speakers: dict[str, VCTKSpeaker] = {}
        self.utterances: list[Utterance] = []

    # ---------- Phase 1a: metadata ----------

    def load_speaker_metadata(self) -> dict[str, VCTKSpeaker]:
        """Parse speaker-info.txt into self.speakers, applying accent_filter."""
        if not self.speaker_info_path.exists():
            print(f"WARNING: {self.speaker_info_path} not found.")
            return {}

        raw = self.speaker_info_path.read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines()

        # accent match is case- and whitespace-insensitive
        want = None if self.accent_filter is None else self.accent_filter.strip().lower()

        for line in raw[1:]:  # skip header row
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            tokens = line.split()
            if len(tokens) < 4:
                continue

            spk_raw, age, gender, accents = tokens[0], tokens[1], tokens[2], tokens[3]

            # REGION is columns 5+, minus any trailing "(...)" COMMENTS.
            rest = " ".join(tokens[4:]).strip()
            rest = re.sub(r"\s*\([^)]*\)\s*$", "", rest).strip()

            if want is not None and accents.strip().lower() != want:
                continue

            spk_id = _normalize_speaker_id(spk_raw)

            self.speakers[spk_id] = VCTKSpeaker(
                speaker_id=spk_id,
                gender="female" if gender.strip().upper().startswith("F") else "male",
                age_group=_age_to_group(age),
                ses_class="unknown",
                recording_era="vctk_2012_2019",
                accent=accents.strip(),
                region=rest or "unknown",
            )

        print(f"Loaded metadata for {len(self.speakers)} VCTK speakers "
              f"(accent filter: {self.accent_filter or 'none'})")
        return self.speakers

    # ---------- Phase 1b: audio discovery ----------

    def _detect_audio_pattern(self) -> Optional[str]:
        """Prefer _mic1.flac (VCTK 0.92); fall back to any .flac then .wav."""
        for d in self.audio_dir.iterdir() if self.audio_dir.exists() else []:
            if not d.is_dir():
                continue
            for pat in ("*_mic1.flac", "*.flac", "*.wav"):
                if any(d.glob(pat)):
                    return pat
        return None

    def discover_audio_files(self):
        """Attach audio files to each already-loaded VCTKSpeaker."""
        pattern = self._detect_audio_pattern()
        if pattern is None:
            print(f"WARNING: no recognizable audio under {self.audio_dir}")
            return

        total_files = 0
        for spk_id in list(self.speakers.keys()):
            spk_dir = self.audio_dir / spk_id
            if not spk_dir.exists():
                continue
            for audio_file in sorted(spk_dir.glob(pattern)):
                self.speakers[spk_id].audio_files.append(str(audio_file))
                total_files += 1

        n_with = sum(1 for s in self.speakers.values() if s.audio_files)
        print(f"Discovered {total_files} audio files across {n_with} speakers "
              f"(pattern {pattern})")

    # ---------- Phase 1c: transcript lookup ----------

    def load_transcript(self, audio_path: str) -> Optional[str]:
        """Locate the matching .txt under txt/pXXX/ for a given audio path."""
        stem = _utterance_stem(audio_path)
        spk_id = stem.split("_")[0]  # 'p225' from 'p225_001'
        txt_path = self.transcripts_dir / spk_id / f"{stem}.txt"
        if not txt_path.exists():
            return None
        return txt_path.read_text(encoding="utf-8", errors="ignore").strip()

    # ---------- Phase 1d: build utterance list ----------

    def build_utterance_list(self) -> list[Utterance]:
        """Assemble Utterance objects with duration + transcript filtering."""
        self.utterances = []
        skipped_short = skipped_long = skipped_no_txt = skipped_error = 0

        for spk_id, speaker in self.speakers.items():
            for audio_path in speaker.audio_files:
                try:
                    info = sf.info(audio_path)
                    duration = info.duration
                    sr = info.samplerate
                except Exception:
                    skipped_error += 1
                    continue

                if duration < self.min_duration:
                    skipped_short += 1
                    continue
                if duration > self.max_duration:
                    skipped_long += 1
                    continue

                transcript = self.load_transcript(audio_path)
                if transcript is None or len(transcript.strip()) < 5:
                    skipped_no_txt += 1
                    continue

                self.utterances.append(Utterance(
                    utterance_id=_utterance_stem(audio_path),
                    speaker_id=spk_id,
                    audio_path=audio_path,
                    transcript=transcript,
                    duration_sec=duration,
                    sample_rate=sr,
                    speaker_metadata=asdict(speaker),
                ))

        print(f"Built {len(self.utterances)} valid VCTK utterances "
              f"(skipped: {skipped_short} short, {skipped_long} long, "
              f"{skipped_no_txt} no-transcript, {skipped_error} read-error)")
        spk_with_utts = {u.speaker_id for u in self.utterances}
        print(f"  Speakers with utterances: {len(spk_with_utts)}")
        self._print_distribution_summary()
        return self.utterances

    def _print_distribution_summary(self):
        spk_with_utts = {u.speaker_id for u in self.utterances}
        for var in ("gender", "age_group", "accent", "region"):
            counts = Counter()
            for spk_id in spk_with_utts:
                if spk_id in self.speakers:
                    counts[getattr(self.speakers[spk_id], var, "unknown")] += 1
            # Cap "region" output to top 10 to keep the log readable
            items = counts.most_common(10) if var == "region" else counts.items()
            print(f"  {var}: {dict(items)}")

    # ---------- Reference / target selection (used by SpoofPipeline) ----------

    def get_speaker_utterances(self, speaker_id: str) -> list[Utterance]:
        return [u for u in self.utterances if u.speaker_id == speaker_id]

    def get_reference_and_target_utterances(
        self, speaker_id: str, n_reference: int = 3
    ) -> tuple[list[Utterance], list[Utterance]]:
        """Same split rule as DECTELoader: first n_reference utts are the
        voice-identity references, the rest are candidate text targets."""
        utts = self.get_speaker_utterances(speaker_id)
        if len(utts) <= n_reference:
            mid = max(1, len(utts) // 2)
            return utts[:mid], utts[mid:]
        return utts[:n_reference], utts[n_reference:]
