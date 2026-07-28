# Chapter 2 — Background and Related Work

*Draft. Written to be read by the thesis supervisor first, then polished
into final prose. Every paper-specific claim carries a `[citation
needed]` placeholder; the working bibliography for this thesis is
tracked separately and the correct reference will be slotted in
during the final polish pass.*

---

## 2.1 Chapter overview

This chapter introduces the research areas needed to understand the
rest of the thesis. It is structured around four blocks that the
later chapters will draw on individually:

- **Audio deepfake detection and anti-spoofing** — the task, the
  standard benchmarks, and the metrics used to evaluate detectors
  (Section 2.2).
- **Detector architectures** — the classical hand-crafted feature
  baselines and the modern neural end-to-end systems (AASIST in
  particular), which together correspond to the two detectors this
  thesis evaluates (Section 2.3).
- **Speech synthesis and voice cloning** — the modern zero-shot
  voice-cloning systems that produce the spoofed audio a
  contemporary anti-spoofing detector must reject, including the
  two generators (XTTS v2 and OpenVoice v2) used in this thesis
  (Section 2.4).
- **Cross-domain robustness and dialect / accent effects in speech
  technology** — the two literatures that most directly motivate
  the thesis' research questions (Sections 2.5 and 2.6).

Sections 2.7 and 2.8 briefly describe the corpora relevant to this
thesis (DECTE and VCTK) and articulate the specific research gap
the thesis addresses; Section 2.9 closes the chapter by connecting
the background to the thesis' research questions from Chapter 1.

---

## 2.2 Audio deepfake detection and anti-spoofing

Audio anti-spoofing — sometimes called synthetic-speech detection
or, in more recent framings, audio deepfake detection — is the
task of deciding whether a given audio clip is a genuine ("bonafide")
recording of a human speaker or a synthetic ("spoof") clip produced
by some text-to-speech (TTS), voice-conversion (VC), or replay
system. The task sits alongside speaker verification and speech
synthesis in the broader speech-technology literature but is
distinct from both: unlike speaker verification, it does not need
to identify *who* is speaking; unlike synthesis, its objective is
to detect artefacts rather than to generate speech.

The most influential benchmark series in this area is the ASVspoof
challenges. **ASVspoof 2019** [Todisco2019_ASVspoof] introduced two
main scenarios — logical access (LA), covering TTS and VC attacks,
and physical access (PA), covering replay attacks — together with
a shared evaluation protocol and the two headline metrics that
almost every subsequent paper uses: the **equal-error rate (EER)**,
which reports the operating point at which the false-accept and
false-reject rates coincide on the receiver-operating-characteristic
curve, and a tandem detection cost function (t-DCF) that combines
spoofing-detection cost with speaker-verification cost. The database
paper [ASVspoof2019_Database] describes the actual protocol,
speaker splits, and baseline systems (LFCC-GMM and CQCC-GMM
baselines are shipped with the challenge material) in detail.

**ASVspoof 2021** [Yamagishi2021_ASVspoof2021] extended the
challenge in two directions relevant to this thesis. First, it
added a **deepfake detection track** that scored systems on
transmitted / compressed audio, reflecting the more realistic
deployment condition in which detectors see audio degraded by
codecs, telephone channels, or lossy transmission. Second, it
introduced ***in-the-wild* evaluation** conditions
[Liu2022_ASVspoofInTheWild] that specifically probed whether
detectors trained on one source dataset generalise to another —
a question later chapters of this thesis pick up under the label
*cross-corpus generalisation*.

The **ADD (Audio Deepfake Detection) challenges** [Yi2022_ADD]
broadened the field beyond the ASVspoof framing. ADD 2022 added
tracks for low-quality and partially-fake audio, and ADD 2023
[Yi2023_ADD] added tracks for manipulation-region localisation
and for *algorithm or source recognition* — the task of
identifying which specific synthesis algorithm produced a given
spoof. The algorithm-recognition framing is directly relevant to
this thesis' RQ2, which asks whether the choice of spoof
generator materially changes detector behaviour.

