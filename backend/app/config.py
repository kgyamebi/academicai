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
    database_read_url: str = ""
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-jwt"
    jwt_secret_previous: str = ""
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    max_refresh_sessions: int = 10
    email_verification_hours: int = 24
    password_reset_hours: int = 2
    email_resend_cooldown_seconds: int = 60
    # Enforce MX/A DNS for real inboxes (always on outside APP_ENV=test unless explicitly disabled).
    email_validate_mx: bool = True
    disposable_email_domains: str = ""
    # When True (default), password reset is only emailed to verified accounts.
    require_verified_for_password_reset: bool = True
    # Staging/production: require SMTP credentials when provider=smtp (validated at startup).
    email_smtp_probe_on_startup: bool = True

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
    ai_circuit_threshold: int = 5
    ai_circuit_cooldown_seconds: int = 30
    ai_cache_ttl_seconds: int = 300
    db_pool_size: int = 10
    db_max_overflow: int = 20

    email_provider: Literal["console", "smtp", "resend"] = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    # auto | required | starttls | disabled (disabled = local Mailpit/sink only)
    smtp_tls: Literal["auto", "required", "starttls", "disabled"] = "auto"
    smtp_timeout_seconds: int = 15
    # Production always requires SMTP auth. Staging/dev may use Mailpit without auth when false.
    smtp_require_auth: bool = False
    smtp_ehlo_hostname: str = ""
    # Resend HTTP API (Invoice App pattern). EMAIL_API_KEY or RESEND_API_KEY.
    email_api_key: str = ""
    resend_api_key: str = ""
    email_from: str = "noreply@academiccheck.ai"
    email_envelope_from: str = ""
    email_reply_to: str = ""
    # Prefer RQ "email" queue; sync fallback when Redis/workers unavailable.
    email_async: bool = True

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
    field_encryption_key_previous: str = ""
    backup_encryption_key: str = ""
    backup_encryption_key_previous: str = ""
    cookie_secure: bool = False
    require_queue: bool = False
    admin_bootstrap_email: str = ""
    admin_bootstrap_password: str = ""
    clamav_host: str = ""
    clamav_required: bool = False
    webhook_tolerance_seconds: int = 300
    share_default_hours: int = 72
    # Minimal alerting (Slack/Discord incoming webhook URL or local sink file).
    alert_webhook_url: str = ""
    alert_sink_file: str = ""
    alert_throttle_seconds: int = 120
    alert_5xx_window_seconds: int = 60
    alert_5xx_threshold: int = 5
    pagerduty_routing_key: str = ""
    pagerduty_api_key: str = ""

    @property
    def resend_key(self) -> str:
        return (self.email_api_key or self.resend_api_key or "").strip()

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def require_email_verification(self) -> bool:
        # Gate privileged features (PDF, share, billing, advanced history) when not in test.
        # Login remains allowed for unverified users (Invoice App pattern).
        return self.app_env in {"production", "staging", "development"}

    def assert_deployable_secrets(self) -> None:
        if not (self.is_production or self.is_staging):
            return
        weak = {
            "",
            "change-me",
            "change-me-jwt",
            "ci-secret",
            "test-secret",
            "dev-secret-change-me-academiccheck",
            "dev-jwt-secret-change-me",
        }
        if self.jwt_secret_key in weak or len(self.jwt_secret_key.encode("utf-8")) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes and must not use a default value.")
        if self.app_secret_key in weak or len(self.app_secret_key) < 16:
            raise RuntimeError("APP_SECRET_KEY is too weak for production/staging.")
        if not self.field_encryption_key.strip():
            raise RuntimeError("FIELD_ENCRYPTION_KEY is required in production/staging.")
        if self.is_production and not self.cookie_secure:
            raise RuntimeError("COOKIE_SECURE=true is required in production (HTTPS only).")
        if (self.is_production or self.is_staging) and self.email_provider == "console":
            raise RuntimeError("EMAIL_PROVIDER=smtp or resend is required in staging/production.")
        if self.email_provider == "smtp":
            if not self.smtp_host.strip() or "@" not in self.email_from:
                raise RuntimeError("EMAIL_PROVIDER=smtp requires SMTP_HOST and a valid EMAIL_FROM.")
            if self.is_production and self.smtp_tls == "disabled":
                raise RuntimeError("SMTP_TLS=disabled is not allowed in production.")
            if self.is_production or self.smtp_require_auth:
                if not self.smtp_user.strip() or not self.smtp_password:
                    raise RuntimeError("Production SMTP requires SMTP_USER and SMTP_PASSWORD.")
        if self.email_provider == "resend":
            if not self.resend_key or "@" not in self.email_from:
                raise RuntimeError("EMAIL_PROVIDER=resend requires EMAIL_API_KEY (or RESEND_API_KEY) and EMAIL_FROM.")
        if not (self.alert_webhook_url.strip() or self.alert_sink_file.strip() or self.pagerduty_routing_key.strip()):
            raise RuntimeError(
                "Set ALERT_WEBHOOK_URL, ALERT_SINK_FILE, or PAGERDUTY_ROUTING_KEY so outages are not silent."
            )
        if self.is_production and not self.require_queue:
            raise RuntimeError("REQUIRE_QUEUE=true is required in production.")


@lru_cache
def get_settings() -> Settings:
    from app.core.secrets import inject_secrets_file

    inject_secrets_file()
    return Settings()
