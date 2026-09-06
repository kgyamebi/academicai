from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class VerifyIn(BaseModel):
    token: str


class RefreshIn(BaseModel):
    refresh_token: str | None = None


class ShareCreateIn(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    hours: int | None = Field(default=None, ge=1, le=720)


class ShareUnlockIn(BaseModel):
    password: str | None = None


class AssignmentCreateIn(BaseModel):
    title: str = Field(default="Untitled assignment", max_length=255)
    question: str = Field(default="", max_length=20000)
    academic_level: str = Field(default="undergraduate", max_length=64)
    citation_style: str = Field(default="apa7", max_length=32)
    discipline: str | None = None
    target_word_count: int | None = None
    notes: str = ""
    rubric_text: str = ""
    rubric_criteria: list[dict[str, Any]] = Field(default_factory=list)


class AssignmentUpdateIn(BaseModel):
    title: str | None = None
    question: str | None = None
    academic_level: str | None = None
    citation_style: str | None = None
    notes: str | None = None
    rubric_text: str | None = None
    rubric_criteria: list[dict[str, Any]] | None = None


class PasteDocumentIn(BaseModel):
    assignment_id: UUID | None = None
    title: str = "Pasted draft"
    text: str = Field(min_length=40, max_length=400000)
    filename: str = "draft.txt"


class AnalysisCreateIn(BaseModel):
    assignment_id: UUID
    document_id: UUID | None = None
    analysis_type: str = "full"
    include_ai_indicator: bool = False


class CoachIn(BaseModel):
    assignment_id: UUID
    question: str = Field(min_length=5, max_length=4000)


class CompareIn(BaseModel):
    assignment_id: UUID
    version_a_id: UUID
    version_b_id: UUID


class VersionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    document_id: UUID | None = None
    notes: str = ""


class CheckoutIn(BaseModel):
    plan_slug: str
    provider: str = "stripe"
    currency: str = "USD"


class CreditPurchaseIn(BaseModel):
    pack_id: str
    provider: str = "stripe"
    currency: str = "USD"


class AnalyticsIn(BaseModel):
    event_name: str = Field(max_length=80)
    path: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class Paginated(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
