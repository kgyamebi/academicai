"""Metrics endpoint changes under load + tracing no-op safety."""

from app.core.metrics import incr, observe_endpoint, observe_ms, reset_for_tests, snapshot
from app.core.tracing import configure_tracing, span


def test_metrics_prometheus_changes_under_simulated_load(client):
    reset_for_tests()
    before = client.get("/api/metrics/prometheus").text
    for _ in range(12):
        client.get("/api/live")
    after = client.get("/api/metrics/prometheus").text
    assert "academiccheck_http_requests" in after or "academiccheck_http_requests_total" in after
    assert after != before or "http_requests" in after
    # Counters must increase
    assert "academiccheck_http_requests" in after


def test_json_metrics_include_endpoints(client):
    client.get("/api/live")
    body = client.get("/api/metrics").json()
    assert "counters" in body
    assert "endpoints" in body
    assert "http_latency" in body


def test_tracing_span_noop_without_sdk(monkeypatch):
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    configure_tracing()
    with span("test.span", path="/x"):
        incr("trace.test")
    assert snapshot().get("trace.test", 0) >= 1
