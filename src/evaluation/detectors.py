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
        """
        Load the AASIST architecture and checkpoint weights.

        IMPORTANT: This is a template. Replace the import and instantiation
        below with your actual model class from auralguard-aasistpp.
        Common AASIST implementations define a class like `Model(args)` or
        `AASIST(config)` — check your original repo's model.py.
        """
        if self.model_module_path:
            import sys
            sys.path.insert(0, self.model_module_path)

        try:
            # ADAPT: import your actual AASIST model class here
            # Example (from the original AASIST repo structure):
            # from models.AASIST import Model as AASISTModel
            # self.model = AASISTModel(config_dict)
            raise NotImplementedError(
                "Import your AASIST model class here. See auralguard-aasistpp "
                "repo for the original model.py / AASIST.py definition. "
                "Replace this block with: "
                "from models.AASIST import Model; self.model = Model(config)"
            )
        except NotImplementedError:
            print(
                "\n⚠️  AASISTDetector.load() needs your model import filled in.\n"
                "   Open src/evaluation/detectors.py and follow the ADAPT comments.\n"
            )
            raise

        state_dict = torch.load(self.checkpoint_path, map_location=self.device)
        # Some checkpoints wrap weights in a dict with a "model" or "state_dict" key
        if isinstance(state_dict, dict) and "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    def _load_audio(self, audio_path: str) -> torch.Tensor:
        """Load and preprocess audio to match AASIST's expected input."""
        waveform, sr = torchaudio.load(audio_path)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if sr != self.target_sr:
            waveform = torchaudio.transforms.Resample(sr, self.target_sr)(waveform)

        # AASIST typically expects a fixed-length input (commonly ~4 sec,
        # achieved via padding/cropping — "Repeat_padding" in the original repo).
        # ADAPT this to match your training preprocessing exactly, or results
        # will be meaningless (train/test preprocessing mismatch is a very
        # common silent bug).
        target_len = self.target_sr * 4  # 4 seconds, ADAPT if different
        cur_len = waveform.shape[1]
        if cur_len < target_len:
            n_repeats = target_len // cur_len + 1
            waveform = waveform.repeat(1, n_repeats)[:, :target_len]
        else:
            waveform = waveform[:, :target_len]

        return waveform.to(self.device)

    @torch.no_grad()
    def score(self, audio_path: str) -> float:
        """
        Run AASIST on one file, return bonafide-ness score.

        ADAPT the output handling to match your model's actual output shape.
        AASIST commonly outputs 2 logits [spoof_logit, bonafide_logit].
        """
        waveform = self._load_audio(audio_path)
        output = self.model(waveform)

        # ADAPT: match your model's actual output format
        if isinstance(output, tuple):
            output = output[-1]  # some AASIST impls return (hidden, logits)

        # Softmax over [spoof, bonafide] logits, take bonafide probability
        probs = torch.softmax(output, dim=-1)
        bonafide_score = probs[0, 1].item()  # index 1 = bonafide, ADAPT if reversed

        return bonafide_score
