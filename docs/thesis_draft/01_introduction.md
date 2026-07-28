# Chapter 1 — Introduction

*Draft. Written to be read by the thesis supervisor first, then polished
into final prose. Citation keys follow the Chapter 2 style — bracketed
short keys like `[Todisco2019_ASVspoof]` that will be expanded to
full references in the polish pass.*

---

## 1.1 Opening motivation

Audio deepfakes — synthetic speech that mimics a target speaker's
voice from a short reference recording — have moved from a
research demonstration to a routine capability of publicly
available voice-cloning systems in the last few years
[Casanova2024_XTTS] [Qin2023_OpenVoice]. Zero-shot cloning
pipelines that once required a specialist ML team can now be run
from open-source libraries with a handful of lines of code, and
the output quality is high enough that a listener without prior
context can plausibly mistake it for genuine speech. The
detection side of that story has developed in parallel: the
anti-spoofing and audio-deepfake-detection literature has
produced a series of shared benchmarks and detector architectures
that report very low error rates on the challenge conditions
they were designed against [Todisco2019_ASVspoof]
[Yamagishi2021_ASVspoof2021] [Yi2022_ADD].

However, low error on a benchmark is not the same as reliability
in the field. Recent cross-domain analyses have shown that
detectors trained on one source distribution often generalise
poorly to another — to unseen recording conditions, unseen
speaker populations, or unseen spoof-generator families
[Li2024_CrossDomainADD] [Muller2024_HarderDifferent]. A separate
line of speech-technology research has documented that speech
systems trained predominantly on standard-accent material can
perform unevenly on dialectal or non-standard-accent speech
[Koenecke2020_ASRDisparities] [Serditova2025_NewcastleASR],
though almost all of that work is about automatic speech
recognition rather than about anti-spoofing.

Putting those two literatures next to each other raises a
natural question that this thesis is built around: if
anti-spoofing detectors are already known to generalise poorly
across source datasets in the abstract, and if speech systems
are already known to behave unevenly across accents in
transcription tasks, how do audio deepfake detectors behave
specifically on dialectal / interview-style real speech — and
does the answer depend on which voice-cloning generator produced
the spoof they are asked to reject?

---

## 1.2 Problem statement

Standard anti-spoofing benchmarks are typically built from
studio-quality read speech, in a limited range of recording
conditions, and against a fixed list of spoofing systems
[Todisco2019_ASVspoof] [ASVspoof2019_Database]. Real speech that
a deployed detector might see is not distributed the same way.
It varies by dialect, by accent, by recording condition and
channel, by speaker demographics, and by the pragmatic style of
the utterance (conversation, interview, phone call, read
sentence). It is also produced by spoofing systems that may not
match any of the systems present at the detector's training
time — voice-cloning tools are released and updated on a
timescale much faster than any single anti-spoofing benchmark.

This thesis narrows that broad problem to a specific empirical
question: does the choice of *corpus* (specifically, dialectal
Tyneside DECTE versus standard-accent English VCTK) change how a
modern anti-spoofing detector behaves on the spoofed audio it
must reject, and does the observed change depend on which
voice-cloning generator produced the spoof? Because the two
corpora used here differ on several axes at once — dialect,
recording style, channel quality, speaker demographics — the
observed effect is described throughout the thesis as a
**dialect / domain gap** rather than as a "pure dialect bias".
That phrasing is a deliberate discipline: the evidence in this
thesis supports the former, not the latter, and Chapter 8
explains at length why.

---

## 1.3 Research aim

The aim of this thesis is to measure whether dialect / domain
and generator choice affect an audio anti-spoofing detector's
error behaviour, and to test whether a small controlled
adaptation of the detector can reduce the clearest observed gap.

Concretely, the thesis reports a four-part study on the same
underlying material:

- a **corpus comparison** between DECTE (Tyneside dialectal /
  interview-style English) and VCTK 0.92 (a standard-accent
  English control), holding the detector and generator fixed;
- a **generator comparison** between XTTS v2 [Casanova2024_XTTS]
  and OpenVoice v2 [Qin2023_OpenVoice] under identical
  evaluation conditions;
- a **cross-detector replication** using a hand-crafted-feature
  LFCC + Logistic Regression classifier alongside the primary
  AuralGuard-AASISTPP wrapper around AASIST [Jung2022_AASIST];
  and
- a **controlled adaptation experiment** — mitigation v2, a
  partial-backbone fine-tune of the primary detector on a
  leakage-safe DECTE speaker split — evaluated on a held-out
  DECTE test slice and a VCTK out-of-training-domain guardrail.

