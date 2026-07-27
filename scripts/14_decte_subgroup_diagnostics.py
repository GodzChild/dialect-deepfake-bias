#!/usr/bin/env python3
"""
Script 14: DECTE Subgroup Diagnostics by Gender, Age Group, Recording Era (Entry 11)
======================================================================================
Descriptive per-subgroup metrics on the DECTE mitigation test slice
(16 held-out speakers, 86 bonafide + 86 XTTS spoofs = 172 files), for
both the baseline AuralGuard-AASIST detector and its mitigation v2
fine-tune from Entry 7. Uses existing prediction CSVs only -- no
rescoring, no retraining, no manifest / checkpoint / audio changes.

Purpose: add a sociolinguistic diagnostic layer to the thesis --
report where detector errors concentrate across metadata subgroups
BEFORE and AFTER mitigation v2, so the reader can see whether
mitigation moved subgroups uniformly or unevenly.

**This is a DIAGNOSTIC analysis, not a fairness audit.** With only
16 held-out speakers, per-subgroup sample sizes are small; no causal
"detector is biased against X" claims should be drawn. Wording in the
output and downstream log entry stays descriptive ("concentration of
errors in group X", "worth flagging"), not causal.

Method
------
  - Load both prediction CSVs (baseline_decte, mitigated_decte).
  - Merge on (audio_path, label) with validate="one_to_one" to
    guarantee the two evaluations covered the same file set.
  - For each grouping column in [speaker_gender, speaker_age_group,
    speaker_recording_era], iterate its distinct values and compute
    metrics separately for baseline and mitigated arms.
  - A subgroup is "main-table eligible" iff it has >= 10 bonafide AND
    >= 10 spoof rows; otherwise it goes into a low-n diagnostic table.
  - Also emits an "overall / ALL" reference row and, separately, a
    per-speaker_id breakdown (always low-n given 16 test speakers, but
    useful as a diagnostic appendix).
  - Metric functions reused from src.evaluation.metrics.compute_metrics
    (never re-implemented).

Output
------
  results/subgroup_diagnostics/decte_subgroup_metrics.csv
  (wide format: one row per subgroup, baseline + mitigated side-by-
  side, plus delta_eer_pp and below_n_threshold flags).

Usage (in the `dialectbias` env):
    conda activate dialectbias
    python scripts/14_decte_subgroup_diagnostics.py
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.evaluation.metrics import compute_metrics


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "results" / "mitigation_v2" / "baseline_decte" / "detector_predictions.csv"
DEFAULT_MITIGATED = REPO_ROOT / "results" / "mitigation_v2" / "mitigated_decte" / "detector_predictions.csv"
RESULTS_DIR = REPO_ROOT / "results" / "subgroup_diagnostics"
RESULTS_CSV = RESULTS_DIR / "decte_subgroup_metrics.csv"

# Headline grouping columns (per Entry 11 task spec)
HEADLINE_GROUP_COLS = [
    "speaker_gender",
    "speaker_age_group",
    "speaker_recording_era",
]

# Diagnostic appendix column -- always low-n given ~5-6 files per speaker
APPENDIX_GROUP_COL = "speaker_id"

# Sample-size thresholds
MIN_N_MAIN = 10   # main-table eligibility
MIN_N_METRIC = 5  # below this the metrics themselves are undefined

# Skip these group values (they mean "missing metadata", not a real group)
SKIP_VALUES = {"unknown", "mixed", "fill_in", "", "nan"}


# ------------- helpers -------------

def _load_one(path: Path, detector_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"predictions CSV not found: {path}")
    df = pd.read_csv(path).dropna(subset=["score"])
    if "detector_name" in df.columns:
        df = df[df["detector_name"] == detector_name]
    return df


def load_and_align(
    baseline_csv: Path, mitigated_csv: Path, detector_name: str = "aasist",
) -> pd.DataFrame:
    """Load both prediction CSVs and align by (audio_path, label). Returns
    a DataFrame with all metadata columns from the baseline plus
    score_baseline and score_mitigated per row."""
    bas = _load_one(baseline_csv, detector_name)
    mit = _load_one(mitigated_csv, detector_name)

    # Metadata columns we want to preserve (from baseline) for grouping.
    meta_cols = [c for c in bas.columns if c not in ("score", "detector_name")]
    bas = bas[meta_cols + ["score"]].rename(columns={"score": "score_baseline"})
    mit = mit[["audio_path", "label", "score"]].rename(columns={"score": "score_mitigated"})

    merged = pd.merge(
        bas, mit, on=["audio_path", "label"], how="inner", validate="one_to_one",
    )
    n_bas_only = len(bas) - len(merged)
    n_mit_only = len(mit) - len(merged)
    if n_bas_only or n_mit_only:
        print(f"WARNING: {n_bas_only} rows only in baseline, {n_mit_only} rows only "
              f"in mitigated. Proceeding with the {len(merged)} matched pairs only.")
    return merged


def _compute_arm_metrics(bon: np.ndarray, spf: np.ndarray) -> dict:
    """Metrics for one arm; NaN-only if insufficient data."""
    if len(bon) < MIN_N_METRIC or len(spf) < MIN_N_METRIC:
        return {
            "eer": float("nan"), "auc": float("nan"), "accuracy": float("nan"),
            "far": float("nan"), "frr": float("nan"),
        }
    m = compute_metrics(bon, spf)
    return {
        "eer": m.eer, "auc": float(m.auc) if not np.isnan(m.auc) else float("nan"),
        "accuracy": m.accuracy,
        "far": m.false_accept_rate, "frr": m.false_reject_rate,
    }


def subgroup_row(
    df: pd.DataFrame, grouping_variable: str, group_value: str,
) -> dict:
    """Compute the wide-format row for one subgroup."""
    n_bon = int((df["label"] == 1).sum())
    n_spf = int((df["label"] == 0).sum())

    bas_bon = df.loc[df["label"] == 1, "score_baseline"].to_numpy()
    bas_spf = df.loc[df["label"] == 0, "score_baseline"].to_numpy()
    mit_bon = df.loc[df["label"] == 1, "score_mitigated"].to_numpy()
    mit_spf = df.loc[df["label"] == 0, "score_mitigated"].to_numpy()

    bas = _compute_arm_metrics(bas_bon, bas_spf)
    mit = _compute_arm_metrics(mit_bon, mit_spf)

    delta_eer = (mit["eer"] - bas["eer"]) if not (np.isnan(bas["eer"]) or np.isnan(mit["eer"])) else float("nan")

    return {
        "grouping_variable": grouping_variable,
        "group_value": str(group_value),
        "n_bonafide": n_bon,
        "n_spoof": n_spf,
        "baseline_eer_percent": None if np.isnan(bas["eer"]) else round(bas["eer"], 3),
        "baseline_auc": None if np.isnan(bas["auc"]) else round(bas["auc"], 4),
        "baseline_accuracy": None if np.isnan(bas["accuracy"]) else round(bas["accuracy"], 4),
        "baseline_far_percent": None if np.isnan(bas["far"]) else round(bas["far"], 3),
        "baseline_frr_percent": None if np.isnan(bas["frr"]) else round(bas["frr"], 3),
        "mitigated_eer_percent": None if np.isnan(mit["eer"]) else round(mit["eer"], 3),
        "mitigated_auc": None if np.isnan(mit["auc"]) else round(mit["auc"], 4),
        "mitigated_accuracy": None if np.isnan(mit["accuracy"]) else round(mit["accuracy"], 4),
        "mitigated_far_percent": None if np.isnan(mit["far"]) else round(mit["far"], 3),
        "mitigated_frr_percent": None if np.isnan(mit["frr"]) else round(mit["frr"], 3),
        "delta_eer_pp": None if np.isnan(delta_eer) else round(delta_eer, 3),
        "below_n_threshold": (n_bon < MIN_N_MAIN or n_spf < MIN_N_MAIN),
    }


def build_subgroup_table(merged: pd.DataFrame) -> pd.DataFrame:
    rows = []

    # Overall / ALL reference
    rows.append(subgroup_row(merged, "overall", "ALL"))

    # Headline grouping columns
    for col in HEADLINE_GROUP_COLS:
        if col not in merged.columns:
            print(f"WARNING: column {col!r} not in predictions -- skipped.")
            continue
        values = (
            merged[col].dropna().astype(str).str.strip().str.lower().unique().tolist()
        )
        values = sorted([v for v in values if v not in SKIP_VALUES])
        for v in values:
            sub = merged[merged[col].astype(str).str.strip().str.lower() == v]
            rows.append(subgroup_row(sub, col, v))

    # Diagnostic appendix -- speaker_id (always low-n)
    if APPENDIX_GROUP_COL in merged.columns:
        for spk in sorted(merged[APPENDIX_GROUP_COL].dropna().unique().tolist()):
            sub = merged[merged[APPENDIX_GROUP_COL] == spk]
            rows.append(subgroup_row(sub, APPENDIX_GROUP_COL, spk))

    return pd.DataFrame(rows)


# ------------- reporting -------------

def print_table(title: str, df: pd.DataFrame, display_cols: list[str]):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    if df.empty:
        print("(empty)")
        return
    with pd.option_context(
        "display.width", 220, "display.max_columns", None,
        "display.float_format", lambda x: f"{x:.3f}",
    ):
        print(df[display_cols].to_string(index=False))


def print_diagnostic_notes(main_df: pd.DataFrame):
    """Descriptive-only summary. No causal / fairness claims."""
    print()
    print("=" * 80)
    print("DIAGNOSTIC NOTES  (descriptive only -- NOT a fairness audit)")
    print("=" * 80)
    print(
        "* This analysis reports per-subgroup EER on a single held-out DECTE\n"
        "  test slice (16 speakers, 86 bonafide + 86 XTTS spoofs = 172 files).\n"
        "* Subgroup sample sizes are small; deltas below +/- a few percentage\n"
        "  points are almost certainly within sampling noise for this N. Wide\n"
        "  bootstrap CIs would be needed to make any per-subgroup 'better' or\n"
        "  'worse' claim.\n"
        "* Wording should stay descriptive: 'error concentration in group X',\n"
        "  'worth flagging'. Do NOT write 'the detector is biased against X'\n"
        "  or 'mitigation helped group X specifically' from this table alone.\n"
    )
    rows_with_delta = main_df.dropna(subset=["delta_eer_pp"])
    if not rows_with_delta.empty:
        max_row = rows_with_delta.loc[rows_with_delta["delta_eer_pp"].idxmax()]
        min_row = rows_with_delta.loc[rows_with_delta["delta_eer_pp"].idxmin()]
        overall = main_df[main_df["grouping_variable"] == "overall"]
        print(
            "Descriptive extremes across MAIN-TABLE subgroups (min-N passed):\n"
            f"  overall delta EER (baseline -> mitigated) : "
            f"{overall.iloc[0]['delta_eer_pp']:+.3f} pp\n"
            f"  largest positive delta (EER got worse)    : "
            f"{max_row['delta_eer_pp']:+.3f} pp in "
            f"{max_row['grouping_variable']}={max_row['group_value']}\n"
            f"  largest negative delta (EER improved)     : "
            f"{min_row['delta_eer_pp']:+.3f} pp in "
            f"{min_row['grouping_variable']}={min_row['group_value']}\n"
        )


# ------------- main -------------

def main():
    parser = argparse.ArgumentParser(
        description="DECTE subgroup diagnostics: baseline vs mitigated v2 by "
                    "gender/age/era on the held-out XTTS test slice."
    )
    parser.add_argument("--baseline-predictions", default=str(DEFAULT_BASELINE))
    parser.add_argument("--mitigated-predictions", default=str(DEFAULT_MITIGATED))
    parser.add_argument("--output", default=str(RESULTS_CSV))
    parser.add_argument("--detector-name", default="aasist")
    args = parser.parse_args()

    print("=" * 80)
    print("DECTE SUBGROUP DIAGNOSTICS -- baseline vs mitigation v2 (Entry 11)")
    print("=" * 80)
    print(f"Baseline predictions : {args.baseline_predictions}")
    print(f"Mitigated predictions: {args.mitigated_predictions}")
    print(f"Detector             : {args.detector_name}")

    merged = load_and_align(
        Path(args.baseline_predictions), Path(args.mitigated_predictions),
        detector_name=args.detector_name,
    )
    print(f"Matched (audio_path, label) rows : {len(merged)} "
          f"({(merged['label']==1).sum()} bonafide, {(merged['label']==0).sum()} spoof)")

    result = build_subgroup_table(merged)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)

    display_cols = [
        "grouping_variable", "group_value", "n_bonafide", "n_spoof",
        "baseline_eer_percent", "mitigated_eer_percent", "delta_eer_pp",
        "baseline_auc", "mitigated_auc",
    ]

    # Overall + headline main-table subgroups
    is_headline = result["grouping_variable"].isin(["overall"] + HEADLINE_GROUP_COLS)
    main_df = result[is_headline & ~result["below_n_threshold"]]
    lown_df = result[is_headline & result["below_n_threshold"]]
    appendix_df = result[result["grouping_variable"] == APPENDIX_GROUP_COL]

    print_table(
        "MAIN TABLE  (subgroups with >= 10 bonafide AND >= 10 spoof)",
        main_df, display_cols,
    )
    if not lown_df.empty:
        print_table(
            "LOW-N DIAGNOSTIC TABLE  (headline groupings, below threshold)",
            lown_df, display_cols,
        )
    print_table(
        f"APPENDIX  ({APPENDIX_GROUP_COL} breakdown -- always low-n, diagnostic only)",
        appendix_df, display_cols,
    )
    print_diagnostic_notes(main_df)
    print()
    print(f"Saved to {args.output} (gitignored via results/ rule)")


if __name__ == "__main__":
    main()
