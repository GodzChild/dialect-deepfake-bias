# Chapter 4 — Detector Verification and Experimental Setup

*Draft. Written to be read by the thesis supervisor first, then polished
into final prose. All quantitative claims trace back to a specific
Entry in `docs/THESIS_FINDINGS_LOG.md` and to a specific committed
script under `scripts/`.*

---

## 4.1 Why detector verification was necessary

Every downstream claim in this thesis — the DECTE-vs-VCTK corpus
gaps in Chapter 5, the mitigation effect in Chapter 6, and the
subgroup diagnostics in Chapter 7 — is a claim *about a specific
detector's behaviour on specific audio*. If the detector is not the
one it is stated to be, or if the score it produces is not what the
metric functions think it is, then every EER, AUC, and confidence
interval derived from it is meaningless. Detector verification is
not a formality here — it is a requirement for everything else
in the empirical part of the thesis.

Two failure modes are especially dangerous here, because they
can be silent — the pipeline runs to completion and produces
plausible-looking numbers even though the underlying detector is
broken:

1. **A checkpoint that fails to load correctly** but does not raise
   an error. PyTorch's `load_state_dict(state, strict=False)`
   silently ignores unmatched keys. If the checkpoint keys do not
   match the model class, `strict=False` can load *zero* trained
   tensors while returning normally, leaving the model running at
   its random initialisation.
2. **A score-direction mismatch.** If the detector's score is
   interpreted as "higher = more likely fake" while the metric
   functions expect "higher = more likely bonafide", the AUC and
   EER will still compute — but the AUC will drop below 0.5 and
   the reported EER will be far from the model's true performance.

Both failure modes were encountered during the early phase of this
work (Entry 1). This chapter documents how each was diagnosed,
what the correction consisted of, and how the corrected pipeline
was validated against an independent reference before any
DECTE / VCTK numbers were interpreted.

---

## 4.2 The original checkpoint-loading issue

The primary detector used in this thesis is the AuralGuard-AASISTPP
wrapper around the AASIST backbone \cite{Jung2022_AASIST}, described in
Chapter 3, Section 3.4.1. The pre-trained checkpoint
`auralguard-aasistpp/results/final_accent_globe_wavefake_balanced_full/
best.pt` stores 235 named tensors, all of which are namespaced under
the `AuralGuardAASISTPP` module structure — for example
`backbone.encoder.0.0.conv1.weight`, `binary_head.weight`,
`attack_head.bias`, and so on.

