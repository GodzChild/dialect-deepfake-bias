# Reproducing the experiments

This file documents the experiment order used for the thesis. The repository contains the code, but not the licensed datasets, generated audio, checkpoints or result folders.

## 1. Expected local folders

The main local layout is:

```text
data/
├── 01_chunks/
├── 01_chunk_transcripts/
├── decte/
│   └── metadata/
├── generated_spoofs/
├── generated_spoofs_vctk/
└── vctk/

checkpoints/
├── aasist/
├── mitigation_v1_decte_finetune/
└── mitigation_v2_partial_unfreeze/

results/
```

These folders are intentionally ignored by Git.

## 2. Prepare DECTE and VCTK

Useful preparation scripts are:

```bash
python scripts/00_build_chunk_transcripts.py
python scripts/01_extract_decte_speaker_metadata.py
python scripts/01_prepare_decte.py
python scripts/01b_bridge_metadata_by_audio.py
python scripts/00b_verify_vctk_layout.py
```

The exact DECTE source files cannot be included in this repository. The preparation scripts assume that the user already has authorised access to the corpus.

## 3. Generate spoofed speech

The common entry point is:

```bash
python scripts/02_generate_spoofs.py --config configs/spoof_gen.yaml
```

Other configuration files in `configs/` were used for smaller test runs, VCTK runs and generator-specific experiments.

The main generators used in the final thesis are:

- XTTS v2
- OpenVoice v2

Generated audio and manifests are written under `data/` and are not committed.

## 4. Run AASIST evaluation

The baseline detector configuration is:

```text
configs/detectors.yaml
```

The main scoring script is:

```bash
python scripts/03_run_detectors.py --config configs/detectors.yaml
```

The script also accepts manifest, output-directory and corpus arguments for the different experimental conditions.

A quick detector sanity check is available in:

```bash
python scripts/03b_detector_sanity_check.py
```

I used the in-domain check before interpreting the DECTE/VCTK results, because it confirmed that the detector loader and preprocessing reproduced the expected validation behaviour.

## 5. Corpus and generator comparisons

The main statistical scripts are:

```text
scripts/04_balanced_generator_comparison.py
scripts/05_bootstrap_vctk_generator_ci.py
scripts/06_bootstrap_xtts_corpus_gap.py
scripts/12_bootstrap_openvoice_corpus_gap.py
```

The bootstrap analyses use 1,000 iterations and seed 42 by default.

The exact thesis values are recorded in `docs/THESIS_FINDINGS_LOG.md`.

## 6. Second detector

The second detector is LFCC + Logistic Regression:

```bash
python scripts/11_lfcc_lr_second_detector.py
```

The OpenVoice replication uses:

```bash
python scripts/13_lfcc_lr_openvoice_corpus_gap.py
```

This detector was added as a deliberately different baseline so that the main corpus-gap direction was not based only on the AASIST architecture.

## 7. Mitigation experiment

The mitigation split is built with:

```bash
python scripts/09_build_mitigation_csvs.py
```

Training of the adapted AASIST checkpoints was carried out in the separate AuralGuard project. The resulting checkpoints are referenced here through:

```text
configs/detectors_mitigated.yaml
configs/detectors_mitigated_v2.yaml
```

The before/after effect is evaluated with:

```bash
python scripts/10_bootstrap_mitigation_effect.py
```

## 8. Subgroup diagnostics

The descriptive DECTE subgroup analysis is run with:

```bash
python scripts/14_decte_subgroup_diagnostics.py
```

It compares baseline and mitigated predictions by gender, age group and recording era where enough samples are available.

The subgroup output is exploratory. The held-out test set is small, so these numbers should not be treated as a complete demographic fairness evaluation.

## 9. Results and large files

The following are intentionally not versioned:

- raw DECTE audio
- generated DECTE-derived audio
- VCTK audio
- detector checkpoints
- cached LFCC features
- prediction CSVs
- bootstrap output CSVs
- figures generated from the result files

Most of these are reproducible from the scripts once the datasets and checkpoints are available.

## 10. Source of thesis numbers

For checking a number before using it in a report, the safest order is:

1. `docs/THESIS_FINDINGS_LOG.md`
2. the corresponding analysis script
3. the generated CSV in `results/`, if available locally
4. the LaTeX thesis chapter that cites the result

The findings log also contains the caveats attached to each experiment.
