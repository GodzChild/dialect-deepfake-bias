# Thesis Tables and Figures Inventory

*Polish-pass step 5. Written to track every planned table and figure
for the thesis, with draft captions and placement decisions. No
figure-generation scripts are written by this document; that is
step 6 of the polish pass. Chapter drafts are not edited by this
document either. Sources: `docs/THESIS_ASSEMBLY_PLAN.md`,
`docs/THESIS_WRITING_PLAN.md`, `docs/THESIS_FINDINGS_LOG.md`,
`docs/thesis_draft/*.md`.*

---

## 1. Overview

This inventory tracks eight planned main tables (T1–T8) and six
planned figures (F1–F6) for the thesis, alongside the placement
and generation status of each.

Every item is tagged with one of:

- **Main chapter** — belongs in the main body of the thesis.
- **Appendix** — belongs in an appendix, not the main body.
- **Optional** — planned but the thesis can ship without it.
- **Needs generation** — currently does not exist as a table or
  figure artefact; must be produced during the polish pass.
- **Already represented in prose/table** — the content is already
  present in a chapter draft as an inline table or as prose. The
  polish pass may reformat it for the final template but does not
  need to produce new content.

The two categories are not mutually exclusive: a table can be
both "Main chapter" (its placement) and "Already represented"
(its status), which just means it is committed inline in the
chapter draft and only needs template formatting for the final
build.

