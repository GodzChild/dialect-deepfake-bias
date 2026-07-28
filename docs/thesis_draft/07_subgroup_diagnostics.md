# Chapter 7 — Subgroup Diagnostics

*Draft. Written to be read by the thesis supervisor first, then polished
into final prose. All quantitative claims trace back to a specific
Entry in `docs/THESIS_FINDINGS_LOG.md` and to a specific committed
script under `scripts/`.*

---

## 7.1 Chapter overview

Chapter 6 established that mitigation v2 reduced the AASIST
detector's DECTE XTTS EER on a held-out DECTE test slice by
−17.44 pp, with a 95 % paired-bootstrap CI of [−28.49, −9.30] pp,
and did so without a statistically significant regression on the
VCTK XTTS guardrail. That result was reported as a *single overall
number* for the mitigation effect.

This chapter asks a narrower question. The overall −17.44 pp
improvement is an average across every audio file in the held-out
DECTE test slice. That average could correspond to a uniform
per-subgroup improvement, or it could correspond to some subgroups
improving substantially while others barely move. If the underlying
distribution of baseline errors was itself uneven — for example,
concentrated in a specific age band or recording era — then a
subgroup-level view is what makes that visible.

The chapter therefore reports a **subgroup-level diagnostic view**
of the mitigation effect on the same 172-file DECTE XTTS test
slice, broken down by three per-speaker metadata columns:
`speaker_gender`, `speaker_age_group`, and `speaker_recording_era`.
It does *not* attempt a formal fairness audit, and it does not
compute per-subgroup bootstrap confidence intervals.
Section 7.11 discusses why the sample size makes those stronger
statistical claims out of scope.

---

## 7.2 Why subgroup diagnostics were included

The thesis is framed around dialect / domain effects. Chapters 5
and 6 both treat DECTE as a whole — a single dialectal / domain-
shifted test condition. Corpus-level metrics on DECTE are the
correct unit of analysis for the RQ1, RQ2, RQ3, RQ4 arguments
those chapters make.

But corpus-level metrics can also hide uneven error
concentration. A single overall EER of, say, 40 % on 172 files
can arise from many combinations of per-subgroup EERs: it could
be roughly 40 % everywhere, or it could be, say, 60 % on one
subgroup and 25 % on another. The two situations look identical
at the corpus level but suggest very different pictures of what
the detector is actually doing.

DECTE metadata gives three coarse metadata axes along which such
concentration can be described:

- **Gender** (`speaker_gender`) — recorded per speaker in the
  DECTE speaker-info files (Chapter 3, Section 3.2.1).
- **Age band** (`speaker_age_group`) — recorded per speaker in
  10-year bins (16–20, 21–30, ..., 81–90).
- **Recording era** (`speaker_recording_era`) — the DECTE
  interview period the speaker was recorded in (1960s–1970s,
  1990s, 2007–2008, 2008–2009, 2010–2011).

Reporting per-subgroup EER for both the baseline and the
mitigated detector, on the same file set, lets a reader see
*where the improvement lands* and *where baseline errors were
concentrated*. That is diagnostic information. It is not evidence
of causal fairness or unfairness, and this chapter does not
claim to be one.

Two things this chapter deliberately does **not** do:

- It does not fit a subgroup-conditional model of detector
  behaviour. Every reported number is a plain per-subgroup EER,
  computed via the same `compute_metrics` function used elsewhere
  in the thesis (Chapter 3, Section 3.5).
- It does not attempt to attribute causation to gender, age, or
  recording era. The reported differences are descriptive
  properties of the detector's error distribution on this
  specific held-out slice; they are not evidence that any given
  metadata axis *caused* the errors.

---

## 7.3 Diagnostic protocol

The diagnostic follows the protocol laid out in Chapter 3,
Section 3.8. The salient points are:

- **Inputs (existing predictions only).** The baseline and
  mitigated v2 detector prediction CSVs from Chapter 6 are
  reused: `results/mitigation_v2/baseline_decte/detector_
  predictions.csv` and `results/mitigation_v2/mitigated_decte/
  detector_predictions.csv`. No file is rescored; no detector is
  reloaded; no manifest is modified.