The original implementation of `AASISTDetector.load()` in
`src/evaluation/detectors.py` (before this thesis' correction)
constructed a *raw* AASIST model class from the official
`clovaai/aasist` repository, whose parameter names have no
`backbone.` prefix (for example `encoder.0.0.conv1.weight` rather
than `backbone.encoder.0.0.conv1.weight`). It then called
`load_state_dict(state, strict=False)` on this raw model. Because
`strict=False` treats unmatched keys as a warning rather than an
error, the load returned normally, but every single one of the
235 checkpoint tensors was silently discarded — none of them
matched the model's namespaced expectations.

The consequence was a model in its random initialisation. Because
AASIST's forward path terminates in a bounded softmax, a random-
init model does not produce *nonsense* output; it produces
*near-constant* output. In the first DECTE / VCTK evaluation, the
detector's score across 667 files ranged only over about 0.001
around a mean of roughly 0.436 (Entry 1 diagnostic prints in
`scripts/03_run_detectors.py`). Because bonafide and spoof scores
were essentially identical, the resulting AUC came out well below
0.5. The pipeline itself was working — reading audio, computing
softmax, writing metrics — but the model driving it was untrained.

Two specific diagnostics made the fault visible:

- **A per-file score-span check** printed inside
  `scripts/03_run_detectors.py`. A span of 0.001 across hundreds of
  files is not compatible with any working discriminative model on
  a mixed bonafide/spoof set. The check now aborts with a warning
  if the span is below `1e-3`.
- **A parameter-load audit** run against a fresh construction of
  the raw AASIST model, which reported `missing_keys=211` and
  `unexpected_keys=235` — that is, 235 checkpoint keys had no home
  in the raw model, and 211 model parameters were left at their
  random initialisation. This is a strict-mode-only diagnostic; it
  is invisible when `strict=False` is used silently.

---

## 4.3 The corrected AuralGuard-wrapper loading

The corrected `AASISTDetector.load()` reflects the actual structure
of the checkpoint: the trained weights belong to the wrapper, not
to the raw backbone. The correction has three parts:

1. **Instantiate the raw AASIST backbone with no checkpoint.** The
   backbone provides the untrained scaffold that the wrapper's
   trained parameters expect to sit on top of.
2. **Wrap it with `AuralGuardAASISTPP(backbone, feature_dim=160)`.**
   The wrapper adds the three trained linear task heads
   (`binary_head`, `attack_head`, `explanation_head`) alongside the
   backbone, matching the checkpoint's namespacing exactly.
3. **Load the full checkpoint into the wrapper with
   `strict=True`.** Because every checkpoint key now has a
   corresponding model parameter, `strict=True` succeeds and *any*
   remaining mismatch (for example, from a future architecture
   change) would raise a loud `RuntimeError` rather than silently
   discarding weights.

This three-line change — construct-wrap-load-strict — is the
minimum correction that guarantees the trained parameters are the
ones actually used at inference time. Deferring the `strict=True`
requirement to the wrapper (rather than the raw backbone) is what
makes it work: the wrapper's parameter set is designed to be a
bit-for-bit match to the checkpoint.

The full patched loader is in `src/evaluation/detectors.py`. It is
called by every downstream script in this thesis
(`scripts/03_run_detectors.py`, `scripts/06_indomain_sanity_check.py`,
and the two mitigation-evaluation runs), so a single correct load
propagates to every DECTE / VCTK / mitigation number.

---

## 4.4 Score direction convention

Metric functions in `src/evaluation/metrics.py` — `compute_eer`,
`compute_metrics`, `roc_auc_score` via scikit-learn — all assume the
convention

> **higher score → more likely bonafide (real)**.

This is the ASVspoof convention \cite{Todisco2019_ASVspoof} and it is the
convention every EER, AUC, and confidence interval in this thesis
is computed under. Getting the direction wrong is a classic silent
bug: EER and AUC still compute, but AUC drops below 0.5 and the
reported error rate goes toward the opposite of the model's true
performance.

The AuralGuard wrapper's `binary_head` is trained under the
*opposite* convention: `class 0 = REAL`, `class 1 = FAKE`. The
official inference reference in `auralguard-aasistpp/src/infer.py`
takes `torch.softmax(outputs["binary_logits"], dim=-1)[0, 1]`
(the fake probability) as its primary output. The thesis's detector
wrapper therefore computes:

```
score = torch.softmax(outputs["binary_logits"], dim=-1)[0, 0]
```

taking **class 0 = real (bonafide)** to match the metric functions'
"higher = bonafide" convention. Explicitly written in the
`AASISTDetector.score()` implementation.

The AuralGuard training CSVs used for the mitigation fine-tune
(Chapter 6) preserve the AuralGuard convention — `binary_label = 0`
for bonafide, `binary_label = 1` for spoof — so the training path
is unchanged. The convention flip happens only at score time, when
the wrapper's output is fed into the metric functions.

For the second detector (LFCC + Logistic Regression), the same
"higher = bonafide" convention is enforced at score time by taking
`predict_proba(...)[:, bon_col]` where `bon_col = model.classes_
.index(0)` (`sklearn` sorts classes ascending, so class 0 =
bonafide sits at column index 0). A run-time assertion in
`scripts/11_lfcc_lr_second_detector.py` verifies `model.classes_
== [0, 1]` before scoring — if `sklearn` ever changes its class-
ordering convention, the assertion will fire loudly rather than
silently emitting flipped scores.

---

## 4.5 Shared audio preprocessing

Both detectors use the same audio preprocessing at score time —
this is a deliberate methodology choice discussed in Chapter 3,
Section 3.4. In summary, every file scored by any detector in this
thesis is:

- read with `soundfile.read(..., dtype="float32",
  always_2d=True)` (bypassing torchaudio's optional torchcodec
  backend for portability);
- averaged across channels to mono;
- resampled to 16 kHz if needed;
- deterministically zero-padded or truncated to exactly 4.0 seconds
  (64,000 samples), starting from position 0 (no random crop at
  evaluation time).

Sharing preprocessing between the two detectors is what lets the
cross-architecture replication in Chapter 5 (Sections 5.5, and the
cross-detector OpenVoice reversal) be interpreted as an
architecture-level comparison rather than a preprocessing-level
comparison. If the two detectors saw different audio, any
similarity or difference between them could reflect the audio
pipeline rather than the model.

The 4-second window matches the training-time preprocessing of the
baseline AuralGuard checkpoint (recorded in the checkpoint's `args`
metadata as `duration_sec: 4.0, sample_rate: 16000`) and is
therefore not a free parameter — it is fixed by the pre-trained
model.

---

## 4.6 The in-domain sanity check

The correction described in Sections 4.3 and 4.4 is *plausible*
(the load succeeds, the score direction is documented) but not
*sufficient* — a stronger validation is required. If the corrected
loader really does put the trained weights in the right places and
the score direction really does match the metric convention, then
scoring the corrected pipeline on the checkpoint's own training-
distribution validation set should reproduce the training-time
validation EER. This is the central test.

### 4.6.1 Reference validation set

The reference set is the AuralGuard-original validation CSV
`auralguard-aasistpp/data/metadata/val_final_accent_globe_wavefake_
balanced.csv`, containing **9,514 rows**: 4,757 bonafide and 4,757
spoof (`tts_vc`), drawn from six source datasets: ASVspoof2019_LA
(6,775 rows), DECTE (1,014), WaveFake (530), EdAcc (500),
EnglishDialects (495), and GLOBE (200). This is the same
distribution the checkpoint's own training run selected `best.pt`
against, so the training-time recorded EER is a *definition* of
what the correctly-loaded model should reproduce.

The AuralGuard CSV uses the opposite label convention
(`binary_label = 0` bonafide, `binary_label = 1` spoof); the sanity-
check script translates this internally before feeding the metric
functions.

### 4.6.2 Sanity-check protocol

`scripts/06_indomain_sanity_check.py` implements the check. Two
modes are supported:

- **Sanity subsample** (default): 500 files per class (1,000
  total), stratified across the six source datasets by seed 42.
  Fast (~1 minute) and used as a first pass.
- **Full validation set**: all 9,514 files. Longer wall time
  (~8 minutes on GPU) and used to lock the final verdict.

For each file, the script resolves the audio path (either absolute
or relative to the AuralGuard project root, handling all three
path formats present in the CSV), scores it with the corrected
`AASISTDetector`, and accumulates the scores into per-class arrays.
The metric functions from `src/evaluation/metrics.py` then produce
EER, AUC, accuracy, FAR, and FRR — the same metric functions used
for every DECTE / VCTK number in later chapters.

### 4.6.3 Sanity-check verdict thresholds

The script encodes explicit thresholds for the verdict, so the
check is a pass/fail gate rather than a subjective judgement:

- **PASS**: overall EER ≤ 5 %. The corrected loader is consistent
  with the training-time behaviour.
- **PARTIAL**: 5 % < EER ≤ 15 %. Detector discriminates but not as
  well as its training-time metrics would suggest. Some drift
  remains — worth investigating preprocessing / audio decoding
  before publishing downstream numbers.
- **FAIL**: EER > 15 %. Detector fails on its own in-domain
  validation set. DECTE / VCTK numbers under this checkpoint
  cannot be interpreted as domain-transfer difficulty; the
  pipeline is broken and must be fixed first.

The 5 % threshold is deliberately loose. A perfectly-loaded
detector should reproduce its training-time EER to within
fractions of a percentage point; a 5 % ceiling therefore has
significant headroom for benign preprocessing or numerical drift.
Any DECTE / VCTK number in later chapters is contingent on this
threshold having been met.

### 4.6.4 Verdict

Both the sanity subsample and the full validation set were
scored with the corrected loader. Both runs returned **PASS**.
The full in-domain sanity check achieved **1.71 % EER**, which
was close to the checkpoint's saved validation result and passed
the predefined ≤ 5 % verification threshold. The overall AUC was
near-perfect. The per-dataset breakdown and the exact sanity-
subsample numbers are logged in Entry 3 of the findings log and
archived in `results/indomain_sanity_metrics.csv`.

---

## 4.7 Why the DECTE / VCTK results can be interpreted after verification

Once the corrected pipeline is shown to reproduce the training-
time validation performance on the training-distribution
validation set, the interpretation of the downstream DECTE / VCTK
numbers changes noticeably. Before the sanity check, an elevated
EER on DECTE would be indistinguishable from a bug (as the
0.32-AUC run in Section 4.2 illustrates). After the sanity check,
an elevated EER on DECTE cannot be a bug of the same kind: the
same code path, the same audio pipeline, and the same score-
direction convention already work on 9,514 files from the
training distribution. Any elevated EER on DECTE (or VCTK) must
therefore reflect a genuine domain-transfer difficulty rather than
a residual pipeline failure.

This does not automatically make the DECTE / VCTK numbers correct
in every respect. Two orthogonal risks remain:

- **Sample-size uncertainty.** Even a correctly-loaded detector,
  scored on a small held-out slice, produces point estimates with
  wide bootstrap CIs. This is addressed by attaching 95 % non-
  parametric bootstrap CIs to every headline number, as described
  in Chapter 3, Section 3.6.
- **Interpretational scope.** The verified detector is one
  detector (AuralGuard-AASISTPP). Whether any given DECTE / VCTK
  effect is architecture-specific is a separate question,
  addressed by the cross-architecture LFCC + LR replication
  in Chapter 5.

Neither of these risks reduces to a hidden pipeline bug once the
sanity check has passed. That is what the check is for.

---

## 4.8 LFCC + Logistic Regression baseline setup

The second detector used in this thesis is a hand-crafted-feature
+ linear-classifier baseline. Its architecture and training
procedure are described in Chapter 3, Section 3.4.2, and are not
repeated here. This section covers only the aspects that are
specific to how the LFCC + LR detector itself is *verified* to
be behaving as expected.

Unlike the primary AASIST detector, the LFCC + LR classifier has
no pre-existing checkpoint against which to verify — it is fit
from scratch inside this project on the leakage-filtered
AuralGuard training CSV. There is therefore no equivalent of the
in-domain sanity check in Section 4.6: no external reference EER
exists to reproduce.

Instead, three verification points are enforced at fit time and
at score time:

- **Class ordering.** After the pipeline is fit,
  `model.named_steps["lr"].classes_` is printed. The expected
  value is `[0 1]`, which locks `predict_proba[:, 0]` as the
  bonafide probability. If a future version of scikit-learn ever
  changed class-sorting behaviour, the printed value would change,
  and the fixed `bon_col = 0` assumption in the scoring path
  would then need to be re-checked.
- **Path resolution and existence pre-check.** Every training
  audio path is resolved to an absolute path (the AuralGuard CSV
  uses paths relative to the AuralGuard project root, not the
  dialect-deepfake-bias repo root) and checked for existence
  before feature extraction begins. If more than 5 % of training
  paths cannot be resolved, the script aborts with a clear error
  rather than silently proceeding with a partial training set.
  On the actual data, 80 of ~33,700 paths (0.24 %) were missing
  — well below the abort threshold and reported in the run log
  for transparency.
- **Leakage filter accounting.** The 16 DECTE test speakers held
  out for the mitigation and evaluation slices are filtered from
  the AuralGuard training CSV before feature extraction. The
  script prints the number of rows removed and the per-speaker
  removal counts, so leakage protection is externally auditable.
  In the actual run, 1,445 rows were removed and DECTE rows
  dropped from 8,057 to 6,612.

These checks do not certify the LFCC + LR classifier as a
deployment-grade detector — it is not one, and the thesis does
not claim it to be one. They certify only that the classifier is
being fit and scored as documented. Its role in the thesis is
to answer the cross-architecture-replication question
(Chapter 5, Section 5.5), and that role requires only that the
classifier be *itself*, not that it be *good in absolute terms*.

---

## 4.9 Limitations of detector verification

Even with the loader fix, the score-direction fix, and the passing
in-domain sanity check, the detector verification in this chapter
has several limits worth flagging up front.

- **Verification is against a single reference set.** The
  in-domain sanity check reproduces the checkpoint's training-
  distribution EER on the checkpoint's own validation split. If
  the training-distribution split itself has an unrepresentative
  slice (for example, if its DECTE rows happen to be easier than
  DECTE in general), the sanity check would still pass and
  downstream DECTE EER would look worse for reasons not caught by
  the check. Chapter 8 discusses the closely related in-training
  DECTE-exposure caveat.
- **Verification confirms the loader, not the model.** The sanity
  check ensures that the trained parameters are loaded and scored
  correctly. It does not (and cannot) validate that the AASIST
  architecture itself is a good choice for anti-spoofing on
  dialectal speech. Whether a different anti-spoofing model would
  produce very different DECTE / VCTK numbers is a separate
  research question, only partly addressed by the LFCC + LR
  cross-architecture check in Chapter 5.
- **No score-direction sanity check for LFCC + LR beyond the
  class-ordering assertion.** The class-ordering assertion
  (`model.classes_ == [0, 1]`) guarantees the correct column
  index. It does not guarantee that scikit-learn's
  `predict_proba` is monotonic in the same direction as the
  underlying logistic regression's coefficient (this is a hard
  invariant of `sklearn` and would only fail as a library bug),
  but it is worth naming as an unproven invariant rather than a
  verified property of this thesis.
- **No formal float / dtype audit.** All scoring is done in
  `float32` audio → `float32` features → `float64` probability.
  The occasional `numpy` warning about mixed precision has been
  eyeballed and is not central, but a full numerical audit
  of the pipeline is not part of this thesis.
- **Verification does not address the audio-quality confound.**
  Even a perfectly-loaded detector will react differently to
  16-kHz down-mixed VCTK (originally 48 kHz) than to native
  16-kHz DECTE chunks. The audio pipeline is the same for both,
  but the input distributions genuinely differ in bandwidth and
  channel characteristics. This is discussed in the DECTE /
  VCTK caveats in Chapter 3 and revisited in Chapter 8.

None of these limits invalidate the verification. Together with
the passing in-domain sanity check, they set the scope inside
which the DECTE / VCTK claims in Chapters 5–7 are made.

---

*End of Chapter 4 draft.*
