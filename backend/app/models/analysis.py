from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.document import Document


class AnalysisJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_jobs"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assignment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    stage: Mapped[str] = mapped_column(String(64), default="queued")
    analysis_type: Mapped[str] = mapped_column(String(64), default="full")
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1")
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    assignment: Mapped["Assignment | None"] = relationship(back_populates="jobs")
    document: Mapped["Document | None"] = relationship(back_populates="jobs")
    report: Mapped["AnalysisReport | None"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )


class AnalysisReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_reports"

    job_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True)
    assignment_id: Mapped[UUID | None] = mapped_column(ForeignKey("assignments.id"), nullable=True, index=True)
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    strengths_json: Mapped[str] = mapped_column(Text, default="[]")
    weaknesses_json: Mapped[str] = mapped_column(Text, default="[]")
    priority_actions_json: Mapped[str] = mapped_column(Text, default="[]")
    structure_map_json: Mapped[str] = mapped_column(Text, default="[]")
    question_analysis_json: Mapped[str] = mapped_column(Text, default="{}")
    readability_json: Mapped[str] = mapped_column(Text, default="{}")
    word_count_json: Mapped[str] = mapped_column(Text, default="{}")
    rubric_json: Mapped[str] = mapped_column(Text, default="{}")
    share_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    share_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default=(
            "AI-assisted analysis only. Results are not an official grade, "
            "plagiarism determination, or definitive AI-use determination."
        ),
    )

    job: Mapped["AnalysisJob"] = relationship(back_populates="report")
    findings: Mapped[list["AnalysisFinding"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    scores: Mapped[list["AnalysisScore"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class AnalysisFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_findings"

    report_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_reports.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    location: Mapped[str] = mapped_column(String(255), default="")
    paragraph: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_text: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text, default="")
    teaching_note: Mapped[str] = mapped_column(Text, default="")
    example: Mapped[str] = mapped_column(Text, default="")
    improved_sentence: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[int] = mapped_column(Integer, default=70)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    report: Mapped["AnalysisReport"] = relationship(back_populates="findings")


class AnalysisScore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_scores"

    report_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_reports.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(64))
    score: Mapped[int] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    weight: Mapped[int] = mapped_column(Integer, default=10)
    rationale: Mapped[str] = mapped_column(Text, default="")

    report: Mapped["AnalysisReport"] = relationship(back_populates="scores")


class AIIndicatorReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_indicator_reports"

    report_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_reports.id", ondelete="CASCADE"), index=True)
    level: Mapped[str] = mapped_column(String(32), default="low")
    explanation: Mapped[str] = mapped_column(Text, default="")
    signals_json: Mapped[str] = mapped_column(Text, default="[]")
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default=(
            "AI-writing detection is inherently uncertain and should not be treated "
            "as proof that a student used AI."
        ),
    )


class ComparisonReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "comparison_reports"

    assignment_id: Mapped[UUID] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version_a_id: Mapped[UUID] = mapped_column(ForeignKey("assignment_versions.id"))
    version_b_id: Mapped[UUID] = mapped_column(ForeignKey("assignment_versions.id"))
    report_a_id: Mapped[UUID | None] = mapped_column(ForeignKey("analysis_reports.id"), nullable=True)
    report_b_id: Mapped[UUID | None] = mapped_column(ForeignKey("analysis_reports.id"), nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")

    assignment: Mapped["Assignment"] = relationship(back_populates="comparisons")
