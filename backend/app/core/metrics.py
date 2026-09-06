"""In-process counters for operations, billing, AI cost, and errors.

These are process-local. Production scrapes /api/metrics from each replica
or forwards the same names to the configured metrics backend.
"""

from __future__ import annotations

from collections import Counter
from threading import Lock

_lock = Lock()
_counts: Counter[str] = Counter()


def incr(name: str, n: int = 1) -> None:
    with _lock:
        _counts[name] += n


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counts)
