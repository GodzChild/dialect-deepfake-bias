# Chapter 8 — Discussion, Limitations, and Threats to Validity

*Draft. Written to be read by the thesis supervisor first, then polished
into final prose. Interpretation chapter — quantitative results already
reported in Chapters 5–7 are not re-tabulated here; specific numbers
appear only when needed to anchor an interpretation.*

---

## 8.1 Chapter overview

Chapters 5, 6, and 7 reported the empirical findings of this thesis
one at a time: the corpus-and-generator behaviour of the primary
detector and its cross-architecture LFCC + LR replication
(Chapter 5), the effect of a conservative partial-backbone
adaptation on the DECTE XTTS setting (Chapter 6), and the
per-subgroup diagnostic view of that adaptation on the held-out
DECTE test slice (Chapter 7). Each chapter interpreted its own
results narrowly.

This chapter puts the four findings together. Its role is
interpretive rather than empirical. Section 8.2–8.5 summarise the
four main findings in the language the thesis will use in its
Conclusion and Abstract; Section 8.6 argues for why "dialect /
domain gap" is the right phrase rather than "dialect bias";
Section 8.7 collects the threats to validity across the entire
study; Section 8.8 sketches the practical implications; and
Section 8.9 lists what the thesis explicitly does *not* claim.
Section 8.10 restates the final interpretation the thesis will
carry into Chapter 9.

---

## 8.2 Main finding 1 — dialect / domain effects matter for XTTS

Under both detectors evaluated in this thesis (the primary
AuralGuard-AASISTPP wrapper and the secondary LFCC + Logistic
Regression baseline), the DECTE XTTS EER was substantially higher
than the VCTK XTTS EER, and the DECTE-minus-VCTK gap CI lay
entirely above zero at 95 % (Chapter 5, Sections 5.3 and 5.4). The
two detectors disagreed on absolute EER level — LFCC + LR is a
weaker classifier and its EER on both corpora was ~ 10 pp higher
than the AASIST equivalents — but they agreed on the sign of the
gap and, remarkably, on its rough magnitude: ~ 12 pp on both
detectors, with overlapping bootstrap CIs.

The **cross-detector replication** does substantive work here.
A DECTE-vs-VCTK gap on one detector could plausibly be an
architecture-specific artefact — a quirk of AASIST's graph-attention
pipeline on interview-style audio, say. The same gap appearing on
a completely different classifier family (linear model on
hand-crafted spectral features) rules out that specific escape.
The gap is therefore a property of the *DECTE-vs-VCTK-under-XTTS*
condition rather than of any one detector.

The safe framing throughout is **dialect / domain gap**, not
*pure dialect bias*. Section 8.6 spells out why. In one sentence:
DECTE and VCTK differ on several axes simultaneously (dialect,
recording style, channel quality, age distribution, transcript
pipeline), and Chapter 5's design does not isolate the dialect
axis from the others. What the two chapters do isolate — and
support at 95 % on two detectors — is that DECTE-style
dialectal / interview-style audio produces higher XTTS detection
error rates than VCTK-style studio-read audio does under the
detectors tested.

---

## 8.3 Main finding 2 — generator choice changes the direction of the corpus gap

The Chapter 5 result that most reshapes the thesis' original
framing is the OpenVoice comparison (Sections 5.5 and 5.6). Under
identical evaluation conditions to the XTTS comparison — same
detector, same bonafide pools, same audio preprocessing, same
bootstrap protocol — swapping XTTS for OpenVoice reverses the
sign of the DECTE-vs-VCTK EER gap. The DECTE arm becomes the
easier of the two; the VCTK arm becomes the harder. Both
detectors show this reversal at 95 %.

Interpretationally, the OpenVoice reversal rules out a reading of
Chapter 5 as "DECTE is uniformly harder for anti-spoofing than
VCTK". A uniformly-harder-corpus effect would preserve the sign
of the gap across generators. The observed sign flip is only
compatible with a *joint* dependence: **detector reliability
depends jointly on the corpus / domain of the input and on the
generator that produced the spoof**. Neither factor alone predicts
the sign of the gap; only the combination does.

