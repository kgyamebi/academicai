from pathlib import Path

from fastapi import HTTPException

from app.services.ai.circuit import allow, record_failure, reset_circuits
from app.services.billing import _flutterwave_checkout, _paystack_checkout, _stripe_checkout
from app.services.documents.storage import StorageError, _s3_call
from app.services.emailer import SMTPEmailProvider, send_email


def test_rate_limit_reuses_shared_redis_pool():
    text = Path(__file__).resolve().parents[1].joinpath("app/core/rate_limit.py").read_text(encoding="utf-8")
    assert "from app.workers.queue import redis_client" in text
    assert "Redis.from_url" not in text


def test_postgres_statement_and_lock_timeouts_are_set():
    text = Path(__file__).resolve().parents[1].joinpath("app/db/session.py").read_text(encoding="utf-8")
    assert "statement_timeout=30000" in text
    assert "lock_timeout=10000" in text
    assert "connect_timeout" in text


def test_ai_retries_use_jittered_backoff():
    text = Path(__file__).resolve().parents[1].joinpath("app/services/ai/provider.py").read_text(encoding="utf-8")
    assert "wait_random_exponential" in text
    assert "timeout=settings.ai_timeout_seconds" in text


def test_s3_client_sets_connect_and_read_timeouts():
    text = Path(__file__).resolve().parents[1].joinpath("app/services/documents/storage.py").read_text(encoding="utf-8")
    assert "connect_timeout=5" in text
    assert "read_timeout=15" in text


def test_s3_circuit_open_fails_fast():
    reset_circuits()
    for _ in range(5):
        record_failure("s3")
    try:
        _s3_call("put", lambda: None)
        raise AssertionError("open circuit must fail")
    except StorageError as exc:
        assert "temporarily unavailable" in str(exc)


def test_billing_circuit_open_fails_without_provider_http(monkeypatch):
    reset_circuits()
    for _ in range(5):
        record_failure("stripe")
        record_failure("paystack")
        record_failure("flutterwave")
    monkeypatch.setattr("app.services.billing.get_settings", lambda: type("S", (), {
        "stripe_secret_key": "sk_test_x",
        "paystack_secret_key": "sk_test_x",
        "flutterwave_secret_key": "sk_test_x",
    })())
    user = type("U", (), {"id": "u", "email": "a@b.c", "full_name": "A"})()
    payment = type("P", (), {"id": "p", "idempotency_key": "k"})()
    db = type("DB", (), {})()
    for fn in (_stripe_checkout, _paystack_checkout, _flutterwave_checkout):
        try:
            if fn is _stripe_checkout:
                fn(db, user, payment, "plan", 100, "USD", False)
            else:
                fn(db, user, payment, "plan", 100, "USD")
            raise AssertionError("open circuit must fail")
        except HTTPException as exc:
            assert exc.status_code == 503
            assert "temporarily unavailable" in str(exc.detail)


def test_smtp_circuit_open_does_not_send(monkeypatch):
    reset_circuits()
    for _ in range(5):
        record_failure("smtp")
    sent = {"n": 0}

    class FakeSMTP(SMTPEmailProvider):
        def send(self, *_args, **_kwargs):
            sent["n"] += 1

    monkeypatch.setattr("app.services.emailer.get_email_provider", lambda: FakeSMTP())
    send_email("a@b.c", "s", "b")
    assert sent["n"] == 0
    assert allow("smtp") is False


def test_live_returns_request_id(client):
    response = client.get("/api/live", headers={"X-Request-ID": "rel-cert-1"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "rel-cert-1"


def test_prometheus_exposes_named_circuits(client):
    reset_circuits()
    record_failure("openai")
    body = client.get("/api/metrics/prometheus").text
    assert "academiccheck_circuit" in body
    assert 'name="openai"' in body


def test_rq_retry_intervals_are_jittered():
    from app.workers.queue import _retry_intervals_with_jitter

    first = _retry_intervals_with_jitter()
    assert len(first) == 3
    assert 15 <= first[0] <= 20
    assert 60 <= first[1] <= 75
    assert 180 <= first[2] <= 210
    samples = {_retry_intervals_with_jitter()[0] for _ in range(30)}
    assert len(samples) >= 2  # jitter actually varies


def test_circuit_half_opens_after_cooldown(monkeypatch):
    reset_circuits()
    monkeypatch.setattr("app.services.ai.circuit.get_settings", lambda: type("S", (), {
        "ai_circuit_threshold": 2,
        "ai_circuit_cooldown_seconds": 0,
    })())
    record_failure("openai")
    record_failure("openai")
    # cooldown 0 → allow() immediately half-opens
    assert allow("openai") is True


def test_timeout_inventory_external_calls_are_finite():
    """Contract: no hanging client constructors without a timeout argument."""
    root = Path(__file__).resolve().parents[1] / "app"
    snippets = {
        "db/session.py": ("connect_timeout", "statement_timeout", "lock_timeout"),
        "workers/queue.py": ("socket_timeout=2", "socket_connect_timeout=2"),
        "workers/rq_worker.py": ("socket_timeout=5",),
        "services/ai/provider.py": ("timeout=settings.ai_timeout_seconds",),
        "services/billing.py": ("timeout=15",),
        "services/emailer.py": ("smtp_timeout_seconds", "timeout=timeout"),
        "services/documents/storage.py": ("connect_timeout=5", "read_timeout=15"),
        "core/alerting.py": ("timeout=5",),
    }
    for rel, needles in snippets.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{rel} missing {needle}"