- **Paired join.** The two prediction CSVs are joined on
  `(audio_path, label)` with `validate="one_to_one"` — a join
  that fails loudly if the two files disagree on which audio
  files were evaluated. This guarantees the subgroup diagnostic
  compares baseline and mitigated numbers over the same file
  set.
- **Matched rows.** The join produces **172 matched rows** total:
  **86 bonafide** matched originals and **86 XTTS spoof**
  files. This is the same file set that Chapter 6, Section 6.6
  reports the overall mitigation delta on.
- **Groupings.** Three headline grouping columns are used for
  the main table: `speaker_gender`, `speaker_age_group`,
  `speaker_recording_era`. `speaker_id` is reported only as a
  diagnostic appendix (see Section 7.9). `speaker_ses_class` is
  omitted because for DECTE this field is essentially all
  `"unknown"` (Chapter 3, Section 3.2.1 caveat).
- **Main-table threshold.** A subgroup enters the main table
  only if it has at least **10 bonafide** and at least **10
  spoof** files in the joined slice. Below that, the subgroup is
  reported as a low-n diagnostic entry and is not used for any
  headline claim in the chapter (Chapter 3, Section 3.8.2).
- **Skipped values.** The values `unknown`, `mixed`, `fill_in`,
  `""`, and `nan` are skipped for the headline grouping columns
  because they represent missing metadata rather than a real
  subgroup.
- **No per-subgroup bootstrap CIs.** With N ≤ 40 files per
  subgroup, bootstrap CIs on per-subgroup EER would be wide
  enough that most between-group deltas would sit inside sampling
  noise. This chapter therefore reports point estimates only, and
  the wording throughout is descriptive rather than
  statistical-comparative (see Section 7.10 and Section 7.11).

The full per-subgroup CSV (including the low-n table and the
per-speaker appendix) is written by
`scripts/14_decte_subgroup_diagnostics.py` to
`results/subgroup_diagnostics/decte_subgroup_metrics.csv`.

---

## 7.4 Overall reference result

Before the per-subgroup breakdown, the overall (paired,
across-all-172-files) result on the joined slice reproduces
Chapter 6's mitigation number as expected:

| Arm | n_bonafide | n_spoof | EER (%) |
|---|---:|---:|---:|
| Baseline | 86 | 86 | 40.70 |
| Mitigated v2 | 86 | 86 | 23.26 |
| **Delta (mitigated − baseline)** | — | — | **−17.44 pp** |

This matches the Chapter 6 headline delta on the same file set
and confirms that the subgroup diagnostic is being computed on
the same joined slice, not on a subtly different subset. The
95 % paired-bootstrap CI on this overall delta — [−28.49,
−9.30] pp — is reported in Chapter 6 and is not repeated in the
per-subgroup tables below, where no per-subgroup CI is claimed.

---

## 7.5 Gender subgroup results

Two gender subgroups meet the main-table threshold on the joined
DECTE test slice: `female` and `male`. (The `mixed` and
`unknown` values are skipped per Section 7.3.)

| Group value | n_bonafide | n_spoof | Baseline EER (%) | Mitigated v2 EER (%) | Delta (pp) |
|---|---:|---:|---:|---:|---:|
| female | 39 | 39 | 30.77 | 24.36 | −6.41 |
| male | 26 | 26 | 38.46 | 11.54 | **−26.92** |

Both subgroups improved after mitigation, and the improvement
size differed materially between them (−6.41 pp for female, −26.92
pp for male). The baseline EER was also different across the two
subgroups on this slice: the detector's baseline errors were more
concentrated on the male-labelled files than on the female-labelled
files.

**No fairness claim** is made from these two numbers. In particular:

- The male-vs-female baseline gap (~ 7.7 pp) and the difference in
  per-subgroup mitigation delta (~ 20.5 pp) are point-estimate
  differences on subgroups with fewer than 40 files each. Bootstrap
  CIs on either quantity would be wide.
- The DECTE test slice is a 16-speaker held-out slice; the gender
  distribution within it is what the deterministic 82 → 16 speaker
  split of Chapter 3, Section 3.7.1 produced, not a demographically
  representative sample of Tyneside speakers in general.
- The mitigation was DECTE-and-XTTS-scoped (Chapter 6); nothing in
  this thesis has evaluated whether the same gender pattern
  reproduces under different generators, different detectors, or
  larger DECTE slices.