The right phrase for this — used consistently throughout the
thesis — is **generator-specific corpus interaction**. It captures
that OpenVoice v2's failure mode is not a dialect effect and not
a corpus-quality effect on its own, but an interaction between the
generator's output distribution and the corpus the detector is
being asked to compare it against. The reversal is well-supported
statistically (both CIs entirely below zero) and cross-detector
(both AASIST and LFCC + LR show the same sign), so the phrase is
descriptively accurate.

Two things this thesis does not claim from the OpenVoice
finding: it does not claim OpenVoice v2 is a "worse" or "more
dangerous" generator than XTTS in absolute terms, and it does
not claim the OpenVoice reversal generalises to every anti-spoofing
detector or every recording condition. Different detectors trained
on different data may exhibit very different patterns. What this
thesis establishes is that under the two detectors and two corpora
tested, generator choice clearly changes not only the size of
the corpus gap but its sign.

---

## 8.4 Main finding 3 — targeted adaptation can reduce the DECTE XTTS gap

Chapter 6's mitigation v2 was designed as a **controlled
adaptation** — a small, targeted increase in the AuralGuard-
AASISTPP wrapper's trainable-parameter budget (the last
heterogeneous-GAT stage of the AASIST backbone plus the three
AuralGuard task heads, approximately 10.5 % of the model's total
parameters), fine-tuned on a leakage-safe DECTE speaker split and
then evaluated on a held-out DECTE test slice under the same
protocol as Chapter 5.

Three conditions from the writing plan's success criteria for a
mitigation experiment (Chapter 6, Section 6.10) were all
satisfied:

- The DECTE XTTS EER on the held-out slice dropped substantially,
  and the 95 % paired-bootstrap CI on the delta lay entirely
  below zero (statistically supported improvement).
- The VCTK XTTS EER on the out-of-training-domain guardrail did
  not change in a statistically supported way; the delta CI
  included zero (no significant regression).
- The mitigated checkpoint's in-domain sanity EER remained inside
  the ≤ 5 % PASS band defined in Chapter 4 (no catastrophic
  forgetting of the training-distribution behaviour).

The thesis therefore reports the mitigation as a **statistically
supported reduction of the DECTE XTTS gap on the primary detector**
that also preserves out-of-training-domain performance on the
tested guardrail and preserves in-domain performance on the
original training distribution. Under RQ3, this is a positive
answer: a conservative, lightweight adaptation of the detector
can reduce the observed dialect / domain gap without regressing
on the out-of-training-domain data slice tested.

Two boundaries on this claim, both from Chapter 6:

- The mitigation is **scoped to AASIST**. The LFCC + LR detector
  used in Chapter 5's cross-architecture replication was not
  fine-tuned in this thesis; whether the same partial-unfreeze
  idea would transfer to a linear classifier on hand-crafted
  features is out of scope and queued as future work.
- The mitigation is **scoped to DECTE-and-XTTS**. It does not
  attempt to address the OpenVoice reversal of Section 8.3, and
  it does not evaluate on OpenVoice audio. The residual DECTE
  XTTS EER post-mitigation is still far above the training-
  distribution EER; the mitigated checkpoint is not a production
  deepfake detector, and no such claim is made.

---

## 8.5 Main finding 4 — subgroup diagnostics show uneven improvement

Chapter 7's per-subgroup view of the same held-out DECTE test
slice found that **every main-table subgroup improved after
mitigation v2**, but that the size of the improvement varied
substantially between subgroups (from −5.00 pp to −34.38 pp
across the main-table recording-era rows, and from −6.41 pp to
−26.92 pp across the two gender rows). The uniformity of the
*direction* of the mitigation effect (no subgroup went the wrong
way) is a genuinely reassuring diagnostic result — it rules out
the concerning scenario in which the overall improvement of
Chapter 6 was driven by large gains in some subgroups combined
with regressions in others.

Chapter 7 was explicit that the per-subgroup findings are
**diagnostic**, not evidence of fairness or its absence. With
only 16 held-out DECTE speakers and per-subgroup counts in the
10–40 files-per-class range, per-subgroup bootstrap CIs would be
wide enough that most between-subgroup differences in delta EER
would sit inside sampling noise. No such per-subgroup CIs are
computed, and no per-subgroup difference is claimed as
statistically supported. The chapter's diagnostic conclusion —
that *error concentration and mitigation benefit were not uniform
across DECTE metadata groups on the 16-speaker held-out test
slice* — is descriptive of the point-estimate spread and no more.

