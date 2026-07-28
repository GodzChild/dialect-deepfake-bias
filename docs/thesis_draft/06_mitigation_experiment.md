# Chapter 6 — Mitigation Experiment

*Draft. Written to be read by the thesis supervisor first, then polished
into final prose. All quantitative claims trace back to a specific
Entry in `docs/THESIS_FINDINGS_LOG.md` and to a specific committed
script under `scripts/`.*

---

## 6.1 Chapter overview

Chapter 5 established two headline results with 95 % bootstrap
support: XTTS v2 produces a positive DECTE-vs-VCTK EER gap (DECTE
harder) on both detectors tested, and OpenVoice v2 produces a
negative gap (VCTK harder) on both detectors. Chapter 5 was
descriptive: it measured what happens without any intervention.

This chapter asks a different question. Given the XTTS
dialect / domain gap of Chapter 5, is that gap something the
detector can be *adapted* to reduce, or is it a fixed property of
the detector–corpus combination? Specifically, can a small,
controlled adaptation of the primary detector shrink the DECTE
XTTS EER on a held-out DECTE test slice without hurting its
out-of-training-domain performance on VCTK?

This chapter mainly answers **RQ3** from the writing plan
(*"Can a conservative, lightweight adaptation of the detector
reduce the observed dialect / domain gap without regressing on
out-of-training-domain speech?"*). It does not attempt to solve
audio-deepfake detection in general, and it does not evaluate
the OpenVoice failure mode of Chapter 5 (the mitigation is
scoped to DECTE XTTS by design — see Section 6.11).

Two versions of the mitigation are reported. The first (v1) is
included briefly as motivation for the design change that
produced the second (v2); the headline result of the chapter is
the v2 result reported in Sections 6.6, 6.7, and 6.8.

---

## 6.2 Why mitigation was needed

The Chapter 5 result that most invites a mitigation attempt is the
XTTS row of the main 2 × 2 table. Under both the primary detector
(AuralGuard-AASISTPP) and the secondary detector (LFCC + LR), the
DECTE XTTS EER was substantially above the VCTK XTTS EER, and the
DECTE-minus-VCTK gap CI lay entirely above zero on both detectors.
That is a well-supported gap in the *bad* direction: dialectal /
interview-style speech is harder for the detector to correctly
classify than standard-accent studio speech is, and the effect
size is roughly comparable across two very different detector
architectures.

The mitigation experiment is therefore scoped to the DECTE XTTS
setting for three reasons:

- It is the setting where the gap is clearest across the two
  detectors — an intervention that helps here should be measurable.
- It is the setting the thesis' original research question was
  framed around (*"Does your accent make you vulnerable?"*). If a
  small adaptation can meaningfully reduce the XTTS DECTE gap,
  that is directly interpretable evidence for RQ3.
- The OpenVoice reversal (VCTK is *harder* than DECTE for that
  generator) is a different failure mode and would need a
  different intervention design. Chapter 6 deliberately leaves
  it out of scope; Chapter 8 discusses this as a limitation.

The chapter's goal is a controlled adaptation, not a new
detector. The baseline AuralGuard-AASISTPP checkpoint verified
in Chapter 4 remains the reference point; the mitigation
produces a fine-tuned checkpoint that inherits from it, and every
before / after comparison is against the same checkpoint under
identical evaluation conditions. Nothing in this chapter proposes
a deployment-grade detector.

---

## 6.3 Leakage-safe mitigation split

Producing a defensible before / after comparison requires the
mitigation to be trained on data that has zero speaker overlap
with the data it is later evaluated on. Without this, an
apparent "mitigation improvement" could be nothing more than the
adapted model recognising speakers it saw at fine-tune time. The
mitigation split (introduced in Chapter 3, Section 3.7.1) enforces
this:

- **82 eligible speakers** — the intersection of the DECTE
  speakers who have valid bonafide utterances and the DECTE
  speakers who have at least one successful XTTS spoof in the
  DECTE manifest.
- **52 training speakers** — used for the mitigation fine-tune.
- **14 validation speakers** — used for early stopping and
  best-checkpoint selection during the fine-tune.
- **16 test speakers** — held out entirely from fine-tuning and
  used only to evaluate the fine-tuned checkpoint against the
  baseline checkpoint.

The partition is deterministic (seed 42, `numpy.random.default_
rng.permutation` over the alphabetically sorted eligible speaker
list), so it can be regenerated at will. A leakage-check step in
`scripts/09_build_mitigation_csvs.py` verifies that the three
resulting speaker sets are disjoint at the speaker level *and*
that the resulting file sets are disjoint at the audio-file
level, and aborts before writing any outputs if either check
fails. This eliminates the most likely category of silent
leakage bug.

Applied to the DECTE spoof manifest, the 16-speaker held-out
test set produced a paired evaluation slice of:

- **86 matched bonafide originals** (each an actual DECTE audio
  clip used as the source of a spoof), and
- **86 XTTS v2 spoofs** produced from those same originals.

The bonafide side comes from the `source_audio_path` field
introduced in Chapter 3, Section 3.5; the spoof side is drawn
from the corresponding `output_path` field. Every bonafide file
is paired with exactly one spoof file, and every spoof was
generated with reference audio from the same speaker (though not
from the same utterance — reference audio and target audio are
disjoint by construction; see Chapter 3, Section 3.3.3).

Both the baseline detector and the mitigated detector are
evaluated on this same 172-file slice, so the before / after
comparison in the rest of the chapter is a within-file paired
comparison in the sense of Chapter 3, Section 3.6.2 (paired
within-file bootstrap).

---

## 6.4 Mitigation v1 as motivation

An initial mitigation attempt (v1) was tried with the entire
AASIST backbone frozen and only the three AuralGuard task heads
(`binary_head`, `attack_head`, `explanation_head` — see Chapter 3,
Section 3.4.1) left trainable. The rationale was minimal-capacity:
if changing only the linear heads on top of a frozen feature
extractor is enough to shrink the DECTE XTTS gap, then no deeper
adaptation is needed. Head-only fine-tuning has approximately 1,600
trainable parameters, so catastrophic forgetting of the backbone
is impossible by construction.

The v1 result on the held-out DECTE test slice was:

- Baseline DECTE XTTS EER: **40.70 %**
- v1 mitigated DECTE XTTS EER: **36.05 %**
- Delta (v1 mitigated − baseline): **−4.65 pp**
- 95 % paired bootstrap CI on the delta: **[−12.79, +2.91] pp**

The point-estimate direction is favourable — the mitigated
detector is numerically better than the baseline on the DECTE
XTTS slice — but the 95 % CI on the delta crosses zero. In the
verdict language of Chapter 3, Section 3.6.3 this is
*not statistically distinguishable at 95 %*, i.e. the delta could
plausibly be zero (or slightly positive) under the sampling
distribution of a 172-file slice.

The v1 outcome is therefore reported here as **suggestive but
not statistically confirmed**. It is not by itself an argument
that "mitigation works" or "mitigation doesn't work" — it is an
argument that head-only capacity is not enough to establish that
mitigation works on this slice at this sample size. The v2 design
described in the next section was the response to this
observation.

Detailed v1 evaluation numbers (accuracy, FAR, FRR, VCTK
guardrail) are recorded in the mitigation-v1 predecessor entry
and are not repeated here.

---

## 6.5 Mitigation v2 design

The v2 design keeps almost everything about v1 — same
initialisation from the baseline checkpoint, same training data
split, same hyperparameters, same early-stopping criterion — but
adds a targeted increase in trainable capacity through
*partial-backbone unfreezing*.

Instead of freezing the entire AASIST backbone, v2 also
un-freezes the five modules corresponding to the *final*
heterogeneous graph-attention (H-GAT) stage of the AASIST
backbone plus its two associated pooling layers and its
learnable master token:

- `HtrgGAT_layer_ST21`
- `HtrgGAT_layer_ST22`
- `pool_hS2`
- `pool_hT2`
- `master2`

All five modules feed the concatenated pooled features that the
`AuralGuardAASISTPP` wrapper uses as input to its `binary_head`
(and the two auxiliary heads). Chapter 3, Section 3.4.1 documents
that the wrapper reads `result[0]` (the last-hidden features)
from the AASIST backbone, so these five modules are the last
part of the backbone that clearly affects what the wrapper's
binary head sees. Everything upstream of them — the raw-waveform
SincConv front-end, the encoder blocks, the first-GAT stage, and
the first heterogeneous GAT stage — is left frozen.

Specifically, at the start of the v2 training run, the fine-tuning
script reports:

- **31,372 trainable parameters**, and
- **268,104 frozen parameters**.

That is, only about 10.5 % of the model's total parameters are
adapted. All other AASIST parameters retain their baseline
checkpoint values exactly.

The rationale for this specific unfreezing pattern is documented
in Chapter 3, Section 3.7.4:

- Choosing the *final* backbone stage rather than any earlier
  stage keeps the model's learned low-level and mid-level
  acoustic representations intact. Only the top-of-backbone
  view — the graph-attention interactions between spectral and
  temporal pooled representations — is allowed to shift.
- Choosing the second heterogeneous GAT stage (`ST21`, `ST22`)
  rather than the first (`ST11`, `ST12`) keeps the shift as close
  as possible to the classifier heads without touching them
  purely: the heads themselves also update, but the features
  they consume are still 90 % determined by the frozen upstream
  stack.
- Adding `master2` to the unfrozen set is because that master
  token is the input to the second H-GAT stage and cannot
  usefully move separately from it.

Training hyperparameters, unchanged from v1: 5 epochs, batch
size 4, learning rate 3 × 10⁻⁵, `num_workers = 0`, single GPU.
The best checkpoint is selected on validation-set EER over the
five epochs and saved as `checkpoints/mitigation_v2_partial_
unfreeze/best.pt`. The full training command and the
`--unfreeze-modules` flag added to `auralguard-aasistpp/src/
train.py` for this purpose are documented in Chapter 3,
Section 3.7.4.

Everything about v2 is therefore a *controlled adaptation* rather
than a re-training. The pre-existing checkpoint is the starting
point; only ~10.5 % of the parameters are allowed to move; and
the movement is confined to the top of the feature extractor
plus the task heads.

---

## 6.6 DECTE mitigation result

Evaluating the v2 mitigated checkpoint on the 172-file held-out
DECTE test slice (Section 6.3) and comparing it against the
baseline checkpoint on the same slice produced the primary
result of this chapter.

| Arm | Detector | n_bonafide | n_spoof | EER (%) |
|---|---|---:|---:|---:|
| Baseline | AASIST | 86 | 86 | **40.70** |
| Mitigated v2 | AASIST | 86 | 86 | **23.26** |

Delta EER (mitigated v2 − baseline) on the DECTE XTTS test slice:

- **Point estimate**: −17.44 pp
- **95 % paired bootstrap CI**: **[−28.49, −9.30] pp**

The full delta CI lies below zero. In the verdict language of
Chapter 3, Section 3.6.3, this is a **statistically supported
improvement at 95 %** — the sampling distribution of the delta
under the resampling protocol used throughout the thesis does
not include zero at the 95 % level.

Two additional points about how to read this result:

- The 172 test files are drawn from **16 speakers not seen at
  fine-tuning time**. The improvement therefore cannot be
  attributed to the mitigated detector recognising specific
  speakers from its training set. The paired-bootstrap CI is a
  within-file paired quantity (same files under both
  checkpoints; see Chapter 3, Section 3.6.2), so it isolates the
  effect of the fine-tune from the noise of which files happen
  to be resampled.
- The v2 improvement (−17.44 pp) is nearly four times the v1
  improvement (−4.65 pp), and unlike v1 the CI does not include
  zero. The design change between v1 and v2 (adding ~ 30,000
  backbone parameters to the ~ 1,600 head parameters) closed the
  statistical-support gap without changing anything else.

Reproducer: `scripts/03_run_detectors.py` on both the baseline
config and `configs/detectors_mitigated_v2.yaml`, evaluated on
`data/generated_spoofs/manifest_mitigation_test.jsonl`, then
`scripts/10_bootstrap_mitigation_effect.py` for the paired-
bootstrap CI. Details are in Entry 7 of the findings log.

---

## 6.7 VCTK guardrail result

A DECTE-only improvement is not by itself evidence of a *useful*
mitigation. If the mitigated detector improves on DECTE by
sacrificing its performance on out-of-training-domain speech,
the net contribution is neutral or negative — the model has
just moved its errors elsewhere. To rule this out, the same v2
checkpoint was also evaluated on the VCTK XTTS manifest from
Chapter 5 (which contains no DECTE speakers by construction and
was not touched at fine-tune time).

| Arm | Detector | n_bonafide | n_spoof | EER (%) |
|---|---|---:|---:|---:|
| Baseline | AASIST | 120 | 100 | **21.83** |
| Mitigated v2 | AASIST | 120 | 100 | **19.17** |

Delta EER (mitigated v2 − baseline) on the VCTK XTTS guardrail:

- **Point estimate**: −2.67 pp
- **95 % paired bootstrap CI**: **[−5.42, +3.17] pp**

The 95 % CI includes zero — the change in VCTK XTTS EER between
the baseline and the v2 mitigated detector is not statistically
distinguishable from zero at 95 %. Because the direction the
guardrail is protecting against is *worsening* on VCTK (a
positive delta), the fact that the CI's upper bound is +3.17 pp
is the relevant number: the mitigation cannot be statistically
argued to have *hurt* VCTK performance at 95 %.

In the verdict language of Chapter 3, Section 3.6.3 this is
**no statistically significant VCTK regression**. The mitigation
does not appear to have simply displaced errors from DECTE onto
VCTK.

Reproducer: same as Section 6.6, evaluated on
`data/generated_spoofs_vctk/manifest.jsonl` under both configs.

---

## 6.8 In-domain sanity check after mitigation

The two evaluations above (Sections 6.6 and 6.7) both live inside
the DECTE / VCTK evaluation slice used elsewhere in the thesis.
A separate risk with any fine-tune is that it may catastrophically
forget the *training* distribution the baseline was optimised on
— that is, the mitigated detector may become better at DECTE
XTTS but simultaneously become substantially worse at the
ASVspoof / WaveFake / GLOBE / EdAcc / EnglishDialects mixture
the baseline was originally trained against.

The in-domain sanity check of Chapter 4, Section 4.6 is exactly
the right instrument for this. The mitigated v2 checkpoint was
scored on the AuralGuard-original validation set (9,514 files
across the six source datasets) using the same script that
verified the baseline in Chapter 4.

- **Mitigated v2 in-domain sanity EER**: **2.50 %**
- **Verdict** against the ≤ 5 % PASS threshold from Chapter 4,
  Section 4.6.3: **PASS**

The baseline's in-domain sanity EER was 1.71 % (Chapter 4,
Section 4.6.4). The mitigated v2 checkpoint is therefore
approximately 0.8 pp worse than the baseline on the training-
distribution validation set, which is small relative to the
verification threshold and consistent with the small parameter
budget the fine-tune was allowed to move (~ 10.5 % of the model).

