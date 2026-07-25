"""
Detector Interface
===================
Abstract interface so we can swap in multiple detectors (AASIST, a
Wav2Vec2-based detector, a Whisper-feature detector) without rewriting
the evaluation loop each time.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import torch
import torchaudio
import sys
from pathlib import Path


class BaseDetector(ABC):
    """Interface every detector must implement."""

    name: str

    @abstractmethod
    def load(self):
        """Load model weights."""
        ...

    @abstractmethod
    def score(self, audio_path: str) -> float:
        """
        Return a single bonafide-ness score for one audio file.
        Convention: HIGHER score = more likely REAL (bonafide).
        If your model naturally outputs a "fakeness" probability,
        negate or invert it here so the convention holds everywhere else.
        """
        ...

    def score_batch(self, audio_paths: list[str]) -> np.ndarray:
        """Default batch implementation — override for real batching/speed."""
        return np.array([self.score(p) for p in audio_paths])


class AASISTDetector(BaseDetector):
    """
    Wrapper around your AASIST model (from the earlier auralguard-aasistpp
    project). Adapt `_load_architecture` and `_forward` to match your
    actual model code and checkpoint format.
    """

    name = "aasist"

    def __init__(
        self,
        checkpoint_path: str,
        model_module_path: str = None,
        device: str = "cuda",
        target_sr: int = 16000,
    ):
        """
        Args:
            checkpoint_path: Path to your trained/pretrained AASIST .pth file.
            model_module_path: Optional path to your AASIST model definition
                (from auralguard-aasistpp), if it's not installed as a package.
            device: "cuda" or "cpu".
            target_sr: AASIST expects 16kHz mono input.
        """
        self.checkpoint_path = checkpoint_path
        self.model_module_path = model_module_path
        self.device = device
        self.target_sr = target_sr
        self.model = None

    def load(self):
        AURALGUARD_ROOT = Path(
            r"C:\Users\AYO\Desktop\JKU\Extra Semester\THESIS AND PRACTICAL\auralguard-aasistpp"
        )
        sys.path.insert(0, str(AURALGUARD_ROOT / "src"))
        from aasist_loader import build_aasist_backbone
        from model_aasistpp import AuralGuardAASISTPP

        aasist_root = AURALGUARD_ROOT / "external" / "aasist"
        aasist_config = AURALGUARD_ROOT / "external" / "aasist" / "config" / "AASIST.conf"

        # Build the raw AASIST backbone (no checkpoint yet -- the trained
        # weights live in the wrapper's state_dict under "backbone.*").
        backbone = build_aasist_backbone(
            aasist_root=aasist_root,
            aasist_config=aasist_config,
            checkpoint=None,
            device=self.device,
        )

        # Wrap with AuralGuard's multi-task heads (binary_head is the
        # trained deepfake classifier).
        self.model = AuralGuardAASISTPP(backbone, feature_dim=160).to(self.device)

        # Strict load: all 235 checkpoint tensors must map to model params.
        ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
        state = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
        self.model.load_state_dict(state, strict=True)
        self.model.eval()

        print("AuralGuardAASISTPP loaded successfully (strict=True)")

    def _load_audio(self, audio_path: str) -> torch.Tensor:
        """Match auralguard-aasistpp/src/dataset.py::load_audio_fixed exactly
        (soundfile-based, mono average, resample, zero-pad, deterministic
        crop from 0). Same preprocessing the checkpoint was trained on --
        any divergence here silently breaks the detector."""
        import soundfile as sf
        import numpy as np
        import torch.nn.functional as F

        data, sr = sf.read(audio_path, dtype="float32", always_2d=True)
        wav = torch.from_numpy(np.ascontiguousarray(data.T))
        if wav.ndim == 2:
            wav = wav.mean(dim=0)
        else:
            wav = wav.flatten()
        if sr != self.target_sr:
            wav = torchaudio.functional.resample(wav, sr, self.target_sr)
        wav = wav.float()

        num_samples = int(self.target_sr * 4.0)  # 4-sec window matches training
        if wav.numel() < num_samples:
            wav = F.pad(wav, (0, num_samples - wav.numel()))
        else:
            wav = wav[:num_samples]

        return wav.unsqueeze(0).to(self.device)  # -> [1, num_samples]

    @torch.no_grad()
    def score(self, audio_path: str) -> float:
        """Run AuralGuardAASISTPP on one file, return bonafide-ness score.

        AuralGuard binary_head convention (see
        auralguard-aasistpp/src/infer.py:45): index 0 = REAL, index 1 = FAKE.
        metrics.py expects HIGHER score = MORE bonafide, so we take
        softmax(binary_logits)[0, 0].
        """
        waveform = self._load_audio(audio_path)
        outputs = self.model(waveform)
        probs = torch.softmax(outputs["binary_logits"], dim=-1)
        return probs[0, 0].item()
