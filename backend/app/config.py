from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AcademicCheck AI"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me"
    app_api_url: str = "http://localhost:8000"
    app_web_url: str = "http://localhost:3000"
    app_cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://academiccheck:academiccheck@localhost:5432/academiccheck"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    email_verification_hours: int = 48
    password_reset_hours: int = 2

    guest_retention_hours: int = 24
    guest_max_checks: int = 2
    guest_max_words: int = 2000

    max_upload_mb: int = 15
    max_pdf_pages: int = 80
    max_extracted_chars: int = 400000
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = "./storage"
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "academiccheck"
    s3_region: str = "auto"

    ai_default_provider: str = "openai"
    openai_api_key: str = ""
    openai_model_strong: str = "gpt-4o-mini"
    openai_model_fast: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model_strong: str = "claude-3-5-haiku-latest"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    ai_timeout_seconds: int = 90
    ai_max_retries: int = 2
    ai_daily_token_budget: int = 2_000_000

    email_provider: Literal["console", "smtp"] = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@academiccheck.ai"

    billing_default_currency: str = "USD"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""
    flutterwave_secret_key: str = ""
    flutterwave_webhook_hash: str = ""

    crossref_mailto: str = "hello@academiccheck.ai"
    openalex_email: str = "hello@academiccheck.ai"
    semantic_scholar_api_key: str = ""

    sentry_dsn: str = ""
    log_level: str = "INFO"
    field_encryption_key: str = ""
    cookie_secure: bool = False
    require_queue: bool = False
    admin_bootstrap_email: str = ""
    admin_bootstrap_password: str = ""
    clamav_host: str = ""
    webhook_tolerance_seconds: int = 300
    share_default_hours: int = 72

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
