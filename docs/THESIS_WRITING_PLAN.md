# Thesis Writing Plan

**Programme:** Bachelor of Science in Artificial Intelligence
**Institution:** Johannes Kepler University Linz
**Institute:** Institute of Computational Perception
**Source of truth for numbers/claims:** `docs/THESIS_FINDINGS_LOG.md`
(Entries 1–11, all committed on `origin/main`).

This is a **planning document**. No thesis prose is written yet.
Its purpose is to lock in structure, claim boundaries, and figure/table
inventory before drafting begins.

---

## 1. Proposed thesis title

**Primary title (recommended):**

> **Does Your Accent Make You Vulnerable? Dialect and Generator
> Effects in Audio Deepfake Detection**

**Formal alternative:**

> **Dialect and Generator Effects in Audio Deepfake Detection**

Both titles keep *dialect* as the leading concept — matching the
thesis' original research question and the empirical anchor of the
work (DECTE) — while acknowledging in the body that the generator
dimension carries co-headline findings (Entries 5, 9, 10). The
generator dimension is a modifier of the dialect story, not a
replacement for it, and the title reflects that priority.

The current placeholder in `README.md` (*"Quantifying Dialect Bias
in Audio Deepfake Detection on Tyneside English"*) uses the word
"bias" more strongly than the evidence supports (Entry 6 caveat:
DECTE-vs-VCTK is a corpus/domain comparison, not a pure dialect
comparison). Prefer "effect" or "gap" in the final title. The
"Tyneside English" scoping — while accurate — is deliberately
dropped from the recommended titles so the thesis reads as a
methodological contribution first and an area-studies contribution
second. Tyneside remains the empirical anchor; that is made explicit
in the abstract and throughout Chapter 3.

---

## 2. Research questions

Three primary + one supporting.

- **RQ1 (headline).** Does dialectal / domain-shifted speech affect
  the performance of a modern audio-deepfake detector, holding the
  detector, generator, and evaluation protocol fixed?
  *→ Answered by Entries 1, 3, 5, 6.*
- **RQ2.** Does the effect of dialect/domain shift interact with the
  choice of spoof generator?
  *→ Answered by Entries 2, 4, 5, 9.*
- **RQ3.** Can a conservative, lightweight adaptation of the detector
  reduce the observed dialect/domain gap without regressing on
  out-of-training-domain speech?
  *→ Answered by Entries 7 (mitigation v2) and 11 (subgroup breakdown
  of the mitigation).*
- **RQ4 (supporting robustness / replication question).** Do the
  main corpus-gap patterns persist across detector architectures?
  Framed as a *robustness check* on RQ1 and RQ2 — a replication
  question rather than a separate central thesis. The result would
  only weaken the RQ1/RQ2 story if the patterns failed to replicate;
  it does not stand alone.
  *→ Answered by Entries 8 (LFCC-LR XTTS replication) and 10
  (LFCC-LR OpenVoice replication).*

---

## 3. Contribution list

Five main contributions. Additional pipeline-verification and
reproducibility work is essential to the validity of these five
but is treated as *methodology* (Chapter 3) or *reproducibility
infrastructure* (Appendix A) rather than as a standalone headline
contribution.

1. **A DECTE–VCTK evaluation benchmark for dialect / domain effects
   on audio deepfake detection.** A leakage-safe, matched-N,
   bootstrap-supported protocol for evaluating an anti-spoofing
   detector on Tyneside dialectal speech against a standard-accent
   VCTK control, with per-cell 95% CIs and paired-original bonafide
   selection via manifest-level `source_audio_path` (Entries 5, 6).
2. **A cross-generator finding.** XTTS v2 shows a positive DECTE −
   VCTK gap (+12.80 pp, 95% CI [+6.13, +22.07]), consistent with a
   dialect / domain-shift interpretation. OpenVoice v2 *reverses*
   the direction (−26.74 pp, 95% CI [−35.69, −18.26]) — VCTK is
   harder than DECTE. The two generators do not fail the detector
   the same way, and the reversal cannot be explained as a dialect
   effect (Entries 6, 9).
3. **Cross-detector replication.** Both the XTTS gap (+12.44 pp,
   CI [+1.96, +21.76]) and the OpenVoice reversal (−42.62 pp,
   CI [−50.78, −35.64]) reproduce on a hand-crafted-feature +
   Logistic-Regression detector — an architecturally very different
   second detector — with same-direction CIs. The direction split
   by generator is therefore not specific to the AASIST architecture
   (Entries 8, 10).
4. **A statistically supported mitigation.** A conservative partial-
   backbone unfreeze of the AuralGuard-AASIST detector (only the
   last heterogeneous-GAT block plus the AuralGuard task heads —
   31,372 of ~300,000 parameters trainable) significantly reduces
   held-out DECTE XTTS EER (40.70 % → 23.26 %, delta −17.44 pp,
   95% CI [−28.49, −9.30]) without a statistically significant VCTK
   regression (Entry 7).
5. **Sociolinguistic subgroup diagnostics.** On the held-out DECTE
   slice, mitigation v2 improves every main-table subgroup (gender,
   age band, recording era), with substantial spread in magnitude
   (−5 pp to −34 pp). Reported as descriptive diagnostics, not a
   formal fairness audit (Entry 11).

*Supporting work not listed as a headline contribution:*
- *Pipeline verification* (Entry 3, in-domain sanity check at
  1.71 % EER) confirms the detector-loading and preprocessing paths
  are correct and lets every downstream DECTE / VCTK number be
  attributed to domain transfer rather than a residual pipeline
  bug. Described as methodology in Chapter 3 and Chapter 4.
- *Detector-loading fix* (Entry 1) is a load-bearing correctness
  step for the entire study but is a bug fix on prior code, not a
  contribution in its own right. Documented in Chapter 3.
- *Reproducibility infrastructure* — the commit/script trail from
  Entry 1 through Entry 11, deterministic seeds throughout,
  gitignored data and results layouts, and the merge-safe manifest
  writer — is treated as an appendix (Appendix A) rather than a
  headline contribution.

---

## 4. Chapter outline

Target length: **40–55 pages** of body text, plus front matter,
references, and appendices. This maps to approximately
**14,000–20,000 words** of prose.

### Chapter 1 — Introduction (target ~3–4 pages)
- Motivation: audio deepfakes, dialect/accent under-representation
  in ASV / anti-spoofing literature, the specific Tyneside case.
- Research questions (RQ1–RQ4) stated verbatim.
- Contributions (numbered list, mirrors Section 3 above).
- Roadmap: which chapter covers which RQ.

### Chapter 2 — Background & Related Work (target ~5–6 pages)
- Audio-deepfake detection at a glance (ASVspoof lineage).
- AASIST family and the AuralGuardAASISTPP wrapper used here
  (the wrapper's per-head structure is load-bearing for Entry 1's
  detector-loading fix — describe it briefly).
- XTTS v2 and OpenVoice v2: how they differ as voice-cloning systems
  (XTTS end-to-end zero-shot, OpenVoice base-TTS + tone-colour
  converter).
- DECTE (Tyneside): dialect background, recording era spread,
  interview-style speech.
- VCTK 0.92: studio-read English, speaker demographics, accent
  metadata (as used in Entry 5's speaker selection).
- Related work: prior anti-spoofing evaluations across dialects,
  domain shift in ASV, generator-specific vulnerability literature.

### Chapter 3 — Data and Methodology (target ~6–8 pages)
- DECTE data pipeline: chunk audio, Whisper/FairFix transcripts,
  audio-stem-keyed metadata bridge (`speaker_info_by_audio.json`).
- VCTK data pipeline: layout verification, loose-English-accent
  selection (Entry 4's decision), 20-speaker slate.
- Spoof generation protocol: 3 reference utterances + 5 target
  utterances per speaker per generator, deterministic seed 42.
- **Evaluation methodology (load-bearing):**
  - Fixed 4-second, 16 kHz, deterministic-crop audio preprocessing
    identical across both detectors used (matches training).
  - Matched-pair bonafide selection via `source_audio_path`
    (justified by Entry 5's schema extension, Entry 6's fix).
  - Bootstrap protocol: 1000 iterations, seed 42, joint independent
    resampling per corpus, per-iteration EER + gap recorded — used
    by Entries 2, 6, 8, 9, 10 (contribution 4).
- **Detector-loading verification (Entry 1 + 3).**
  Explain the wrapper-vs-raw-AASIST bug briefly; show that the fix
  reproduced the training-time val EER (1.71 %).
- Threats to validity that arise from methodology (deferred to
  Chapter 8 for full treatment; briefly named here).

### Chapter 4 — Baseline Evaluation and Detector Verification (target ~3–4 pages)
- Naive Phase 2 result before the loader fix (broken constant
  scores) — briefly, to motivate the fix.
- Fixed detector's in-domain val EER (1.71 %, matches training).
- Initial DECTE Phase 2 numbers (38 % EER overall) with the caveat
  that they mix generators.
- Rationale for the balanced generator comparison in Chapter 5.
- **Supported by:** Entries 1, 3.

### Chapter 5 — Corpus × Generator Analysis with Statistical Support (target ~8–10 pages) — MAIN RESULTS
- **5.1 Balanced DECTE generator comparison (Entry 2):** XTTS 34.63 %
  vs OpenVoice 47.84 %, both with CIs.
- **5.2 Matched-control VCTK generation (Entries 4, 5):** 20
  English-accent VCTK speakers × 5 utterances × 2 generators = 200
  spoofs. Justification, speaker composition (65 % southern, 35 %
  non-southern, gender balance, age-band skew).
- **5.3 XTTS corpus/domain gap (Entry 6) — thesis headline:** joint
  bootstrap on DECTE XTTS vs VCTK XTTS. Gap +12.80 pp, 95% CI
  [+6.13, +22.07]. Interval entirely above zero → RQ1 answered yes
  for XTTS.
- **5.4 OpenVoice corpus-gap reversal (Entry 9):** same protocol,
  OpenVoice arm. Gap −26.74 pp, 95% CI [−35.69, −18.26]. Interval
  entirely below zero. Direction opposite to XTTS.
- **5.5 Cross-architecture replication (Entries 8, 10):** LFCC + LR
  as a second detector; both gaps replicate in the same direction
  with CIs on the same sides of zero. RQ4 answered yes.
- **5.6 The full 2 × 2 × 2 table** (corpus × generator × detector),
  all four gap CIs displayed together. This is the visual centrepiece
  of the thesis.

### Chapter 6 — Mitigation (target ~5–7 pages) — RQ3
- **6.1 v1 attempt (head-only fine-tune):** setup, why it failed
  (delta CI still crossed zero), what it taught us.
- **6.2 v2 approach (partial-backbone unfreeze):** motivation
  (last heterogeneous-GAT block adapts feature representation, not
  just classifier), the `--unfreeze-modules` flag patch to
  `auralguard-aasistpp/src/train.py`, trainable-parameter budget
  (31,372 of 300,000 ≈ 10.5 %).
- **6.3 Result (Entry 7):** DECTE XTTS 40.70 % → 23.26 %, delta
  −17.44 pp, 95% CI [−28.49, −9.30]. VCTK guardrail (delta −2.67 pp,
  CI includes zero — no significant regression). In-domain val EER
  post-adaptation (2.50 % — PASS).
- **6.4 Discussion:** why partial-unfreeze worked when head-only
  did not; catastrophic-forgetting risk assessed and passed.
- **6.5 Non-goal:** mitigation was DECTE-XTTS-scoped and is not
  claimed as a general anti-spoofing improvement.

### Chapter 7 — Sociolinguistic Subgroup Diagnostics (target ~3–4 pages) — RQ3 depth
- Motivation: does the mitigation help every subgroup equally, or
  concentrate benefit unevenly?
- Method (Entry 11): baseline vs mitigated on same 172 files;
  per-subgroup EER; ≥10-per-class main-table threshold; low-n
  diagnostic appendix.
- **Result:** every main-table subgroup improved. Range: −5 pp
  (`recording_era=2010-2011`) to −34 pp (`recording_era=1990s`).
  Gender / age / era breakdown tables.
- **Descriptive framing throughout.** Explicitly *not* a fairness
  audit. Use "concentration", "worth flagging"; never "biased
  against", "unfair to", "helped X specifically".

### Chapter 8 — Discussion, Limitations, and Threats to Validity (target ~4–6 pages)
- Synthesis of Chapters 5–7: three claims that survived
  cross-detector replication; one (mitigation) that has only
  AASIST support.
- Limitations (full treatment — see Section 8 of this plan).
- Threats to validity: corpus/domain vs pure dialect confound;
  small held-out slice; single generator per family; bootstrap
  file-level (not speaker-level) independence assumption.
- Ethical / responsible-use notes: deepfake detection improvements
  can be used offensively; DECTE is a research-restricted corpus.

### Chapter 9 — Conclusion and Future Work (target ~2–3 pages)
- Recap of RQ answers.
- Future work list (Section 9 of this plan).
- One-paragraph outlook on the broader "detector fairness across
  language varieties" research direction.

### Appendices (target ~3–5 pages)
- **A. Reproducibility index:** commit-to-entry table mirroring
  `docs/THESIS_FINDINGS_LOG.md`.
- **B. Full trainable-parameter list for mitigation v2** (from Entry 7).
- **C. VCTK speaker slate** (Entry 5 composition: region / gender /
  age band).
- **D. Low-n subgroup diagnostic table** from Entry 11
  (excluded from Chapter 7 headline).

---

## 5. Entry-to-chapter support map

Quick-reference matrix for finding load-bearing numbers when writing.

| Entry | Ch 1 | Ch 2 | Ch 3 | Ch 4 | Ch 5 | Ch 6 | Ch 7 | Ch 8 | Ch 9 | App |
|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|  1 |  ●  |     |  ●  |  ●  |     |     |     |  ●  |     |     |
|  2 |     |     |  ●  |  ●  |  ●  |     |     |     |     |     |
|  3 |  ●  |     |  ●  |  ●  |     |     |     |  ●  |     |  ●  |
|  4 |     |     |  ●  |     |  ●  |     |     |     |     |     |
|  5 |     |     |  ●  |     |  ●  |     |     |  ●  |     |  ●  |
|  6 |  ●  |     |     |     |  ●  |     |     |  ●  |  ●  |     |
|  7 |  ●  |     |     |     |     |  ●  |  ●  |  ●  |  ●  |  ●  |
|  8 |     |     |     |     |  ●  |     |     |  ●  |     |     |
|  9 |  ●  |     |     |     |  ●  |     |     |  ●  |  ●  |     |
| 10 |     |     |     |     |  ●  |     |     |  ●  |     |     |
| 11 |     |     |     |     |     |     |  ●  |  ●  |     |  ●  |

---

## 6. Main tables and figures needed

Numbered so early drafts can leave placeholders.

### Tables

- **T1 — Full 2×2×2 result matrix (headline).** Corpus × generator ×
  detector, EER with 95% CI per cell (12 cells + 4 gap rows).
  Sources: Entries 6, 8, 9, 10. **This is the single most important
  table in the thesis.**
- **T2 — Balanced DECTE generator comparison (baseline detector).**
  Reproduces Entry 2 with the 100-vs-100 downsample. Sits at the
  start of Chapter 5.
- **T3 — VCTK speaker slate composition.** Region / gender / age
  band across the 20 selected speakers. From Entry 5.
- **T4 — In-domain sanity result.** Baseline detector on
  AuralGuard's own val set, PASS/PARTIAL/FAIL verdict. Entry 3.
- **T5 — Mitigation v2 result.** Baseline vs mitigated on DECTE test
  slice and VCTK guardrail, deltas + CIs. Entry 7.
- **T6 — Subgroup diagnostics main table.** Per-subgroup baseline vs
  mitigated EER + delta EER (gender, age, era). Entry 11.
- **T7 (appendix) — Low-n subgroup diagnostic table.** Entry 11.
- **T8 (appendix) — Reproducibility index.** Commit hash → entry
  number → primary script(s) → primary output file.

### Figures

- **F1 — 2×2×2 forest plot.** One horizontal error bar per cell
  (12 EER intervals) plus four gap intervals below. Colour-coded
  by generator; shape-coded by detector. **Headline figure.**
- **F2 — Bootstrap distribution histogram for the XTTS corpus gap.**
  1000-iter DECTE-minus-VCTK delta EER distribution with the
  point estimate and 95% CI overlaid. From `results/xtts_corpus_gap_bootstrap_ci.csv`
  or re-computed for the figure. Illustrates why "gap CI above zero"
  is a stronger claim than "point estimate is positive".
- **F3 — Direction-flip figure.** Two number-line plots stacked
  (XTTS gap and OpenVoice gap), both showing 95% CIs and zero line.
  Visually communicates the reversal.
- **F4 — Mitigation before/after bar chart, subgroup-broken.**
  Grouped bars per subgroup (gender, age, era). Delta on top of
  each pair. From Entry 11.
- **F5 (optional) — Score distribution histograms** for baseline
  detector on VCTK OpenVoice bonafide vs spoof. Explains the
  sub-random AUC (0.16 / 0.08) intuitively.
- **F6 (optional) — DECTE / VCTK pipeline schematic.** Data flow
  from raw corpora → generator → manifest → detector → bootstrap.
  Useful as Chapter 3 opener.

---

## 7. Exact claims that are safe to make

The following claims are directly supported by committed entries
with 95% bootstrap CIs. They can be stated in the thesis without
softening.

- The detector-loading and preprocessing pipeline is verified: it
  achieves 1.71 % EER on the AuralGuard validation set, close to the
  1.7 % training-time val_metrics EER. Downstream DECTE and VCTK
  EER numbers therefore reflect **domain-transfer difficulty**, not
  a residual implementation bug. (Entry 3)
- **XTTS v2 corpus/domain gap:** on the fixed AuralGuard-AASIST
  detector under a shared protocol, DECTE XTTS EER (34.63 %) exceeds
  VCTK XTTS EER (21.83 %) by +12.80 percentage points with a 95%
  paired-bootstrap CI of [+6.13, +22.07] pp. **The interval lies
  entirely above zero at 95 %.** (Entry 6)
- The XTTS gap **replicates** on an architecturally very different
  detector (LFCC + Logistic Regression, hand-crafted features): gap
  +12.44 pp with 95% CI [+1.96, +21.76] pp, again entirely above zero.
  The XTTS corpus/domain gap is therefore **not specific to the
  AASIST architecture**. (Entry 8)
- **OpenVoice v2 corpus-gap reversal:** under identical detector,
  bonafide-pool, and audio-preprocessing conditions, DECTE OpenVoice
  EER (47.84 %) is *lower* than VCTK OpenVoice EER (74.58 %); the
  DECTE − VCTK gap is −26.74 pp with 95% CI [−35.69, −18.26] pp,
  **entirely below zero at 95 %**. (Entry 9)
- The OpenVoice reversal also **replicates** on the LFCC + LR
  detector at −42.62 pp with 95% CI [−50.78, −35.64] pp, again
  entirely below zero. (Entry 10)
- The direction split by generator is therefore **cross-architecture
  supported**: both detectors agree on the sign of both gaps.
- **Mitigation v2 (partial-backbone unfreeze) statistically reduces
  DECTE XTTS EER on the held-out test slice:** 40.70 % → 23.26 %,
  a change of −17.44 pp with 95% paired-bootstrap CI of [−28.49,
  −9.30] pp. **The interval lies entirely below zero at 95 %.** No
  statistically significant regression on the VCTK guardrail. (Entry 7)
- Mitigation v2 improved **every** main-table subgroup (gender,
  age band, recording era) on the DECTE held-out slice, with delta
  EER ranging from −5.00 pp to −34.38 pp. This is a **descriptive**
  finding and does not support a formal fairness claim. (Entry 11)
- The entire measurement pipeline is **reproducible**: every headline
  number in the thesis has a corresponding script under `scripts/`
  and a corresponding commit on `origin/main`; every bootstrap uses
  the same seed (42) and iteration count (1000).

---

## 8. Claims that must be avoided or softened

These are claims the *data does not support* at the strength they
would imply, or that risk causal / fairness / normative wording the
evidence cannot back.

- **Do NOT write "the detector is biased against Tyneside speakers"
  or "AASIST is unfair to dialect X".** Frame instead as
  "*dialect / domain-shifted speech produces higher detector EER
  in this evaluation*". Bias is a socio-technical claim that
  requires additional axes of evidence (deployment context, harm
  analysis, human-in-the-loop error costs) not present in this thesis.
- **Do NOT write "the dialect gap proves detector bias".** DECTE-vs-
  VCTK is a corpus/domain comparison confounded on multiple axes
  (dialect + interview vs studio + variable-vs-clean channel +
  age-band skew). Use the phrase **"dialect / domain gap"** — not
  "dialect gap alone" — unless a later study isolates dialect
  specifically. (Entry 6 caveat.)
- **Do NOT write "our mitigation solves the dialect problem".** The
  mitigation reduces DECTE XTTS EER on a 16-speaker held-out slice
  under one detector; it does not close the entire XTTS gap, does
  not touch OpenVoice, and is not claimed to generalise to other
  detector families or larger DECTE cuts. (Entry 7 caveat.)
- **Do NOT write "OpenVoice is generally worse than XTTS".** The
  OpenVoice-vs-XTTS comparison in this thesis is scoped to a
  *specific detector on specific corpora*. Different anti-spoofing
  detectors trained on OpenVoice-generated data may not show the
  same pattern. Frame as "for the two detectors evaluated, OpenVoice
  v2 spoofs were harder to reject than XTTS v2 spoofs".
- **Do NOT write "the mitigation helped group X specifically" from
  Entry 11's per-subgroup deltas.** Per-subgroup CIs are wide at
  N ≤ 40 files per subgroup. Frame as "*mitigation improved every
  main-table subgroup; magnitude varied substantially across
  subgroups*". (Entry 11 explicit caveat.)
- **Do NOT cite absolute LFCC + LR EER numbers as "how good the
  detector is".** LFCC + LR is a classical baseline used as one leg
  of the cross-architecture direction check. Its 80.83 % EER on VCTK
  OpenVoice is meaningful only in comparison to its 38.21 % EER on
  DECTE OpenVoice. Frame accordingly. (Entry 10 caveat.)
- **Do NOT overstate the sample sizes.** DECTE held-out test slice
  is 16 speakers / 172 files; VCTK matched control is 20 speakers /
  ≤ 220 files per generator. Bootstrap CIs are wide; report them.
- **Do NOT claim the VCTK generator subsets are fully paired.** The
  VCTK XTTS and OpenVoice source-utterance sets share 80 of 120
  originals (Entry 5 RandomState footnote); they are a *balanced
  per-generator comparison*, not a *fully paired
  utterance-by-utterance comparison*.
- **Do NOT generalise to other generators, dialects, or detectors
  not tested.** Only XTTS v2, OpenVoice v2, DECTE (Tyneside), and
  VCTK (loose-English-accent 20 speakers) were evaluated. State this
  scoping explicitly in the introduction and again in the discussion.

---

## 9. Limitations section (dedicated)

Draft outline for Chapter 8's limitations subsection. Each bullet
maps to a specific committed caveat so the thesis can cite them.

1. **Single primary detector family.** AASIST via the AuralGuard
   wrapper is the only deep detector evaluated end-to-end (Entry 6,
   7, 9). The LFCC + LR detector (Entries 8, 10) provides
   architecture-independent replication but is a weaker classical
   baseline, not a deployment-grade alternative.
2. **Single generator per family.** XTTS v2 (Coqui) and OpenVoice v2
   (MyShell) are one representative each of end-to-end zero-shot
   cloning and base-TTS-plus-tone-converter architectures
   respectively. RVC, StyleTTS 2, and Melo-based direct synthesis are
   not covered.
3. **Corpus/domain vs pure-dialect confound.** DECTE and VCTK differ
   simultaneously on dialect (Tyneside vs mixed English), recording
   style (interview vs studio-read), channel quality (variable vs
   clean), age distribution (multi-decade vs 21–30 dominant), and
   transcript pipeline (Whisper/FairFix vs corpus-supplied).
   "Dialect / domain gap" is the honest phrase; disentangling
   dialect from those factors requires further controlled subsets
   (Northern English VCTK, age-matched slices, channel-matched noise).
4. **Small held-out slice sizes.** DECTE mitigation test: 16 speakers,
   172 files (86 + 86). VCTK matched control: 20 speakers,
   ≤ 220 files per generator. Bootstrap CIs are correspondingly wide.
5. **VCTK generator overlap is 80 %, not 100 %.** RandomState
   divergence between separate XTTS-only and OpenVoice-only runs
   means the two 100-spoof subsets share 80 source originals, not
   all 100. This is a *balanced per-generator comparison*, not a
   *fully paired utterance-by-utterance comparison* (Entry 5).
6. **Bootstrap assumes file-level independence.** Each of the 1000
   iterations resamples files with replacement, not speakers.
   Speaker-block bootstrap would produce wider (and more honest) CIs
   at N = 16–20 speakers.
7. **In-training exposure in the AASIST baseline.** The AuralGuard
   training CSV contains 8,057 DECTE rows before filtering; the LFCC
   + LR replication (Entry 8) explicitly removed the 16 test speakers
   before training, but the AASIST baseline did not — its 40.70 %
   DECTE baseline EER may partly reflect this seen-speaker exposure.
   Discussed as a threat to validity in Chapter 8.
8. **Mitigation is DECTE-XTTS-scoped.** Entry 7's mitigation was
   fine-tuned on DECTE + XTTS spoofs only. It is not evaluated on
   OpenVoice and not claimed as a universal anti-spoofing
   improvement.
9. **VCTK age-band skew.** 19 of 20 VCTK speakers used are in
   `21–30`. DECTE spans multiple decades. Age is a co-confound with
   dialect / channel.
10. **AuralGuard training set overlap with VCTK-like data.** GLOBE
    (US-English, studio-clean) is in the training distribution;
    VCTK is not identical but shares stylistic properties.
    Detector's *bonafide* recognition on VCTK likely benefits from
    that exposure. The *spoof-side* EER is therefore the
    load-bearing number, not the bonafide-mean-score comparisons.
11. **No sociolinguistic causal claim from Entry 11.** Per-subgroup
    deltas are descriptive on a 16-speaker slice; per-subgroup CIs
    would be wide.

---

## 10. Future work section (dedicated)

Draft outline for Chapter 9's future work subsection.

1. **Second AASIST-alternative deep detector.** Wav2Vec2-XLS-R + AASIST-style
   head, or the RawGAT-ST family. Would extend the cross-architecture
   confirmation from LFCC + LR (linear-on-hand-crafted) to
   deep-learned-alternative-representation.
2. **More generators.** RVC, StyleTTS 2, and (as they mature)
   emerging diffusion-based voice-cloning systems. Testing whether
   the "generator-specific corpus reversal" pattern is unique to
   OpenVoice v2 or a more general phenomenon.
3. **Larger DECTE test slice.** The 16-speaker held-out slice is what
   forces wide CIs. A 40-speaker slice would materially tighten
   every per-subgroup number in Entry 11 and every mitigation-effect
   CI in Entry 7.
4. **Pre-picked target-set fix** for future XTTS-vs-OpenVoice runs on
   the same corpus (Entry 5 RandomState footnote). Code-only fix in
   `SpoofPipeline.run()`; enables truly paired 100/100/100 comparisons.
5. **Speaker-block bootstrap** across all headline bootstrap
   analyses, replacing file-level bootstrap. More honest CI widths
   given ≤ 20-speaker slices.
6. **A standardised-accent dialect control.** Two possible directions:
   (a) a Northern-English VCTK subset (harder to build from VCTK 0.92
   alone), or (b) using the EdAcc corpus's regional accent breakdown
   as a bridge between VCTK and DECTE.
7. **Field-recording quality-matched VCTK subset.** Adding controlled
   noise / EQ / bandwidth restriction to VCTK to match DECTE's SNR
   profile would isolate the dialect effect from the audio-quality
   effect.
8. **LFCC + LR mitigation replication.** Would give Entry 7's
   mitigation the same cross-architecture status that Entries 8 and
   10 already give the corpus/reversal gaps.
9. **Deployment-scoped mitigation.** Extend the mitigation training
   set beyond DECTE to include multi-dialect fine-tuning data;
   evaluate whether a single detector can hold both the XTTS gap and
   the OpenVoice reversal at deployment-grade EER.
10. **A formal fairness audit** of the mitigated detector across a
    demographically balanced multi-dialect corpus (out of scope for
    this thesis; would need its own study design with informed
    consent and demographic sampling).

---

## 11. Writing workflow suggestion (process, not content)

The plan itself is done. When drafting begins, this order minimises
back-tracking:

1. **First**: draft Chapter 3 (Data & Methodology). It is the most
   protocol-heavy chapter; nailing down the methodology text lets
   Chapters 4–7 refer back to it consistently.
2. **Second**: draft Chapter 5 (Main Results) using the numbers
   directly from Entries 2, 4, 5, 6, 8, 9, 10. This is where the
   thesis stands or falls; get it right early.
3. **Third**: draft Chapters 6 and 7 (Mitigation, Subgroups). They
   are self-contained relative to Chapter 5.
4. **Fourth**: draft Chapter 4 (Baseline & Verification) and
   Chapter 8 (Discussion & Limitations). Chapter 4 short; Chapter 8
   collects caveats already present in the entries.
5. **Fifth**: draft Chapter 2 (Background). Deliberately late — the
   related-work framing benefits from knowing exactly which results
   need supporting.
6. **Last**: draft Chapter 1 (Introduction) and Chapter 9 (Conclusion).
   These are the shortest chapters but the most "final" in tone;
   easier to write after the rest is stable.

Throughout, treat `docs/THESIS_FINDINGS_LOG.md` as the source of
truth for every number cited. Every quantitative claim in the thesis
should correspond to a specific Entry and — where applicable — a
specific committed script.

---

## 12. What this plan is NOT

- Not a decision on final chapter numbering, section headings, or
  page counts. All targets in Section 4 are indicative.
- Not a decision on the citation style, template, or figure
  formatting (JKU / Institute-of-Computational-Perception house
  style takes precedence).
- Not a substitute for supervisor review. The recommended title,
  RQ phrasing, and contribution list should all be checked with the
  thesis advisor before drafting Chapter 1.
- Not the thesis itself. No prose yet.

---

## 13. Open questions for the supervisor / thesis author before drafting

1. Confirm the final title (Section 1 recommends the two-effect
   framing).
2. Confirm the four RQs (Section 2) match what was agreed for the
   thesis proposal.
3. Confirm the ordering of Chapters 5 → 6 → 7 (results-then-
   mitigation-then-diagnostics) rather than interleaving them.
4. Decide whether to include the LFCC + LR mitigation replication
   (queued in Entry 11) *before* thesis drafting begins, or leave it
   as future work in Chapter 9. If included, it would extend the
   cross-architecture replication (Contribution 3) to the mitigation
   result (Contribution 4), giving the mitigation claim the same
   cross-detector footing the two headline gap claims already have.
5. Confirm scope of the appendix (Section 4). Reproducibility index
   is strongly recommended; the low-n subgroup table is optional.
