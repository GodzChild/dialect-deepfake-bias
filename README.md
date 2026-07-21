# Dialect Bias in Audio Deepfake Detection

**Thesis:** *Does Your Accent Make You Vulnerable? Quantifying Dialect Bias in Audio Deepfake Detection on Tyneside English*

**Author:** Calvin Oluyemi  
**Institute:** Institute of Computational Perception, Johannes Kepler University Linz  
**Corpus:** Diachronic Electronic Corpus of Tyneside English (DECTE)

## Research Question

Do state-of-the-art audio deepfake detectors exhibit systematically worse performance
when evaluating synthetic speech generated from dialectal speakers (Tyneside English)
compared to standard-accent speakers — and do these performance gaps correlate with
social variables (age, gender, socioeconomic status)?

## Relationship to Prior Work

- **Serditova & Tang (Interspeech 2025; arxiv 2603.24549):** Studied ASR transcription
  bias on DECTE — found phonological dialect features cause systematic ASR errors,
  patterned by gender, age, and SES.
- **This work:** Studies deepfake *detection* bias on the same corpus — asking whether
  the same speakers who are poorly served by ASR are also poorly protected by
  spoofing countermeasures.

## Project Structure

```
dialect-deepfake-bias/
├── configs/
│   ├── spoof_gen.yaml          # TTS/VC system configs
│   ├── detectors.yaml          # Detector model configs
│   └── evaluation.yaml         # Eval protocol configs
├── src/
│   ├── data/
│   │   ├── decte_loader.py     # Load & parse DECTE audio + metadata
│   │   ├── vctk_loader.py      # Load VCTK control group
│   │   └── dataset.py          # Unified dataset class
│   ├── spoof_gen/
│   │   ├── base.py             # Abstract spoof generator
│   │   ├── xtts_gen.py         # Coqui XTTS v2
│   │   ├── openvoice_gen.py    # OpenVoice v2
│   │   ├── styletts_gen.py     # StyleTTS 2
│   │   └── pipeline.py         # Orchestrates all generators
│   ├── evaluation/
│   │   ├── metrics.py          # EER, AUC, min t-DCF
│   │   ├── bias_analysis.py    # Per-group performance breakdown
│   │   └── run_eval.py         # Main eval script
│   └── mitigation/
│       ├── accent_adversarial.py   # Gradient-reversal accent branch
│       └── augmentation.py         # Dialect-aware data augmentation
├── scripts/
│   ├── 01_prepare_decte.py     # Preprocess DECTE for pipeline
│   ├── 02_generate_spoofs.py   # Run spoof generation
│   ├── 03_run_detectors.py     # Run all detectors
│   └── 04_analyze_bias.py      # Statistical analysis + plots
├── notebooks/
│   └── exploration.ipynb       # Data exploration
├── docs/
│   └── CONTINUATION_PROMPT.md  # Prompt for resuming with Claude
├── requirements.txt
└── README.md
```

## Phase Plan

| Phase | Weeks | Deliverable |
|-------|-------|-------------|
| 1 — Spoof Generation | 1–3 | DECTE-Spoof + VCTK-Spoof paired dataset |
| 2 — Detector Evaluation | 3–6 | EER/AUC per detector × speaker group |
| 3 — Mitigation | 6–9 | Accent-adversarial AASIST, ablation results |
| 4 — Write-up | 9–12 | Thesis + conference paper draft |

## Setup

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/dialect-deepfake-bias.git
cd dialect-deepfake-bias
pip install -r requirements.txt

# Place DECTE audio in data/decte/audio/
# Place DECTE metadata/transcripts in data/decte/metadata/
# VCTK auto-downloads via torchaudio or manual download
```

## Dataset Acknowledgements

- **DECTE:** Corrigan, K.P., Buchstaller, I., Mearns, A.J. and Moisl, H.L. (2012).
  Non-commercial academic use under Creative Commons licence.
- **VCTK:** Yamagishi, J. et al. CC-BY-4.0.

## License

Code: MIT. Datasets carry their own licenses (see above).
