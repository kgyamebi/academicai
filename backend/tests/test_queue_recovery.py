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
    assert live.status_code == 200
    assert health.status_code == 200
    assert metrics.status_code == 200
    assert "counters" in metrics.json()
    assert "database" in health.json()
