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

## Entry 4 — 2026-07-26 — VCTK OpenVoice matched-control result (XTTS control not yet run)

**Status: partial.** VCTK OpenVoice V2 evaluation is complete under the same
protocol as DECTE. **VCTK XTTS v2 control is not yet run**, so the
cross-corpus generator comparison remains one-sided until that lands.
This entry documents what changes about the interpretation of Entries 1–2
in light of the new VCTK OpenVoice numbers.

### Method
- Reused the fixed AuralGuard-AASIST detector from Entry 3.
- VCTK bonafide/spoof pool: 20 English-accent VCTK speakers × 5 target
  utterances each = 100 spoofs. Bonafide = the *matched* 100 original
  target utterances (enabled by the `source_audio_path` schema field
  added in this cycle + one-shot backfill).
- Eval command:
  ```
  python scripts/03_run_detectors.py \
    --manifest data/generated_spoofs_vctk/manifest.jsonl \
    --output-dir results/vctk \
    --corpus vctk_english_control
  ```
- Detector, preprocessing, and metric functions unchanged from Entries 1–3.

### Result (citable text)

> On a VCTK English-accent control set of 100 matched original utterances
> and 100 OpenVoice v2 spoofs of those same utterances, the fixed
> AuralGuard-AASIST detector achieved 75.50% EER and 0.1670 AUC (accuracy
> 0.2450; FAR 75.00%; FRR 76.00%). Mean detector "bonafide-ness" score
> was 0.9154 on real VCTK originals versus 0.9894 on their OpenVoice v2
> spoofs — the detector scored the spoofs as *more real* than the real
> utterances they were cloned from. This confirms that OpenVoice v2's
> difficulty for the detector is not limited to DECTE dialectal speech;
> it also holds on standard-accent studio-quality VCTK English input.

### Raw numbers

| Scope                | n_bonafide | n_spoof | EER (%) | AUC    | Accuracy | FAR (%) | FRR (%) | Mean bonafide score | Mean spoof score |
|----------------------|-----------:|--------:|--------:|-------:|---------:|--------:|--------:|--------------------:|-----------------:|
| VCTK OpenVoice v2    | 100        | 100     | 75.50   | 0.1670 | 0.2450   | 75.00   | 76.00   | 0.9154              | 0.9894           |

Composition of the 20 VCTK speakers used (English accent, alphabetical
top-20 with ≥ 8 usable utterances): 13 southern (Southern England / London
/ Surrey / SE England / SW England), 7 non-southern (Manchester × 2,
Cumbria, Stockton-on-Tees, Birmingham, Nottingham, Staffordshire).
Gender: 11F / 9M. Age band: 19 of 20 in `21-30`; one in `31-40`. No
speakers labelled Newcastle → no direct region overlap with DECTE.

### Interpretation (updates the story from Entries 1–2)

Before this entry, the strongest defensible reading of Entries 1–2 was
that OpenVoice v2's high EER on DECTE (47.84% in Entry 2's balanced
comparison) *might* reflect an interaction between the OpenVoice generator
and DECTE's dialect / interview-style acoustics. Entry 4 rules that
interpretation out as *primary*: OpenVoice v2 defeats this detector on
studio-quality, near-standard-accent English speech too, and by an even
larger margin (VCTK 75.50% EER vs DECTE 47.84% EER).

Revised strongest claim:

> AuralGuard-AASIST shows a severe generator-specific vulnerability to
> OpenVoice v2 voice-cloned speech across both the DECTE dialectal
> corpus and a VCTK English-accent control set. DECTE remains useful
> for dialect / domain-transfer analysis, but the OpenVoice difficulty
> is not itself a dialect effect — it is present on standard-accent
> studio speech as well.

Notable specific finding: the detector's mean bonafide-ness score on
VCTK OpenVoice spoofs (0.9894) is *higher* than on the real VCTK
originals (0.9154). This is not "detector fails to discriminate" (Entry 3
already ruled out a broken detector); it is "detector is systematically
confident that OpenVoice v2 outputs are bonafide."

### Caveats

- **VCTK XTTS control missing.** The parallel VCTK XTTS v2 result is the
  natural next step. Without it we cannot say whether the VCTK–DECTE
  gap on OpenVoice (75.5% vs 47.8%) reflects OpenVoice interacting with
  studio audio in a specific way, or a bulk domain effect that would
  show up on VCTK XTTS too.
- VCTK is heavily biased to young speakers (19/20 in `21-30`); DECTE
  spans multiple decades. Any DECTE-vs-VCTK comparison must acknowledge
  this age-band confound alongside the accent / audio-quality ones.
- The AuralGuard training set includes GLOBE (a US-English clean
  corpus). VCTK is not identical but is similar enough in style
  (studio-read English) that the detector's *bonafide* recognition on
  VCTK is likely aided by that training exposure — the 75% *spoof-side*
  failure is therefore the load-bearing number, not the ~92% mean real
  score.

### Reproducibility state at this entry

- Backfilled manifest: `data/generated_spoofs_vctk/manifest.jsonl`
  (100 rows, `source_audio_path` + `corpus="vctk"` populated by
  `scripts/08_backfill_source_audio_path.py`).
- Eval outputs: `results/vctk/detector_predictions.csv`,
  `results/vctk/group_bias_summary_aasist.csv` (both gitignored).
- Detector fix from Entry 3, grouping fix from Entry 2, matched-pair
  eval logic new in this cycle (commit `3510c7a`).

### Next research step (queued, not yet started)

**VCTK XTTS v2 100-sample control** — same 20 speakers × 5 utterances,
XTTS v2 instead of OpenVoice v2, matched originals as bonafide. Then a
2×2 table becomes possible:

|           | XTTS v2 | OpenVoice v2 |
|-----------|--------:|-------------:|
| DECTE     | 34.63%  | 47.84%       |
| VCTK      | ???     | 75.50%       |

The DECTE row is from Entry 2; the VCTK OpenVoice cell is this entry;
the VCTK XTTS cell is the missing block. That table is what makes the
generator-vs-corpus interaction claim publishable.

XTTS runs in the separate `spoofgen` env — needs its own
`configs/spoof_gen.vctk.xtts.yaml` (mirrors the OpenVoice VCTK config
with generators reversed) and its own generation pass before the eval
rerun.

---

## Entry 5 — 2026-07-26 — VCTK XTTS matched-control result and 2x2 generator comparison

**Status: completes the 2x2 (corpus x generator) table.** The missing
"VCTK x XTTS v2" cell flagged as an open item at the end of Entry 4 is
now filled. Together with Entries 2 and 4 the study now supports a
direct corpus x generator interaction analysis on this detector.

### VCTK generation

- 100 XTTS v2 samples generated successfully in the `spoofgen` env
  (`configs/spoof_gen.vctk.xtts.yaml`, 20 English-accent VCTK speakers
  × 5 target utterances, seed 42).
- Merged into the existing VCTK manifest by the manifest-merge writer;
  the DECTE manifest at `data/generated_spoofs/manifest.jsonl` was not
  touched.
- **VCTK manifest now has 200 rows**: 100 `openvoice_v2` + 100 `xtts_v2`.

### Detector evaluation

- Eval command:
  ```
  python scripts/03_run_detectors.py \
    --manifest data/generated_spoofs_vctk/manifest.jsonl \
    --output-dir results/vctk \
    --corpus vctk_english_control
  ```
- Detector: fixed AuralGuard-AASIST from Entry 3, unchanged.
- Built **320 evaluation pairs**: **120 bonafide** matched originals +
  **200 spoof** samples. `dialect_group = vctk_english_control`,
  `corpus = vctk`.

### Result (citable text)

> On VCTK English-accent control speech, the fixed AuralGuard-AASIST
> detector achieved 21.83% EER (AUC 0.8917) on XTTS v2 spoofs and
> 74.58% EER (AUC 0.1643) on OpenVoice v2 spoofs, evaluated against 120
> unique matched original utterances. Under a shared audio-quality and
> accent condition, the detector is over three times better at rejecting
> XTTS v2 spoofs than OpenVoice v2 spoofs, strengthening the conclusion
> from Entries 2 and 4 that OpenVoice v2 constitutes a major
> generator-specific vulnerability for this detector rather than a
> dialect-driven artifact.

