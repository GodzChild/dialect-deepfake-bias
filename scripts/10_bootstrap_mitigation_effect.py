#!/usr/bin/env python3
"""
Script 10: Bootstrap 95% CI for the Mitigation v1 Effect
=========================================================
Compares the baseline and mitigated AASIST detectors on the SAME
held-out DECTE test files (and optionally on VCTK as an
out-of-training guardrail), reusing already-scored prediction CSVs.

Method:
  - Load baseline and mitigated `detector_predictions.csv` files.
  - Align rows by (audio_path, label) so each file's baseline_score and
    mitigated_score sit on the same row. Refuse to proceed if the two
    CSVs disagree on which files are present.
  - Paired stratified bootstrap: on each of 1000 iterations, draw
    bonafide indices and spoof indices independently with replacement.
    The SAME indices are used for both models -> every bootstrap sample
    scores the exact same files under both models -> the resulting
    per-iteration delta (mitigated_EER - baseline_EER) is a paired
    within-file comparison, isolating the effect of the fine-tune.
  - Report per-model EER + AUC + 95% CI, and CI on the delta.

Reads only. Does not rescore audio, does not retrain, does not touch
any manifest, checkpoint, or generation output.

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/10_bootstrap_mitigation_effect.py

Output:
    results/mitigation_v1/mitigation_effect_bootstrap_ci.csv
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.metrics import compute_metrics, compute_eer


# ---------------- default paths (all under results/mitigation_v1/) ----------------

MITIG_DIR = Path("results/mitigation_v1")
DECTE_BASELINE = MITIG_DIR / "baseline_decte" / "detector_predictions.csv"
DECTE_MITIGATED = MITIG_DIR / "mitigated_decte" / "detector_predictions.csv"
VCTK_BASELINE = MITIG_DIR / "baseline_vctk" / "detector_predictions.csv"
VCTK_MITIGATED = MITIG_DIR / "mitigated_vctk" / "detector_predictions.csv"

OUT_CSV = MITIG_DIR / "mitigation_effect_bootstrap_ci.csv"


# ---------------- helpers ----------------

def load_and_align(
    baseline_csv: Path, mitigated_csv: Path,
    generator_filter: str | None = None,
) -> pd.DataFrame:
    """Load both prediction CSVs, filter (bonafide + one spoof generator)
    if requested, align by (audio_path, label), refuse mismatch.
    Returns a DataFrame with columns:
        audio_path, label, score_baseline, score_mitigated
    Only rows present in BOTH CSVs are kept (matched pairs).
    """
    def _load(path: Path) -> pd.DataFrame:
        df = pd.read_csv(path).dropna(subset=["score"])
        if "detector_name" in df.columns:
            df = df[df["detector_name"] == "aasist"]
        if generator_filter is not None:
            # Keep bonafide rows + the requested generator's spoofs
            df = df[
                (df["generator_name"] == "bonafide")
                | (df["generator_name"] == generator_filter)
            ]
        return df[["audio_path", "label", "score"]].copy()

    bas = _load(baseline_csv).rename(columns={"score": "score_baseline"})
    mit = _load(mitigated_csv).rename(columns={"score": "score_mitigated"})

    merged = pd.merge(
        bas, mit, on=["audio_path", "label"], how="inner", validate="one_to_one",
    )

    n_bas_only = len(bas) - len(merged)
    n_mit_only = len(mit) - len(merged)
    if n_bas_only or n_mit_only:
        print(f"WARNING: {n_bas_only} rows in baseline missing from mitigated, "
              f"{n_mit_only} rows in mitigated missing from baseline. "
              f"Continuing with the {len(merged)} matched rows only.")

    return merged


def paired_bootstrap(
    merged: pd.DataFrame, n_iters: int, seed: int, ci_level: float = 0.95,
) -> dict:
    """Paired stratified bootstrap. Resamples bonafide indices and spoof
    indices independently with replacement; uses the SAME sampled indices
    for both models so the delta isolates the fine-tune's effect.

    Returns per-model EER CI + delta EER CI + point estimates.
    """
    rng = np.random.default_rng(seed)

    bon_idx_all = merged.index[merged["label"] == 1].to_numpy()
    spf_idx_all = merged.index[merged["label"] == 0].to_numpy()
    n_bon, n_spf = len(bon_idx_all), len(spf_idx_all)
    if n_bon < 5 or n_spf < 5:
        raise ValueError(f"Too few paired rows (bonafide={n_bon}, spoof={n_spf}).")

    bas_bon = merged["score_baseline"].to_numpy()
    mit_bon = merged["score_mitigated"].to_numpy()

    bas_eers = np.empty(n_iters, dtype=np.float64)
    mit_eers = np.empty(n_iters, dtype=np.float64)
    deltas = np.empty(n_iters, dtype=np.float64)

    for i in range(n_iters):
        b_idx = rng.choice(bon_idx_all, size=n_bon, replace=True)
        s_idx = rng.choice(spf_idx_all, size=n_spf, replace=True)

        bas_eer, _ = compute_eer(bas_bon[b_idx], bas_bon[s_idx])
        mit_eer, _ = compute_eer(mit_bon[b_idx], mit_bon[s_idx])
        bas_eers[i] = bas_eer
        mit_eers[i] = mit_eer
        deltas[i] = mit_eer - bas_eer

    alpha = (1.0 - ci_level) / 2.0
    def pct(a):
        return (
            float(np.percentile(a, alpha * 100)),
            float(np.percentile(a, (1.0 - alpha) * 100)),
            float(np.percentile(a, 50)),
        )

    # Point estimates from the actual (un-resampled) arrays
    bas_full = compute_metrics(bas_bon[bon_idx_all], bas_bon[spf_idx_all])
    mit_full = compute_metrics(mit_bon[bon_idx_all], mit_bon[spf_idx_all])

    bas_lo, bas_hi, bas_med = pct(bas_eers)
    mit_lo, mit_hi, mit_med = pct(mit_eers)
    dlt_lo, dlt_hi, dlt_med = pct(deltas)

    return {
        "n_bonafide": n_bon,
        "n_spoof": n_spf,
        "baseline_point": bas_full,
        "mitigated_point": mit_full,
        "baseline_ci": (bas_lo, bas_hi, bas_med),
        "mitigated_ci": (mit_lo, mit_hi, mit_med),
        "delta_point": mit_full.eer - bas_full.eer,
        "delta_ci": (dlt_lo, dlt_hi, dlt_med),
    }


def verdict_for_delta(delta_lo: float, delta_hi: float, direction: str) -> str:
    """direction = 'decte' (want delta < 0) or 'vctk' (want delta ~ 0)."""
    if direction == "decte":
        if delta_hi < 0:
            return "WIN (mitigation reduced EER at 95%)"
        if delta_lo > 0:
            return "LOSS (mitigation INCREASED EER at 95%)"
        return "NEUTRAL (CI includes 0 - no clear effect at 95%)"
    else:  # vctk guardrail
        if delta_lo > 0:
            return "REGRESSION (VCTK EER significantly INCREASED)"
        if delta_hi < 0:
            return "unexpected IMPROVEMENT on VCTK (also treat carefully)"
        return "OK (no significant VCTK change at 95%)"


def rows_for_csv(corpus_tag: str, result: dict) -> list[dict]:
    """Flatten the bootstrap result into three CSV rows: baseline, mitigated, delta."""
    bas = result["baseline_point"]
    mit = result["mitigated_point"]
    bas_lo, bas_hi, _ = result["baseline_ci"]
    mit_lo, mit_hi, _ = result["mitigated_ci"]
    dlt_lo, dlt_hi, dlt_med = result["delta_ci"]
    return [
        {
            "corpus": corpus_tag, "arm": "baseline",
            "n_bonafide": result["n_bonafide"], "n_spoof": result["n_spoof"],
            "eer_percent": round(bas.eer, 3),
            "eer_ci95_lo": round(bas_lo, 3), "eer_ci95_hi": round(bas_hi, 3),
            "auc": round(bas.auc, 4),
        },
        {
            "corpus": corpus_tag, "arm": "mitigated",
            "n_bonafide": result["n_bonafide"], "n_spoof": result["n_spoof"],
            "eer_percent": round(mit.eer, 3),
            "eer_ci95_lo": round(mit_lo, 3), "eer_ci95_hi": round(mit_hi, 3),
            "auc": round(mit.auc, 4),
        },
        {
            "corpus": corpus_tag, "arm": "delta_mit_minus_bas_pp",
            "n_bonafide": result["n_bonafide"], "n_spoof": result["n_spoof"],
            "eer_percent": round(result["delta_point"], 3),
            "eer_ci95_lo": round(dlt_lo, 3), "eer_ci95_hi": round(dlt_hi, 3),
            "auc": None,
        },
    ]


# ---------------- main ----------------

def main():
    p = argparse.ArgumentParser(
        description="Bootstrap CI for the mitigation v1 effect (baseline vs mitigated)."
    )
    p.add_argument("--decte-baseline", default=str(DECTE_BASELINE))
    p.add_argument("--decte-mitigated", default=str(DECTE_MITIGATED))
    p.add_argument("--vctk-baseline", default=str(VCTK_BASELINE),
                   help="Optional; skipped if the file is missing.")
    p.add_argument("--vctk-mitigated", default=str(VCTK_MITIGATED),
                   help="Optional; skipped if the file is missing.")
    p.add_argument("--output", default=str(OUT_CSV))
    p.add_argument("--bootstrap-iters", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    print("=" * 60)
    print("MITIGATION v1 EFFECT — BOOTSTRAP 95% CI (paired)")
    print("=" * 60)

    # ---- DECTE (headline) ----
    dec_bas_path = Path(args.decte_baseline)
    dec_mit_path = Path(args.decte_mitigated)
    for label, p_ in [("DECTE baseline", dec_bas_path), ("DECTE mitigated", dec_mit_path)]:
        if not p_.exists():
            print(f"ERROR: {label} predictions not found: {p_}")
            print("Run the four evaluation commands from the prior step first.")
            sys.exit(1)

    print(f"\nDECTE baseline  : {dec_bas_path}")
    print(f"DECTE mitigated : {dec_mit_path}")
    dec_merged = load_and_align(dec_bas_path, dec_mit_path, generator_filter="xtts_v2")
    print(f"Matched DECTE pairs (bonafide+xtts_v2): "
          f"{(dec_merged['label']==1).sum()} bonafide, {(dec_merged['label']==0).sum()} spoof")

    dec_res = paired_bootstrap(dec_merged, args.bootstrap_iters, args.seed)

    print()
    print(f"DECTE baseline  EER : {dec_res['baseline_point'].eer:.3f}%  "
          f"[{dec_res['baseline_ci'][0]:.3f}, {dec_res['baseline_ci'][1]:.3f}]")
    print(f"DECTE mitigated EER : {dec_res['mitigated_point'].eer:.3f}%  "
          f"[{dec_res['mitigated_ci'][0]:.3f}, {dec_res['mitigated_ci'][1]:.3f}]")
    dlt_lo, dlt_hi, _ = dec_res["delta_ci"]
    print(f"DECTE delta (mitigated - baseline): "
          f"{dec_res['delta_point']:+.3f}pp  95% CI [{dlt_lo:+.3f}, {dlt_hi:+.3f}]pp")
    print(f"DECTE VERDICT: {verdict_for_delta(dlt_lo, dlt_hi, 'decte')}")

    # ---- VCTK guardrail (optional) ----
    vctk_bas_path = Path(args.vctk_baseline)
    vctk_mit_path = Path(args.vctk_mitigated)
    vctk_res = None
    if vctk_bas_path.exists() and vctk_mit_path.exists():
        print(f"\nVCTK baseline   : {vctk_bas_path}")
        print(f"VCTK mitigated  : {vctk_mit_path}")
        vctk_merged = load_and_align(
            vctk_bas_path, vctk_mit_path, generator_filter="xtts_v2",
        )
        print(f"Matched VCTK-XTTS pairs (bonafide+xtts_v2): "
              f"{(vctk_merged['label']==1).sum()} bonafide, "
              f"{(vctk_merged['label']==0).sum()} spoof")

        vctk_res = paired_bootstrap(
            vctk_merged, args.bootstrap_iters, args.seed + 1,
        )
        print()
        print(f"VCTK-XTTS baseline  EER : {vctk_res['baseline_point'].eer:.3f}%  "
              f"[{vctk_res['baseline_ci'][0]:.3f}, {vctk_res['baseline_ci'][1]:.3f}]")
        print(f"VCTK-XTTS mitigated EER : {vctk_res['mitigated_point'].eer:.3f}%  "
              f"[{vctk_res['mitigated_ci'][0]:.3f}, {vctk_res['mitigated_ci'][1]:.3f}]")
        vlo, vhi, _ = vctk_res["delta_ci"]
        print(f"VCTK-XTTS delta (mitigated - baseline): "
              f"{vctk_res['delta_point']:+.3f}pp  95% CI [{vlo:+.3f}, {vhi:+.3f}]pp")
        print(f"VCTK VERDICT: {verdict_for_delta(vlo, vhi, 'vctk')}")
    else:
        print("\nVCTK guardrail SKIPPED "
              "(baseline_vctk or mitigated_vctk predictions not found).")

    # ---- write CSV ----
    all_rows = rows_for_csv("DECTE_XTTS", dec_res)
    if vctk_res is not None:
        all_rows += rows_for_csv("VCTK_XTTS", vctk_res)
    out_df = pd.DataFrame(all_rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    print()
    print("=" * 60)
    print("RESULTS TABLE")
    print("=" * 60)
    print(out_df.to_string(index=False))
    print(f"\nSaved to {out_path} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
