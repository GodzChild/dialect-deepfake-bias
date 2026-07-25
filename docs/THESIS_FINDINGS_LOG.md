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

## Entry 2 — [DATE] — [next milestone, e.g. balanced comparison / mitigation results]

*(add here once available)*