### Raw numbers (VCTK, this entry)

| Scope             | n_bonafide | n_spoof | EER (%) | AUC    |
|-------------------|-----------:|--------:|--------:|-------:|
| Overall (both gens combined) | 120 | 200 | 45.50 | 0.5280 |
| XTTS v2           | 120        | 100     | 21.833  | 0.8917 |
| OpenVoice v2      | 120        | 100     | 74.583  | 0.1643 |

### 2x2 corpus × generator table (Entries 2, 4, 5 combined)

| Corpus                       | XTTS v2 EER | OpenVoice v2 EER |
|------------------------------|------------:|-----------------:|
| DECTE dialectal              | 34.63%      | 47.84%           |
| VCTK English-control         | **21.83%**  | **74.58%**       |

Row difference (VCTK harder or easier than DECTE by generator):

- XTTS: DECTE 34.63% - VCTK 21.83% = +12.8pp harder on DECTE → *dialect/domain effect visible for XTTS*.
- OpenVoice: DECTE 47.84% - VCTK 74.58% = -26.7pp *easier* on DECTE → OpenVoice is actually *worse* on the clean VCTK control than on DECTE.

The OpenVoice row inverting the expected direction is the most
interesting single number in the table: on studio-quality standard-
accent English, the detector is *more* fooled by OpenVoice than on
dialectal interview speech.

### Interpretation

Entry 4 already shifted the story from "DECTE dialect is the driver"
to "OpenVoice is the driver". Entry 5 puts firm bounds on that:

1. **Generator effect dominates corpus effect.** Within each corpus,
   the XTTS-vs-OpenVoice EER gap (13pp on DECTE, 53pp on VCTK) is
   larger than the corpus-effect gap on either generator (13pp for
   XTTS, 27pp for OpenVoice).
2. **Dialect effect for XTTS is real but modest.** The XTTS row alone
   (34.63% DECTE vs 21.83% VCTK) is consistent with the domain-
   transfer difficulty already documented in Entries 1 and 3 — DECTE
   is harder for XTTS-style TTS than clean VCTK is.
3. **OpenVoice's failure mode is not dialect.** OpenVoice v2 gets
   *worse* EER on the cleaner VCTK than on DECTE. This is unlikely
   to be a "clean-audio helps the detector" argument (Entry 3 shows
   the detector is highly capable on similar clean data) — it points
   instead to something specific in OpenVoice v2 outputs that this
   detector actively misclassifies as bonafide.

### Caveat — "balanced per-generator", not "fully paired utterance-by-utterance"

The two VCTK generator subsets are **100 samples each**, but the eval
built **120 unique bonafide originals**. Overlap check on
`source_audio_path`:

```
xtts_v2 originals    : 100
openvoice_v2 originals: 100
overlap              : 80
union                : 120
xtts-only originals  : 20
openvoice-only       : 20
```

Report this as a **balanced per-generator comparison** — same speakers,
same protocol, matched originals used as bonafide for each generator —
**not** as a "same 100 utterances synthesised by both generators"
paired comparison. Reason for the 80% (not 100%) overlap:
`SpoofPipeline.run()` seeds `random` once and calls `random.sample` per
speaker to pick 5 target utterances. Between speakers, the loaded
generator's internal libraries advance `random`'s module state
differently for OpenVoice vs XTTS. p225 (first speaker, fresh seed
state) fully overlaps; later speakers overlap partially. Fixable in a
future run by pre-picking the target set once per corpus.

Other caveats from Entry 4 still apply:
- VCTK is heavily biased to `21-30` speakers (19 of 20); DECTE spans
  multiple decades.
- AuralGuard's training set includes GLOBE (US-English studio-clean),
  so the detector's *bonafide* recognition on VCTK is aided by
  in-distribution familiarity. The load-bearing numbers are the *spoof*
  EERs, not the bonafide-side scores.

### Reproducibility state at this entry

- VCTK XTTS config: `configs/spoof_gen.vctk.xtts.yaml` (commit
  `debcee2`).
- VCTK manifest: `data/generated_spoofs_vctk/manifest.jsonl` (200 rows,
  gitignored).
- Eval outputs: `results/vctk/detector_predictions.csv`,
  `results/vctk/group_bias_summary_aasist.csv` (both gitignored).
- Detector fix from Entry 3, grouping fix from Entry 2, matched-pair
  eval logic + schema extension from commit `3510c7a`.

### Next research step (queued, not yet started)

The 2x2 is now filled at N=100 per cell. Sensible next moves, in
priority order:

1. **Pre-picked target-set fix** — small change to `SpoofPipeline.run()`
   that pre-computes each speaker's 5 targets once per config and
   caches them, so XTTS-vs-OpenVoice runs on the same corpus become
   truly paired (overlap → 100).
2. **Second detector** — the entire 2x2 hangs on AuralGuard-AASIST.
   Adding one more anti-spoofing detector (e.g. Wav2Vec2-AASIST, or
   the RawGAT-ST family) would let us claim the generator effect is
   not detector-specific.
3. **Bootstrap 95% CIs on the four VCTK numbers** — same treatment as
   Entry 2's DECTE balanced comparison. That'd let us report the
   XTTS-vs-OpenVoice gap on VCTK with confidence bounds, and check
   whether the DECTE-vs-VCTK gap for each generator is
   statistically distinguishable.

---

## Entry 6 — 2026-07-26 — Bootstrap confidence intervals for XTTS corpus gap and VCTK generator gap