Read together with Chapter 6, the subgroup layer supports two
narrow substantive claims. First, the overall mitigation result
in Chapter 6 is not an artefact of averaging across a
homogeneously-improving pool: the direction is uniform across
metadata subgroups on this slice. Second, the observed spread in
per-subgroup delta EER is worth flagging for a follow-up study
with tighter per-subgroup samples — as future work, not as a
finding this thesis makes.

---

## 8.6 Why "dialect / domain gap" is the correct wording

The single wording choice this thesis has been most disciplined
about is **"dialect / domain gap"** in place of "dialect bias",
"dialect effect", or "accent bias". The reason is empirical, not
merely rhetorical.

DECTE and VCTK differ in at least five simultaneous ways:

- **Dialect.** DECTE is Tyneside English throughout; the VCTK
  slate used here is loose English-accent VCTK, majority-southern.
- **Recording style.** DECTE is interview-format speech;
  VCTK is studio-read isolated sentences.
- **Channel and audio quality.** DECTE mixes analog reel-to-reel
  (1960s–1970s), 1990s field recording, and 2000s digital field
  recording; VCTK 0.92 is clean 48 kHz studio material, downsampled
  to 16 kHz for evaluation.
- **Speaker demographics.** DECTE spans multiple decades of age
  and includes 200 speakers across the extractor's metadata;
  the VCTK 20-speaker slate used in Chapter 5 is heavily
  concentrated in the 21–30 age band.
- **Transcript pipeline.** DECTE spoof transcripts came from a
  Whisper + FairFix pipeline (which may lightly normalise
  dialectal spellings); VCTK spoof transcripts came from the
  corpus's own supplied text.

Chapter 5's design holds the detector and generator fixed and
compares the two corpora, but it does not isolate the dialect
axis from any of the other four. A finding that DECTE EER exceeds
VCTK EER under XTTS therefore reflects the combined effect of
all five axes — the observed +12.80 pp gap on AASIST and +12.44 pp
gap on LFCC + LR cannot be attributed exclusively to dialect
without an additional control that this thesis does not run.

The consequence for wording is a fairness contract with the
reader. The safe empirical claim is:

> Under the detectors tested, DECTE-style dialectal / interview-
> style speech creates a measurable detection challenge relative
> to standard-accent studio-read VCTK speech, when the spoof
> generator is XTTS v2.

The unsafe claim, which the evidence does not support, would be:

> The detector is biased against Tyneside dialect specifically.

Every quantitative result in Chapters 5–7 is compatible with the
safe claim; none of them are strong enough to support the unsafe
claim without further controls. Section 8.9 lists the unsafe
claims this thesis therefore explicitly does not make.

---

## 8.7 Threats to validity

Standard four-plus-one categories \cite{ShadishCookCampbell2002_Validity}, each
grounded in a specific Chapter 5–7 caveat.

### 8.7.1 Construct validity

EER, AUC, accuracy, FAR, and FRR are properties of a *detector's
score distribution* against a labelled bonafide/spoof split. They
are not measurements of how convincing a spoof sounds to a human
listener. This thesis reports detector performance, not
human-perceptual naturalness. A generator whose outputs the
detector fails to flag is not necessarily a generator whose outputs
a human listener would fail to flag, and vice versa. The two
questions have different constructs; this thesis measures the
former.

Related: EER treats false accepts and false rejects as
symmetrically costly. Real deployment contexts typically weight the
two asymmetrically (a fraud-prevention setting cares much more
about false accepts than false rejects, for instance). Nothing in
this thesis is calibrated to a specific deployment cost model.

### 8.7.2 Internal validity

The corpus / domain confound named in Section 8.6 is the largest
internal-validity concern. Every corpus-gap result in this thesis
is a joint effect of dialect, recording style, channel, speaker
demographics, and transcript pipeline. Attributing the observed
gap to any single one of those axes would require follow-up
studies with axis-matched controls (an age-matched VCTK subset, a
channel-noised VCTK subset, a Northern-English VCTK subset, or a
DECTE re-transcription pipeline). None of those are run here.

