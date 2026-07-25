"""
OpenVoice V2 Spoof Generator
=============================
Two-stage voice cloning:
  1. MeloTTS synthesises the input text in a neutral base voice.
  2. OpenVoice ToneColorConverter retargets the tone colour to the
     DECTE reference audio, producing the final spoofed clip.

Runs in a dedicated `openvoice` conda env — do NOT try to import this
module from `dialectbias` or `spoofgen`, its dependencies are isolated.
"""

import time
from pathlib import Path

import torch
import torchaudio

from .base import BaseSpoofGenerator, SpoofResult


class OpenVoiceGenerator(BaseSpoofGenerator):
    """Generate spoofs using OpenVoice V2 (MeloTTS base + tone colour convert)."""

    def __init__(
        self,
        output_dir: str,
        converter_ckpt_dir: str,
        base_speaker_ses_path: str,
        melo_language: str = "EN",
        melo_speaker_key: str = "EN-Newest",
        device: str = "cuda",
        target_sr: int = 16000,
    ):
        super().__init__(name="openvoice_v2", output_dir=output_dir, device=device)
        self.converter_ckpt_dir = Path(converter_ckpt_dir)
        self.base_speaker_ses_path = Path(base_speaker_ses_path)
        self.melo_language = melo_language
        self.melo_speaker_key = melo_speaker_key
        self.target_sr = target_sr

        self.melo = None
        self.converter = None
        self.source_se = None

    def load_model(self):
        from melo.api import TTS as MeloTTS
        from openvoice.api import ToneColorConverter

        print(f"Loading OpenVoice V2 (MeloTTS + ToneColorConverter) on {self.device}...")

        self.melo = MeloTTS(language=self.melo_language, device=self.device)

        self.converter = ToneColorConverter(
            str(self.converter_ckpt_dir / "config.json"), device=self.device
        )
        self.converter.load_ckpt(str(self.converter_ckpt_dir / "checkpoint.pth"))

        self.source_se = torch.load(
            str(self.base_speaker_ses_path), map_location=self.device
        )

        print("OpenVoice V2 loaded successfully")

    def _prepare_reference(
        self, reference_audio_paths: list[str], max_duration: float = 10.0
    ) -> str:
        """Concatenate up to `max_duration` seconds of reference audio.

        Mirrors XTTSGenerator._prepare_reference so both generators consume
        the same DECTE reference chunks the same way.
        """
        if len(reference_audio_paths) == 1:
            return reference_audio_paths[0]

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
                remaining = max_duration - total_duration
                samples_needed = int(remaining * self.target_sr)
                waveform = waveform[:, :samples_needed]
                chunks.append(waveform)
                break

            chunks.append(waveform)
            total_duration += duration

        combined = torch.cat(chunks, dim=1)
        ref_output = self.output_dir / "_temp_reference.wav"
        torchaudio.save(str(ref_output), combined, self.target_sr)
        return str(ref_output)

    def _extract_target_se(self, reference_wav: str):
        """Extract target speaker embedding directly, bypassing se_extractor.

        `openvoice.se_extractor` imports faster_whisper (which imports av)
        at module load, and PyAV's DLL is broken in this env. Since our
        reference audio is already clean speech from _prepare_reference
        (mono, 16 kHz, <=10 s), we don't need VAD/whisper segmentation --
        the converter's own extract_se() reads the wav with librosa and
        computes the tone-colour embedding directly.
        """
        return self.converter.extract_se([reference_wav], se_save_path=None)

    def generate(
        self,
        text: str,
        reference_audio_paths: list[str],
        output_path: str,
        language: str = "en",
    ) -> SpoofResult:
        if self.melo is None or self.converter is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()

        try:
            ref_path = self._prepare_reference(reference_audio_paths)

            base_tmp = str(self.output_dir / "_base_tmp.wav")
            speaker_id = self.melo.hps.data.spk2id[self.melo_speaker_key]
            self.melo.tts_to_file(text, speaker_id, base_tmp, speed=1.0)

            target_se = self._extract_target_se(ref_path)

            self.converter.convert(
                audio_src_path=base_tmp,
                src_se=self.source_se,
                tgt_se=target_se,
                output_path=output_path,
                message="@dialect-deepfake-bias",
            )

            if Path(output_path).exists():
                waveform, sr = torchaudio.load(output_path)
                if sr != self.target_sr:
                    waveform = torchaudio.transforms.Resample(sr, self.target_sr)(waveform)
                    torchaudio.save(output_path, waveform, self.target_sr)

            gen_time = time.time() - start_time

            return SpoofResult(
                source_utterance_id=Path(output_path).stem,
                source_speaker_id="",
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
        for attr in ("melo", "converter"):
            obj = getattr(self, attr, None)
            if obj is not None:
                del obj
                setattr(self, attr, None)
        self.source_se = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        for tmp_name in ("_temp_reference.wav", "_base_tmp.wav"):
            tmp = self.output_dir / tmp_name
            if tmp.exists():
                tmp.unlink()