A recurring finding in the ASVspoof and ADD literatures is that
detectors that perform very well on the challenge's own evaluation
set can still perform noticeably worse on unseen spoofing
attacks, unseen source datasets, or unseen channel conditions
[Li2024_CrossDomainADD]. This *cross-condition* or *cross-domain*
generalisation problem is what Section 2.5 discusses in more
depth; it is also the problem that most closely maps onto this
thesis' DECTE-vs-VCTK evaluation design.

---

## 2.3 Detector architectures for spoof detection

Anti-spoofing systems in the literature roughly divide into two
families: **classical hand-crafted-feature systems** with
statistical classifiers, and **end-to-end neural systems** that
learn features from raw or lightly-preprocessed audio. Both
families remain in use as of the writing of this thesis, and
both are represented in the two detectors this thesis evaluates.

### 2.3.1 Classical feature-based systems

Classical anti-spoofing baselines typically pair a **spectral or
cepstral front-end** with a **statistical classifier**. The two
most common front-ends in the ASVspoof lineage are Linear
Frequency Cepstral Coefficients (**LFCC**) — which resample a
short-time spectrum onto a linear (rather than perceptually
warped) frequency axis before a discrete cosine transform — and
Constant-Q Cepstral Coefficients (**CQCC**) [Todisco2017_CQCC],
which use a constant-Q transform whose frequency resolution scales
with frequency and is argued to capture manipulation artefacts
that a mel-scale front-end may smooth over.

Historically, both feature families were paired with a Gaussian
Mixture Model (GMM) classifier fit on bonafide and spoof
utterances separately, producing a log-likelihood-ratio score
[Todisco2019_ASVspoof]. The ASVspoof challenges continue to ship
LFCC-GMM and CQCC-GMM systems as reference baselines
[ASVspoof2019_Database]. Simpler but useful variants replace the
GMM with a logistic regression or a support-vector machine over
a fixed-length pooled feature vector.

Classical systems are typically *weaker* than modern neural
end-to-end systems on standard benchmarks, but they have three
properties that make them useful as a **secondary detector** in
cross-architecture studies: they are convex or near-convex in
their training objective (so training is reproducible and
determinisitic to seed), they have very few hyperparameters, and
their feature pipeline is transparent and inspectable. This
thesis' secondary detector — LFCC + logistic regression, described
in Chapter 3, Section 3.4.2 — uses this family for exactly these
reasons.

### 2.3.2 Neural end-to-end systems

Modern anti-spoofing systems typically learn features directly
from raw waveform or from a light spectral front-end, using a
deep neural network whose parameters are trained end-to-end on a
labelled bonafide/spoof corpus. Several dozen such architectures
have been published in the ASVspoof lineage; the two most
directly relevant to this thesis are the AASIST family and its
predecessor RawGAT-ST.

**RawGAT-ST** [Tak2021_RawGATST] introduced a spectro-temporal
graph-attention network operating on raw audio, in which
spectral and temporal graph-attention layers process orthogonal
views of the input and then fuse. It was among the first end-to-
end architectures to combine graph-attention operations over both
axes of the time-frequency plane in a single model.

**AASIST** [Jung2022_AASIST] extended the graph-attention idea
with heterogeneous graph-attention layers that operate on the
concatenated spectro-temporal representation, and with a set of
learnable graph-pooling operations that produce a compact
utterance-level representation. AASIST reported strong results on
ASVspoof 2019 LA and was quickly adopted as a reference
architecture in subsequent anti-spoofing work.

For this thesis, AASIST is used as the *primary* detector — but
via the **AuralGuard-AASISTPP wrapper** described in Chapter 3,
Section 3.4.1. The wrapper adds three linear task heads on top of
AASIST's hidden features (a binary bonafide/spoof head, an
attack-type head, and an explanation head) and was fine-tuned on
a mixture of ASVspoof2019_LA, WaveFake, GLOBE, EdAcc,
EnglishDialects, and DECTE material by prior work outside this
thesis. This thesis inherits that checkpoint as its baseline
detector, verifies its loading in Chapter 4, and evaluates and
adapts it in Chapters 5–7.

