# Thesis Findings Log

Running log of citable, thesis-ready result snippets. Append new dated
entries as new phases complete — don't overwrite old ones, since earlier
results may still be relevant for a "before/after mitigation" comparison
in the final writeup.

---

## Entry 1 — 2026-07 — Phase 2 baseline: AuralGuard-AASIST on DECTE + XTTS/OpenVoice spoofs

**Status: diagnostic, not yet finalized.** See verification checklist below
before using this as a headline thesis number.

### Dataset
- 216 bonafide DECTE utterances (Tyneside English)
- 516 spoof utterances total
  - 416 generated with XTTS v2
  - 100 generated with OpenVoice v2
- Detector: AuralGuardAASISTPP wrapper (checkpoint:
  `final_accent_globe_wavefake_balanced_full/best.pt`), loaded with
  `strict=True` after fixing the wrapper-vs-raw-AASIST loading bug.

### Result (citable text)

> Using 216 bonafide DECTE utterances and 516 generated spoof samples, the
> AuralGuard-AASIST detector achieved 38.17% EER and 0.6626 AUC overall.
> Generator-specific evaluation showed 35.61% EER / 0.6855 AUC on XTTS v2
> spoofs and 47.84% EER / 0.5675 AUC on OpenVoice v2 spoofs, suggesting that
> OpenVoice v2 samples were more challenging for the detector in this
> dialectal DECTE setting.

### Raw numbers (for tables/figures)

| Scope        | n_bonafide | n_spoof | EER (%) | AUC    | Accuracy | FAR (%) | FRR (%) |
|--------------|-----------:|--------:|--------:|--------|---------:|--------:|--------:|
| Overall      | 216        | 516     | 38.17   | 0.6626 | 0.6175   | 38.37   | 37.96   |
| XTTS v2      | 216        | 416     | 35.61   | 0.6855 | —        | —       | —       |
| OpenVoice v2 | 216        | 100     | 47.84   | 0.5675 | —        | —       | —       |

### Caveat (citable text)

> The OpenVoice subset is smaller than the XTTS subset, so a balanced
> comparison should either expand OpenVoice further or downsample XTTS to
> match OpenVoice.

### Verification checklist before treating this as a final/headline number

- [ ] **In-domain sanity check**: run the same fixed detector on the
      dataset/split it was originally trained or validated on. If EER
      there is low (single digits), it confirms the wrapper-loading fix
      worked and the 38% here reflects genuine domain transfer difficulty,
      not a lingering pipeline bug.
- [ ] **Balanced generator comparison**: downsample XTTS to 100 spoof
      samples (seed 42) to match OpenVoice's n=100, recompute EER/AUC for
      both, confirm the gap direction and rough magnitude holds.
- [ ] **Bootstrap confidence intervals**: with n=100 for OpenVoice, get a
      95% CI on EER for both generators before claiming the 35.6% vs 47.8%
      gap is a real effect rather than sampling noise.
- [ ] **speaker_info_by_audio.json completeness**: confirm gender/age/era
      breakdowns aren't dominated by "mixed"/"unknown" categories, which
      would weaken any social-variable claims.

---

## Entry 2 — 2026-07-26 — Balanced generator comparison (matched N = 100, bootstrap 95% CI)

**Status: primary evidence for the generator-specific EER gap.** Addresses the
"Balanced generator comparison" and "Bootstrap confidence intervals" boxes on
Entry 1's verification checklist.

### Method
- Reused Phase 2 predictions (`results/detector_predictions.csv`); no rescoring.
- All 216 bonafide DECTE rows.
- All 100 OpenVoice v2 spoof rows.
- 100 XTTS v2 spoof rows sampled without replacement from the 416-row pool
  (`numpy.random.default_rng(seed=42).choice(..., replace=False)`).
- Metrics via `src/evaluation/metrics.compute_metrics`; 95% bootstrap CI on
  EER via 1000 iterations of independent-with-replacement resampling of the
  bonafide and spoof arrays. Reproducer:
  `python scripts/04_balanced_generator_comparison.py`.