The pattern is worth reporting as *descriptive error concentration*
that mitigation v2 reduced by different amounts across the two
subgroups. It is not evidence that the detector is (or is not)
"biased against" either subgroup — the phrasing to avoid is named
explicitly in Section 7.10.

---

## 7.6 Age-group subgroup results

Three age-band subgroups meet the main-table threshold on the
joined slice: `16-20`, `21-30`, and `41-50`. (Other age bands
either had fewer than 10 files per class after the split or were
labelled `mixed` / `unknown` and skipped per Section 7.3.)

| Group value | n_bonafide | n_spoof | Baseline EER (%) | Mitigated v2 EER (%) | Delta (pp) |
|---|---:|---:|---:|---:|---:|
| 16-20 | 37 | 37 | 37.84 | 5.41 | **−32.43** |
| 21-30 | 15 | 15 | 66.67 | 33.33 | **−33.33** |
| 41-50 | 10 | 10 | 45.00 | 35.00 | −10.00 |

Every main-table age band improved. The largest improvements landed
on the youngest two bands (`16-20` and `21-30`, both around −32 pp)
and the smallest on `41-50` (−10 pp). The baseline EER pattern
across age bands is not monotonic on this slice — `21-30` had the
highest baseline EER (66.67 %), while `16-20` and `41-50` were
lower — so the pattern of improvement does not simply follow the
pattern of baseline errors.

The descriptive reading of this table is that **baseline errors on
this slice were concentrated differently across age bands, and
mitigation v2 reduced errors in all main-table age bands but by
substantially different amounts**. That is all this table is
evidence for.

Small sample sizes prevent any stronger subgroup claim. The
per-band file counts are all in the 10–40 range; even a
double-figure per-band delta could sit inside sampling noise under
a per-subgroup bootstrap. The observations above should be read as
diagnostic starting points for future larger-slice studies (see
Section 7.11), not as conclusions about how the AASIST detector
behaves on any specific age band in general.

---

## 7.7 Recording-era subgroup results

Four recording-era subgroups meet the main-table threshold on the
joined slice: `1960s-1970s`, `1990s`, `2007-2008`, and
`2010-2011`. (The `2008-2009` era and the `mixed` / `unknown`
labels either fell below the threshold or were skipped per
Section 7.3.)

| Group value | n_bonafide | n_spoof | Baseline EER (%) | Mitigated v2 EER (%) | Delta (pp) |
|---|---:|---:|---:|---:|---:|
| 1960s-1970s | 24 | 24 | 68.75 | 47.92 | −20.83 |
| 1990s | 32 | 32 | 40.63 | 6.25 | **−34.38** |
| 2007-2008 | 10 | 10 | 20.00 | 5.00 | −15.00 |
| 2010-2011 | 20 | 20 | 25.00 | 20.00 | −5.00 |

Every main-table recording era improved. The largest improvement
was on the `1990s` era (−34.38 pp, the largest per-subgroup delta
in the entire chapter); the smallest was on the `2010-2011` era
(−5.00 pp, the smallest per-subgroup delta). Baseline EER was
noticeably higher on the older eras (`1960s-1970s` at 68.75 %,
`1990s` at 40.63 %) than on the newer ones (`2007-2008` at 20.00 %,
`2010-2011` at 25.00 %). The mitigation reduced this baseline
spread substantially — after mitigation, the `1990s` and
`2007-2008` eras are both in the single digits, while the
`1960s-1970s` era remains materially higher (47.92 %).

A cautious reading of this table: on this 16-speaker slice, the
recording-era axis is where the largest per-subgroup differences
appear both at baseline and in mitigation delta. The most likely
substantive interpretation is *not* that the calendar year of the
recording is doing the work directly — it is that recording era
in DECTE is confounded with channel characteristics (analog reel-
to-reel in the 1960s-1970s vs digital in the 2000s+), interview
technology, and the speaker demographics of each survey wave. The
observed spread in per-era baseline EER and per-era mitigation
delta could therefore reflect any combination of channel, speaker
population, and time-period effects. Attributing it to time
period alone would over-interpret the data. Chapter 8 revisits
this confound at greater length.