This reduces the concern that the DECTE improvement in Section 6.6
came at the cost of catastrophic forgetting. In combination with
the VCTK guardrail of Section 6.7, the picture is that the
mitigation shifted the model's DECTE XTTS behaviour noticeably
while leaving both a same-generator out-of-training-domain slice
(VCTK XTTS) and the original training-distribution validation
slice essentially intact.

---

## 6.9 Summary table

Sections 6.6, 6.7, and 6.8 collected into one compact view of
the mitigation experiment:

| Setting | Baseline EER (%) | Mitigated v2 EER (%) | Delta (pp) | 95 % CI (pp) | Interpretation |
|---|---:|---:|---:|---:|:---|
| DECTE XTTS held-out test (86 + 86) | 40.70 | 23.26 | **−17.44** | **[−28.49, −9.30]** | Statistically supported improvement at 95 % |
| VCTK XTTS guardrail (120 + 100) | 21.83 | 19.17 | −2.67 | [−5.42, +3.17] | No significant regression at 95 % |
| In-domain sanity (AuralGuard val set) | 1.71 | 2.50 | +0.79 | — (not bootstrapped) | Still PASS under ≤ 5 % threshold from Chapter 4 |

The DECTE improvement CI is fully below zero; the VCTK guardrail
CI includes zero; the in-domain sanity result stays inside the
PASS band. These three conditions together are what the writing
plan calls the *success criteria* for a mitigation experiment
under RQ3, and they are all satisfied for v2.