### 2.3.3 Why this thesis uses both

The pair — a deep AASIST-family detector as primary, an LFCC +
logistic regression as secondary — was chosen so that a same-
direction finding on both detectors could rule out the
architecture-specific-artefact reading. The two detectors differ
on nearly every architecturally-meaningful axis (feature
representation, model family, optimisation regime, capacity), so
if a corpus- or generator-level gap appears on *both* of them
under identical evaluation conditions, that gap is very unlikely
to be a specific quirk of either architecture. Chapter 5 uses
this cross-architecture check for both the XTTS and the
OpenVoice corpus comparisons.

---

## 2.4 Speech synthesis and voice cloning systems

The spoof-side of the anti-spoofing task is currently dominated
by **zero-shot voice-cloning** TTS models: systems that can
produce speech in a target speaker's voice given a short reference
clip and a text prompt, without any per-speaker fine-tuning. The
last five years have seen substantial improvements in both the
audio quality and the speaker-similarity of such systems, and the
two used in this thesis (XTTS v2 and OpenVoice v2) are recent
representatives of two different design philosophies inside this
family.

### 2.4.1 The two generators used in this thesis

**XTTS v2** [Casanova2024_XTTS] is a **massively multilingual
zero-shot TTS model** developed by Coqui and released as part of
the Coqui TTS library. It takes a short reference audio clip and
a text prompt and produces speech in the reference speaker's
voice as an end-to-end generative TTS system. XTTS was chosen as
one of the two generators in this thesis because it represents
the *single-model end-to-end zero-shot* design philosophy — one
network learns the full mapping from text plus reference to
output waveform.

**OpenVoice v2** [Qin2023_OpenVoice] takes a different design
approach: it separates the task into two stages, a base TTS model
(MyShell's MeloTTS in this thesis' setup) that produces speech in
a fixed base voice given the text, and a **tone-colour converter**
that retargets the tone colour of the base audio to match the
target speaker's reference clip. OpenVoice was chosen as the
second generator because this two-stage design contrasts with
XTTS's end-to-end one, and because it is a widely available and
actively maintained representative of the tone-colour-conversion
family.

### 2.4.2 Broader context

Several other zero-shot voice-cloning systems form the broader
context in which XTTS and OpenVoice sit. **YourTTS**
[Casanova2022_YourTTS] was an earlier zero-shot multi-speaker TTS
system built on the VITS architecture and remains a common
baseline for zero-shot voice conversion. **VALL-E**
[Wang2023_Valle] introduced neural codec language models to the
zero-shot TTS setting, treating speech synthesis as an
autoregressive next-token prediction problem over discrete
neural codec tokens and producing state-of-the-art speaker
similarity at the time of publication. **Voicebox**
[Le2023_Voicebox] and related large-scale generative-speech
systems from Meta AI represent the current frontier of
multilingual multi-task speech generation.

This thesis does not evaluate on any of YourTTS, VALL-E, or
Voicebox — it uses only XTTS v2 and OpenVoice v2. The broader
context matters because the OpenVoice-specific corpus reversal
observed in Chapter 5 raises the natural question of whether
similar generator-specific interactions would appear under other
recent voice-cloning systems. Chapter 9 flags this as future
work.

### 2.4.3 Why generator choice matters for detection

An important qualitative point that recurs in the anti-spoofing
literature is that **different generation systems leave different
detectable artefacts** [Frank2021_WaveFake]. Vocoder-based systems
tend to leave characteristic phase and spectral-envelope
artefacts; end-to-end neural systems may leave systematic biases
in specific frequency bands; tone-colour-conversion pipelines
may introduce mismatches at the speaker-identity level while
producing very high per-frame audio quality. Complementing this,
the **WaveFake** dataset [Frank2021_WaveFake] specifically
catalogues audio generated by multiple different architectures
and shows that anti-spoofing detectors' error patterns vary
substantially across generator families.