A subgroup diagnostic layer over the mitigation slice is added
as an appendix-style descriptive analysis. Every headline number
in the study is reported with a 95 % non-parametric bootstrap
confidence interval computed under a single fixed protocol so
that all reported quantities are directly comparable.

---

## 1.4 Research questions

Four research questions structure the empirical work.

- **RQ1.** Does DECTE dialect / domain speech create a
  measurable detection gap compared with VCTK English-control
  speech?
- **RQ2.** Does this corpus gap depend on the spoof generator?
- **RQ3.** Can a targeted, controlled mitigation reduce the
  DECTE XTTS detection gap?
- **RQ4 (supporting robustness / replication question).** Do the
  main corpus-gap patterns persist across detector architectures?

RQ4 is framed as a *robustness check* on RQ1 and RQ2 rather than
as a separate central thesis: it would only weaken the RQ1 / RQ2
story if the patterns failed to replicate on a second detector,
and it does not stand alone.

---

## 1.5 Method overview

The full experimental setup is documented in Chapter 3 and
verified in Chapter 4. In brief:

- **Two speech corpora.** DECTE and VCTK 0.92 provide,
  respectively, dialectal / interview-style Tyneside speech and
  a loose-English-accent standard-accent control drawn from a
  20-speaker VCTK slate.
- **Two voice-cloning generators.** XTTS v2 (an end-to-end
  zero-shot TTS system) and OpenVoice v2 (a two-stage system
  combining MeloTTS synthesis with a tone-colour converter)
  represent two different design philosophies inside the
  contemporary zero-shot voice-cloning space.
- **Two detectors.** A primary AuralGuard-AASISTPP wrapper
  around the AASIST backbone [Jung2022_AASIST] and a secondary
  LFCC + Logistic Regression classifier are used together
  specifically so that a same-direction finding on both can rule
  out the interpretation that a given result is an
  architecture-specific artefact.
- **Bootstrap 95 % confidence intervals** on every headline
  quantity, using 1000 iterations and a fixed base seed so the
  intervals reported in different chapters are directly
  comparable.
- **Controlled adaptation** — mitigation v2 — evaluated on a
  leakage-safe held-out DECTE speaker split and against a VCTK
  out-of-training-domain guardrail, with the in-domain sanity
  check from Chapter 4 rerun on the mitigated checkpoint as a
  catastrophic-forgetting safeguard.
- **Subgroup diagnostics** on the same held-out slice, reported
  as descriptive per-metadata point estimates rather than as a
  formal fairness audit.

---

## 1.6 Main contributions

Five main contributions organise what the thesis puts on
record. Additional pipeline verification and reproducibility
work is treated as methodology or as an appendix rather than as
a standalone contribution.

1. **A DECTE–VCTK evaluation benchmark for dialect / domain
   effects on audio deepfake detection.** A leakage-safe,
   matched-N, bootstrap-supported protocol for evaluating an
   anti-spoofing detector on Tyneside dialectal speech against a
   standard-accent VCTK control, with per-cell 95 % confidence
   intervals and paired-original bonafide selection (Chapters 3
   and 5).
2. **A cross-generator finding — a generator-specific corpus
   interaction.** XTTS v2 shows a positive DECTE − VCTK EER gap
   (DECTE harder); OpenVoice v2 reverses the direction (VCTK
   harder). The two generators do not fail the detector the
   same way, and the reversal cannot be explained as a dialect
   effect (Chapter 5).
3. **Cross-detector replication.** Both the XTTS gap and the
   OpenVoice reversal reproduce on a hand-crafted-feature +
   Logistic-Regression detector — an architecturally very
   different second detector — with same-direction 95 %
   bootstrap CIs. The direction split by generator is therefore
   not specific to the AASIST architecture (Chapter 5).
4. **A statistically supported controlled adaptation.** A
   conservative partial-backbone unfreeze of the AuralGuard-
   AASISTPP detector significantly reduces held-out DECTE XTTS
   error rate without a statistically significant VCTK
   regression, and without failing the in-domain sanity check
   from Chapter 4 (Chapter 6).
5. **Sociolinguistic subgroup diagnostics.** On the held-out
   DECTE slice, mitigation v2 improves every main-table subgroup
   (gender, age band, recording era), with substantial spread in
   magnitude. Reported as descriptive diagnostics, not as a
   formal fairness audit (Chapter 7).

The thesis does not claim any of these as first-of-a-kind
results. Cross-domain robustness for anti-spoofing has already
been established in the recent literature
[Li2024_CrossDomainADD] [Muller2024_HarderDifferent]; dialectal
speech-technology bias has already been documented for automatic
speech recognition [Koenecke2020_ASRDisparities]. What this
thesis contributes is the specific bridge between those two
existing concerns, at the specific scope of the corpora,
generators, and detectors described in Chapter 3.