---

## 6.10 Interpretation

The v2 mitigation reduced the DECTE XTTS EER on a leakage-safe
held-out test slice, and the improvement was statistically
supported at 95 %. On the same detector, on an out-of-training-
domain guardrail (VCTK XTTS), no statistically significant
regression was observed. On the baseline detector's original
training-distribution validation set, the mitigated checkpoint
retained PASS status under the verification threshold from
Chapter 4.

Put together, these results back the RQ3 claim that **a
conservative, lightweight adaptation of the detector can reduce
the observed dialect / domain XTTS gap without regressing on
the out-of-training-domain data slice tested**. In particular,
they are consistent with the interpretation that some of the
DECTE XTTS gap observed in Chapter 5 was *not* an intrinsic
property of the AASIST architecture but was addressable by
allowing the top of its feature extractor to shift under
DECTE-adapted data.

Three things this chapter deliberately does **not** claim:

- It does not claim to solve audio deepfake detection generally.
  A ~17 pp EER reduction on a 172-file DECTE slice under one
  detector, one generator, one dialect, and one adaptation
  design is a scoped result. The residual DECTE XTTS EER
  (23.26 %) is still far above the training-distribution EER of
  1.71 % and remains unusable for deployment.
- It does not claim that the mitigation is *architecture-invariant*.
  Only the AASIST detector was fine-tuned; the LFCC + LR
  detector was not. Whether the same partial-unfreeze idea
  transfers to other detector families is out of scope for this
  chapter and is queued for future work.
