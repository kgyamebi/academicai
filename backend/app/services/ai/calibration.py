"""Calibration diagnostics. Do not expose uncalibrated scores to students."""

from __future__ import annotations

from app.services.ai.stats import brier_score, expected_calibration_error


def hard_label_calibration(correct: list[bool]) -> dict:
    """Treat each hard decision as p=1.0. This is a diagnostic, not a UI score."""
    if not correct:
        return {
            "n": 0,
            "ece": None,
            "brier": None,
            "exposed_in_ui": False,
            "passes_calibration": False,
            "note": "No held-out correctness vector. Confidence must not be shown.",
        }
    conf = [1.0] * len(correct)
    ece = expected_calibration_error(conf, correct)
    brier = brier_score([[1.0, 0.0] if ok else [0.0, 1.0] for ok in correct], [0 if ok else 1 for ok in correct])
    # Overconfident hard labels fail unless they are perfect on a large independent set.
    passes = ece is not None and ece <= 0.02 and all(correct) and len(correct) >= 1000
    return {
        "n": len(correct),
        "ece": ece,
        "brier": brier,
        "exposed_in_ui": False,
        "passes_calibration": bool(passes),
        "note": (
            "Classifiers emit hard labels. ECE here assumes p=1.0 on every decision. "
            "Student-facing confidence is disabled until a calibrated probability model exists."
        ),
    }
