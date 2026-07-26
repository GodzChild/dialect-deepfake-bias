"""
Abstract base class for spoof generators.
Each TTS/VC system implements this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import torch


@dataclass
class SpoofResult:
    """Result of generating a single spoofed utterance."""
    source_utterance_id: str
    source_speaker_id: str
    generator_name: str
    output_path: str
    reference_audio_paths: list[str]
    input_transcript: str
    success: bool
    error_message: str = ""
    generation_time_sec: float = 0.0
    # Populated by SpoofPipeline.run() -- enables the matched
    # "original vs spoof" bonafide pairing in build_evaluation_pairs.
    # Defaults preserve backward compat with pre-schema-change manifests.
    source_audio_path: str = ""
    corpus: str = ""


class BaseSpoofGenerator(ABC):
    """
    Interface for TTS/VC spoof generation systems.
    Each system (XTTS, OpenVoice, etc.) implements this.
    """

    def __init__(self, name: str, output_dir: str, device: str = "cuda"):
        self.name = name
        self.output_dir = Path(output_dir) / name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = device

    @abstractmethod
    def load_model(self):
        """Load the TTS/VC model weights."""
        ...

    @abstractmethod
    def generate(
        self,
        text: str,
        reference_audio_paths: list[str],
        output_path: str,
        language: str = "en",
    ) -> SpoofResult:
        """
        Generate a spoofed utterance.

        Args:
            text: Transcript to synthesize.
            reference_audio_paths: Audio files providing speaker identity.
            output_path: Where to save the generated audio.
            language: Language code.

        Returns:
            SpoofResult with generation outcome.
        """
        ...

    @abstractmethod
    def cleanup(self):
        """Release model resources."""
        ...