For this thesis, that observation supplies the motivation for
running the DECTE-vs-VCTK comparison under *two* generators
rather than one. If XTTS v2 and OpenVoice v2 leave qualitatively
different artefacts, the same detector may see them as
qualitatively different problems — and the interaction of those
different problems with the two corpora is exactly what Chapter 5
measures.

---

## 2.5 Cross-domain and cross-generator robustness

A recurring finding in the recent anti-spoofing literature is
that detectors performing very well on their training and
evaluation distributions still generalise poorly to unseen
domains: unseen recording conditions, unseen source datasets,
unseen speaker populations, or unseen spoof-generator families
[Li2024_CrossDomainADD]. This cross-domain generalisation problem
is directly relevant to this thesis, which reports a similar
generalisation failure under a dialect / domain shift
specifically.

**Li et al. (2024) — Cross-Domain Audio Deepfake Detection**
[Li2024_CrossDomainADD] presents a dataset and analysis that
focus specifically on this failure mode. The paper argues that
audio-deepfake detectors face substantial cross-domain
generalisation problems, especially against recent zero-shot TTS
models, and reports large EER increases when a detector trained
on one source dataset is evaluated on another. That result is
what the DECTE-vs-VCTK comparison in this thesis' Chapter 5
extends to a specific dialect / domain condition.

**Müller et al. (2024) — Harder or Different?**
[Muller2024_HarderDifferent] adds a subtler point. The paper
argues that performance drops on newer or unseen fakes should not
be uniformly attributed to "newer fakes are harder"; rather, the
drops often reflect that newer fakes are *different* in ways that
the detector's training distribution did not cover. That framing
matches this thesis' OpenVoice reversal in Chapter 5: OpenVoice
v2's failure mode against the primary detector is not that
OpenVoice is a more sophisticated attack than XTTS v2 (it is not
obviously more sophisticated), but that its outputs interact
differently with the detector under different corpora — a
*"different, not harder"* effect specialised to the corpus ×
generator crossing.

Other relevant work on generalisation includes proposals for
adversarial-training or meta-learning approaches to make
detectors more robust to unseen spoofing attacks
[WangHansen2024_MetaRobustness], and work on generator-
fingerprinting techniques that attempt to identify the specific
generator responsible for a given spoof
[Gasenzer2023_GeneralizingDeepAudioFake]. This thesis does not
evaluate those specific approaches; the mitigation study in
Chapter 6 uses a much more modest **partial-backbone-unfreeze
fine-tune** rather than a full adversarial-training or
meta-learning regime.

The specific extension this thesis contributes to the
cross-domain literature is to hold *detector*, *generator*, and
*evaluation protocol* fixed and vary only the *corpus*, then to
hold everything fixed except the *generator*, then to repeat the
whole design under a *second detector*. Section 2.8 states this
extension as a research gap.

---

## 2.6 Dialect, accent, and speech-technology reliability

Uneven performance across accents, dialects, and speaker groups
is a well-documented problem in speech technology — but the
existing literature is heavily concentrated on **automatic
speech recognition (ASR)** rather than anti-spoofing.

**Koenecke et al. (2020) — Racial Disparities in Automated Speech
Recognition** [Koenecke2020_ASRDisparities] is the most-cited
demonstration of this problem. The paper reports substantial word-error-rate
disparities between white and Black American speakers across five
major commercial ASR systems and links those disparities to
pronunciation and prosodic differences that the systems' training
data did not adequately cover. The paper is not about
anti-spoofing, but the underlying methodological pattern — that a
speech-technology system can perform well on its benchmark
distribution while performing unevenly across demographic
subgroups when deployed on more diverse speech — is directly
applicable to the setting this thesis studies.

