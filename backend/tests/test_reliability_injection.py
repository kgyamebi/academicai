import time

from app.services.ai.cache import cache_key, get_cached, reset_cache, set_cached
from app.services.ai.circuit import allow, record_failure, record_success, reset_circuits, snapshot
from app.services.ai.provider import AIResponse, complete_with_fallback
from app.workers.queue import enqueue_analysis
from app.workers.tasks import record_poison_job


def test_redis_outage_fails_closed():
    assert enqueue_analysis("00000000-0000-0000-0000-000000000001") is False


def test_worker_crash_is_logged_not_raised():
    record_poison_job("job-crash", "simulated worker crash")


def test_readiness_stays_200_when_sqlite_test_db_is_up(client):
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True
    assert response.json()["database"] is True


def test_readiness_returns_503_when_database_is_down(client, monkeypatch):
    class Boom:
        def connect(self):
            raise RuntimeError("database restart")

    monkeypatch.setattr("app.api.v1.health.engine", Boom())
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert response.json()["database"] is False


def test_liveness_stays_up_during_dependency_failure(client, monkeypatch):
    class Boom:
        def connect(self):
            raise RuntimeError("database restart")

    monkeypatch.setattr("app.api.v1.health.engine", Boom())
    live = client.get("/api/live")
    ready = client.get("/api/ready")
    assert live.status_code == 200
    assert ready.status_code == 503


def test_openai_outage_falls_through_providers(monkeypatch):
    reset_circuits()
    reset_cache()

    class Dead:
        name = "openai"

        def complete(self, *_args, **_kwargs):
            raise RuntimeError("openai outage")

    monkeypatch.setattr("app.services.ai.provider.available_providers", lambda: [Dead()])
    assert complete_with_fallback("ping") is None


def test_circuit_opens_after_threshold_failures():
    reset_circuits()
    assert allow("openai") is True
    for _ in range(5):
        record_failure("openai")
    assert allow("openai") is False
    assert snapshot()["openai"] == "open"
    record_success("openai")
    assert allow("openai") is True


def test_identical_prompt_is_cached():
    reset_cache()
    key = cache_key("same prompt", strong=False)
    set_cached(key, AIResponse("{}", "unit", "cache", 1))
    hit = get_cached(key)
    assert isinstance(hit, AIResponse)
    assert hit.provider == "cache"


def test_request_collapse_waits_for_leader(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    reset_circuits()
    reset_cache()
    started = Event()
    calls = {"n": 0}

    class Slow:
        name = "openai"

        def complete(self, *_args, **_kwargs):
            calls["n"] += 1
            started.set()
            time.sleep(0.15)
            return AIResponse("{}", "unit", "collapse", 1)

    monkeypatch.setattr("app.services.ai.provider.available_providers", lambda: [Slow()])
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(complete_with_fallback, "collapse-prompt")
        assert started.wait(2)
        second = pool.submit(complete_with_fallback, "collapse-prompt")
        results = [first.result(timeout=5), second.result(timeout=5)]
    assert all(isinstance(item, AIResponse) for item in results)
    assert calls["n"] == 1



def test_metrics_expose_circuit_state(client):
    reset_circuits()
    record_failure("gemini")
    body = client.get("/api/metrics").json()
    assert "ai_circuits" in body
    assert "counters" in body
