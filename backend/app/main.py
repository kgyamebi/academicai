import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from app import models  # noqa: F401
from app.api.v1 import admin, analysis, assignments, auth, billing, citations, coach, dashboard, documents, health, public, reports
from app.config import get_settings
from app.core.csrf import enforce_csrf
from app.core.http_cache import apply_cache_headers
from app.core.logging import configure_logging, get_logger
from app.core.metrics import incr, observe_endpoint, observe_ms
from app.core.tracing import configure_tracing, span
from app.db.session import Base, engine
from app.deps import require_roles
from app.models.user import User
from app.seed import disable_insecure_default_admin, seed_if_needed

log = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    configure_tracing("academiccheck-api")
    settings = get_settings()
    if settings.is_production and settings.database_url.startswith("sqlite"):
        raise RuntimeError("SQLite is not allowed in production. Use PostgreSQL.")
    settings.assert_deployable_secrets()
    if settings.app_env in {"development", "test"}:
        Base.metadata.create_all(bind=engine)
        seed_if_needed()
    else:
        disable_insecure_default_admin()
    if settings.sentry_dsn:
        from app.core.sentry_bootstrap import init_sentry

        init_sentry(service="api")
    elif settings.is_production or settings.is_staging:
        from app.core.alerting import fire_alert

        fire_alert(
            "observability_gap",
            title="SENTRY_DSN is empty",
            detail="API is up without Sentry. Alerts still go to webhook/sink; configure SENTRY_DSN for stack traces.",
            severity="warning",
        )
    from app.services.emailer import assert_smtp_config, smtp_delivery_ready

    assert_smtp_config()
    if settings.email_provider == "smtp" and settings.email_smtp_probe_on_startup:
        if not smtp_delivery_ready(force=True):
            from app.core.alerting import fire_alert

            fire_alert(
                "smtp_unreachable",
                title="SMTP probe failed at startup",
                detail="EMAIL_PROVIDER=smtp but the server did not accept a connection. Verification mail will fail until fixed.",
                severity="critical",
            )
            if settings.is_production or settings.is_staging:
                raise RuntimeError("SMTP probe failed at startup (staging/production fail-closed).")
    if (settings.is_production or settings.is_staging) and settings.email_provider == "console":
        raise RuntimeError("EMAIL_PROVIDER=smtp or resend is required in staging/production.")
    log.info("startup", env=settings.app_env, require_queue=settings.require_queue, email_provider=settings.email_provider)
    yield


settings = get_settings()
_docs_enabled = settings.app_env in {"development", "test"}
app = FastAPI(
    title="AcademicCheck AI API",
    description="Academic writing analysis platform. AI-assisted feedback is not an official grade.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if _docs_enabled else None,
    redoc_url="/api/redoc" if _docs_enabled else None,
    openapi_url="/api/openapi.json" if _docs_enabled else None,
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Stripe-Signature", "X-CSRF-Token", "X-Paystack-Signature"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    bind_contextvars(request_id=request_id)
    try:
        enforce_csrf(request)
    except HTTPException as exc:
        clear_contextvars()
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status": exc.status_code},
            headers={"X-Request-ID": request_id},
        )
    started = time.perf_counter()
    try:
        with span("http.request", path=request.url.path, method=request.method, request_id=request_id):
            response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        observe_ms(duration_ms)
        observe_endpoint(request.url.path, status_code=response.status_code, duration_ms=duration_ms)
        incr("http.requests")
        if response.status_code >= 500:
            incr("http.5xx")
            from app.core.alerting import note_http_5xx

            note_http_5xx(path=request.url.path, status_code=response.status_code)
        elif response.status_code >= 400:
            incr("http.4xx")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        apply_cache_headers(request, response)
        response.headers["X-Request-ID"] = request_id
        if get_settings().is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response
    finally:
        clear_contextvars()


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(coach.router)
app.include_router(citations.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(public.router)
app.include_router(admin.router)


if settings.is_staging:

    @app.get("/api/docs", include_in_schema=False)
    def staging_docs(_user: User = Depends(require_roles("admin"))):
        return get_swagger_ui_html(openapi_url="/api/openapi.json", title="AcademicCheck AI API")

    @app.get("/api/redoc", include_in_schema=False)
    def staging_redoc(_user: User = Depends(require_roles("admin"))):
        return get_redoc_html(openapi_url="/api/openapi.json", title="AcademicCheck AI API")

    @app.get("/api/openapi.json", include_in_schema=False)
    def staging_openapi(_user: User = Depends(require_roles("admin"))):
        return app.openapi()


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "status": exc.status_code})


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Please check the submitted information.", "status": 422},
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    from app.core.alerting import format_exception, notify_unhandled_exception

    stack = format_exception(exc)
    log.error(
        "unhandled_error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=exc,
    )
    notify_unhandled_exception(
        path=request.url.path,
        error=str(exc),
        stack=stack,
        request_id=request.headers.get("x-request-id"),
    )
    incr("http.5xx")
    from app.core.alerting import note_http_5xx

    note_http_5xx(path=request.url.path, status_code=500)
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong. Please try again.", "status": 500},
    )
