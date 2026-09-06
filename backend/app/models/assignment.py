from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis import AnalysisJob, ComparisonReport
    from app.models.document import Document
    from app.models.user import User


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "assignments"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled assignment")
    academic_level: Mapped[str] = mapped_column(String(64), default="undergraduate")
    citation_style: Mapped[str] = mapped_column(String(32), default="apa7")
    discipline: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)

    user: Mapped["User"] = relationship(back_populates="assignments")
    question: Mapped["AssignmentQuestion | None"] = relationship(
        back_populates="assignment", uselist=False, cascade="all, delete-orphan"
    )
    rubric: Mapped["Rubric | None"] = relationship(
        back_populates="assignment", uselist=False, cascade="all, delete-orphan"
    )
    versions: Mapped[list["AssignmentVersion"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="assignment")
    jobs: Mapped[list["AnalysisJob"]] = relationship(back_populates="assignment")
    comparisons: Mapped[list["ComparisonReport"]] = relationship(back_populates="assignment")


class AssignmentQuestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assignment_questions"

    assignment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), unique=True, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text)
    command_words: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[str] = mapped_column(Text, default="")
    scope: Mapped[str] = mapped_column(Text, default="")
    required_concepts: Mapped[str] = mapped_column(Text, default="")
    interpretation: Mapped[str] = mapped_column(Text, default="")
    analysis_json: Mapped[str] = mapped_column(Text, default="{}")

    assignment: Mapped["Assignment"] = relationship(back_populates="question")


class Rubric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rubrics"

    assignment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="Assignment rubric")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="pasted")

    assignment: Mapped["Assignment"] = relationship(back_populates="rubric")
    criteria: Mapped[list["RubricCriterion"]] = relationship(
        back_populates="rubric", cascade="all, delete-orphan"
    )


class RubricCriterion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rubric_criteria"

    rubric_id: Mapped[UUID] = mapped_column(ForeignKey("rubrics.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    weight_percent: Mapped[int] = mapped_column(Integer, default=0)
    max_points: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    rubric: Mapped["Rubric"] = relationship(back_populates="criteria")


class AssignmentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "assignment_versions"

    assignment_id: Mapped[UUID] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), default="Draft 1")
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    assignment: Mapped["Assignment"] = relationship(back_populates="versions")