Wording contract for every caption in this inventory (mirrors
Chapter 8's discipline):

- Use *dialect / domain gap* — never *pure dialect bias* or
  *pure dialect effect*.
- Use *generator-specific corpus interaction* for the OpenVoice
  reversal.
- Use *cross-detector replication* for LFCC + LR replications of
  AASIST findings.
- Use *controlled adaptation* for the mitigation.
- Chapter 7's per-subgroup material must be labelled
  *diagnostic* (never *fairness audit*, never *bias against
  group X*).

---

## 2. Main tables inventory

### T1 — Dataset and corpus overview

- **Likely chapter:** Chapter 3.
- **Placement:** Main chapter.
- **Status:** Needs generation (not currently a discrete table;
  Chapter 3, Sections 3.2 and Chapter 2, Section 2.7 describe
  the corpora in prose).
- **Source data:** Chapter 3 Sections 3.2 and 3.4.2, Chapter 2
  Section 2.7 (working bibliography of corpora referenced by the
  thesis).
- **Rows (planned):**
  - DECTE — Diachronic Electronic Corpus of Tyneside English
    (Corrigan et al.). Role: primary dialectal / domain test
    material. Size used: 744 valid utterances across 96 speakers
    after 2–15 s duration and non-empty-transcript filter.
  - VCTK 0.92 (Yamagishi et al.). Role: standard-accent English
    control. Size used: 20-speaker slate filtered to
    `ACCENTS == "English"`, ~ 120 target bonafide originals.
  - WaveFake (Frank & Schönherr 2021). Role: contributes to the
    AuralGuard baseline training mixture — not evaluated on
    directly.
  - ASVspoof2019 LA. Role: contributes to the AuralGuard baseline
    training mixture and the LFCC + LR training set.
  - GLOBE / EdAcc / EnglishDialects. Role: additional AuralGuard
    training mixture components.
- **Columns (planned):** Dataset · Role in thesis · Speakers used ·
  Utterances used · Sampling rate at evaluation · Access notes
  (public / restricted).
- **Short caption:** Datasets used in the thesis, by role.
- **Longer caption:** Datasets used at any stage of the thesis
  pipeline. DECTE and VCTK 0.92 are the two speech corpora
  compared in Chapters 5–7. WaveFake, ASVspoof2019 LA, GLOBE,
  EdAcc, and EnglishDialects contribute to the AuralGuard
  baseline training mixture that Chapter 4 verifies but are not
  evaluated on directly in this thesis. Access status is noted
  because DECTE is research-restricted (see Chapter 3,
  Section 3.9.6).

### T2 — Spoof generation scale summary

- **Likely chapter:** Chapter 3, or an appendix.
- **Placement:** Optional in main text; recommend Appendix if the
  chapter is already tight.
- **Status:** Needs generation (currently in prose across
  Chapter 3 Section 3.3 and the findings log Entry 5).
- **Source data:** Findings-log Entries 2 and 5;
  `data/generated_spoofs/manifest.jsonl` counts;
  `data/generated_spoofs_vctk/manifest.jsonl` counts.
- **Rows (planned):** one row per (corpus × generator) cell:
  - DECTE XTTS v2 (416 successful spoofs in the balanced pool,
    100 sampled for evaluation).
  - DECTE OpenVoice v2 (100 successful spoofs, all used).
  - VCTK XTTS v2 (100 successful spoofs).
  - VCTK OpenVoice v2 (100 successful spoofs).
- **Columns (planned):** Corpus · Generator · Successful spoofs
  produced · Spoofs used at evaluation · Manifest path.
- **Short caption:** Spoof generation coverage per corpus and
  generator.
- **Longer caption:** Successful spoof counts per (corpus × generator)
  cell after the generation pipeline in Chapter 3, Section 3.3.
  DECTE XTTS pool is deliberately larger than needed for the
  balanced comparison so that the same pool can supply the
  mitigation train / val / test split of Chapter 6 (Section 6.3).

### T3 — Detector verification summary

- **Likely chapter:** Chapter 4.
- **Placement:** Main chapter.
- **Status:** Partially already represented (Chapter 4 Sections
  4.3, 4.4, 4.6 describe each verification step in prose; a
  single compact summary table does not yet exist).
- **Source data:** Findings-log Entries 1 and 3.
- **Rows (planned):**
  - Checkpoint loading (AuralGuard-wrapper `strict=True` instead
    of raw AASIST `strict=False` → 235 / 235 tensors loaded).
  - Score-direction convention (`softmax[..., 0]` for
    `P(bonafide)` — higher-is-bonafide throughout the metric
    functions).
  - In-domain sanity check (mitigated baseline EER = 1.71 % on
    the AuralGuard validation set; PASS band ≤ 5 %).
- **Columns (planned):** Verification check · Symptom before fix ·
  Fix applied · Post-fix result · Findings-log Entry.
- **Short caption:** Detector-verification checks and their
  outcomes.
- **Longer caption:** Three verification checks were required
  before any DECTE or VCTK number reported later could be
  interpreted: checkpoint loading, score-direction convention,
  and an in-domain sanity check against the AuralGuard baseline's
  own training distribution. Each is described in Chapter 4;
  this table gives the compact per-check summary.

### T4 — Main 2 × 2 × 2 corpus × generator × detector result table

- **Likely chapter:** Chapter 5.
- **Placement:** Main chapter.
- **Status:** Already represented (Chapter 5, Section 5.7 has the
  full text-only version). Only template typesetting is needed
  for the final build.
- **Source data:** Findings-log Entries 6, 8, 9, 10 combined.
- **Rows (already committed):**
  - AASIST + XTTS v2 — DECTE 34.63 % / VCTK 21.83 %, gap +12.80 pp
    [+6.13, +22.07].
  - LFCC + LR + XTTS v2 — DECTE 44.19 % / VCTK 31.75 %, gap
    +12.44 pp [+1.96, +21.76].
  - AASIST + OpenVoice v2 — DECTE 47.84 % / VCTK 74.58 %, gap
    −26.74 pp [−35.69, −18.26].
  - LFCC + LR + OpenVoice v2 — DECTE 38.21 % / VCTK 80.83 %, gap
    −42.62 pp [−50.78, −35.64].
- **Columns (already committed):** Detector · Generator · DECTE EER
  (95 % CI) · VCTK EER (95 % CI) · Gap DECTE − VCTK (95 % CI) ·
  Interpretation.
- **Short caption:** The 2 × 2 × 2 corpus × generator × detector
  result matrix.
- **Longer caption:** Headline result table of the thesis. Rows
  1 and 2 (XTTS) show a positive DECTE − VCTK EER gap on both
  detectors — the *dialect / domain gap* result. Rows 3 and 4
  (OpenVoice) reverse the sign — the *generator-specific corpus
  interaction* result. All four gap 95 % CIs lie entirely on their
  respective sides of zero, and every row's finding replicates
  across detector architectures (*cross-detector replication*).

### T5 — Mitigation v1 / v2 summary

- **Likely chapter:** Chapter 6.
- **Placement:** Main chapter.
- **Status:** Partially already represented — Chapter 6 Section
  6.4 (v1) and Section 6.6 (v2) each have their own compact
  summary; a single side-by-side v1-vs-v2 table does not yet
  exist.
- **Source data:** Findings-log Entry 7 (v2) and its preceding
  v1 attempt (recorded in the v1 predecessor entry referenced
  in Chapter 6, Section 6.4).
- **Rows (planned):**
  - Baseline (no fine-tune) — DECTE XTTS EER on the 172-file
    held-out test slice: 40.70 %.
  - Mitigation v1 (heads only, ~ 1,600 trainable params) — DECTE
    XTTS EER 36.05 %; delta −4.65 pp; 95 % paired CI [−12.79,
    +2.91] (crosses zero → not statistically supported).
  - Mitigation v2 (partial-backbone unfreeze, ~ 31,372 trainable
    params, ~ 10.5 % of the model) — DECTE XTTS EER 23.26 %;
    delta −17.44 pp; 95 % paired CI [−28.49, −9.30] (entirely
    below zero → statistically supported at 95 %).
- **Columns (planned):** Configuration · Trainable parameters
  (approximate) · DECTE XTTS EER · Delta vs baseline · 95 % paired
  bootstrap CI · Verdict.
- **Short caption:** Comparison of mitigation attempts v1
  (head-only) and v2 (partial-backbone unfreeze).
- **Longer caption:** v1 was tried first with all backbone
  parameters frozen (~ 1,600 trainable head parameters). The
  point-estimate direction was favourable but the 95 % paired-
  bootstrap CI on the delta crossed zero, so v1 was not
  statistically supported on this test slice. v2 added the last
  heterogeneous-GAT stage of the AASIST backbone to the
  trainable set, bringing trainable-parameter count to ~ 31,372
  (~ 10.5 % of the model). The v2 delta is nearly four times
  larger than v1's and the 95 % CI lies entirely below zero.

### T6 — Mitigation v2 guardrail summary

- **Likely chapter:** Chapter 6.
- **Placement:** Main chapter.
- **Status:** Already represented (Chapter 6, Section 6.9 has
  the full three-row summary table). Only template typesetting
  is needed.
- **Source data:** Findings-log Entry 7.
- **Rows (already committed):**
  - DECTE XTTS held-out test (86 + 86) — baseline 40.70 % / v2
    23.26 %, delta −17.44 pp, 95 % paired CI [−28.49, −9.30]
    → statistically supported improvement at 95 %.
  - VCTK XTTS guardrail (120 + 100) — baseline 21.83 % / v2
    19.17 %, delta −2.67 pp, 95 % paired CI [−5.42, +3.17]
    → no significant regression at 95 %.
  - In-domain sanity (AuralGuard val set) — baseline 1.71 % / v2
    2.50 %, delta +0.79 pp (not bootstrapped) → still PASS under
    ≤ 5 % threshold from Chapter 4.
- **Columns (already committed):** Setting · Baseline EER · v2
  EER · Delta · 95 % CI · Interpretation.
- **Short caption:** Mitigation v2 delta on the DECTE XTTS held-out
  test slice, the VCTK XTTS guardrail, and the in-domain sanity
  check.
- **Longer caption:** Chapter 6's three-part guardrail table.
  The DECTE improvement CI lies entirely below zero; the VCTK
  guardrail CI includes zero (no statistically significant
  regression); the in-domain sanity result remains inside the
  PASS band defined in Chapter 4. Together these three
  conditions satisfy the writing plan's success criteria for a
  mitigation experiment under RQ3.

### T7 — Subgroup diagnostics summary

- **Likely chapter:** Chapter 7.
- **Placement:** Main chapter.
- **Status:** Already represented (Chapter 7, Section 7.8 has the
  full 10-row table). Only template typesetting is needed.
- **Source data:** Findings-log Entry 11.
- **Rows (already committed):** overall (86 + 86); gender —
  female (39 + 39), male (26 + 26); age — 16-20 (37 + 37),
  21-30 (15 + 15), 41-50 (10 + 10); recording era — 1960s-1970s
  (24 + 24), 1990s (32 + 32), 2007-2008 (10 + 10), 2010-2011
  (20 + 20).
- **Columns (already committed):** Grouping variable · Group ·
  n_bonafide · n_spoof · Baseline EER · Mitigated v2 EER · Delta
  (pp) · Interpretation.
- **Short caption:** Per-subgroup baseline and mitigated EER on
  the DECTE held-out test slice — diagnostic, not a fairness
  audit.
- **Longer caption:** Per-subgroup breakdown of the mitigation
  effect on the 172-file DECTE held-out test slice, by gender,
  age band, and recording era. Every main-table subgroup
  improved; magnitude spread is substantial. Per-subgroup
  bootstrap CIs are not computed because at 10–40 files per
  class per subgroup they would be wide enough to obscure
  between-subgroup comparisons. Reported as diagnostic evidence
  only — no fairness claim is made, and the wording contract
  from Chapter 7, Section 7.10 applies.

### T8 — Future work / limitations matrix

- **Likely chapter:** Chapter 8 or Chapter 9.
- **Placement:** Optional.
- **Status:** Needs generation. Not currently a table.
- **Source data:** Chapter 8 Section 8.7 (threats to validity),
  Chapter 8 Section 8.9 (non-claims), Chapter 9 Section 9.7
  (future work). This table would explicitly connect each
  limitation to the follow-up study that would resolve it.
- **Rows (planned):** one row per limitation, connecting it to
  the corresponding future-work item.
- **Columns (planned):** Limitation (from Chapter 8) · Follow-up
  study that would address it (from Chapter 9) · Priority.
- **Short caption:** Thesis limitations mapped to future-work
  directions.
- **Longer caption:** Each row pairs a specific limitation
  identified in Chapter 8 (small held-out slice, only two
  detectors, only two generators, AASIST-only mitigation, no
  per-subgroup CIs, no compression / channel evaluation) with
  the future-work study proposed in Chapter 9 that would
  address it. Priority is a subjective judgement of what would
  most tighten the thesis' external validity.

---

## 3. Figures inventory

None of these currently exist as image files. All require
generation in a later polish step from the sources named below.

### F1 — Experimental design overview

- **Likely chapter:** Chapter 3 (opener).
- **Placement:** Main chapter.
- **Status:** Needs generation.
- **Source:** Chapter 3 methodology as a whole — corpora
  (Section 3.2), generators (Section 3.3), detectors
  (Section 3.4), evaluation protocol (Section 3.5), bootstrap
  (Section 3.6), mitigation (Section 3.7), subgroup diagnostics
  (Section 3.8).
- **Type:** Flow diagram (rectangles + arrows; not a plot).
- **Content:** Two speech corpora (DECTE, VCTK) → two spoof
  generators (XTTS v2, OpenVoice v2) → two detectors
  (AuralGuard-AASISTPP, LFCC + LR) → per-cell metrics with
  bootstrap CIs → downstream mitigation and subgroup diagnostic
  layers.
- **Short caption:** Experimental design of the thesis.
- **Longer caption:** Overview of the four-stage pipeline
  described in Chapter 3: data preparation, spoof generation,
  detector evaluation, and statistical analysis with a downstream
  mitigation and subgroup-diagnostic layer. Each stage feeds the
  next; every headline number in Chapters 5–7 originates from
  this pipeline under a fixed random seed.

### F2 — Detector verification flow

- **Likely chapter:** Chapter 4.
- **Placement:** Optional (main-chapter prose already covers the
  same content).
- **Status:** Needs generation.
- **Source:** Chapter 4 Sections 4.2–4.6.
- **Type:** Simple diagram (rectangles + arrows).
- **Content:** AuralGuard baseline checkpoint → wrapper-based
  loading (`strict=True` against `AuralGuardAASISTPP`) → score
  direction convention (`softmax[..., 0]` = `P(bonafide)`) →
  in-domain sanity check on the AuralGuard validation set → PASS
  band ≤ 5 %.
- **Short caption:** Detector-verification pipeline used in
  Chapter 4.
- **Longer caption:** Chapter 4's verification steps in schematic
  form: checkpoint construction, wrapper-based loading with
  `strict=True`, score-direction convention, and the in-domain
  sanity check that must pass before any DECTE or VCTK number is
  interpreted. Kept optional because the same content is
  described in the main-chapter prose.

### F3 — Main corpus-gap bar chart

- **Likely chapter:** Chapter 5.
- **Placement:** Optional in main text; may be more
  space-efficient than the summary table for a visual reader.
- **Status:** Needs generation.
- **Source:** `results/detector_predictions.csv`,
  `results/vctk/detector_predictions.csv` (for AASIST); LFCC + LR
  prediction CSVs from Script 11 / Script 13.
- **Type:** Grouped bar chart (four bars per group; two groups —
  XTTS and OpenVoice — on the x-axis; DECTE and VCTK per detector
  as bar colours).
- **Content:** Per-cell EER bars for the eight cells of the
  2 × 2 × 2 matrix, with 95 % bootstrap CI error bars.
- **Short caption:** Per-cell EER for the 2 × 2 × 2 corpus ×
  generator × detector matrix.
- **Longer caption:** Bar-chart view of the same data reported in
  T4 (Chapter 5, Section 5.7). Each bar is a cell's point-estimate
  EER; error bars are the 95 % bootstrap confidence intervals
  reported in Sections 5.3–5.6.

### F4 — Gap direction plot

- **Likely chapter:** Chapter 5.
- **Placement:** Main chapter. Recommended as the single most
  important figure of the thesis.
- **Status:** Needs generation.
- **Source:** the four DECTE − VCTK gap CIs from findings-log
  Entries 6, 8, 9, 10.
- **Type:** Point plot with horizontal 95 % confidence intervals
  (a "forest plot"), with a vertical reference line at 0.
- **Content:** Four rows — AASIST + XTTS, LFCC + LR + XTTS,
  AASIST + OpenVoice, LFCC + LR + OpenVoice — showing the DECTE −
  VCTK gap point estimate and the 95 % CI for each. The top two
  rows sit entirely to the right of 0 (positive gaps → DECTE
  harder for XTTS); the bottom two rows sit entirely to the left
  of 0 (negative gaps → VCTK harder for OpenVoice).
- **Short caption:** DECTE − VCTK gap 95 % CIs across all four
  detector × generator cells.
- **Longer caption:** Point estimates and 95 % non-parametric
  bootstrap confidence intervals for the DECTE − VCTK EER gap in
  each detector × generator cell. Positive values mean DECTE is
  harder for the detector than VCTK; negative values mean VCTK
  is harder. The vertical reference line at 0 makes the sign of
  each interval visually explicit: both XTTS gaps lie entirely
  above zero (*dialect / domain gap* result), and both OpenVoice
  gaps lie entirely below zero (*generator-specific corpus
  interaction*, the same-sign result across two detectors is the
  *cross-detector replication*).

### F5 — Mitigation effect plot

- **Likely chapter:** Chapter 6.
- **Placement:** Main chapter.
- **Status:** Needs generation.
- **Source:** Chapter 6, Section 6.9 table (three rows).
- **Type:** Before / after paired-bar plot.
- **Content:** Two paired columns — DECTE XTTS and VCTK XTTS —
  each showing baseline vs mitigated v2 EER. Delta values and
  95 % paired-bootstrap CIs annotated on each pair.
- **Short caption:** Baseline vs mitigation v2 EER on the DECTE
  XTTS held-out test slice and the VCTK XTTS guardrail.
- **Longer caption:** Before / after view of the mitigation v2
  result. On DECTE XTTS the mitigation delta CI lies entirely
  below zero (statistically supported improvement); on VCTK XTTS
  the delta CI includes zero (no statistically significant
  regression). The in-domain sanity check (not shown as a paired
  bar because the baseline is not a DECTE-scoped number) also
  passed the ≤ 5 % threshold post-mitigation and is reported in
  T6.

### F6 — Subgroup mitigation delta plot

- **Likely chapter:** Chapter 7.
- **Placement:** Main chapter or Appendix (a judgement call —
  see Section 5 below). Recommended in the main chapter as the
  visual complement to T7.
- **Status:** Needs generation.
- **Source:** `results/subgroup_diagnostics/decte_subgroup_metrics.csv`
  (Entry 11 CSV).
- **Type:** Horizontal bar chart, one bar per main-table
  subgroup, sorted by delta magnitude.
- **Content:** Ten bars — overall row plus the nine subgroup
  rows from T7 — with delta EER on the x-axis. All ten
  main-table bars point in the negative direction (improvement);
  the visual variety in bar length is the "improvement uniform
  in direction, uneven in magnitude" observation of Chapter 7.
- **Short caption:** Per-subgroup mitigation delta EER on the
  DECTE held-out test slice — diagnostic only, no fairness
  claim.
- **Longer caption:** Per-subgroup point estimates of the
  mitigation v2 delta EER on the 172-file DECTE held-out test
  slice. Every main-table subgroup improved; the magnitude
  spread across bars is the "directionally uniform, magnitudinally
  uneven" observation of Chapter 7. **Diagnostic evidence only.**
  Per-subgroup bootstrap CIs are not shown because at 10–40 files
  per class per subgroup they would be wide enough to obscure
  between-bar comparisons. No fairness claim is supported by
  this figure.

---

## 4. Draft caption summary table

Compact table for the polish pass's caption drafter to work from.
Every item is listed with its short caption, source Entry (or
chapter section), generation status, and body / appendix
recommendation.

| ID | Short caption | Source | Needs generation? | Body / appendix |
|---|---|---|:---:|---|
| T1 | Datasets used in the thesis, by role | Ch 3 §3.2 + Ch 2 §2.7 | Yes | Main text |
| T2 | Spoof generation coverage per corpus and generator | Entries 2, 5 | Yes | Appendix |
| T3 | Detector-verification checks and their outcomes | Entries 1, 3 | Yes (compact form) | Main text |
| T4 | The 2 × 2 × 2 corpus × generator × detector result matrix | Entries 6, 8, 9, 10 | No — already in Ch 5 §5.7 | Main text |
| T5 | Comparison of mitigation attempts v1 and v2 | Entry 7 + v1 predecessor | Yes (side-by-side form) | Main text |
| T6 | Mitigation v2 delta on DECTE, VCTK, and in-domain sanity | Entry 7 | No — already in Ch 6 §6.9 | Main text |
| T7 | Per-subgroup baseline and mitigated EER on the DECTE slice | Entry 11 | No — already in Ch 7 §7.8 | Main text |
| T8 | Thesis limitations mapped to future-work directions | Ch 8 §8.7 + Ch 9 §9.7 | Yes | Optional / appendix |
| F1 | Experimental design of the thesis | Ch 3 as a whole | Yes | Main text |
| F2 | Detector-verification pipeline used in Chapter 4 | Ch 4 §4.2–4.6 | Yes | Optional / appendix |
| F3 | Per-cell EER for the 2 × 2 × 2 matrix | Prediction CSVs | Yes | Skip for now |
| F4 | DECTE − VCTK gap 95 % CIs across all four cells | Entries 6, 8, 9, 10 | Yes | Main text (headline figure) |
| F5 | Baseline vs mitigation v2 EER on DECTE XTTS and VCTK XTTS | Ch 6 §6.9 | Yes | Main text |
| F6 | Per-subgroup mitigation delta EER on the DECTE slice | Entry 11 CSV | Yes | Main text (diagnostic-only label required) |

---

## 5. Placement decisions

All placements below are **locked**. Any change to these locks
should be a deliberate revision to this section, not an implicit
drift during the figure-generation step.

### 5.1 Locked for the main text

- **T1** — dataset and corpus overview. Reader orientation for
  Chapter 3.
- **T3** — detector-verification summary. Chapter 4 depends on
  the reader accepting the verification story; a compact table
  makes it auditable at a glance.
- **T4** — main 2 × 2 × 2 result matrix. The single most cited
  table in the thesis; already committed inline in Chapter 5.
- **T5** — mitigation v1 vs v2 side-by-side. Anchors the
  "why v2 was needed" argument in Chapter 6.
- **T6** — mitigation v2 guardrail summary. Chapter 6's headline
  three-row table; already committed inline.
- **T7** — subgroup diagnostics summary. Chapter 7's main-table
  view; already committed inline. Must ship with the *diagnostic
  only* labelling from Chapter 7, Section 7.10 preserved.
- **F1** — experimental-design overview. Reader orientation for
  Chapter 3.
- **F4** — gap-direction forest plot. The single most important
  figure of the thesis.
- **F5** — mitigation effect before / after plot. Chapter 6's
  visual complement to T6.
- **F6** — per-subgroup mitigation delta plot. Chapter 7's
  visual complement to T7. **Locked for main text with a
  diagnostic-only label required on the figure surface** (see
  Section 5.3 for the exact requirement).

### 5.2 Locked for appendix or optional

- **T2** — spoof generation scale summary. **Locked for the
  appendix.** The per-corpus manifest counts are implementation-
  heavy and the main text reads well without them.
- **T8** — limitations-to-future-work matrix. **Locked as
  optional / appendix.** Would be a nice touch in Chapter 9 but
  is not essential; the same connection is made in Chapter 8 §8.7
  and Chapter 9 §9.7 prose.
- **F2** — detector-verification flow diagram. **Locked as
  optional / appendix.** Chapter 4 prose already covers the same
  content in narrative form; ship only if the final template has
  room.
- **F3** — per-cell EER bar chart. **Locked as skipped for now.**
  Substantially overlaps T4 in content; only revisit if the final
  layout ends up needing an extra visual summary of the eight
  cells.

### 5.3 Locked-decision notes

Three items carry a specific decision note that the
figure-generation step (polish-step 6) must honour:

- **F6 — locked for Chapter 7 main text with a diagnostic-only
  label required.** The figure surface itself (not only the
  caption) must carry a visible *"diagnostic only, not a
  fairness audit"* annotation. Chapter 7 §7.10 documents the
  wording contract that this label must respect.
- **T2 — locked for the appendix.** No main-text placement;
  the main text should refer to the appendix table by number
  when the reader needs the per-corpus counts.
- **F3 — locked as skipped for now.** No generation script
  should be written for F3 unless the final template layout
  explicitly needs an extra visual summary alongside T4.

---

## 6. Generation plan (no scripts yet)

For each figure and each new table, the sources listed below are
the artefacts a later polish step would draw from. This section
is a specification, not an implementation — no scripts are
written by this document.

- **T1** — manual table from Chapter 3 Section 3.2 prose and
  Chapter 2 Section 2.7 (working bibliography).
- **T2** — count query over
  `data/generated_spoofs/manifest.jsonl` (DECTE) and
  `data/generated_spoofs_vctk/manifest.jsonl` (VCTK).
- **T3** — manual table from Chapter 4 prose and Entries 1, 3
  in the findings log.
- **T4** — already in Chapter 5 §5.7. No new generation.
- **T5** — manual table combining Entry 7 and the v1
  predecessor entry.
- **T6** — already in Chapter 6 §6.9. No new generation.
- **T7** — already in Chapter 7 §7.8. No new generation.
- **T8** — manual table pairing Chapter 8 §8.7 items with
  Chapter 9 §9.7 items.
- **F1** — hand-drawn diagram (or `graphviz` / `mermaid` / TikZ
  in the final template).
- **F2** — hand-drawn diagram (same options as F1).
- **F3** — Python script reading from
  `results/detector_predictions.csv`,
  `results/vctk/detector_predictions.csv`, and the LFCC + LR
  prediction CSVs. Bars produced from `compute_metrics(...)`;
  error bars from `bootstrap_ci(...)`.
- **F4** — Python script that either (a) recomputes the four
  gap CIs from the same prediction CSVs, or (b) reads the four
  gap CIs from a hand-populated `results/main_gap_cis.csv`
  compiled from findings-log Entries 6, 8, 9, 10. Option (b) is
  simpler and cheaper.
- **F5** — Python script reading the baseline and mitigated v2
  prediction CSVs used by `scripts/10_bootstrap_mitigation_effect.py`.
- **F6** — Python script reading
  `results/subgroup_diagnostics/decte_subgroup_metrics.csv`
  (already produced by `scripts/14`).

All generation scripts should live under `scripts/figures/` when
they are written (polish-step 6). Generated PNG or PDF files
should live under `docs/figures/`, gitignored except for the
final versions that ship with the thesis.

---

## 7. Risk checks

Every table and figure that goes into the thesis must pass these
checks. Any item that fails a check must be corrected (or
dropped) before submission.

- **No causal fairness claim in any figure or caption.** No
  language of the form *"the detector is biased against group X"*,
  *"unfair to group Y"*, or *"gender / age / era caused the
  errors"* is permitted in F6 or in T7's caption. Chapter 7 §7.10
  documents the exact phrasing contract.
- **F6 must be labelled *diagnostic*.** The figure caption and,
  ideally, an annotation on the figure surface itself, must carry
  the *diagnostic only, not a fairness audit* label.
- **Gap plots must use "DECTE − VCTK" explicitly.** F3 and F4
  must state the sign convention (positive → DECTE harder,
  negative → VCTK harder) in the caption so no reader can flip
  the reading.
- **Mitigation plots must not imply production readiness.** F5's
  caption must not state or imply that the mitigated checkpoint
  is a deployment-grade detector. Residual DECTE XTTS EER is
  still ~ 23 % — far above any operational threshold. Chapter 6
  §6.10 documents this explicitly.
- **All captions use *dialect / domain gap*.** Never *pure
  dialect bias*, *pure dialect effect*, or *dialect
  discrimination*. Chapter 1 §1.2 and Chapter 8 §8.6 explain
  why.
- **OpenVoice reversal captions use *generator-specific corpus
  interaction*.** Not *"OpenVoice is a worse generator"*. The
  reversal is scoped to the (detector, corpus) crossing, not a
  general claim about OpenVoice.
- **Cross-detector agreement captions use *cross-detector
  replication*.** Not *"the AASIST result generalises"* — the
  claim is specifically the two-detector one.
- **Number consistency.** Every number that appears in a figure
  or table caption must match the same number as reported in
  the source chapter (or the source Entry). The polish pass must
  re-verify this after final template typesetting.

---

## 8. What this inventory does NOT do

- It does not edit any chapter draft. All existing inline tables
  in Chapters 4, 5, 6, 7 stay as committed.
- It does not create `references.bib`, add citations, or change
  citation keys.
- It does not create any figure-generation script under
  `scripts/figures/`. That is polish-step 6.
- It does not generate any image file under `docs/figures/`.
- It does not decide the LaTeX vs Word template question — that
  is deferred to the assembly plan's Section 7 (still "to
  decide").
- It does not touch code, data, results, checkpoints, manifests,
  or generated audio.

---

*End of tables and figures inventory.*