- It does not claim the mitigation is a fairness fix. The
  descriptive per-subgroup breakdown of the mitigation effect
  is the subject of Chapter 7; that chapter treats it as
  diagnostic evidence, not as a fairness audit or a demographic-
  bias remedy.

Chapter 6's role in the thesis' overall argument is therefore
modest: it shows that the DECTE XTTS gap of Chapter 5 is at
least partly *reducible* by a controlled adaptation of the
primary detector, under conditions that also protect against
the two most likely artefacts — in-training-domain forgetting
and out-of-training-domain regression. It does not try to close
the gap entirely, and it does not try to show the same for
OpenVoice.

---

## 6.11 Limitations

Five limitations narrow the scope of the mitigation claims in
this chapter. Chapter 8 revisits them alongside the
Chapter 5-scope limitations.

- **Single detector.** The mitigation was designed for and
  evaluated on the AuralGuard-AASISTPP architecture only. The
  LFCC + LR detector used in Chapter 5 as a cross-architecture
  replication check is *not* fine-tuned here. Whether the
  DECTE XTTS gap the LFCC + LR detector shows can be closed by
  an analogous adaptation is queued as future work — no claim
  is made in this chapter about detector-family invariance of
  the mitigation.
- **Single generator.** The mitigation was scoped to the DECTE
  XTTS setting, the setting where Chapter 5 established a
  positive DECTE-vs-VCTK gap. The OpenVoice reversal of
  Chapter 5 (VCTK harder than DECTE) is a different failure
  mode and would need a different intervention design; nothing
  here transfers automatically to OpenVoice.
