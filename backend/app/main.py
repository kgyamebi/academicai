from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse

from app import models  # noqa: F401
from app.api.v1 import admin, analysis, assignments, auth, billing, coach, dashboard, documents, health, public, reports
from app.config import get_settings
from app.core.csrf import enforce_csrf
from app.core.logging import configure_logging, get_logger
from app.core.metrics import incr
from app.db.session import Base, engine
from app.deps import require_roles
from app.models.user import User
from app.seed import disable_insecure_default_admin, seed_if_needed

log = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    settings = get_settings()
    if settings.is_production and settings.database_url.startswith("sqlite"):
        raise RuntimeError("SQLite is not allowed in production. Use PostgreSQL.")
    if settings.app_env in {"development", "test"}:
        Base.metadata.create_all(bind=engine)
        seed_if_needed()
    else:
        disable_insecure_default_admin()
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env, traces_sample_rate=0.1)
        except Exception as exc:  # noqa: BLE001
            log.error("sentry_init_failed", error=str(exc))
    log.info("startup", env=settings.app_env)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Stripe-Signature", "X-CSRF-Token", "X-Paystack-Signature"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    try:
        enforce_csrf(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "status": exc.status_code})
    response = await call_next(request)
    incr("http.requests")
    if response.status_code >= 500:
        incr("http.5xx")
    elif response.status_code >= 400:
        incr("http.4xx")
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["Cache-Control"] = "no-store"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(coach.router)
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
async def unhandled(_request: Request, exc: Exception):
    log.error("unhandled_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong. Please try again.", "status": 500},
    )
