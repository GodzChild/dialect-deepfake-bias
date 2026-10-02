# Environment notes

I used separate Python environments during the thesis because the speech-generation packages did not always agree on the same dependency versions.

## Main analysis environment

The main environment was used for:

- DECTE/VCTK preparation
- AASIST evaluation
- pandas/scikit-learn analysis
- bootstrap experiments
- LFCC + Logistic Regression
- plotting and result tables

The packages in `requirements.txt` cover the common dependencies for this part of the project.

A typical setup is:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Linux/macOS the activation command is:

```bash
source .venv/bin/activate
```

PyTorch should be installed in a version that matches the local CUDA setup if GPU evaluation is required.

## XTTS v2

XTTS v2 was kept in a separate environment during the experiments because Coqui TTS had stricter dependency requirements than the analysis code.

The generator is implemented in:

```text
src/spoof_gen/xtts_gen.py
```

and is normally run through:

```text
scripts/02_generate_spoofs.py
```

The thesis runs used a dedicated environment named `spoofgen`. I have not turned that environment into a frozen lock file, so `requirements.txt` should be treated as a starting point rather than an exact historical snapshot.

## OpenVoice v2

OpenVoice was also easier to manage separately from the XTTS environment.

The implementation is in:

```text
src/spoof_gen/openvoice_gen.py
```

OpenVoice itself is not installed automatically by `requirements.txt`. Follow the OpenVoice installation instructions for the version being used, then point the generation config at the local checkpoints.

## AASIST / AuralGuard checkpoint

The AASIST experiments use the AuralGuard model architecture and checkpoints from my separate `auralguard-aasistpp` project.

This repository does not include those weights. Place the required files under:

```text
checkpoints/
├── aasist/
│   └── baseline_best.pt
├── mitigation_v1_decte_finetune/
│   └── best.pt
└── mitigation_v2_partial_unfreeze/
    └── best.pt
```

The YAML files in `configs/` use these relative paths.

## Why there is no exact lock file

The experiments were run across more than one environment and some generation packages were installed directly from their upstream repositories. Rather than add a lock file that would give a false impression of exact reproducibility, I have documented the separation here.

A future cleanup step would be to export tested Conda/uv lock files for each environment separately.
