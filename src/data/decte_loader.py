"""
DECTE Corpus Loader
====================
Loads audio and metadata from the Diachronic Electronic Corpus of Tyneside English.

DECTE structure (adapt paths to your actual download):
  - Audio: WAV files organized by interview/speaker
  - Transcripts: TEI-XML files with human-annotated transcriptions
  - Your Whisper transcripts: text files matching audio filenames

The loader pairs each audio segment with:
  1. Speaker metadata (gender, age, SES, recording era)
  2. Transcript text (from your Whisper transcriptions)
  3. Audio waveform (resampled to target SR)
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torchaudio
import torch
import re


def normalize_decte_stem(path_or_stem) -> str:
    stem = Path(path_or_stem).stem.lower()

    if "_chunk_" in stem:
        stem = stem.split("_chunk_")[0]

    if "_seg" in stem:
        stem = stem.split("_seg")[0]

    if stem.endswith("audio"):
        stem = stem[:-5]

    return stem



@dataclass
class DECTESpeaker:
    """Metadata for a single DECTE speaker."""
    speaker_id: str
    gender: str                          # "M" or "F"
    age_group: str                       # "young", "middle", "old"
    ses_class: str                       # socioeconomic status label
    recording_era: str                   # "1960s-70s", "1990s", "2007-2010"
    audio_files: list[str] = field(default_factory=list)
    transcript_files: list[str] = field(default_factory=list)


@dataclass
class Utterance:
    """A single utterance with all associated data."""
    utterance_id: str
    speaker_id: str
    audio_path: str
    transcript: str
    duration_sec: float
    sample_rate: int
    speaker_metadata: dict


class DECTELoader:
    """
    Load and organize the DECTE corpus for spoof generation.

    You'll need to adapt the parsing logic to match your actual
    DECTE file organization. The corpus comes as TEI-XML with audio.
    """

    def __init__(
        self,
        audio_dir: str,
        metadata_path: str,
        transcripts_dir: str,
        target_sr: int = 16000,
        min_duration: float = 2.0,
        max_duration: float = 15.0,
    ):
        self.audio_dir = Path(audio_dir)
        self.metadata_path = Path(metadata_path)
        self.transcripts_dir = Path(transcripts_dir)
        self.target_sr = target_sr
        self.min_duration = min_duration
        self.max_duration = max_duration

        self.speakers: dict[str, DECTESpeaker] = {}
        self.utterances: list[Utterance] = []

    def load_speaker_metadata(self) -> dict[str, DECTESpeaker]:
        """
        Load speaker metadata from your prepared JSON file.

        YOU MUST CREATE THIS FILE from the DECTE documentation.
        It maps speaker IDs to their social variables.

        Expected format of speaker_info.json:
        {
            "PVC_001": {
                "gender": "M",
                "age_group": "old",
                "ses_class": "working",
                "recording_era": "1960s-70s"
            },
            ...
        }
        """
        if not self.metadata_path.exists():
            print(f"WARNING: {self.metadata_path} not found.")
            print("Create speaker_info.json from DECTE documentation.")
            print("See docs/DECTE_METADATA_GUIDE.md for instructions.")
            return {}

        with open(self.metadata_path) as f:
            raw = json.load(f)

        for spk_id, meta in raw.items():
            self.speakers[spk_id] = DECTESpeaker(
                speaker_id=spk_id,
                gender=meta.get("gender", "unknown"),
                age_group=meta.get("age_group", "unknown"),
                ses_class=meta.get("ses_class", "unknown"),
                recording_era=meta.get("recording_era", "unknown"),
            )

        print(f"Loaded metadata for {len(self.speakers)} speakers")
        return self.speakers

    def discover_audio_files(self):
        """
        Scan the audio directory and associate files with speakers.

        ADAPT THIS to your actual DECTE file naming convention.
        Common patterns in DECTE:
          - Files named by interview ID (e.g., "INT001.wav")
          - Multiple speakers per interview file
          - Or pre-segmented per speaker

        If your audio is NOT pre-segmented by speaker, you'll need
        to use the DECTE time-alignments or your own VAD to segment.
        """
        audio_extensions = {".wav", ".flac", ".mp3"}

        for audio_file in sorted(self.audio_dir.rglob("*")):
            if audio_file.suffix.lower() not in audio_extensions:
                continue

            # --- DECTE filename parsing ---
            #
            # Example:
            # decten2y07i001audio.mp3
            #
            # We want:
            # i001


            spk_id = normalize_decte_stem(audio_file)

            

            # --- END DECTE parsing ---

            print(
                "DEBUG:",
                audio_file.name,
                "=>",
                spk_id,
                "MATCH:",
                spk_id in self.speakers
            )

            if spk_id in self.speakers:
                self.speakers[spk_id].audio_files.append(str(audio_file))

        total_files = sum(len(s.audio_files) for s in self.speakers.values())
        print(f"Discovered {total_files} audio files across {len(self.speakers)} speakers")

    def load_transcript(self, audio_path: str) -> Optional[str]:
        """
        Load transcript for a DECTE chunk audio file.

        Example:
        audio:
            decten1tlsg01audio_chunk_00001.wav

        transcript:
            decten1tlsg01audio_chunk_00001.txt
        """
        audio_stem_exact = Path(audio_path).stem.lower()

        # First: exact chunk transcript match
        txt_matches = list(self.transcripts_dir.rglob(f"{audio_stem_exact}.txt"))
        if txt_matches:
            return txt_matches[0].read_text(
                encoding="utf-8",
                errors="ignore"
            ).strip()

        # Second: fallback to normalized full-file transcript
        audio_stem_normalized = normalize_decte_stem(audio_path)

        txt_matches = list(self.transcripts_dir.rglob(f"{audio_stem_normalized}.txt"))
        if txt_matches:
            return txt_matches[0].read_text(
                encoding="utf-8",
                errors="ignore"
            ).strip()

        return None


    
    

    def load_audio(self, audio_path: str) -> tuple[torch.Tensor, int]:
        """Load and resample audio to target sample rate."""
        waveform, sr = torchaudio.load(audio_path)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Resample if needed
        if sr != self.target_sr:
            resampler = torchaudio.transforms.Resample(sr, self.target_sr)
            waveform = resampler(waveform)

        return waveform, self.target_sr

    def build_utterance_list(self) -> list[Utterance]:
        """
        Build the complete list of utterances with metadata and transcripts.
        Filters by duration constraints.
        """
        self.utterances = []

        for spk_id, speaker in self.speakers.items():
            for audio_path in speaker.audio_files:
                try:
                    info = sf.info(audio_path)
                    duration = info.duration
                    sample_rate=info.samplerate,
                except Exception as e:
                    print(f"  Skipping {audio_path}: {e}")
                    continue

                if duration < self.min_duration or duration > self.max_duration:
                    continue

                transcript = self.load_transcript(audio_path)
                if transcript is None or len(transcript.strip()) < 5:
                    continue  # XTTS needs text input

                utt = Utterance(
                    utterance_id=Path(audio_path).stem,
                    speaker_id=spk_id,
                    audio_path=audio_path,
                    transcript=transcript,
                    duration_sec=duration,
                    sample_rate=sf.info(audio_path).samplerate,
                    speaker_metadata=asdict(speaker),
                )
                self.utterances.append(utt)

        print(f"Built {len(self.utterances)} valid utterances")
        print(f"  Speakers with utterances: {len(set(u.speaker_id for u in self.utterances))}")

        # Print distribution summary
        self._print_distribution_summary()
        return self.utterances

    def _print_distribution_summary(self):
        """Print speaker distribution across social variables."""
        from collections import Counter

        speakers_with_data = {u.speaker_id for u in self.utterances}

        for var in ["gender", "age_group", "ses_class", "recording_era"]:
            counts = Counter()
            for spk_id in speakers_with_data:
                if spk_id in self.speakers:
                    val = getattr(self.speakers[spk_id], var, "unknown")
                    counts[val] += 1
            print(f"  {var}: {dict(counts)}")

    def get_speaker_utterances(self, speaker_id: str) -> list[Utterance]:
        """Get all utterances for a specific speaker."""
        return [u for u in self.utterances if u.speaker_id == speaker_id]

    def get_reference_and_target_utterances(
        self, speaker_id: str, n_reference: int = 3
    ) -> tuple[list[Utterance], list[Utterance]]:
        """
        Split a speaker's utterances into reference (for voice cloning)
        and target (text to synthesize as spoofs).

        Reference utterances provide the voice identity.
        Target utterances provide the text content to synthesize.
        """
        utts = self.get_speaker_utterances(speaker_id)
        if len(utts) <= n_reference:
            # Not enough utterances — use first half as ref, rest as target
            mid = max(1, len(utts) // 2)
            return utts[:mid], utts[mid:]

        return utts[:n_reference], utts[n_reference:]
