"""
Bias Analysis
==============
Breaks detector performance down by speaker social variables
(gender, age_group, ses_class, recording_era) — this is the core
analysis for the thesis's research question.
"""

import pandas as pd
import numpy as np

from .metrics import compute_metrics, metrics_to_dict


def compute_grouped_metrics(
    predictions_df: pd.DataFrame,
    group_cols: list[str] = None,
) -> pd.DataFrame:
    """
    Compute detection metrics overall and broken down by each social variable.

    Expects predictions_df with columns:
        - label: 1 for bonafide, 0 for spoof
        - score: bonafide-ness score from the detector
        - speaker_gender, speaker_age_group, speaker_ses_class,
          speaker_recording_era, generator_name (optional)

    Returns a DataFrame with one row per (grouping_variable, group_value)
    plus an "overall" row, so you get a single table for the thesis.
    """
    if group_cols is None:
        group_cols = [
            "speaker_gender",
            "speaker_age_group",
            "speaker_ses_class",
            "speaker_recording_era",
            "generator_name",
            "dialect_group",  # decte vs vctk, if you've added the control set
        ]

    rows = []

    # Overall metrics (baseline to compare every group against)
    bonafide = predictions_df[predictions_df["label"] == 1]["score"].values
    spoof = predictions_df[predictions_df["label"] == 0]["score"].values
    if len(bonafide) > 0 and len(spoof) > 0:
        m = compute_metrics(bonafide, spoof)
        row = metrics_to_dict(m, group_name="ALL")
        row["grouping_variable"] = "overall"
        rows.append(row)

    # Per-group metrics
    for col in group_cols:
        if col not in predictions_df.columns:
            continue

        for group_value in predictions_df[col].dropna().unique():
            if group_value in ("FILL_IN", "unknown", ""):
                continue  # skip unfilled metadata

            subset = predictions_df[predictions_df[col] == group_value]
            bonafide = subset[subset["label"] == 1]["score"].values
            spoof = subset[subset["label"] == 0]["score"].values

            if len(bonafide) < 5 or len(spoof) < 5:
                # Too few samples for a reliable EER — flag rather than
                # silently reporting a noisy number
                continue

            m = compute_metrics(bonafide, spoof)
            row = metrics_to_dict(m, group_name=str(group_value))
            row["grouping_variable"] = col
            rows.append(row)

    result = pd.DataFrame(rows)
    if not result.empty:
        cols_order = ["grouping_variable", "group"] + [
            c for c in result.columns if c not in ("grouping_variable", "group")
        ]
        result = result[cols_order]

    return result


def compute_dialect_vs_standard_gap(
    predictions_df: pd.DataFrame,
    dialect_col: str = "dialect_group",
    dialect_value: str = "decte",
    standard_value: str = "vctk",
) -> dict:
    """
    The headline number for the thesis: the EER gap between dialectal
    (DECTE) and standard-accent (VCTK) speakers on the same detector.

    Only meaningful once you have the VCTK control set generated —
    returns None with a note if VCTK data isn't present yet.
    """
    if dialect_col not in predictions_df.columns:
        return {"note": "dialect_group column not found — add VCTK control set first"}

    dialect_df = predictions_df[predictions_df[dialect_col] == dialect_value]
    standard_df = predictions_df[predictions_df[dialect_col] == standard_value]

    if standard_df.empty:
        return {"note": "No VCTK (standard-accent) data yet — this is Phase 1.5, not blocking"}

    dialect_bonafide = dialect_df[dialect_df["label"] == 1]["score"].values
    dialect_spoof = dialect_df[dialect_df["label"] == 0]["score"].values
    standard_bonafide = standard_df[standard_df["label"] == 1]["score"].values
    standard_spoof = standard_df[standard_df["label"] == 0]["score"].values

    dialect_metrics = compute_metrics(dialect_bonafide, dialect_spoof)
    standard_metrics = compute_metrics(standard_bonafide, standard_spoof)

    gap = dialect_metrics.eer - standard_metrics.eer

    return {
        "dialect_eer_percent": round(dialect_metrics.eer, 3),
        "standard_eer_percent": round(standard_metrics.eer, 3),
        "eer_gap_percent": round(gap, 3),
        "interpretation": (
            f"Detector EER is {abs(gap):.2f} percentage points "
            f"{'WORSE' if gap > 0 else 'BETTER'} on dialectal (DECTE) speakers "
            f"compared to standard-accent (VCTK) speakers."
        ),
    }
