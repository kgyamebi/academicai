from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  — register metadata
from app.api.v1 import admin, analysis, assignments, auth, billing, coach, dashboard, documents, health, public, reports
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import Base, engine
from app.seed import seed_if_needed

log = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    seed_if_needed()
    log.info("startup", env=settings.app_env)
    yield


settings = get_settings()
app = FastAPI(
    title="AcademicCheck AI API",
    description="Academic writing analysis platform. AI-assisted feedback is not an official grade.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Stripe-Signature"],
)

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