The recording-era subgroup result in Chapter 7 has an analogous
internal-validity concern at the subgroup level: DECTE recording
era correlates with channel technology, interview format, and
speaker-demographic composition of each survey wave. The wide
per-era spread of both baseline EER and mitigation delta cannot
be attributed to time period alone.

The AuralGuard baseline had prior exposure to DECTE-style
bonafide speech during earlier training, but not to the held-out
DECTE XTTS spoof condition evaluated in the mitigation
experiment. Therefore, the mitigation result should be
interpreted as adaptation under partial corpus familiarity,
not as performance on a completely unseen corpus. In detail,
the AuralGuard training CSV contains approximately 8,057 DECTE
rows (Chapter 3, Section 3.4.2 filter accounting); the 16
DECTE speakers held out for the mitigation test slice were
filtered from the LFCC + LR training set (Chapter 4,
Section 4.8) but not from the AuralGuard training pipeline,
which ran before this thesis began. Chapter 5's corpus-gap
directions are unaffected (both arms of each comparison inherit
the same exposure), but the absolute baseline AASIST DECTE
EER on the held-out slice should be read with this partial
familiarity in mind.

### 8.7.3 External validity

Every quantitative claim in this thesis is scoped to:

- Two detectors (AuralGuard-AASISTPP and LFCC + Logistic
  Regression).
- Two generators (XTTS v2 and OpenVoice v2).
- Two corpora (DECTE Tyneside and loose-English-accent VCTK).
- One evaluation protocol (deterministic 4-second preprocessing,
  matched-N or matched-pair evaluation, 1000-iteration seed-42
  bootstrap).

Whether the findings generalise beyond these scoping choices — to
other anti-spoofing detectors (Wav2Vec2-based, RawGAT-ST, etc.),
to other zero-shot voice-cloning generators (RVC, StyleTTS 2), to
other English dialects (Scottish, Irish, Northern English, Indian
English), or to non-English languages — is not established here.
Chapter 9 sketches the follow-up studies that would extend the
external validity envelope.

### 8.7.4 Statistical validity

Every headline result in Chapters 5, 6, and 7 is a small-sample
result. The DECTE mitigation test slice is 172 files (86 + 86)
across 16 speakers; the VCTK XTTS subset is 220 files (120 + 100)
across 20 speakers. Bootstrap CIs on the corpus gaps are on the
order of ± 10 pp on each individual arm; the gap CIs are similarly
wide.

Two specific choices need noting:

- Bootstrap resampling is at the *file* level, not the *speaker*
  level. A speaker-block bootstrap would produce wider (and more
  honest) CIs at the ≤ 20-speaker slice sizes used here. The
  thesis reports file-level bootstrap CIs and flags this as a
  limitation; a speaker-block redo is queued for future work.
- Per-subgroup Chapter 7 tables report point estimates only,
  without per-subgroup CIs, precisely because at 10–40 files per
  subgroup the CIs would be very wide. Chapter 7 is deliberate
  about this and does not claim per-subgroup statistical
  distinguishability.

The VCTK XTTS / OpenVoice pair share 80 of 120 source originals
rather than all 100 that a truly paired design would have shared
(Chapter 5, Section 5.9). This is a *balanced per-generator
comparison*, not a *fully paired utterance-by-utterance
comparison*, and Chapter 5 is careful to phrase it that way. The
divergence originates in a RandomState reproducibility footnote
(Entry 5); a pre-picked target-set fix is queued as future work.

### 8.7.5 Reproducibility validity

Reproducing every quantitative result in this thesis end-to-end
requires four external artefacts that are not distributed with the
committed code (Chapter 3, Section 3.9.6): DECTE corpus access
(research-restricted), VCTK 0.92 (public download), the
AuralGuard-AASISTPP baseline checkpoint (in a neighbouring
project), and the two generator checkpoints (XTTS auto-download,
OpenVoice manual placement). Anyone with access to all four should
be able to rerun every script under `scripts/` and reproduce every
number in the findings log.

Reproducibility is otherwise well-supported: seed 42 throughout,
merge-safe manifests, per-Entry commit-to-log traceability, and
three isolated Conda environments so that generator dependency
drift does not silently affect evaluation numbers.

---

## 8.8 Practical implications

Four narrow practical takeaways for anti-spoofing evaluation
practice, following from the four main findings above.

