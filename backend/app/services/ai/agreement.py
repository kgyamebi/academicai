"""Reviewer-agreement harness. Does not invent lecturer labels."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.ai.stats import cohen_kappa, fleiss_kappa, pairwise_agreement

SCHEMA_PATH = Path(__file__).with_name("reviewer_labels.schema.json")
LABELS_PATH = Path(__file__).with_name("reviewer_labels.jsonl")


def load_reviews(path: Path | None = None) -> list[dict]:
    target = path or LABELS_PATH
    if not target.exists():
        return []
    rows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def agreement_report(rows: list[dict]) -> dict:
    if not rows:
        return {
            "n": 0,
            "cohen_a_b": None,
            "cohen_a_ai": None,
            "cohen_b_ai": None,
            "fleiss": None,
            "pairwise_a_b": None,
            "pairwise_a_ai": None,
            "note": "No dual reviewer labels are on disk. Lecturer agreement is unmeasured.",
        }
    a = [r["reviewer_a"] for r in rows]
    b = [r["reviewer_b"] for r in rows]
    ai = [r["ai"] for r in rows]
    return {
        "n": len(rows),
        "cohen_a_b": cohen_kappa(a, b),
        "cohen_a_ai": cohen_kappa(a, ai),
        "cohen_b_ai": cohen_kappa(b, ai),
        "fleiss": fleiss_kappa([[x, y, z] for x, y, z in zip(a, b, ai)]),
        "pairwise_a_b": pairwise_agreement(a, b),
        "pairwise_a_ai": pairwise_agreement(a, ai),
        "note": "Do not treat AI–reviewer kappa as lecturer certification unless raters are named academics.",
    }
