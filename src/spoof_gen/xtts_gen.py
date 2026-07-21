"""
XTTS v2 Spoof Generator
========================
Uses Coqui TTS library to perform zero-shot voice cloning.
This is the primary generator — start here, validate pipeline, then add others.

XTTS v2 works by:
  1. Taking a reference audio clip (3-10 sec) of the target speaker
  2. Taking input text
  3. Generating new speech in the target speaker's voice saying the input text

This is particularly interesting for our study because XTTS was trained
predominantly on standard English, so its ability to reproduce Tyneside
dialect features is itself an interesting variable.
"""

import time
from pathlib import Path

import torch
import torchaudio
import soundfile as sf

from .base import BaseSpoofGenerator, SpoofResult


class XTTSGenerator(BaseSpoofGenerator):
    """Generate spoofs using Coqui XTTS v2."""

    def __init__(
        self,
        output_dir: str,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: str = "cuda",
        target_sr: int = 16000,
    ):
        super().__init__(name="xtts_v2", output_dir=output_dir, device=device)
        self.model_name = model_name
        self.target_sr = target_sr
        self.model = None

    def load_model(self):
        """Load XTTS v2 model via Coqui TTS."""
        from TTS.api import TTS

        print(f"Loading XTTS v2 model on {self.device}...")
        self.model = TTS(model_name=self.model_name).to(self.device)
        print("XTTS v2 loaded successfully")

    def _prepare_reference(
        self, reference_audio_paths: list[str], max_duration: float = 10.0
    ) -> str:
        """
        Prepare a single reference audio file from potentially multiple sources.
        XTTS works best with 6-10 seconds of clean reference audio.

        If multiple reference files provided, concatenate up to max_duration.
        """
        if len(reference_audio_paths) == 1:
            return reference_audio_paths[0]

        # Concatenate multiple reference files
        chunks = []
        total_duration = 0.0

        for ref_path in reference_audio_paths:
            waveform, sr = torchaudio.load(ref_path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            if sr != self.target_sr:
                waveform = torchaudio.transforms.Resample(sr, self.target_sr)(waveform)

            duration = waveform.shape[1] / self.target_sr
            if total_duration + duration > max_duration:
                # Take only what we need
                remaining = max_duration - total_duration
                samples_needed = int(remaining * self.target_sr)
                waveform = waveform[:, :samples_needed]
                chunks.append(waveform)
                break

            chunks.append(waveform)
            total_duration += duration

        combined = torch.cat(chunks, dim=1)

        # Save to temp file
        ref_output = self.output_dir / "_temp_reference.wav"
        torchaudio.save(str(ref_output), combined, self.target_sr)
        return str(ref_output)

    def generate(
        self,
        text: str,
        reference_audio_paths: list[str],
        output_path: str,
        language: str = "en",
    ) -> SpoofResult:
        """Generate a spoofed utterance using XTTS v2 voice cloning."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()

        try:
            # Prepare reference audio
            ref_path = self._prepare_reference(reference_audio_paths)

            # Generate with XTTS
            # tts_to_file handles everything: voice cloning + synthesis
            self.model.tts_to_file(
                text=text,
                speaker_wav=ref_path,
                language=language,
                file_path=output_path,
            )

            # Verify output exists and resample to target SR if needed
            if Path(output_path).exists():
                waveform, sr = torchaudio.load(output_path)
                if sr != self.target_sr:
                    waveform = torchaudio.transforms.Resample(sr, self.target_sr)(waveform)
                    torchaudio.save(output_path, waveform, self.target_sr)

            gen_time = time.time() - start_time

            return SpoofResult(
                source_utterance_id=Path(output_path).stem,
                source_speaker_id="",  # filled by pipeline
                generator_name=self.name,
                output_path=output_path,
                reference_audio_paths=reference_audio_paths,
                input_transcript=text,
                success=True,
                generation_time_sec=gen_time,
            )

        except Exception as e:
            gen_time = time.time() - start_time
            return SpoofResult(
                source_utterance_id=Path(output_path).stem,
                source_speaker_id="",
                generator_name=self.name,
                output_path=output_path,
                reference_audio_paths=reference_audio_paths,
                input_transcript=text,
                success=False,
                error_message=str(e),
                generation_time_sec=gen_time,
            )

    def cleanup(self):
        """Release GPU memory."""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        # Clean temp reference file
        temp_ref = self.output_dir / "_temp_reference.wav"
        if temp_ref.exists():
            temp_ref.unlink()