---

## 7.8 Summary table

Consolidating Sections 7.4–7.7 into a single view of the DECTE
subgroup diagnostic:

| Grouping variable | Group | n_bonafide | n_spoof | Baseline EER (%) | Mitigated v2 EER (%) | Delta (pp) | Interpretation |
|---|---|---:|---:|---:|---:|---:|:---|
| overall | ALL | 86 | 86 | 40.70 | 23.26 | −17.44 | Same as Chapter 6 headline; reproduces on the joined slice |
| speaker_gender | female | 39 | 39 | 30.77 | 24.36 | −6.41 | Improved; smaller per-subgroup improvement |
| speaker_gender | male | 26 | 26 | 38.46 | 11.54 | −26.92 | Improved; larger per-subgroup improvement |
| speaker_age_group | 16-20 | 37 | 37 | 37.84 | 5.41 | −32.43 | Improved substantially |
| speaker_age_group | 21-30 | 15 | 15 | 66.67 | 33.33 | −33.33 | Improved substantially; highest baseline EER |
| speaker_age_group | 41-50 | 10 | 10 | 45.00 | 35.00 | −10.00 | Improved less than the younger bands |
| speaker_recording_era | 1960s-1970s | 24 | 24 | 68.75 | 47.92 | −20.83 | Improved; still highest post-mitigation EER on the slice |
| speaker_recording_era | 1990s | 32 | 32 | 40.63 | 6.25 | **−34.38** | Largest per-subgroup improvement in the chapter |
| speaker_recording_era | 2007-2008 | 10 | 10 | 20.00 | 5.00 | −15.00 | Improved |
| speaker_recording_era | 2010-2011 | 20 | 20 | 25.00 | 20.00 | **−5.00** | Smallest per-subgroup improvement in the chapter |

The full per-subgroup CSV — including the low-n rows and the
per-speaker breakdown not shown here — is archived at
`results/subgroup_diagnostics/decte_subgroup_metrics.csv`. Two
headline observations from the table above:

- **Every main-table subgroup improved.** No main-table row has a
  positive delta on this slice. In that limited sense the
  mitigation was uniformly beneficial across the three metadata
  axes reported here.
- **The size of the improvement was uneven.** Per-subgroup deltas
  span −5.00 pp (`2010-2011`) to −34.38 pp (`1990s`), a spread of
  about 29 pp. The uniformity of the *direction* of the mitigation
  should not be over-read as uniformity of *magnitude*.

---

## 7.9 Low-n appendix note

The main-table threshold of at least 10 bonafide and at least 10
spoof samples excludes a small number of DECTE metadata subgroups
whose per-class counts on the joined slice fell below the
threshold. Those subgroups are still written to the CSV output for
transparency, but are flagged as `below_n_threshold = True` and
are not used for any claim in this chapter.

`speaker_id` is treated as a diagnostic appendix column rather
than a headline grouping. With 16 held-out speakers producing
approximately 5–6 files each, every per-speaker row would be low-n
by construction; per-speaker EER on that few files is not a
meaningful quantity. The per-speaker breakdown is written to the
same CSV for auditability (so a reader can see which specific
speaker any given per-subgroup number is driven by) but is not
reproduced in the body of the thesis. If the final thesis
version includes a separate appendix for reproducibility material,
the per-speaker rows and the low-n metadata rows would live there.

---

## 7.10 Interpretation

Two summary statements are supported by the tables in
Sections 7.5–7.8:

- **Mitigation v2 improved every main-table subgroup on the
  joined DECTE test slice.** No main-table row went in the wrong
  direction. Given that Chapter 6 already established a
  statistically supported overall improvement, this rules out one
  concerning scenario — that the overall improvement was driven by
  large gains in one or two subgroups while other subgroups got
  materially worse.
- **The size of the improvement was uneven across metadata
  subgroups.** The spread from −5.00 pp to −34.38 pp across the
  main-table recording-era rows, and the spread from −6.41 pp to
  −26.92 pp across the two gender rows, is substantial. The
  overall −17.44 pp average hides this spread.

Together, these two observations support one cautious diagnostic
conclusion for the chapter:

> **Error concentration and mitigation benefit were not uniform
> across DECTE metadata groups on the 16-speaker held-out test
> slice.**