- **Audio deepfake detectors should be evaluated on diverse real
  speech, not only on the training-adjacent benchmark speech that
  the detector was tuned against.** A verified detector that
  achieves near-1 % EER on its own validation set (Chapter 4)
  achieved > 30 % EER on DECTE XTTS under Chapter 5's protocol.
  The two numbers do not measure the same operational reality.
- **Generator-specific testing matters.** A single-generator
  evaluation would not have exposed the OpenVoice reversal of
  Chapter 5. Any anti-spoofing benchmark that reports a single
  generator's EER — even on a diverse corpus — will underestimate
  the joint corpus × generator interaction that determines real
  behaviour.
- **Cross-detector replication is a cheap and informative
  robustness check.** The LFCC + LR classifier in this thesis was
  not designed as a competitive detector; it exists specifically
  to answer the "is this AASIST-specific?" question at low cost.
  Any published anti-spoofing evaluation that reports a
  provocative finding on one detector should consider a similarly
  cheap cross-architecture check before publishing.
- **Adaptation can help but needs guardrails.** Chapter 6's
  mitigation reduced the DECTE XTTS gap without regressing on
  VCTK or on the training-distribution validation set — but only
  because those two guardrails were explicitly measured. A
  mitigation study that reports only its target-corpus
  improvement risks silently displacing errors elsewhere.

None of these takeaways are a deployment recommendation.
They are process-level notes about how to evaluate anti-spoofing
detectors more carefully than a single benchmark number.

---

## 8.9 What this thesis does not claim

Five explicit non-claims. Each corresponds to a claim a reader
might infer from the results but that the evidence does not
support at the strength required.

- **This thesis does not prove that dialect alone causes detector
  failure.** DECTE and VCTK differ on five simultaneous axes
  (Section 8.6). The safe claim is a dialect / domain-gap claim,
  not a pure dialect-causality claim.
- **This thesis does not prove that the detector is biased against
  any protected group.** Chapter 7's subgroup diagnostic is
  descriptive, not a formal fairness audit. With 16 held-out
  speakers and no per-subgroup CIs, statements of the form "the
  detector is biased against group X" are not supported.
- **This thesis does not solve audio deepfake detection.** The
  mitigated checkpoint's residual DECTE XTTS EER is 23.26 % —
  well above the training-distribution EER of 1.71 % and far
  above any operational usability threshold. The mitigation is
  an adaptation experiment under RQ3, not a deployment-grade
  detector.
- **This thesis does not rank XTTS v2 and OpenVoice v2 by human
  perceptual naturalness.** The reported EERs are detector
  performance numbers. Whether human listeners would find one
  generator's outputs more or less convincing than the other's
  is a separate research question not addressed here.
- **This thesis does not provide a production-ready detector.**
  Neither the baseline AuralGuard-AASISTPP nor the mitigated v2
  checkpoint should be used to make security or fraud decisions
  in a deployment setting on the basis of the numbers reported
  here. Deployment would require additional evaluation on
  application-specific corpora, calibration to
  application-specific cost models, and ongoing monitoring
  against evolving generator technology.

Each of these non-claims names a stronger claim the evidence
*does not* support — so a downstream reader who generalises
past the thesis' scope does so on their own authority, not on
the thesis'.

---

## 8.10 Summary

The four main findings of this thesis converge on a single
descriptive claim about detector behaviour that this thesis
carries into its Conclusion:

> **Detector reliability depends jointly on the corpus / domain
> of the input, on the spoof generator that produced the
> candidate spoof, and on the detector architecture — and only
> the combination of these three factors predicts the observed
> error pattern.**

Chapter 5 established the corpus-and-generator dimensions of that
joint dependence with 95 % bootstrap support on two very
different detector architectures. Chapter 6 showed that at least
one of the resulting problems (the DECTE XTTS gap on the primary
detector) is at least partially reducible by a controlled
adaptation, again with statistical support. Chapter 7 provided a
subgroup-level diagnostic view of that mitigation on the DECTE
held-out slice. Together they answer RQ1–RQ4 in the affirmative
under the specific scoping described in Section 8.7.3.

Chapter 9 concludes the thesis and sketches the follow-up work
that would extend, tighten, and stress-test these findings.

---

*End of Chapter 8 draft.*