- **DECTE and VCTK differ on multiple axes at once.** The
  Chapter 5 limitation applies verbatim: DECTE and VCTK
  differ in dialect, recording style, channel quality, age
  distribution, and transcript pipeline. The mitigation's
  DECTE improvement is best read as *dialect / domain-gap
  reduction* rather than a pure *dialect adaptation*. Which
  of these axes the fine-tune actually adapted to (dialect
  specifically? channel quality? interview-style prosody?) is
  not answered by the experiment as designed.
- **Small held-out test slice.** The 172-file test slice
  (86 + 86 across 16 speakers) produces bootstrap CIs on the
  order of ± 10 pp on each individual arm. The DECTE
  improvement CI ([−28.49, −9.30] pp) is entirely below zero,
  but the width is substantial. A larger held-out DECTE test
  slice would noticeably tighten this CI.
- **Not a production-ready detector.** The mitigated v2
  checkpoint achieves 23.26 % EER on DECTE XTTS and 19.17 %
  on VCTK XTTS. Both remain far above the training-distribution
  EER (~ 1.71 %). Chapter 6 documents an *adaptation experiment*
  under RQ3, not a deployment-grade anti-spoofing detector.
  Using the mitigated checkpoint in a real anti-spoofing
  deployment is out of scope for this thesis, and no such use
  is claimed.

None of these limitations invalidate the qualitative claim in
Section 6.10: the DECTE XTTS gap is at least partially
reducible under a small controlled adaptation of the AASIST
architecture, with no statistically significant VCTK regression
and no failure of the in-domain sanity check. What they
constrain is how *strongly* that claim can be phrased in the
thesis' broader argument — *"targeted adaptation of the final
feature stage plus the task heads can reduce the DECTE XTTS
gap for the AASIST detector on this held-out test slice"*, not
*"the mitigation eliminates detector bias against dialectal
speech"*.

---

*End of Chapter 6 draft.*