### Result (citable text)

> In a balanced generator comparison, XTTS v2 and OpenVoice v2 were each
> evaluated using 100 spoofed DECTE utterances against the same 216 bonafide
> DECTE utterances. The detector achieved 34.63% EER on XTTS v2 spoofs, with
> a 95% bootstrap confidence interval of 29.54–41.10%, and 47.84% EER on
> OpenVoice v2 spoofs, with a 95% bootstrap confidence interval of
> 42.07–54.32%. This suggests that OpenVoice v2 samples were substantially
> more challenging for the detector than XTTS v2 samples in this dialectal
> DECTE setting.

### Raw numbers (for tables/figures)

| Generator     | n_bonafide | n_spoof | EER (%) | EER 95% CI      | AUC    | Accuracy | FAR (%) | FRR (%) |
|---------------|-----------:|--------:|--------:|----------------:|-------:|---------:|--------:|--------:|
| XTTS v2       | 216        | 100     | 34.630  | 29.541 – 41.102 | 0.6792 | 0.6551   | 35.000  | 34.259  |
| OpenVoice v2  | 216        | 100     | 47.843  | 42.065 – 54.315 | 0.5675 | 0.5222   | 48.000  | 47.685  |

### Interpretation (cautious wording)

The two CIs are **nearly disjoint** — XTTS upper bound 41.10% vs OpenVoice lower
bound 42.07%, i.e. a ~1 point gap between the intervals. This is evidence of a
**meaningful generator-specific gap** on Tyneside dialectal speech, not just
sampling noise from unequal N. It should still be reported cautiously: the CIs
are only just separated, and the comparison is on a single detector
(AuralGuard-AASIST) trained without dialect exposure. Whether the gap survives
under different detector families, or under mitigation, is out of scope for
this entry.

### Caveats

- Both generators are being scored by a detector never trained on Tyneside
  English — Entry 1's absolute EER numbers (35–48%) largely reflect that
  domain shift. The *relative* gap between generators is the more defensible
  finding.
- OpenVoice v2 coverage is still concentrated on early PVC / TLSG speakers
  (20 speakers total, 5 utterances each). Expanding to a broader speaker set
  would strengthen generalisation of the gap claim.
- Bootstrap uses independent resampling of bonafide and spoof (standard for
  detection metrics); it does not account for speaker-clustered dependence
  within either arm. If needed later, a speaker-block bootstrap could be
  added.

### Reproducibility state at this entry

- Script: `scripts/04_balanced_generator_comparison.py` (seed 42, 1000 iters).
- Input: `results/detector_predictions.csv` (from Phase 2 rerun after the
  detector-loader + grouping fixes described in Entry 1).
- Output: `results/balanced_generator_comparison.csv` (gitignored via
  `results/` rule).

---

## Entry 3 — 2026-07-26 — In-domain sanity check for fixed AuralGuard detector

**Status: validates the fixed detector pipeline.** Discharges the "In-domain
sanity check" box on Entry 1's verification checklist and gives Entry 2's
generator gap firmer footing.

