"""Evaluation statistics. Intervals are computed, not assumed."""

from __future__ import annotations

import math
import random
from collections import Counter


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = successes / n
    z2 = z * z
    den = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / den
    margin = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def bootstrap_f1(pairs: list[tuple[bool, bool]], rounds: int = 1000, seed: int = 7) -> tuple[float, float]:
    """pairs are (gold_positive_or_correct, predicted_positive_or_correct) for binary;
    for item-level correctness pass (True, predicted==expected).

    Returns 2.5th and 97.5th percentiles of F1 treated as accuracy when pairs are correctness flags.
    """
    if not pairs:
        return (0.0, 0.0)
    rng = random.Random(seed)
    scores = []
    n = len(pairs)
    for _ in range(rounds):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        tp = sum(1 for gold, pred in sample if gold and pred)
        fp = sum(1 for gold, pred in sample if (not gold) and pred)
        fn = sum(1 for gold, pred in sample if gold and (not pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        scores.append(f1)
    scores.sort()
    lo = scores[int(0.025 * (len(scores) - 1))]
    hi = scores[int(0.975 * (len(scores) - 1))]
    return (lo, hi)


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    agree = sum(1 for x, y in zip(a, b) if x == y) / n
    labels = set(a) | set(b)
    pa = Counter(a)
    pb = Counter(b)
    chance = sum((pa[lab] / n) * (pb[lab] / n) for lab in labels)
    if chance == 1:
        return 1.0
    return (agree - chance) / (1 - chance)


def pairwise_agreement(a: list[str], b: list[str]) -> float | None:
    if len(a) != len(b) or not a:
        return None
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)


def fleiss_kappa(ratings: list[list[str]]) -> float | None:
    """ratings[i] is the list of labels from raters for item i. Requires equal rater count."""
    if not ratings or any(len(row) != len(ratings[0]) for row in ratings):
        return None
    n = len(ratings)
    r = len(ratings[0])
    if r < 2:
        return None
    labels = sorted({lab for row in ratings for lab in row})
    p = []
    for lab in labels:
        p.append(sum(row.count(lab) for row in ratings) / (n * r))
    p_bar = 0.0
    for row in ratings:
        p_bar += (sum(row.count(lab) ** 2 for lab in labels) - r) / (r * (r - 1))
    p_bar /= n
    p_e = sum(x * x for x in p)
    if p_e == 1:
        return 1.0
    return (p_bar - p_e) / (1 - p_e)


def brier_score(probs: list[list[float]], labels: list[int]) -> float | None:
    if not probs or len(probs) != len(labels):
        return None
    total = 0.0
    k = len(probs[0])
    for dist, y in zip(probs, labels):
        for i in range(k):
            target = 1.0 if i == y else 0.0
            total += (dist[i] - target) ** 2
    return total / len(probs)


def expected_calibration_error(confidences: list[float], correct: list[bool], bins: int = 5) -> float | None:
    if not confidences or len(confidences) != len(correct):
        return None
    bucket_acc = [0.0] * bins
    bucket_conf = [0.0] * bins
    bucket_n = [0] * bins
    for c, ok in zip(confidences, correct):
        idx = min(bins - 1, int(c * bins))
        bucket_n[idx] += 1
        bucket_acc[idx] += 1.0 if ok else 0.0
        bucket_conf[idx] += c
    ece = 0.0
    n = len(confidences)
    for i in range(bins):
        if not bucket_n[i]:
            continue
        acc = bucket_acc[i] / bucket_n[i]
        conf = bucket_conf[i] / bucket_n[i]
        ece += (bucket_n[i] / n) * abs(acc - conf)
    return ece
