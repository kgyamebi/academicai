from pathlib import Path

from app.core.metrics import latency_snapshot, observe_ms
from app.workers.queue import enqueue_analysis
from app.workers.tasks import record_poison_job


def test_enqueue_without_redis_fails_closed():
    assert enqueue_analysis("00000000-0000-0000-0000-000000000001") is False


def test_poison_job_logger_does_not_raise():
    record_poison_job("job-1", "simulated worker crash")


def test_metrics_and_health_are_public(client):
    live = client.get("/api/live")
    health = client.get("/api/health")
    metrics = client.get("/api/metrics")
    prom = client.get("/api/metrics/prometheus")
    assert live.status_code == 200
    assert health.status_code == 200
    assert metrics.status_code == 200
    assert prom.status_code == 200
    assert "academiccheck_ready" in prom.text
    assert "academiccheck_queue_depth" in prom.text
    assert "counters" in metrics.json()
    assert "database" in health.json()
    assert "http_latency" in metrics.json()


def test_enqueue_uses_stable_job_id_and_pool():
    source = Path(__file__).resolve().parents[1] / "app" / "workers" / "queue.py"
    text = source.read_text(encoding="utf-8")
    assert "job_id=job_id" in text
    assert "max_connections=64" in text
    assert "DuplicateJobError" in text


def test_latency_histogram_records_samples():
    observe_ms(12.5)
    snap = latency_snapshot()
    assert snap["n"] >= 1
    assert "p95_ms" in snap