---

## 1.7 Scope and non-claims

Given the size of the empirical slices, the scope of the
detectors, and the sensitivity of the topic, several explicit
non-claims are worth stating up front so a reader coming to the
results in Chapters 5–7 knows what the thesis is *not* claiming.

- The thesis **does not prove that dialect alone causes detector
  failure.** DECTE and VCTK differ on multiple simultaneous axes
  (dialect, recording style, channel, age distribution,
  transcript pipeline); the safe empirical claim is a *dialect /
  domain gap* claim, not a pure dialect-causality claim
  (Chapter 8, Section 8.6).
- The thesis **does not prove that the detector is biased
  against any protected group.** Chapter 7's subgroup diagnostic
  is descriptive on a 16-speaker held-out slice and does not
  attach per-subgroup bootstrap intervals; fairness claims of
  the shape "the detector is biased against group X" are not
  supported by that evidence.
- The thesis **does not rank XTTS v2 and OpenVoice v2 by human
  perceptual naturalness.** The reported EERs are detector
  performance numbers; whether human listeners would find one
  generator's outputs more or less convincing is a separate
  research question.
- The thesis **does not provide a production-ready detector.**
  The mitigated v2 checkpoint reduces DECTE XTTS error but
  remains far above the training-distribution EER; it is an
  adaptation experiment under RQ3, not a deployment-grade
  system.
- The thesis **studies detection behaviour under controlled
  experimental conditions.** It does not evaluate real-world
  deployment scenarios (compression, telephone channel, ambient
  noise, social-media re-encoding), and it does not calibrate to
  application-specific cost models.

Each non-claim corresponds to a claim shape the evidence does
*not* support at the strength required. A reader who would like
to generalise past the thesis' scope is doing so on their own
authority, not on the thesis' authority.

---

## 1.8 Thesis structure

The remainder of the thesis is organised as follows.

- **Chapter 2 — Background and Related Work.** Introduces the
  four research areas needed to read the rest of the thesis:
  anti-spoofing benchmarks and metrics, detector architectures
  (classical LFCC / CQCC baselines and modern neural systems),
  zero-shot voice-cloning systems, cross-domain robustness in
  anti-spoofing, and dialect / accent effects in speech
  technology. It closes with the specific research gap this
  thesis addresses.
- **Chapter 3 — Data and Methodology.** Describes the two
  corpora (DECTE, VCTK), the two generators (XTTS v2, OpenVoice
  v2), the two detectors (AuralGuard-AASISTPP, LFCC + LR), the
  evaluation protocol, the bootstrap methodology, the mitigation
  training protocol, and the subgroup diagnostic protocol.
- **Chapter 4 — Detector Verification and Experimental Setup.**
  Documents the correctness-check step: why detector verification
  was necessary, the specific checkpoint-loading correction
  applied to the primary detector, the shared audio preprocessing
  and score-direction convention across both detectors, and the
  in-domain sanity check that must pass before any DECTE / VCTK
  number is interpreted.
- **Chapter 5 — Corpus × Generator Analysis with Statistical
  Support.** The main empirical chapter: reports the AASIST XTTS
  corpus gap, the LFCC + LR XTTS replication, the AASIST
  OpenVoice reversal, the LFCC + LR OpenVoice reversal, and the
  combined 2 × 2 × 2 result table. Answers RQ1, RQ2, and RQ4.
- **Chapter 6 — Mitigation Experiment.** Reports the controlled
  partial-backbone fine-tune (mitigation v2), the held-out
  DECTE XTTS result, the VCTK guardrail, the post-mitigation
  in-domain sanity check, and the paired-bootstrap CI on the
  mitigation effect. Answers RQ3.
- **Chapter 7 — Subgroup Diagnostics.** Descriptive per-metadata
  view of the same mitigation on the DECTE held-out slice, by
  gender, age band, and recording era. Reported explicitly as
  diagnostic, not as a fairness audit.
- **Chapter 8 — Discussion, Limitations, and Threats to
  Validity.** Interpretation of the four main findings together;
  standard four-plus-one threats-to-validity discussion;
  practical implications for anti-spoofing evaluation practice;
  and an explicit list of what the thesis does *not* claim.
- **Chapter 9 — Conclusion and Future Work.** Restates the
  research-question answers, the main contributions, and the
  practical implications, and sketches the follow-up studies
  that would broaden the external validity of the findings.

---

*End of Chapter 1 draft.*
