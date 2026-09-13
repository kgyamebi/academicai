from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StrictIn(BaseModel):
    """Reject unknown JSON keys (mass-assignment guard)."""

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class RegisterIn(StrictIn):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=8)

    @field_validator("password")
    @classmethod
    def _password_policy(cls, value: str) -> str:
        from app.core.security import assert_password_policy

        try:
            assert_password_policy(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return value


class LoginIn(StrictIn):
    email: EmailStr
    password: str


class PasswordResetRequestIn(StrictIn):
    email: EmailStr


class PasswordResetIn(StrictIn):
    token: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_policy(cls, value: str) -> str:
        from app.core.security import assert_password_policy

        try:
            assert_password_policy(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return value


class VerifyIn(StrictIn):
    token: str


class RefreshIn(StrictIn):
    refresh_token: str | None = None


class ShareCreateIn(StrictIn):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    hours: int | None = Field(default=None, ge=1, le=720)


class ShareUnlockIn(StrictIn):
    password: str | None = None


class AssignmentCreateIn(StrictIn):
    title: str = Field(default="Untitled assignment", max_length=255)
    question: str = Field(default="", max_length=20000)
    academic_level: str = Field(default="undergraduate", max_length=64)
    citation_style: str = Field(default="apa7", max_length=32)
    discipline: str | None = None
    target_word_count: int | None = None
    notes: str = ""
    rubric_text: str = ""
    rubric_criteria: list[dict[str, Any]] = Field(default_factory=list)


class AssignmentUpdateIn(StrictIn):
    title: str | None = None
    question: str | None = None
    academic_level: str | None = None
    citation_style: str | None = None
    notes: str | None = None
    rubric_text: str | None = None
    rubric_criteria: list[dict[str, Any]] | None = None


class PasteDocumentIn(StrictIn):
    assignment_id: UUID | None = None
    title: str = "Pasted draft"
    text: str = Field(min_length=40, max_length=400000)
    filename: str = "draft.txt"


class AnalysisCreateIn(StrictIn):
    assignment_id: UUID
    document_id: UUID | None = None
    analysis_type: str = "full"
    include_ai_indicator: bool = False


class CoachIn(StrictIn):
    assignment_id: UUID
    question: str = Field(min_length=5, max_length=4000)


class CompareIn(StrictIn):
    assignment_id: UUID
    version_a_id: UUID
    version_b_id: UUID


class VersionIn(StrictIn):
    name: str = Field(min_length=1, max_length=120)
    document_id: UUID | None = None
    notes: str = ""


class CheckoutIn(StrictIn):
    plan_slug: str
    provider: str = "stripe"
    currency: str = "USD"


class CreditPurchaseIn(StrictIn):
    pack_id: str
    provider: str = "stripe"
    currency: str = "USD"


class AdminPlanUpdateIn(StrictIn):
    name: str | None = Field(default=None, max_length=160)
    price_usd_cents: int | None = Field(default=None, ge=0, le=10_000_000)
    checks_per_month: int | None = Field(default=None, ge=0, le=1_000_000)
    max_words: int | None = Field(default=None, ge=0, le=2_000_000)
    features: dict[str, Any] | None = None
    is_active: bool | None = None
    description: str | None = Field(default=None, max_length=2000)


class AdminFlagIn(StrictIn):
    key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_.-]+$")
    enabled: bool = True
    description: str = Field(default="", max_length=500)


class AnalyticsIn(StrictIn):
    event_name: str = Field(max_length=80)
    path: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class CitationVerifyIn(StrictIn):
    reference_id: UUID


class Paginated(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
