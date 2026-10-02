# Dialect Bias in Audio Deepfake Detection

This repository contains the code and thesis material from my bachelor's thesis at Johannes Kepler University Linz.

The project looks at how audio deepfake detectors behave when the same type of spoofing attack is tested on different English speech corpora. I mainly compare Tyneside English from DECTE with VCTK, using XTTS v2 and OpenVoice v2 to generate spoofed speech.

The main detector is an AASIST-based model from my AuralGuard work. I also use a simpler LFCC + Logistic Regression detector as a second check so that the conclusions are not based on only one model.

## Research question

The original question was whether dialectal speech is harder for audio deepfake detectors than more standard English speech.

During the experiments, the result turned out to be more complicated. The difference between DECTE and VCTK depends strongly on the spoof generator. XTTS v2 gives a DECTE > VCTK error gap, while OpenVoice v2 gives the opposite direction. Because DECTE and VCTK also differ in recording conditions, speaker distribution and corpus design, I describe this as a dialect/domain effect rather than a pure accent effect.

## Main results

The table below shows the main corpus-gap results. EER is lower when the detector separates real and spoofed speech more successfully.

| Detector | Generator | DECTE EER | VCTK EER | DECTE - VCTK gap |
| --- | --- | ---: | ---: | ---: |
| AASIST | XTTS v2 | 34.63% | 21.83% | +12.80 pp |
| LFCC + LR | XTTS v2 | 44.19% | 31.75% | +12.44 pp |
| AASIST | OpenVoice v2 | 47.84% | 74.58% | -26.74 pp |
| LFCC + LR | OpenVoice v2 | 38.21% | 80.83% | -42.62 pp |

Bootstrap confidence intervals for all four corpus gaps stay on the same side of zero in the corresponding experiments. Full numbers, confidence intervals and caveats are kept in `docs/THESIS_FINDINGS_LOG.md`.

I also ran a small controlled adaptation experiment on the AASIST model using DECTE XTTS data. On the held-out DECTE test split, EER changed from 40.70% to 23.26% (delta -17.44 percentage points, 95% CI [-28.49, -9.30]). This is a task-specific result, not a claim that the adapted model is generally better for every accent or generator.

## Repository structure

```text
dialect-deepfake-bias/
├── configs/                 experiment configuration files
├── src/
│   ├── data/                DECTE and VCTK loading utilities
│   ├── evaluation/          detector interfaces, metrics and group analysis
│   └── spoof_gen/           XTTS v2 and OpenVoice v2 generation code
├── scripts/                 experiment and analysis scripts
├── docs/                    research notes, findings log and thesis planning files
├── thesis_latex/            final LaTeX thesis source
├── references.bib
├── requirements.txt
└── README.md
```

Most of the later experiments are in `scripts/` because the project developed iteratively while I was working on the thesis. The reusable loading, generation and evaluation code is kept under `src/`.

## Setup

Clone the repository and install the common Python dependencies:

```bash
git clone https://github.com/GodzChild/dialect-deepfake-bias.git
cd dialect-deepfake-bias
pip install -r requirements.txt
```

The datasets, generated audio, model checkpoints and experiment outputs are not stored in Git because of size and licensing restrictions.

The detector configs expect checkpoints inside the local `checkpoints/` folder. See `docs/ENVIRONMENT.md` for the environment setup I used and `docs/REPRODUCIBILITY.md` for the experiment order and expected data layout.

## Data

The two main corpora are:

- **DECTE** — Diachronic Electronic Corpus of Tyneside English. Access and use are subject to the corpus licence.
- **VCTK** — used as the English comparison corpus.

Synthetic speech was generated with **XTTS v2** and **OpenVoice v2**.

I do not redistribute DECTE audio, generated DECTE-derived audio or model checkpoints in this repository.

## Reproducing the experiments

The rough experiment order is:

1. prepare DECTE/VCTK metadata and transcripts,
2. generate spoofed speech,
3. score real and spoofed files with the detector,
4. run the corpus/generator bootstrap comparisons,
5. build the mitigation split and evaluate the adapted detector,
6. run subgroup diagnostics.

Exact scripts, inputs and expected outputs are listed in `docs/REPRODUCIBILITY.md`.

## Thesis

The final thesis source is in `thesis_latex/`. Earlier Markdown chapter drafts and the running findings log are kept in `docs/` because they show how the experiments and interpretation developed.

## Limitations

This is a research project rather than a production deepfake detector. DECTE and VCTK differ in more than accent alone, and several subgroup analyses use small sample sizes. I therefore avoid treating the corpus gap as a clean causal measure of dialect bias.

The subgroup analysis is descriptive and should not be read as a complete fairness audit.