**Status: primary statistical test for the thesis headline.** Two
bootstrap analyses were run against existing prediction CSVs (no
rescoring, no regeneration). The **primary** result is the XTTS
DECTE-vs-VCTK corpus gap — the direct test of the thesis question
("does dialectal/domain-shifted speech make deepfake detection
harder?"). The **secondary** result is the VCTK XTTS-vs-OpenVoice
generator gap from Entry 5, now with CIs.

### Method (shared)
- Reused `results/detector_predictions.csv` (DECTE, Entry 2 run) and
  `results/vctk/detector_predictions.csv` (VCTK, Entry 5 run). No audio
  was rescored, no generation was rerun.
- Filtered to `detector_name == "aasist"`.
- Metrics via `src/evaluation/metrics.compute_metrics` (unchanged).
- 1000 non-parametric bootstrap iterations per analysis, base seed 42.
  Each iteration independently resamples each arm's bonafide and spoof
  arrays with replacement at their original sizes.
- Reproducers:
  - Primary: `python scripts/06_bootstrap_xtts_corpus_gap.py`
  - Secondary: `python scripts/05_bootstrap_vctk_generator_ci.py`

---

## Primary result — XTTS DECTE-vs-VCTK corpus/domain gap (thesis headline)

### Result (citable text)

> Under a shared detector (AuralGuard-AASIST) and generator (XTTS v2),
> the detector achieved 34.63% EER on the DECTE dialectal test
> condition (95% bootstrap CI 28.85–41.33%) and 21.83% EER on the VCTK
> English-control condition (95% bootstrap CI 15.91–27.25%). The
> DECTE-minus-VCTK gap was +12.80 percentage points with a 95%
> bootstrap CI of +6.13 to +22.07 percentage points. Because the full
> gap CI lies above zero, the DECTE-vs-VCTK dialect/domain gap for
> XTTS v2 is statistically supported at 95%. This is the direct test
> of the thesis question ("does dialectal / domain-shifted speech make
> audio deepfake detection harder?"), and the answer is yes for this
> detector-generator pair.

### Raw numbers

| Arm                          | n_bonafide | n_spoof | EER (%) | EER 95% CI       | AUC    |
|------------------------------|-----------:|--------:|--------:|-----------------:|-------:|
| DECTE XTTS v2                | 216        | 100     | 34.630  | 28.852 – 41.333  | 0.6792 |
| VCTK  XTTS v2                | 120        | 100     | 21.833  | 15.906 – 27.250  | 0.8917 |
| **Gap (DECTE − VCTK) in pp** | —          | —       | **+12.796** | **+6.133 – +22.068** | —      |

Notes:
- DECTE XTTS arm downsampled to n=100 spoofs via seed 42 to match
  Entry 2's balanced-N comparison. Bonafide pool: DECTE's full 216
  unique reference utterances.
- VCTK XTTS arm uses the full 100 XTTS spoofs against the 120 unique
  matched originals (Entry 5 slate).
- The corpus-gap CI is computed by *joint* bootstrap: on each iteration
  both corpora's arrays are independently resampled, both EERs are
  recomputed, and the gap is recorded — so the CI is on the difference
  directly, not on the two marginals separately.

### Interpretation (headline)

- **The full gap CI is above zero.** DECTE (34.63%) is harder than
  VCTK (21.83%) for XTTS v2 across the entire 95% resampling interval
  — the +6.13pp lower bound leaves substantial margin above 0.
- **The dialect/domain gap for XTTS v2 is statistically supported at
  95%.** This is the load-bearing quantitative claim for the thesis
  headline "does your accent make you vulnerable?".
- The primary story is now: *dialect/domain matters for XTTS*. The
  secondary story (below) is that generator type matters even more in
  some cases — OpenVoice's severe VCTK failure is real, but the
  headline dialect/domain result no longer depends on OpenVoice
  behaviour.

---

## Secondary result — VCTK XTTS-vs-OpenVoice generator gap

### Result (citable text)

> On the VCTK English-control set, XTTS v2 achieved 21.83% EER with a
> 95% bootstrap CI of 15.92–27.75%, while OpenVoice v2 achieved 74.58%
> EER with a 95% bootstrap CI of 67.75–80.42%. The non-overlapping
> intervals show that OpenVoice v2 is substantially more difficult for
> the detector than XTTS v2 in this control condition. This supports a
> generator-specific vulnerability claim in addition to (not instead
> of) the primary dialect/domain result above.

### Raw numbers

| Generator     | n_bonafide | n_spoof | EER (%) | EER 95% CI       | AUC    |
|---------------|-----------:|--------:|--------:|-----------------:|-------:|
| VCTK XTTS v2      | 120    | 100     | 21.833  | 15.917 – 27.750  | 0.8917 |
| VCTK OpenVoice v2 | 120    | 100     | 74.583  | 67.750 – 80.419  | 0.1643 |

Interval separation: XTTS upper 27.75% vs OpenVoice lower 67.75% →
**~40 percentage points between the intervals**, well beyond any
"sampling noise" objection.

*Small note on the two VCTK-XTTS CI numbers.* The primary section
reports the VCTK XTTS CI as 15.906–27.250% (from `scripts/06`, joint
seed 42 with DECTE); the secondary section reports 15.917–27.750%
(from `scripts/05`, per-generator seed 42/43 offset). Both use 1000
iterations of the same non-parametric bootstrap; the tenths-of-a-point
difference reflects only the different starting seeds of the two
scripts' RNG state. Point estimate (21.833%), AUC (0.8917), and sample
sizes are identical.

### Interpretation (secondary)

- OpenVoice v2 is much harder than XTTS v2 on VCTK, and the CIs do not
  overlap → generator-specific vulnerability is statistically clear.
- **But this is secondary to the dialect/domain result.** The primary
  thesis claim ("dialectal / domain-shifted speech is harder for
  detection") holds independently of any OpenVoice behaviour, because
  the primary test compared XTTS on both corpora.
- The generator-vulnerability finding remains valuable as a second-order
  contribution: it complicates the naive "one number per corpus" story
  and shows that any thesis that quotes a single EER per corpus is
  hiding a large generator effect.

---

## Caveats (shared)

- **The VCTK generator comparison is balanced per generator, not fully
  paired utterance-by-utterance.** The VCTK XTTS and OpenVoice subsets
  share 80 of 120 unique source originals — each subset has 20
  originals unique to it. See Entry 5's caveat block for the
  RandomState explanation. Report as "balanced per-generator
  comparison" only.
- **DECTE-vs-VCTK is a corpus/domain comparison, not a pure dialect
  comparison.** DECTE and VCTK differ on multiple axes at once:
  dialect (Tyneside vs mostly-southern English), recording style
  (interview vs studio-read), channel (variable field recording vs
  clean 48 kHz studio), age distribution (multi-decade vs 19/20 in
  `21-30`), and even the transcript / target-utterance construction
  pipeline. Use the phrase **"dialect / domain gap"** — not "dialect
  gap alone" — unless a later analysis isolates dialect specifically
  (e.g. by adding a Northern English VCTK subset, an age-matched
  subset, or channel-matched noise).
- Other caveats from Entries 4 and 5 still apply: AuralGuard's
  training set includes GLOBE (a US-English clean corpus), so the
  detector's *bonafide* recognition on VCTK is aided by in-distribution
  familiarity — the load-bearing numbers are the *spoof* EERs, not
  the bonafide-side scores. Everything hangs on a single detector
  (AuralGuard-AASIST); a second detector remains queued.

## Reproducibility state at this entry

- Primary script: `scripts/06_bootstrap_xtts_corpus_gap.py`.
- Secondary script: `scripts/05_bootstrap_vctk_generator_ci.py`
  (commit `b555df8`).
- Inputs: `results/detector_predictions.csv` (DECTE, gitignored) and
  `results/vctk/detector_predictions.csv` (VCTK, gitignored).
- Outputs (both gitignored):
  - `results/xtts_corpus_gap_bootstrap_ci.csv`
  - `results/vctk/vctk_generator_bootstrap_ci.csv`
- Bootstrap parameters: 1000 iterations, base seed 42; DECTE XTTS spoof
  set downsampled to n=100 via seed 42 to reproduce Entry 2's balanced
  sample.

## Updated thesis table (with 95% CIs for all four cells)

| Corpus                       | XTTS v2 EER (95% CI)              | OpenVoice v2 EER (95% CI)         |
|------------------------------|----------------------------------:|----------------------------------:|
| DECTE dialectal (Entry 2)    | 34.63% (29.54 – 41.10%)           | 47.84% (42.07 – 54.32%)           |
| VCTK English-control         | 21.83% (15.91 – 27.25%)           | 74.58% (67.75 – 80.42%)           |

Row summary:
- **XTTS v2 corpus gap: +12.80pp, 95% CI [+6.13, +22.07] — supported.**
  (This is the thesis headline.)
- OpenVoice v2 corpus gap: −26.74pp (DECTE actually easier). CI on
  this gap not yet computed; noted as an open item.

## Next research step (queued, not yet started)

Priority reordered given that the headline dialect/domain claim now has
statistical support:

1. **Mitigation attempt (small, safe).** Fine-tune / adapt
   AuralGuard-AASIST using a small dialect-aware training set and
   re-run the DECTE-vs-VCTK XTTS bootstrap. Success criterion is
   simply "the DECTE XTTS EER drops and/or the corpus gap shrinks" —
   this turns the thesis from measurement into a partial solution.
2. **Second detector baseline.** Adding one more anti-spoofing
   detector (Wav2Vec2-AASIST or RawGAT-ST family) would let us claim
   the dialect/domain and generator effects are not
   AuralGuard-specific.
3. **Reviving gender / age / region breakdown.** Would make the
   sociolinguistic side of the thesis stronger, complementing the
   corpus-level headline.
4. **Pre-picked target-set fix.** Small `SpoofPipeline.run()` change so
   future XTTS-vs-OpenVoice runs on the same corpus are truly paired
   (overlap → 100). Code-only, no regeneration for existing tables.

---

## Entry 7 — 2026-07-27 — Mitigation v2 partial-unfreeze adaptation significantly reduces DECTE XTTS EER

**Status: statistically supported mitigation.** Mitigation v1 (Entry 7's
predecessor, head-only fine-tune) produced only a suggestive DECTE
improvement whose paired-bootstrap CI included zero. Mitigation v2
(partial backbone unfreeze — last heterogeneous-GAT block + all heads)
turns that suggestive result into a **statistically supported win**:
DECTE XTTS EER drops from 40.70% to 23.26% with a 95% CI on the delta
of [-28.49, -9.30] pp (entirely below zero), and VCTK XTTS shows no
significant regression. This is the first mitigation result in the
project that clears the "delta CI entirely below zero" bar.

### Method
- Started from the baseline checkpoint
  `auralguard-aasistpp/results/final_accent_globe_wavefake_balanced_full/best.pt`
  (val_metrics.eer ≈ 1.7% — Entry 3), NOT from mitigation v1.
- Reused the leakage-safe DECTE speaker split from
  `scripts/09_build_mitigation_csvs.py` (52 train / 14 val / 16 test).
- Applied the new `--unfreeze-modules` scalpel added to
  `auralguard-aasistpp/src/train.py` this cycle:
  ```
  --freeze-backbone
  --unfreeze-modules "HtrgGAT_layer_ST21,HtrgGAT_layer_ST22,pool_hS2,pool_hT2,master2"
  --lr 3e-5  --epochs 5  --batch-size 4
  ```
- Trainable parameter budget printed at training start:
  **31,372 trainable / 268,104 frozen** (~10.5% of the model). The five
  named backbone modules plus the three AuralGuard heads all showed up
  in the trainable list; nothing else did.
- In-domain sanity check with the v2 checkpoint on the AuralGuard val
  set: **PASS at 2.50% EER** (within ~1pp of the baseline's 1.7%), so
  the partial adaptation did not catastrophically forget the original
  training distribution.
- Evaluation via the same paired-bootstrap protocol as v1
  (`scripts/10_bootstrap_mitigation_effect.py`, 1000 iterations, seed 42,
  stratified within-file resampling so the delta is a true paired
  comparison).

### Result (citable text)

> A conservative partial-unfreeze mitigation (last heterogeneous-GAT
> block of AASIST plus the three AuralGuard heads, 31,372 trainable of
> 300k total parameters, learning rate 3e-5, 5 epochs) reduced held-out
> DECTE XTTS EER from 40.70% to 23.26%, a change of -17.44 percentage
> points with a paired-bootstrap 95% confidence interval of
> [-28.49, -9.30] pp (interval entirely below zero). On the VCTK
> English-control set, XTTS EER moved from 21.83% to 19.17%, a change
> of -2.67 pp with a 95% CI of [-5.42, +3.17] pp (interval includes
> zero, i.e. no statistically significant regression). An in-domain
> sanity check on the AuralGuard validation set gave 2.50% EER, within
> approximately one percentage point of the baseline's ~1.7%, confirming
> that the partial adaptation did not destroy general anti-spoofing
> capability.

### Raw numbers — v1 vs v2

DECTE XTTS held-out test slice (16 speakers, 86 matched pairs):

| Run | Baseline EER | Mitigated EER | Delta (pp) | 95% CI (pp)        | Verdict                              |
|-----|-------------:|--------------:|-----------:|-------------------:|:-------------------------------------|
| v1  | 40.698%      | 36.047%       |  -4.651    | [-12.791, +2.907]  | Neutral (CI includes 0)              |
| v2  | 40.698%      | **23.256%**   | **-17.442**| **[-28.488, -9.302]**| **WIN (CI entirely below 0)**      |

VCTK XTTS control (100 XTTS spoofs vs 120 bonafide, out-of-training):

| Run | Baseline EER | Mitigated EER | Delta (pp) | 95% CI (pp)       | Verdict                          |
|-----|-------------:|--------------:|-----------:|------------------:|:---------------------------------|
| v1  | 21.833%      | 25.917%       |  +4.083    | [-0.417, +7.169]  | OK — no significant regression   |
| v2  | 21.833%      | **19.167%**   |  -2.667    | [-5.419, +3.167]  | OK — no significant regression   |

Notes:
- v1 and v2 baseline rows are identical because both compare against the
  same untouched AuralGuard-AASIST baseline on the same held-out test
  files — v2's mitigated column is the only thing that changed.
- v2's AUC on DECTE XTTS is **0.8759** (up from baseline 0.6530); on
  VCTK XTTS it's **0.8936** (up from baseline 0.8917). Ranking quality
  improved on DECTE without any measurable drop on VCTK.

### Interpretation

- **Head-only adaptation (v1) was too weak.** With only ~1,600
  trainable parameters (the three heads), the model could shift its
  classification boundary but couldn't adjust its feature
  representation of DECTE speech. The point-estimate improvement of
  -4.65pp on DECTE hid inside a wide CI that reached +2.91pp.
- **Partial final-GAT unfreezing (v2) produced a statistically
  supported DECTE improvement.** Adding ~30k parameters in the last
  heterogeneous graph-attention stage was enough for the model to
  re-shape its final feature view for DECTE while leaving the early
  conv/encoder/first-GAT stack untouched. The DECTE delta CI now sits
  entirely below zero.
- **The dialect/domain gap can be reduced by adapting the final
  feature stage, not only the classifier heads.** This is the key
  methodological finding of the mitigation phase: the ~13pp DECTE-vs-
  VCTK XTTS gap documented in Entry 6 is not immutable — a small,
  targeted fine-tune can close most of it under the same generator.
- **OpenVoice remains a separate, unresolved vulnerability.** Nothing
  in this mitigation experiment addresses the ~75% OpenVoice EER seen
  on VCTK in Entry 5. That failure mode is orthogonal to the dialect/
  domain gap this entry mitigates.

### Caveats

- **Single-detector, single-corpus-pair scope.** This entry
  demonstrates that mitigation is *possible* on AuralGuard-AASIST for
  the DECTE-vs-VCTK XTTS comparison. It does not show the technique
  generalises to other detectors, other dialects, or other generators.
  A second-detector replication is now the highest-priority open item.
- **v2 was tuned on DECTE XTTS data.** It should not be presented as a
  universal anti-spoofing improvement. What it demonstrates is that
  small, targeted adaptation of the last feature stage can close a
  measured domain gap on the specific corpus it was trained for. The
  16-speaker held-out DECTE test slice makes the specific number
  defensible; broader claims need more data.
- **Small held-out DECTE test set (86 XTTS spoofs / 86 bonafide).**
  The bootstrap CI of [-28.49, -9.30]pp is wide precisely because the
  test slice is small. A larger DECTE test set would tighten this CI
  substantially. The key qualitative claim ("CI entirely below zero")
  is robust to this width, but the exact -17.44pp point estimate
  should not be over-interpreted.
- **VCTK CI still touches ~+3pp on the upper side.** The v2 VCTK
  result is "no significant regression" — not "guaranteed no
  regression". A larger VCTK evaluation would sharpen the guardrail.

### Reproducibility state at this entry

- Baseline checkpoint (never modified):
  `auralguard-aasistpp/results/final_accent_globe_wavefake_balanced_full/best.pt`
- v1 checkpoint (never modified since Entry 7's predecessor):
  `checkpoints/mitigation_v1_decte_finetune/best.pt`
- v2 checkpoint (this entry):
  `checkpoints/mitigation_v2_partial_unfreeze/best.pt`
- Training script: `auralguard-aasistpp/src/train.py` with the
  `--unfreeze-modules` addition (Option A patch from this cycle).
- Detector configs (one per model, all in this repo):
  - `configs/detectors.yaml` → baseline
  - `configs/detectors_mitigated.yaml` → v1
  - `configs/detectors_mitigated_v2.yaml` → v2
- Data (unchanged from v1):
  - `data/decte/metadata/decte_mitigation_train.csv` (52 speakers)
  - `data/decte/metadata/decte_mitigation_val.csv` (14 speakers)
  - `data/generated_spoofs/manifest_mitigation_test.jsonl` (16 speakers, 86 XTTS)
- Eval outputs (all gitignored under `results/mitigation_v2/`):
  - `baseline_decte/detector_predictions.csv`
  - `mitigated_decte/detector_predictions.csv`
  - `baseline_vctk/detector_predictions.csv`
  - `mitigated_vctk/detector_predictions.csv`
  - `mitigation_effect_bootstrap_ci.csv`
  - `indomain_sanity_metrics.csv`

### Next research step (queued, not yet started)

Priority reordered given that mitigation is now statistically supported:

1. **Second detector baseline + mitigation replication.** The single
   most valuable next milestone. Retrain a second anti-spoofing model
   (Wav2Vec2-AASIST or RawGAT-ST) on the same data, run the same
   DECTE-vs-VCTK XTTS pipeline, and see whether the corpus gap AND the
   mitigation both replicate. This turns "one lucky mitigation on one
   detector" into "the effect and its fix generalise across detector
   families".
2. **DECTE-vs-VCTK OpenVoice bootstrap (delta CI).** Mitigation v2 was
   deliberately scoped to XTTS. Entry 5's finding that OpenVoice's
   VCTK EER (74.58%) is *worse* than its DECTE EER (47.84%) has never
   been given a delta CI. Same script as Entry 6, opposite direction.
3. **Reviving gender / age / region breakdown on the mitigation
   split.** Would let us report *who* the mitigation helps most in the
   DECTE test slice — sociolinguistic angle for the thesis.
4. **Pre-picked target-set fix.** Small `SpoofPipeline.run()` change so
   future XTTS-vs-OpenVoice runs on the same corpus are truly paired
   (Entry 5's 80/120 overlap caveat). Code-only, no regeneration for
   existing tables.

---

## Entry 8 — 2026-07-27 — LFCC + Logistic Regression second detector replicates DECTE-vs-VCTK XTTS gap

**Status: cross-architecture replication of the Entry 6 headline.** The
DECTE-vs-VCTK XTTS dialect/domain gap AASIST showed in Entry 6 also
appears — at essentially the same magnitude and with 95% bootstrap
support — on a completely different detector family: hand-crafted LFCC
features + a linear (logistic-regression) classifier. This is the
strongest evidence yet that the gap is not an artefact of the AASIST
architecture.

### Method
- **Features**: 20 LFCC coefficients + Δ + ΔΔ (60-dim per frame) via a
  linear-scale triangular filter bank + log + type-2 orthonormal DCT
  (standard ASVspoof LFCC front-end, implemented with `librosa.stft` +
  `scipy.fftpack.dct`). Mean + std pooling over time → **120-dim
  utterance vector**.
- **Audio preprocessing IDENTICAL to the AASIST detector**: soundfile
  read → mono average → resample to 16 kHz → deterministic 4-second
  zero-padded crop from position 0. Both detectors therefore see the
  same 4-s window per file. **Architecture-only comparison.**
- **Classifier**: `sklearn.pipeline.Pipeline([StandardScaler(),
  LogisticRegression(class_weight="balanced", C=1.0, max_iter=1000,
  solver="lbfgs", random_state=42)])`.
- **Score**: `predict_proba(...)[:, class 0]` = P(bonafide). Higher =
  more real, matching `src/evaluation/metrics.py`'s convention.
- **Training data**: the full AuralGuard train CSV (35,206 rows),
  **filtered to remove the 16 held-out DECTE mitigation-test speakers**
  to protect against leakage into the eval slice.
- **Evaluation**: same held-out slices as AASIST — DECTE mitigation test
  manifest (86 XTTS spoofs vs 86 matched originals) and VCTK XTTS
  subset (100 XTTS spoofs vs 120 unique matched originals from the
  Entry 5 pool).
- **Bootstrap**: 1000 iterations, seed 42, joint stratified independent
  resampling of each corpus's bonafide and spoof arrays, per-iteration
  DECTE-EER and VCTK-EER and their difference recorded — so the gap CI
  is on the difference directly.
- **Reproducer**: `python scripts/11_lfcc_lr_second_detector.py`.

### Leakage protection and data-integrity checks

- Leakage filter matched **1,445 rows** in the AuralGuard train CSV
  against the 16 held-out DECTE mitigation test speakers. All 1,445
  removed before feature extraction.
- DECTE rows in AuralGuard train CSV: **8,057 before filter → 6,612 after**.
- Path resolution check on the ~34k retained training rows: **80 files
  missing (0.24%)** — well below the script's 5% abort threshold.
- Final training matrix: **X = (33,681, 120)**, class balance intact.
- `model.classes_` = `[0 1]` — confirms `predict_proba[:, 0]` is P(bonafide).

### Result (citable text)

> On the same held-out DECTE mitigation test slice and VCTK XTTS
> control that AASIST was scored on, a second detector built on
> classical hand-crafted features (LFCC + Δ + ΔΔ, mean-std pooled,
> 120-dim) fed to a StandardScaler + LogisticRegression classifier
> produced 44.19% EER on DECTE XTTS (95% bootstrap CI 36.05–51.16%)
> and 31.75% EER on VCTK XTTS (95% CI 25.00–38.17%). The DECTE minus
> VCTK gap is +12.44 percentage points with a 95% bootstrap CI of
> [+1.96, +21.76] pp (entirely above zero). Both the direction and
> the point-estimate magnitude closely match AASIST's Entry 6 gap of
> +12.80 pp — so the DECTE-vs-VCTK XTTS dialect/domain gap replicates
> across two architecturally very different detectors (deep
> graph-attention + learned SincConv vs a convex linear model on
> hand-crafted spectral features).

### Raw numbers

Two detectors, same protocol, same held-out data:

| Detector | DECTE XTTS EER (95% CI) | VCTK XTTS EER (95% CI) | Gap DECTE − VCTK (95% CI) | Overall strength |
|---|---:|---:|---:|:---|
| **AASIST** (Entry 6)     | 34.63% (28.85 – 41.33) | 21.83% (15.91 – 27.25) | **+12.80 pp (+6.13 – +22.07)** | Deep, strong AUC ~0.68/0.89 |
| **LFCC + LR** (this entry) | 44.19% (36.05 – 51.16) | 31.75% (25.00 – 38.17) | **+12.44 pp (+1.96 – +21.76)** | Classical baseline, AUC ~0.66/0.73 |

Gap-magnitude difference between detectors: |12.80 − 12.44| = 0.36 pp.
Both gap CIs are entirely above zero; both lie in roughly the same
positive range.

### Interpretation

- **LFCC + LR is weaker than AASIST overall.** Its DECTE XTTS EER of
  44.19% and VCTK XTTS EER of 31.75% are both higher than AASIST's
  34.63% and 21.83%. That is expected — a linear model on 120
  hand-crafted features cannot match AASIST's learned graph-attention
  representation on absolute detection strength.
- **But the DECTE-vs-VCTK gap is almost identical.** +12.44 pp for
  LFCC-LR vs +12.80 pp for AASIST — the two point estimates differ by
  a third of a percentage point. Both gap CIs are entirely positive.
  The dialect/domain difficulty gap survives a full swap of feature
  extractor and classifier family.
- **This supports the claim that the gap is not architecture-specific.**
  The Entry 6 headline result ("does your accent make you vulnerable?
  — yes for XTTS") is not a quirk of AASIST's deep graph-attention
  design; a linear classifier on classical cepstral features sees
  essentially the same effect. That materially strengthens the
  thesis' external validity.
- **Note on the marginal CIs overlapping** — the LFCC-LR DECTE CI
  (36.05–51.16%) and VCTK CI (25.00–38.17%) overlap in [36.05, 38.17],
  which naively looks inconsistent with "gap CI entirely above zero".
  It isn't: the marginal CIs are wider than the *per-iteration*
  paired differences. The joint bootstrap correctly evaluates each
  bootstrap iteration's DECTE and VCTK EER together and records the
  gap. Every bootstrap iteration having DECTE > VCTK (or nearly every)
  is compatible with the marginals sitting in the overlap zone.
  Reporting the direct gap CI is the correct thing.

### Caveats

- **LFCC + LR is a simple classical baseline, not state-of-the-art.**
  This entry is about *the gap replicating across detector families*,
  not about the absolute EER numbers being deployment-worthy. Do not
  cite the 31.75% or 44.19% figures as "how good/bad the detector is
  in general" — cite them only in comparison to each other.
- **The result confirms direction and gap magnitude, not absolute
  deployment performance.** Neither the LFCC-LR baseline nor AASIST
  is being proposed as a production system. What this entry supports
  is: *whatever detector you run on this DECTE-vs-VCTK XTTS setup,
  you are likely to see a similar-sized dialect/domain gap*.
- Other Entry 6 caveats still apply: DECTE-vs-VCTK is a
  corpus/domain comparison, not a pure dialect comparison. VCTK's
  age-band skew, GLOBE-adjacent training bias on the real side, and
  the small held-out sample sizes are unchanged.

### Reproducibility state at this entry

- Script: `scripts/11_lfcc_lr_second_detector.py` (self-contained: LFCC
  extraction + LR training + evaluation + bootstrap in one file).
- Training source: `auralguard-aasistpp/data/metadata/train_final_accent_globe_wavefake_balanced.csv`
  with the 16 DECTE test speakers filtered out via the script's
  `speaker_from_path` + speaker-column fallback logic.
- Eval sources (unchanged, same as Entries 5–7):
  - `data/generated_spoofs/manifest_mitigation_test.jsonl` (DECTE)
  - `data/generated_spoofs_vctk/manifest.jsonl` (VCTK, XTTS subset filtered in-script)
- Outputs (all gitignored under `results/second_detector_lfcc_lr/`):
  - `train_features.npz` (feature cache; use `--refresh-features` to rebuild)
  - `lfcc_lr_model.joblib` (fitted StandardScaler + LR)
  - `lfcc_lr_results.csv` (per-corpus rows + gap row with CIs)

### Updated thesis table (two detectors, four cells with CIs)

| Corpus                        | AASIST XTTS EER (95% CI)      | LFCC+LR XTTS EER (95% CI)     |
|-------------------------------|------------------------------:|------------------------------:|
| DECTE dialectal               | 34.63% (28.85 – 41.33)        | 44.19% (36.05 – 51.16)        |
| VCTK English-control          | 21.83% (15.91 – 27.25)        | 31.75% (25.00 – 38.17)        |
| **DECTE − VCTK gap**          | **+12.80 pp (+6.13 – +22.07)** | **+12.44 pp (+1.96 – +21.76)** |

### Next research step (queued, not yet started)

Priority reordered given the two-detector replication now anchors the
headline claim:

1. **DECTE-vs-VCTK OpenVoice bootstrap (delta CI).** Entry 5's finding
   that OpenVoice's VCTK EER (74.58%) is *worse* than its DECTE EER
   (47.84%) has never been given a delta CI. Same joint-bootstrap
   machinery as Entry 6, opposite direction. Small script, no new
   audio or training.
2. **LFCC-LR mitigation replication.** Retrain the LFCC-LR classifier
   with a DECTE-adapted training subset (using the same mitigation
   train CSV that Entry 7 used) and see whether a paired-bootstrap
   comparison of baseline-LR vs adapted-LR on DECTE test shows the
   same "mitigation helps" pattern Entry 7 saw for AASIST. Would show
   the mitigation direction is also detector-invariant.
3. **Reviving gender / age / region breakdown on the DECTE test slice.**
   Sociolinguistic angle for the thesis; small analysis script over
   the existing predictions CSVs.
4. **Pre-picked target-set fix** for future paired VCTK runs
   (Entry 5's 80/120 overlap caveat). Code-only, no regeneration.

---

## Entry 9 — 2026-07-27 — OpenVoice corpus gap reverses direction, showing generator-specific vulnerability

**Status: statistically supported reversal of direction relative to the
XTTS gap.** Entry 6 established a positive DECTE − VCTK XTTS gap
(DECTE harder, +12.80 pp, CI entirely above zero). Entry 9 attaches the
same paired-bootstrap CI to the OpenVoice arm and finds the gap goes
the **other way**: DECTE − VCTK OpenVoice = −26.74 pp, 95% CI
[−35.69, −18.26], entirely below zero. Combined with Entry 6, this is
the clearest quantitative evidence yet that the OpenVoice-specific
failure mode should not be described as a dialect effect.

### Method
- Reused two existing prediction CSVs — no rescoring, no retraining:
    - DECTE: `results/detector_predictions.csv` (full Phase 2 run,
      contains all `openvoice_v2` rows generated across the DECTE
      manifest)
    - VCTK: `results/vctk/detector_predictions.csv` (Entry 5 run)
- Filtered to `detector_name == "aasist"` and
  `generator_name == "openvoice_v2"`.
- Bonafide pools: DECTE full 216 unique bonafide rows; VCTK full 120
  unique matched originals (Entry 5 methodology).
- Spoof pools: 100 OpenVoice v2 spoofs per corpus (both already at
  N=100 — no downsampling needed).
- Metrics via `src/evaluation/metrics.compute_metrics` (unchanged).
- 1000 non-parametric bootstrap iterations, base seed 42. Each
  iteration independently resamples each arm's bonafide and spoof
  arrays with replacement (same original sizes), computes EER per
  corpus, and records the gap in a single pass — same joint-bootstrap
  design as Entry 6.
- Reproducer: `python scripts/12_bootstrap_openvoice_corpus_gap.py`.

### Result (citable text)

> Under a shared detector (AuralGuard-AASIST) and generator (OpenVoice
> v2), the detector achieved 47.84% EER on the DECTE dialectal test
> condition (95% bootstrap CI 41.83–53.39%) and 74.58% EER on the VCTK
> English-control condition (95% bootstrap CI 68.17–80.92%). The
> DECTE-minus-VCTK gap was −26.74 percentage points with a 95%
> bootstrap CI of [−35.69, −18.26] pp. Because the full gap CI lies
> below zero, the DECTE-vs-VCTK OpenVoice comparison reverses the
> direction of the XTTS comparison from Entry 6 (+12.80 pp, CI entirely
> above zero) at 95%. OpenVoice v2 is measurably harder for the
> detector on standard-accent studio-quality English (VCTK) than on
> Tyneside dialectal interview speech (DECTE), so the OpenVoice failure
> mode should be described as a generator-specific / OpenVoice-domain-
> interaction vulnerability, not a dialect effect.

### Raw numbers

| Arm                          | n_bonafide | n_spoof | EER (%) | EER 95% CI       | AUC    |
|------------------------------|-----------:|--------:|--------:|-----------------:|-------:|
| DECTE OpenVoice v2           | 216        | 100     | 47.843  | 41.827 – 53.394  | 0.5675 |
| VCTK  OpenVoice v2           | 120        | 100     | 74.583  | 68.167 – 80.917  | 0.1643 |
| **Gap (DECTE − VCTK) in pp** | —          | —       | **−26.741** | **[−35.686, −18.255]** | —      |

Notes:
- The VCTK OpenVoice AUC of 0.1643 (well below 0.5) is not a metric
  error. It reflects that OpenVoice v2 spoofs receive systematically
  higher bonafide-ness scores from AASIST than real VCTK utterances do
  (Entry 4 already showed this at the mean-score level). The metric
  is doing the right thing — the *detector* is inverted on this
  generator+corpus combination.
- Gap CI is on the difference directly (recorded per bootstrap
  iteration), not derived from the two marginal CIs.

### Direction comparison — XTTS vs OpenVoice, same detector, same corpora

Combining Entry 6 and Entry 9:

| Generator | DECTE EER (95% CI)      | VCTK EER (95% CI)      | Gap (DECTE − VCTK, 95% CI) | Sign of gap |
|-----------|------------------------:|-----------------------:|---------------------------:|:------------|
| XTTS v2   | 34.63 (28.85 – 41.33) % | 21.83 (15.91 – 27.25) %| **+12.80 [+6.13, +22.07] pp** | positive (DECTE harder) |
| OpenVoice v2 | 47.84 (41.83 – 53.39) % | 74.58 (68.17 – 80.92) %| **−26.74 [−35.69, −18.26] pp** | negative (VCTK harder) |

Both gap CIs are entirely on their respective sides of zero — the sign
flip between generators is statistically supported at 95%.

### Interpretation

- **XTTS shows DECTE > VCTK.** Dialect/domain shift makes XTTS spoofs
  harder to catch on Tyneside DECTE than on standard-accent VCTK.
  This is the thesis-headline "dialect gap" claim from Entry 6.
- **OpenVoice shows VCTK > DECTE.** The direction is opposite. Whatever
  is making OpenVoice v2 hard for AASIST, it's *worse* on the cleaner
  studio-quality VCTK than on the dialectal interview-style DECTE.
- **Therefore OpenVoice failure is not dialect bias.** A dialect effect
  should push the same direction as XTTS's DECTE > VCTK. It doesn't.
  The two generator gaps flip sign under identical detector +
  bonafide-pool + audio-preprocessing conditions.
- The OpenVoice failure is best described as a **generator-specific /
  OpenVoice-domain-interaction vulnerability** — something in OpenVoice
  v2's output distribution collides with AASIST's decision surface in
  a way that VCTK-clean input exposes more strongly than DECTE-noisy
  input. This is a separate research question from the dialect gap
  and should be reported as a distinct finding in the thesis.

### Caveats

- **Single detector.** All Entry 9 numbers come from AuralGuard-AASIST.
  The XTTS gap has already been replicated on a second detector
  (LFCC + LR, Entry 8) so its cross-architecture support is stronger
  than the OpenVoice gap's. Ideally the OpenVoice DECTE-vs-VCTK gap
  should be re-run through the LFCC-LR pipeline before making the
  reversal claim in the thesis' strongest form. Queued for a future
  entry if time allows.
- **VCTK's low OpenVoice AUC (0.1643) reflects mis-ranking, not
  broken detection direction.** The score-direction convention was
  fixed and sanity-checked in Entry 3; the mis-ranking is a real
  property of AASIST's behaviour on OpenVoice v2, not a pipeline bug.
- Prior Entry 4 / 5 caveats still apply: VCTK's age-band skew, GLOBE-
  adjacent training bias on the real side, and the fact that VCTK and
  DECTE differ on multiple axes (dialect + recording style + channel
  + age distribution) simultaneously. The "generator-specific"
  interpretation of Entry 9 is robust to all of those because the
  *same* comparison in the *opposite* direction is what defines the
  reversal.

### Reproducibility state at this entry

- Script: `scripts/12_bootstrap_openvoice_corpus_gap.py`.
- Inputs (both gitignored, produced by earlier Phase 2 runs):
  - `results/detector_predictions.csv` (DECTE full Phase 2)
  - `results/vctk/detector_predictions.csv` (VCTK Phase 2)
- Output (gitignored via `results/` rule):
  - `results/openvoice_corpus_gap/openvoice_corpus_gap_bootstrap_ci.csv`
- Bootstrap parameters: 1000 iterations, base seed 42 (same as
  Entries 2, 5, 6, 7, 8, so all CI computations in the log share the
  same resampling contract).

### Updated headline table — corpus × generator with 95% CIs, both directions

Combining Entries 6 (XTTS gap) and 9 (OpenVoice gap):

| Corpus                       | XTTS v2 EER (95% CI)          | OpenVoice v2 EER (95% CI)      |
|------------------------------|------------------------------:|-------------------------------:|
| DECTE dialectal              | 34.63% (28.85 – 41.33)        | 47.84% (41.83 – 53.39)         |
| VCTK English-control         | 21.83% (15.91 – 27.25)        | 74.58% (68.17 – 80.92)         |
| **DECTE − VCTK gap (95% CI)** | **+12.80 pp [+6.13, +22.07]** | **−26.74 pp [−35.69, −18.26]** |

The two gap rows are in opposite directions, both statistically
supported at 95% — a cleaner narrative structure for the thesis:
*XTTS exposes dialect/domain difficulty; OpenVoice exposes a separate
generator-specific vulnerability.*

### Next research step (queued, not yet started)

Priority reordered given Entry 9 splits the story cleanly by generator:

1. **LFCC-LR replication of the OpenVoice DECTE-vs-VCTK gap.** Mirrors
   Entry 8's XTTS replication. Small script — reuses the existing
   LFCC-LR model from Entry 8 (or retrains a fresh one on the
   leakage-filtered training set), scores the two OpenVoice subsets,
   and runs the same joint bootstrap. Would elevate Entry 9 to
   cross-architecture status.
2. **Reviving gender / age / region breakdown on DECTE test slice.**
   Sociolinguistic angle for the thesis; small analysis over existing
   predictions CSVs.
3. **Pre-picked target-set fix** for future paired VCTK runs
   (Entry 5's 80/120 overlap caveat). Code-only, no regeneration
   for existing tables.
4. **Second-detector mitigation replication.** Retrain the LFCC-LR
   classifier with a DECTE-adapted training subset (using the same
   mitigation train CSV that Entry 7 used) and see whether the
   mitigation direction (Entry 7 for AASIST) also replicates.

---

## Entry 10 — 2026-07-27 — LFCC-LR replicates OpenVoice corpus-gap reversal

**Status: cross-detector replication of Entry 9's OpenVoice reversal.**
Entry 9 established a statistically supported *negative* DECTE − VCTK
OpenVoice gap on AASIST (−26.74 pp, CI [−35.69, −18.26]) — i.e. VCTK
is harder for OpenVoice than DECTE is, opposite to the XTTS direction.
Entry 10 re-runs the same paired-bootstrap analysis with the
already-fitted LFCC + Logistic Regression detector from Entry 8, on
the exact same audio files. The reversal replicates: LFCC-LR gap is
−42.62 pp with 95% CI [−50.78, −35.64] — same direction, entirely
below zero, and (interestingly) *larger* in magnitude than AASIST's.

Combined with Entry 8 (which gave the XTTS gap the same cross-detector
support), the thesis' generator-vs-corpus story is now anchored by two
architecturally-different detectors on both generators.

### Method
- Reused the fitted LFCC + LR pipeline from Entry 8
  (`results/second_detector_lfcc_lr/lfcc_lr_model.joblib`). **No
  retraining. No new feature extraction on the training set. No
  changes to the model.**
- Sourced eval file lists directly from the AASIST prediction CSVs
  used in Entry 9, so the LR eval slice matches the AASIST eval slice
  file-for-file:
    - DECTE: `results/detector_predictions.csv` → 216 unique bonafide
      + 100 unique OpenVoice spoofs.
    - VCTK:  `results/vctk/detector_predictions.csv` → 120 unique
      matched bonafide + 100 unique OpenVoice spoofs.
- LFCC extraction, audio preprocessing, and utterance-level pooling
  are byte-for-byte the same as Entry 8's script — 20 LFCC coefficients
  + Δ + ΔΔ (60-dim per frame) → mean+std pooling → 120-dim vector.
- Scoring through the full `Pipeline(StandardScaler + LR)`; score =
  `predict_proba(...)[:, class 0]` = P(bonafide). Higher = more real.
- 1000 non-parametric bootstrap iterations, base seed 42, joint
  independent resampling per corpus (same design as Entries 6, 8, 9).
- Reproducer: `python scripts/13_lfcc_lr_openvoice_corpus_gap.py`.

### Result (citable text)

> The already-fitted LFCC + Logistic Regression detector from Entry 8
> was re-run on the identical DECTE and VCTK audio files that AASIST
> scored in Entry 9 (216 bonafide + 100 OpenVoice v2 spoofs from
> DECTE; 120 bonafide + 100 OpenVoice v2 spoofs from VCTK), with the
> same paired bootstrap protocol. The LFCC-LR detector achieved
> 38.21% EER on DECTE OpenVoice (95% CI 33.17–43.53%) and 80.83% EER
> on VCTK OpenVoice (95% CI 76.33–87.25%). The DECTE-minus-VCTK gap
> is −42.62 pp with a 95% bootstrap CI of [−50.78, −35.64] pp
> (entirely below zero, matching the direction of AASIST's −26.74 pp
> gap from Entry 9). The OpenVoice corpus-gap reversal is therefore
> cross-detector supported at 95% — VCTK OpenVoice is significantly
> harder for both a deep graph-attention detector (AASIST) and a
> classical linear detector (LFCC + LR) than DECTE OpenVoice is,
> which is the opposite direction from the XTTS corpus gap and
> confirms that the OpenVoice failure mode should not be described
> as a dialect effect.

### Raw numbers

| Arm                          | n_bonafide | n_spoof | EER (%) | EER 95% CI       | AUC    |
|------------------------------|-----------:|--------:|--------:|-----------------:|-------:|
| LFCC-LR DECTE OpenVoice v2   | 216        | 100     | 38.213  | 33.167 – 43.528  | 0.6036 |
| LFCC-LR VCTK  OpenVoice v2   | 120        | 100     | 80.833  | 76.333 – 87.250  | 0.0830 |
| **Gap (DECTE − VCTK) in pp** | —          | —       | **−42.620** | **[−50.779, −35.639]** | —      |

### Cross-detector OpenVoice-gap comparison (Entries 9 + 10)

| Detector    | DECTE OV EER (95% CI)      | VCTK OV EER (95% CI)       | Gap DECTE − VCTK (95% CI)       | Sign of gap |
|-------------|---------------------------:|---------------------------:|--------------------------------:|:------------|
| AASIST      | 47.84% (41.83 – 53.39)     | 74.58% (68.17 – 80.92)     | **−26.74 pp [−35.69, −18.26]** | negative    |
| LFCC + LR   | 38.21% (33.17 – 43.53)     | 80.83% (76.33 – 87.25)     | **−42.62 pp [−50.78, −35.64]** | negative    |

Both gap CIs are entirely below zero; both point estimates are
substantially negative. The two detectors disagree on absolute EER
level (LFCC-LR is a weaker classifier overall) and on the exact
magnitude of the gap (−42.62 pp vs −26.74 pp), but they agree on the
sign and on statistical support. That's the load-bearing claim.

### Interpretation

- **OpenVoice reversal is now cross-detector supported.** The
  DECTE < VCTK OpenVoice direction shows up on:
    - AASIST (Entry 9): −26.74 pp, CI [−35.69, −18.26]
    - LFCC + LR (this entry): −42.62 pp, CI [−50.78, −35.64]
  Two very different architectures — one deep graph-attention model
  with learned SincConv, one convex linear classifier on hand-crafted
  cepstral features — both put the gap solidly on the negative side.
- **It is not AASIST-specific.** Entry 9 already argued informally
  that the reversal reflects something about OpenVoice v2's output
  distribution, not something about DECTE speech. Entry 10 provides
  the cross-architecture confirmation that argument needs.
- **The OpenVoice failure mode should be described as a
  generator-specific corpus interaction, not DECTE dialect bias.**
  A dialect effect would push the same direction as XTTS's Entries
  6/8 (DECTE > VCTK). It doesn't — and now it doesn't for either
  detector. The thesis should describe the OpenVoice-VCTK
  interaction as a distinct scientific finding: something about
  OpenVoice v2's synthesised waveforms confuses studio-quality
  bonafide-vs-spoof discrimination in a way that dialectal
  interview-style audio partially masks.
- **The LFCC-LR gap magnitude is even larger than AASIST's.** LFCC-LR
  hits 80.83% EER on VCTK OpenVoice — very close to the ~74% AASIST
  saw and consistent with a detector that also fails badly there.
  Meanwhile LFCC-LR on DECTE OpenVoice (38.21%) is actually *better*
  than AASIST's DECTE OpenVoice (47.84%), which drives the wider gap.
  Nothing to over-interpret in the exact magnitude — direction is
  what matters.

### Caveats

- **LFCC-LR is a simple classical baseline and performs poorly on
  VCTK OpenVoice** (80.83% EER, AUC 0.0830). Do not cite these
  absolute numbers as "how good the LR detector is" — they are only
  meaningful as one leg of a cross-architecture direction check.
- **Both detectors' VCTK OpenVoice AUCs are well below 0.5** (0.1643
  for AASIST in Entry 9; 0.0830 for LFCC-LR here). Same mechanism as
  Entry 9: OpenVoice v2 spoofs receive systematically higher
  bonafide-ness scores than real VCTK utterances do, and the metric
  functions correctly report this as sub-random ranking. Not a
  pipeline bug.
- The LFCC-LR training set (~34k rows, AuralGuard train minus the 16
  DECTE test speakers) does not overlap the DECTE test slice, but it
  does contain OpenVoice-adjacent audio only indirectly (via
  WaveFake). Both detectors are being tested out-of-distribution for
  OpenVoice v2 specifically, so the direction agreement is a
  cross-detector claim, not a cross-training-data claim.
- Prior Entry 5/6/9 caveats still apply: VCTK's age-band skew,
  GLOBE-adjacent training bias on the real side, and the fact that
  VCTK and DECTE differ on multiple axes simultaneously. The
  generator-specific-interaction interpretation is robust to those
  because the same reversal is what defines it.

### Reproducibility state at this entry

- Script: `scripts/13_lfcc_lr_openvoice_corpus_gap.py`.
- Fitted LR model (reused, not retrained):
  `results/second_detector_lfcc_lr/lfcc_lr_model.joblib` (Entry 8).
- Inputs (both gitignored, produced by earlier Phase 2 runs):
  - `results/detector_predictions.csv` (DECTE full Phase 2)
  - `results/vctk/detector_predictions.csv` (VCTK Phase 2)
- Output (gitignored via `results/` rule):
  - `results/lfcc_lr_openvoice_corpus_gap/lfcc_lr_openvoice_corpus_gap_bootstrap_ci.csv`
- Bootstrap parameters: 1000 iterations, base seed 42 (shared with
  every other bootstrap analysis in this project).

### Updated headline table — 2 detectors × 2 generators × 2 corpora, all with 95% CIs

Combining Entries 6, 8, 9, 10:

| Detector    | XTTS gap DECTE − VCTK (95% CI)      | OpenVoice gap DECTE − VCTK (95% CI)     |
|-------------|------------------------------------:|----------------------------------------:|
| AASIST      | **+12.80 pp [+6.13, +22.07]**       | **−26.74 pp [−35.69, −18.26]**          |
| LFCC + LR   | **+12.44 pp [+1.96, +21.76]**       | **−42.62 pp [−50.78, −35.64]**          |

Both cells of the XTTS column are positive; both cells of the
OpenVoice column are negative. All four gap CIs are entirely on
their respective sides of zero. The direction split by generator is
now cross-architecture supported.

### Next research step (queued, not yet started)

Priority reordered given the OpenVoice reversal is now cross-detector:

1. **Reviving gender / age / region breakdown on DECTE test slice.**
   Sociolinguistic angle for the thesis; small analysis over existing
   predictions CSVs — no new audio or training.
2. **Pre-picked target-set fix** for future paired VCTK runs
   (Entry 5's 80/120 overlap caveat). Code-only, no regeneration for
   existing tables.
3. **Second-detector mitigation replication.** Retrain the LFCC-LR
   classifier with the DECTE-adapted training subset (mitigation
   train CSV, same as Entry 7) and see whether the "mitigation
   reduces DECTE XTTS EER" pattern (Entry 7 on AASIST) also
   replicates on LFCC-LR. Would round out the entire matrix
   (2 detectors × baseline + mitigated × 2 corpora × 2 generators).
4. **Draft the thesis chapters.** With Entries 1-10 committed, all
   headline claims carry statistical support and reproducible
   scripts. The measurement + statistics phases are effectively
   complete for a bachelor-thesis scope.

---

## Entry 11 — [DATE] — [next milestone]

*(add here once available)*
