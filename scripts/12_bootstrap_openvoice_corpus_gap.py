#!/usr/bin/env python3
"""
Script 12: Bootstrap 95% CI for the OpenVoice DECTE-vs-VCTK Corpus Gap (Entry 9)
=================================================================================
Companion to scripts/06_bootstrap_xtts_corpus_gap.py, run on the same
existing prediction CSVs but for the OpenVoice v2 generator instead of
XTTS v2. Gives the OpenVoice narrative the same statistical rigour the
XTTS narrative already has under Entry 6.

Point estimates already in the log:
  DECTE OpenVoice v2 EER = 47.84% (Entry 2, N=100 balanced)
  VCTK  OpenVoice v2 EER = 74.58% (Entry 5, N=100)
  Naive gap              = -26.74 pp (DECTE *easier* than VCTK for OpenVoice)

This script attaches paired 95% bootstrap CIs to both cells and to the
DECTE - VCTK gap, so the "OpenVoice is more failed on VCTK than on
DECTE" claim from Entry 5 becomes statistically defensible (or not).

Method
------
  - Reuses two existing prediction CSVs (no rescoring, no regeneration):
      results/detector_predictions.csv        (DECTE, full Phase 2 run)
      results/vctk/detector_predictions.csv   (VCTK, Entry 5 run)
  - Filters to detector_name == "aasist" and generator_name == "openvoice_v2".
  - DECTE arm: 100 OpenVoice spoofs (all present) vs DECTE's full 216-row
    bonafide pool.
  - VCTK arm: 100 OpenVoice spoofs (all present) vs VCTK's full 120-row
    bonafide pool (per Entry 5 methodology).
  - No downsampling needed on either arm - both already at N=100.
  - 1000 bootstrap iterations, base seed 42. Each iteration independently
    resamples each corpus's bonafide and spoof arrays with replacement
    (same original sizes), computes EER per corpus, and records the gap.
    Independent resampling is correct because the two corpora share zero
    speakers and zero files.
  - Reports for each corpus: n_bonafide, n_spoof, EER, AUC, 95% CI on
    EER. Reports for the gap: point estimate, 95% CI, and a verdict on
    which direction (if any) is statistically supported.

Output
------
  - results/openvoice_corpus_gap/openvoice_corpus_gap_bootstrap_ci.csv
    (three rows: DECTE, VCTK, GAP)
  - clean terminal summary + verdict line

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/12_bootstrap_openvoice_corpus_gap.py

Does not modify data, manifests, checkpoints, existing configs, or
detector code. Only reads two prediction CSVs and writes to results/.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.metrics import compute_metrics, compute_eer


GENERATOR = "openvoice_v2"


def load_corpus_arrays(
    predictions_path: Path,
    detector_name: str,
    generator_name: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (bonafide_scores, spoof_scores) arrays for one corpus.

    Bonafide pool = all rows with label == 1 for the requested detector.
    Spoof pool    = all rows with label == 0 AND generator_name matching.
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"predictions file not found: {predictions_path}")

    df = pd.read_csv(predictions_path).dropna(subset=["score"])
    if "detector_name" in df.columns:
        df = df[df["detector_name"] == detector_name]

    bonafide = df[df["label"] == 1]["score"].to_numpy()
    spoof = df[
        (df["generator_name"] == generator_name) & (df["label"] == 0)
    ]["score"].to_numpy()
    return bonafide, spoof


def bootstrap_gap(
    dec_bon: np.ndarray, dec_spf: np.ndarray,
    vctk_bon: np.ndarray, vctk_spf: np.ndarray,
    n_iters: int = 1000, seed: int = 42, ci_level: float = 0.95,
) -> dict:
    """Joint bootstrap: on each iteration, resample all four arrays
    independently with replacement, compute EER per corpus, record the
    gap (DECTE - VCTK). Returns dict with per-corpus and gap CIs.
    Mirrors scripts/06_bootstrap_xtts_corpus_gap.py's design.
    """
    rng = np.random.default_rng(seed)
    dec_eers = np.empty(n_iters, dtype=np.float64)
    vctk_eers = np.empty(n_iters, dtype=np.float64)
    gaps = np.empty(n_iters, dtype=np.float64)

    for i in range(n_iters):
        db = rng.choice(dec_bon, size=len(dec_bon), replace=True)
        ds = rng.choice(dec_spf, size=len(dec_spf), replace=True)
        vb = rng.choice(vctk_bon, size=len(vctk_bon), replace=True)
        vs = rng.choice(vctk_spf, size=len(vctk_spf), replace=True)

        dec_eer, _ = compute_eer(db, ds)
        vctk_eer, _ = compute_eer(vb, vs)
        dec_eers[i] = dec_eer
        vctk_eers[i] = vctk_eer
        gaps[i] = dec_eer - vctk_eer

    alpha = (1.0 - ci_level) / 2.0

    def pct(a):
        return (
            float(np.percentile(a, alpha * 100)),
            float(np.percentile(a, (1.0 - alpha) * 100)),
            float(np.percentile(a, 50)),
        )

    return {
        "dec": pct(dec_eers),
        "vctk": pct(vctk_eers),
        "gap": pct(gaps),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap 95% CI for the OpenVoice DECTE-vs-VCTK corpus gap"
    )
    parser.add_argument(
        "--decte-predictions", type=str,
        default="results/detector_predictions.csv",
        help="Predictions CSV from the full DECTE Phase 2 run "
             "(must contain openvoice_v2 rows).",
    )
    parser.add_argument(
        "--vctk-predictions", type=str,
        default="results/vctk/detector_predictions.csv",
        help="Predictions CSV from the VCTK Phase 2 run "
             "(must contain openvoice_v2 rows).",
    )
    parser.add_argument(
        "--output", type=str,
        default="results/openvoice_corpus_gap/openvoice_corpus_gap_bootstrap_ci.csv",
    )
    parser.add_argument("--detector-name", type=str, default="aasist")
    parser.add_argument("--bootstrap-iters", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dec_path = Path(args.decte_predictions)
    vctk_path = Path(args.vctk_predictions)

    print("=" * 60)
    print("OPENVOICE DECTE-vs-VCTK CORPUS GAP - BOOTSTRAP 95% CI")
    print("=" * 60)
    print(f"DECTE predictions : {dec_path}")
    print(f"VCTK predictions  : {vctk_path}")
    print(f"Detector          : {args.detector_name}")
    print(f"Generator         : {GENERATOR}")
    print(f"Bootstrap iters   : {args.bootstrap_iters} (seed {args.seed})")

    try:
        dec_bon, dec_spf = load_corpus_arrays(
            dec_path, args.detector_name, GENERATOR,
        )
        vctk_bon, vctk_spf = load_corpus_arrays(
            vctk_path, args.detector_name, GENERATOR,
        )
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Both DECTE and VCTK Phase 2 runs must have been executed first.")
        sys.exit(1)

    for label, bon, spf in (
        ("DECTE", dec_bon, dec_spf), ("VCTK", vctk_bon, vctk_spf),
    ):
        if len(bon) < 5 or len(spf) < 5:
            print(f"\nERROR: {label} arm has too few samples "
                  f"(bonafide={len(bon)}, spoof={len(spf)}).")
            sys.exit(2)

    # ---- point estimates ----
    dec_metrics = compute_metrics(dec_bon, dec_spf)
    vctk_metrics = compute_metrics(vctk_bon, vctk_spf)
    point_gap = dec_metrics.eer - vctk_metrics.eer

    # ---- joint bootstrap ----
    ci = bootstrap_gap(
        dec_bon, dec_spf, vctk_bon, vctk_spf,
        n_iters=args.bootstrap_iters, seed=args.seed,
    )
    (dec_lo, dec_hi, dec_med) = ci["dec"]
    (vctk_lo, vctk_hi, vctk_med) = ci["vctk"]
    (gap_lo, gap_hi, gap_med) = ci["gap"]

    rows = [
        {
            "row": "DECTE_OPENVOICE",
            "n_bonafide": int(dec_metrics.n_bonafide),
            "n_spoof": int(dec_metrics.n_spoof),
            "eer_percent": round(dec_metrics.eer, 3),
            "eer_ci95_lo": round(dec_lo, 3),
            "eer_ci95_hi": round(dec_hi, 3),
            "eer_boot_median": round(dec_med, 3),
            "auc": round(dec_metrics.auc, 4),
        },
        {
            "row": "VCTK_OPENVOICE",
            "n_bonafide": int(vctk_metrics.n_bonafide),
            "n_spoof": int(vctk_metrics.n_spoof),
            "eer_percent": round(vctk_metrics.eer, 3),
            "eer_ci95_lo": round(vctk_lo, 3),
            "eer_ci95_hi": round(vctk_hi, 3),
            "eer_boot_median": round(vctk_med, 3),
            "auc": round(vctk_metrics.auc, 4),
        },
        {
            "row": "GAP_DECTE_minus_VCTK",
            "n_bonafide": None,
            "n_spoof": None,
            "eer_percent": round(point_gap, 3),
            "eer_ci95_lo": round(gap_lo, 3),
            "eer_ci95_hi": round(gap_hi, 3),
            "eer_boot_median": round(gap_med, 3),
            "auc": None,
        },
    ]
    out_df = pd.DataFrame(rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(out_df.to_string(index=False))

    # ---- verdict ----
    print()
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)
    print(f"DECTE OpenVoice 95% CI : [{dec_lo:.2f}, {dec_hi:.2f}] %")
    print(f"VCTK  OpenVoice 95% CI : [{vctk_lo:.2f}, {vctk_hi:.2f}] %")
    print(f"Corpus-gap 95% CI      : [{gap_lo:.2f}, {gap_hi:.2f}] pp "
          f"(point estimate {point_gap:+.2f} pp)")
    if gap_hi < 0:
        print("VERDICT: gap CI entirely NEGATIVE (VCTK OpenVoice EER > DECTE OpenVoice EER).")
        print("  OpenVoice is HARDER for the detector on VCTK than on DECTE,")
        print("  statistically supported at 95% (0 is outside the interval).")
        print("  Note: this is the OPPOSITE direction from the XTTS gap (Entry 6),")
        print("  which had DECTE > VCTK. OpenVoice's failure mode is not a dialect effect.")
    elif gap_lo > 0:
        print("VERDICT: gap CI entirely POSITIVE (DECTE OpenVoice > VCTK OpenVoice).")
        print("  Same direction as the XTTS gap - unexpected given Entry 5 point")
        print("  estimates. Investigate before publishing.")
    else:
        print("VERDICT: gap CI includes 0.")
        print("  The DECTE-vs-VCTK OpenVoice gap is NOT statistically supported at 95%.")
        print("  Report cautiously; the point-estimate direction may still be worth")
        print("  noting but the specific magnitude cannot be defended.")

    print()
    print(f"Saved to {out_path} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
