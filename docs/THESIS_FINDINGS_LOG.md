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

## Entry 6 — [DATE] — [next milestone]

*(add here once available)*
