"""In-process counters, latency histogram, gauges, and cache stats.

Process-local by design. Prometheus scrapes /api/metrics/prometheus per replica.
OpenTelemetry spans (optional) export independently via OTEL_* env.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from threading import Lock

_lock = Lock()
_counts: Counter[str] = Counter()
_gauges: dict[str, float] = {}
_latencies_ms: list[float] = []
_endpoint_counts: Counter[str] = Counter()
_endpoint_errors: Counter[str] = Counter()
_endpoint_latency: dict[str, list[float]] = defaultdict(list)
_MAX_SAMPLES = 2000
_MAX_ENDPOINT_SAMPLES = 500


def incr(name: str, n: int = 1) -> None:
    with _lock:
        _counts[name] += n


def gauge(name: str, value: float) -> None:
    with _lock:
        _gauges[name] = float(value)


def observe_ms(ms: float) -> None:
    with _lock:
        _latencies_ms.append(ms)
        if len(_latencies_ms) > _MAX_SAMPLES:
            del _latencies_ms[: _MAX_SAMPLES // 2]


def observe_endpoint(path: str, *, status_code: int, duration_ms: float) -> None:
    key = path.split("?")[0][:120] or "unknown"
    with _lock:
        _endpoint_counts[key] += 1
        if status_code >= 500:
            _endpoint_errors[key] += 1
        bucket = _endpoint_latency[key]
        bucket.append(duration_ms)
        if len(bucket) > _MAX_ENDPOINT_SAMPLES:
            del bucket[: _MAX_ENDPOINT_SAMPLES // 2]


def cache_hit(name: str = "default") -> None:
    incr(f"cache.{name}.hit")


def cache_miss(name: str = "default") -> None:
    incr(f"cache.{name}.miss")


def latency_snapshot() -> dict[str, float | int]:
    with _lock:
        samples = sorted(_latencies_ms)
    if not samples:
        return {"n": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0}
    last = len(samples) - 1

    def pct(value: int) -> float:
        return round(samples[min(last, int(last * value / 100))], 2)

    return {"n": len(samples), "p50_ms": pct(50), "p95_ms": pct(95), "p99_ms": pct(99)}


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counts)


def gauges_snapshot() -> dict[str, float]:
    with _lock:
        return dict(_gauges)


def endpoint_snapshot() -> dict[str, dict]:
    with _lock:
        out = {}
        for path, n in _endpoint_counts.items():
            samples = sorted(_endpoint_latency.get(path) or [])
            p95 = samples[min(len(samples) - 1, int((len(samples) - 1) * 0.95))] if samples else 0
            out[path] = {
                "requests": n,
                "errors_5xx": _endpoint_errors.get(path, 0),
                "p95_ms": round(p95, 2),
            }
        return out


def refresh_runtime_gauges() -> None:
    """Best-effort DB pool + queue gauges for /metrics."""
    from app.core.logging import get_logger

    log = get_logger("metrics")
    try:
        from app.db.session import engine

        pool = getattr(engine, "pool", None)
        if pool is not None:
            size = getattr(pool, "size", lambda: 0)()
            checked = getattr(pool, "checkedout", lambda: 0)()
            overflow = getattr(pool, "overflow", lambda: 0)()
            gauge("db.pool.size", float(size))
            gauge("db.pool.checked_out", float(checked))
            gauge("db.pool.overflow", float(overflow))
    except Exception as exc:  # noqa: BLE001
        log.debug("db_pool_gauge_unavailable", error=str(exc))
    try:
        from app.workers.queue import queue_depth, registered_workers

        gauge("queue.depth", float(queue_depth() or 0))
        gauge("queue.workers", float(registered_workers() or 0))
    except Exception as exc:  # noqa: BLE001
        log.debug("queue_gauge_unavailable", error=str(exc))
    try:
        counts = snapshot()
        for bucket in ("ai", "meta"):
            hits = float(counts.get(f"cache.{bucket}.hit", 0))
            misses = float(counts.get(f"cache.{bucket}.miss", 0))
            total = hits + misses
            gauge(f"cache.{bucket}.hit_rate", (hits / total) if total else 0.0)
            gauge(f"cache.{bucket}.miss_rate", (misses / total) if total else 0.0)
    except Exception as exc:  # noqa: BLE001
        log.debug("cache_gauge_unavailable", error=str(exc))


def reset_for_tests() -> None:
    with _lock:
        _counts.clear()
        _gauges.clear()
        _latencies_ms.clear()
        _endpoint_counts.clear()
        _endpoint_errors.clear()
        _endpoint_latency.clear()