### Method
- Script: `scripts/06_indomain_sanity_check.py`.
- Detector: fixed `AuralGuardAASISTPP` wrapper loader with `strict=True`
  (Entry 1's fix), same class the DECTE Phase 2 evaluation uses.
- Validation CSV (source of truth for this checkpoint's training):
  `C:/Users/AYO/Desktop/JKU/Extra Semester/THESIS AND PRACTICAL/auralguard-aasistpp/data/metadata/val_final_accent_globe_wavefake_balanced.csv`
- Full validation set: 9,514 rows (4,757 bonafide + 4,757 spoof), covering
  ASVspoof2019_LA, WaveFake, DECTE, EdAcc, EnglishDialects, GLOBE.
- Also ran a 500-per-class stratified sanity sample first (seed 42,
  stratified by `dataset`) to confirm nothing was broken before the
  full run.
- Label convention flip handled inside the script: AuralGuard CSV uses
  `binary_label 0 = bonafide, 1 = spoof`, opposite of `metrics.py`.

### Result (citable text)

> As an in-domain sanity check, the fixed AuralGuard-AASIST detector was
> evaluated on its original validation set of 9,514 utterances. The
> detector achieved 1.713% EER and 0.9988 AUC, closely matching the
> checkpoint's saved validation EER of approximately 1.7%. This confirms
> that the detector-loading and preprocessing pipeline is functioning
> correctly. Therefore, the much higher EER observed on the DECTE
> dialectal spoof evaluation reflects domain-transfer difficulty rather
> than a remaining implementation bug.

### Raw numbers (for tables/figures)

Sanity sample (500 per class, stratified by dataset, seed 42):

| Scope         | n_bonafide | n_spoof | EER (%) | AUC    | Accuracy | FAR (%) | FRR (%) | Verdict |
|---------------|-----------:|--------:|--------:|-------:|---------:|--------:|--------:|:-------:|
| Sanity sample | 500        | 500     | 2.000   | 0.9975 | 0.9800   | 2.000   | 2.000   | PASS    |

Full validation set:

| Scope       | n_bonafide | n_spoof | EER (%) | AUC    | Accuracy | FAR (%) | FRR (%) | Verdict |
|-------------|-----------:|--------:|--------:|-------:|---------:|--------:|--------:|:-------:|
| Full val    | 4,757      | 4,757   | 1.713   | 0.9988 | 0.9829   | 1.703   | 1.724   | PASS    |

### Interpretation

Confirms the detector-loader + preprocessing fix from Entry 1 is complete:
in-domain EER (1.713%) matches the checkpoint's saved `val_metrics.eer` of
~1.7% to within a fraction of a point. This strengthens Entries 1 and 2:
the elevated EER on DECTE (~38% overall) and the generator gap
(XTTS 34.63% vs OpenVoice 47.84%) reflect the *detector's actual behaviour
under domain shift*, not a lingering pipeline artifact.

### Caveats

- **Does not prove dialect alone is the cause.** DECTE also differs from
  the checkpoint's training distribution in recording conditions
  (interview-style, older analog eras, unmatched microphones), speaker
  population, and the spoof pipeline itself (XTTS/OpenVoice vs the
  ASVspoof/WaveFake TTS/VC systems the detector saw at training). Phrase
  the DECTE EER as "dialectal / domain-transfer difficulty" until a
  standard-accent control set (VCTK or similar) is added.
- The val set is heavily ASVspoof2019_LA-weighted (6,775 / 9,514 rows);
  the DECTE bonafide portion of it (1,014 rows) uses a separate DECTE
  chunks folder (`DECTE_ASR_PROJECT/01_chunks/...`) from this repo, but
  is bonafide-only so does not contribute to per-dataset EER.

### Reproducibility state at this entry

- Script: `scripts/06_indomain_sanity_check.py`.
- Sanity mode: `python scripts/06_indomain_sanity_check.py` (defaults:
  `--n-per-class 500 --stratify dataset --seed 42`).
- Full run: `python scripts/06_indomain_sanity_check.py --full`.
- Output CSV: `results/indomain_sanity_metrics.csv` (gitignored via
  `results/` rule).
- Verdict thresholds (in-script): EER ≤ 5% PASS, 5–15% PARTIAL, > 15% FAIL.

### Next research step (queued, not yet started)

Add a **standard-accent control set** (VCTK is the obvious candidate) and
generate matched XTTS + OpenVoice spoofs from it. Comparing DECTE EER
against VCTK EER on the same detector, same generators, same protocol
isolates the dialect/interview-style contribution from generic domain
shift. Until this control exists, all DECTE numbers must be phrased as
"dialectal / domain-transfer difficulty" rather than "dialect bias".

---

## Entry 4 — [DATE] — [next milestone]

*(add here once available)*
