"""
Detection Metrics
==================
Standard anti-spoofing metrics. EER computation is the one people most often
get wrong — this implementation follows the standard ASVspoof convention.

Convention used throughout this file:
  label = 1  ->  bonafide (real)
  label = 0  ->  spoof (fake)
  score = model's bonafide-ness score (higher = more likely real)

This matches ASVspoof/AASIST convention. If your detector outputs a
"fakeness" score instead, negate it before passing in here.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve


@dataclass
class DetectionMetrics:
    eer: float                 # Equal Error Rate (%, lower is better)
    eer_threshold: float       # Score threshold at which EER occurs
    auc: float                 # Area under ROC curve (0-1, higher is better)
    accuracy: float            # At EER threshold
    f1: float                  # At EER threshold
    false_accept_rate: float   # Spoof classified as bonafide, at EER threshold (%)
    false_reject_rate: float   # Bonafide classified as spoof, at EER threshold (%)
    n_bonafide: int
    n_spoof: int


def compute_eer(bonafide_scores: np.ndarray, spoof_scores: np.ndarray) -> tuple[float, float]:
    """
    Compute Equal Error Rate the standard way used in ASVspoof challenges.

    Returns (eer_percent, threshold).

    EER is the point where False Rejection Rate (bonafide wrongly called
    spoof) equals False Acceptance Rate (spoof wrongly called bonafide).
    """
    labels = np.concatenate([
        np.ones(len(bonafide_scores)),
        np.zeros(len(spoof_scores)),
    ])
    scores = np.concatenate([bonafide_scores, spoof_scores])

    fpr, tpr, thresholds = roc_curve(labels, scores)
    fnr = 1 - tpr  # false negative rate = false rejection rate for bonafide

    # EER is where FPR (false accept) and FNR (false reject) curves cross
    abs_diffs = np.abs(fpr - fnr)
    min_idx = np.argmin(abs_diffs)
    eer = (fpr[min_idx] + fnr[min_idx]) / 2.0
    eer_threshold = thresholds[min_idx]

    return eer * 100, eer_threshold


def compute_metrics(
    bonafide_scores: np.ndarray, spoof_scores: np.ndarray
) -> DetectionMetrics:
    """Compute the full metric suite for a set of bonafide vs spoof scores."""
    labels = np.concatenate([
        np.ones(len(bonafide_scores)),
        np.zeros(len(spoof_scores)),
    ])
    scores = np.concatenate([bonafide_scores, spoof_scores])

    eer, eer_thresh = compute_eer(bonafide_scores, spoof_scores)
    auc = roc_auc_score(labels, scores) if len(set(labels)) > 1 else float("nan")

    # Metrics at the EER threshold
    preds = (scores >= eer_thresh).astype(int)

    tp = int(np.sum((preds == 1) & (labels == 1)))  # correctly called bonafide
    tn = int(np.sum((preds == 0) & (labels == 0)))  # correctly called spoof
    fp = int(np.sum((preds == 1) & (labels == 0)))  # spoof called bonafide (false accept)
    fn = int(np.sum((preds == 0) & (labels == 1)))  # bonafide called spoof (false reject)

    accuracy = (tp + tn) / len(labels) if len(labels) > 0 else float("nan")
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    far = fp / (fp + tn) * 100 if (fp + tn) > 0 else float("nan")  # false accept rate
    frr = fn / (fn + tp) * 100 if (fn + tp) > 0 else float("nan")  # false reject rate

    return DetectionMetrics(
        eer=eer,
        eer_threshold=float(eer_thresh),
        auc=auc,
        accuracy=accuracy,
        f1=f1,
        false_accept_rate=far,
        false_reject_rate=frr,
        n_bonafide=len(bonafide_scores),
        n_spoof=len(spoof_scores),
    )


def metrics_to_dict(m: DetectionMetrics, group_name: str = "overall") -> dict:
    """Flatten metrics into a dict for CSV export."""
    return {
        "group": group_name,
        "eer_percent": round(m.eer, 3),
        "eer_threshold": round(m.eer_threshold, 4),
        "auc": round(m.auc, 4) if not np.isnan(m.auc) else None,
        "accuracy": round(m.accuracy, 4),
        "f1": round(m.f1, 4),
        "false_accept_rate_percent": round(m.false_accept_rate, 3)
        if not np.isnan(m.false_accept_rate) else None,
        "false_reject_rate_percent": round(m.false_reject_rate, 3)
        if not np.isnan(m.false_reject_rate) else None,
        "n_bonafide": m.n_bonafide,
        "n_spoof": m.n_spoof,
    }