**Serditova, Tang and Steffens (2025) — Automatic Speech
Recognition Biases in Newcastle English** [Serditova2025_NewcastleASR]
extends this line of work to the specific dialect the current
thesis is empirically anchored on. The paper studies ASR
performance on Newcastle English and argues for greater dialectal
diversity in speech-technology evaluation. A follow-up paper by
Serditova and Tang [SerditovaTang2026_NewcastleASR] uses DECTE —
the same corpus this thesis uses — for a sociolinguistic analysis
of Newcastle-English ASR error patterns. Both papers motivate the
current thesis by showing that Tyneside English is a dialect
where speech-technology reliability has been documented as
uneven; neither, however, evaluates anti-spoofing performance
specifically.

Related evaluations of accent effects in ASR include work
comparing off-the-shelf recognisers across accented English
dialogue speech [Aksenova2022_AccentASR] and benchmarks
specifically designed for Indian-accented English ASR
[Javed2023_Svarah]. All
these papers are consistent with a broader picture in which
speech-technology systems trained predominantly on standard-
accent speech generalise unevenly to non-standard-accent speech.

**A note on scope.** Most prior dialect / accent work in speech
technology is about ASR performance (transcription accuracy),
not about anti-spoofing performance (deepfake detection). This
thesis studies detection performance and does not measure
transcription accuracy. The relevance of the ASR-bias literature
to the current thesis is therefore as **motivation and precedent**
— *if* speech-technology systems have been documented to
perform unevenly across dialects for one task (ASR), *then* it
is reasonable to ask whether the same pattern extends to
another task (anti-spoofing) — but the results of this thesis
neither replicate nor refute the ASR-bias findings; they extend
the *underlying concern* to a different task. Chapter 8's
discussion of "dialect / domain gap" wording is careful about
this distinction.

---

## 2.7 Corpora relevant to this thesis

Chapter 3 describes the data preparation and evaluation protocol
for both corpora in full. This section only introduces them
briefly, so a reader coming from the related-work sections above
has enough context to follow the methodology chapter.

**DECTE — the Diachronic Electronic Corpus of Tyneside English**
[Corrigan_DECTE] — is a research-restricted corpus of interview-
style speech from speakers in the Tyneside region of North-East
England. It combines the older **NECTE** (Newcastle Electronic
Corpus of Tyneside English) [Allen2007_NECTE] with newer material
collected in subsequent survey waves. The recordings span
several decades — 1960s–1970s reel-to-reel material, a 1990s
follow-up, and a 2007–2011 modern digital survey — which makes
DECTE a corpus of both dialectal *and* diachronic variation.
Chapter 3 uses the metadata extracted from DECTE's TEI-XML
transcripts (gender, age band, recording era) to support the
subgroup diagnostic in Chapter 7.

**VCTK 0.92** [Veaux2017_VCTK] is a widely-used English
multi-speaker corpus of studio-read speech, recorded at 48 kHz
and containing approximately 110 speakers with per-speaker
accent metadata. This thesis uses a 20-speaker subset filtered
to speakers whose `ACCENTS` field is `"English"` as a
standard-accent control condition against which DECTE's
dialectal / interview-style speech is compared. Chapter 3,
Section 3.2.2 documents the exact selection and its known
composition properties (13 southern speakers, 7 non-southern, an
age-band skew toward 21–30).

DECTE and VCTK were chosen because they represent, respectively,
the type of speech the thesis' research question is *about*
(dialectal, interview-style, from a specific non-standard region)
and the type of speech that a modern anti-spoofing detector is
most likely to have seen at training time (studio-clean, mostly
standard-accent English). The comparison between them is the
whole empirical spine of Chapter 5.

Two additional datasets appear in this thesis' machinery without
being subjects of study. **WaveFake** [Frank2021_WaveFake] is a
publicly available audio-deepfake dataset covering multiple
generation architectures; it appears here because it is part of
the training mixture the AuralGuard baseline detector was
originally fine-tuned on. The **AuralGuard training CSV** used to
verify the primary detector in Chapter 4 and to fit the LFCC + LR
secondary detector in Chapter 5 draws from a mixture of
ASVspoof2019_LA, WaveFake, GLOBE, EdAcc, EnglishDialects, and
DECTE material.

