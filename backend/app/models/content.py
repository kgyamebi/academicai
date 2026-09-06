from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SeoPage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_pages"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    meta_description: Mapped[str] = mapped_column(String(320), default="")
    heading: Mapped[str] = mapped_column(String(255))
    body_markdown: Mapped[str] = mapped_column(Text)
    og_title: Mapped[str] = mapped_column(String(255), default="")
    canonical_path: Mapped[str] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(16), default="en")
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)


class BlogPost(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "blog_posts"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    excerpt: Mapped[str] = mapped_column(Text, default="")
    body_markdown: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(120), default="AcademicCheck AI")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)


class FAQ(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "faqs"

    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), default="general")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
