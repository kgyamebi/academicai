"""OpenTelemetry tracing — code-complete; activates when OTEL_EXPORTER_* is set.

Default: no-op if SDK missing or OTEL_SDK_DISABLED=true.
Local proof: OTEL_TRACES_EXPORTER=console or otlp to Jaeger in docker-compose.observability.yml.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

_tracer = None
_configured = False


def configure_tracing(service_name: str = "academiccheck-api") -> None:
    global _tracer, _configured
    if _configured:
        return
    _configured = True
    if os.environ.get("OTEL_SDK_DISABLED", "").lower() in {"1", "true", "yes"}:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    except ImportError:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = (os.environ.get("OTEL_TRACES_EXPORTER") or "none").lower()
    if exporter == "console":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif exporter in {"otlp", "otlp_http", "jaeger"}:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        except ImportError:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("academiccheck")


def get_tracer():
    if _tracer is None:
        configure_tracing()
    return _tracer


@contextmanager
def span(name: str, **attrs) -> Iterator[None]:
    tracer = get_tracer()
    if tracer is None:
        yield
        return
    with tracer.start_as_current_span(name) as current:
        for key, value in attrs.items():
            if value is not None:
                current.set_attribute(key, str(value)[:256])
        yield