That is all the chapter is evidence for. Three claims that
Section 7.11's limitations rule out, and which are also flagged
here explicitly:

- **Do NOT write** *"the detector is biased against group X."*
  Fairness claims of that shape require additional axes of
  evidence (deployment context, per-subgroup CIs, harm analysis,
  human-in-the-loop error costs) that this chapter does not
  provide.
- **Do NOT write** *"the mitigation fixed fairness."* The chapter
  reports descriptive per-subgroup EER changes on one held-out
  slice. It does not measure fairness in any formal sense (see
  Section 7.11).
- **Do NOT write** *"gender / age / era caused the errors."*
  The per-subgroup EER is a property of the detector's behaviour
  on the labelled subset of the slice, not a causal
  attribution to the labelled attribute.

The chapter's wording — *"subgroup diagnostics"*, *"error
concentration"*, *"uneven mitigation gains"* — is chosen to
communicate exactly the descriptive claim above without inviting
the causal readings that would go beyond the evidence.

---

## 7.11 Limitations

Seven limitations narrow the reading of the Chapter 7 tables.
Chapter 8 discusses several of these alongside the Chapter 5 and
Chapter 6 limitations.

- **Only 16 held-out DECTE speakers.** The joined slice covers 16
  speakers total. Per-subgroup speaker counts are consequently in
  the low single digits (for example, `41-50` is driven by a
  small number of the 16 test speakers). This limits how much a
  per-subgroup number can generalise.
- **Small per-subgroup file counts.** Every main-table subgroup
  has n between ~ 10 and ~ 40 files per class. A per-subgroup
  bootstrap CI on any single per-subgroup delta would be wide
  enough that many of the reported between-group differences
  would sit inside sampling noise. No such CIs are computed in
  this chapter; readers should not treat the per-subgroup point
  estimates as statistically comparable to each other.
- **Metadata categories are coarse.** Age bands are 10-year bins;
  gender is binary (`female` / `male`) plus a skipped `mixed`;
  recording era is a categorical bucket per DECTE survey wave.
  Finer or richer metadata (dialect region within Tyneside,
  educational attainment, interview topic, background noise
  level) is not available for this analysis.
- **DECTE metadata may mix speakers per audio stem.** DECTE audio
  chunks are per-interview rather than per-speaker; where
  interviews contain multiple speakers, per-file metadata is
  collapsed to the interview level via the file-level metadata
  bridge described in Chapter 3, Section 3.2.1 (`"mixed"` when
  interview speakers disagree, `"unknown"` when missing). Any
  subgroup number reported here is therefore an interview-level
  proxy, not a strict per-speaker measurement.
- **Recording era is confounded with channel and recording
  conditions.** DECTE eras also correlate with audio-capture
  technology (analog reel-to-reel vs digital), interview format,
  and speaker demographics of each survey wave. The observed
  spread in per-era baseline EER and per-era mitigation delta
  cannot be attributed to time period alone. Section 7.7 already
  notes this in the descriptive interpretation.
- **No per-subgroup bootstrap CIs.** The chapter deliberately
  does not attach per-subgroup statistical intervals to the
  reported point estimates, because the per-subgroup sample
  sizes are too small for those intervals to be tight enough to
  support statistical claims. The overall paired-bootstrap CI
  (from Chapter 6) still applies to the overall delta; no
  equivalent per-subgroup claim is made.
- **Descriptive only, not a formal fairness audit.** A formal
  fairness audit would require, at minimum: pre-specified
  fairness definitions (equalised odds, demographic parity,
  calibration), a demographically balanced evaluation set with
  larger per-subgroup counts, per-subgroup CIs on each fairness
  quantity, and — for actionable claims — an explicit deployment
  context in which the fairness definitions have operational
  meaning. None of these are provided in this chapter, and the
  chapter therefore explicitly does not make fairness claims.

The role of Chapter 7 in the thesis' overall argument is
therefore modest: it complements Chapter 6's overall mitigation
result with a subgroup-level view, shows that the improvement
was directionally uniform but magnitudinally uneven, and flags
where a follow-up study might look. It is not the last word on
detector fairness for dialectal speech, and it is not intended
to be.

---

*End of Chapter 7 draft.*