---

## 2.8 Research gap

Combining the four background sections above, the specific gap
this thesis addresses can be stated concisely.

Existing audio-deepfake work has studied:

- **spoofing attacks** in isolation (which generation systems
  produce hard-to-detect audio; ASVspoof + ADD lineage);
- **detector architectures** (which model families work best on
  clean benchmark distributions; AASIST, RawGAT-ST, LFCC / CQCC
  baselines);
- and, in the last two years, **cross-domain robustness**
  (whether detectors generalise across source datasets,
  channels, and generator families; Cross-Domain ADD and Harder
  or Different).

Separately, the speech-technology-reliability literature has
documented that ASR systems can perform unevenly across
dialects and demographic subgroups (Koenecke et al.;
Serditova / Tang; accent-ASR benchmarks).

What has not been deeply examined is the intersection of these
two literatures: **dialect / domain speech as a reliability
factor specifically for audio deepfake detection**. This thesis
addresses that gap in two connected ways.

First, it evaluates whether the well-documented ASR-side pattern
— speech-technology systems performing unevenly on dialectal /
non-standard speech — extends to audio anti-spoofing, by
comparing an anti-spoofing detector's behaviour on Tyneside
DECTE against its behaviour on standard-accent VCTK under the
same generator, same protocol, and same audio preprocessing
(Chapter 5).

Second, it explicitly asks whether the observed effect depends
on the choice of spoof generator, by running the whole comparison
twice — once with XTTS v2 and once with OpenVoice v2 — and
comparing the results (Chapter 5). This is what motivates the
**2 corpora × 2 generators × 2 detectors** design that Chapters 5
and 8 refer to as the *2 × 2 × 2 structure*.

The thesis then adds two complementary contributions on top of
the measurement: a **cross-detector replication** using the
classical LFCC + LR baseline described in Section 2.3 (Chapter 5),
and a **controlled mitigation experiment** using partial-backbone
fine-tuning of the primary detector (Chapter 6), followed by a
descriptive **subgroup diagnostic** view of the mitigation on
DECTE metadata (Chapter 7).

The thesis does *not* claim to be the first to identify
cross-domain robustness as an anti-spoofing problem — the
Cross-Domain ADD and Harder or Different papers already do that
— and it does not claim to be the first to identify dialectal
speech-technology bias — the ASR-bias literature does that.
What it contributes is the specific bridge between those two
existing concerns, at the specific scope of the corpora,
generators, and detectors described in Chapter 3.

---

## 2.9 Summary

This chapter has introduced the four background areas the rest
of the thesis draws on: audio anti-spoofing benchmarks and
metrics (Section 2.2), classical and neural detector architectures
(Section 2.3), zero-shot voice-cloning generation systems
(Section 2.4), and the two prior-work strands most relevant to
this thesis — cross-domain robustness in anti-spoofing
(Section 2.5) and dialect / accent effects in speech-technology
reliability (Section 2.6). Sections 2.7 and 2.8 briefly framed
the corpora and articulated the specific research gap this
thesis addresses.

At the highest level, the connection to the thesis' research
questions is as follows. This thesis evaluates whether DECTE-
style dialect / domain speech changes an audio-deepfake
detector's performance (RQ1), whether that effect depends on
which spoof generator produced the audio (RQ2), whether a
conservative, targeted adaptation of the detector can reduce the
clearest gap (RQ3), and whether the main corpus-gap patterns
persist under a very different detector architecture (RQ4).

Chapter 3 describes the corpora, generators, detectors, and
evaluation protocol in full. Chapter 4 verifies the primary
detector's loading and score-direction convention before any
downstream numbers are interpreted. Chapters 5–7 report the
empirical results, and Chapter 8 discusses them.

---

*End of Chapter 2 draft.*
