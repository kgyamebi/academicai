from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.document import Document


class Citation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "citations"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    style_guess: Mapped[str | None] = mapped_column(String(32), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    locator: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paragraph_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start: Mapped[int] = mapped_column(Integer, default=0)
    char_end: Mapped[int] = mapped_column(Integer, default=0)
    matched_reference_id: Mapped[UUID | None] = mapped_column(nullable=True)

    document: Mapped["Document"] = relationship(back_populates="citations")


class Reference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "references"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(512), nullable=True)
    year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_fields: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["Document"] = relationship(back_populates="references")


class AcademicSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "academic_sources"

    doi: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    journal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), default="crossref")
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class SourceVerification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_verifications"

    reference_id: Mapped[UUID] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[UUID | None] = mapped_column(ForeignKey("academic_sources.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="could_not_verify")
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    provider: Mapped[str] = mapped_column(String(32), default="crossref")
