from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        return kwargs
    settings = get_settings()
    kwargs["pool_size"] = settings.db_pool_size
    kwargs["max_overflow"] = settings.db_max_overflow
    kwargs["pool_recycle"] = 300
    kwargs["pool_timeout"] = 30
    kwargs["pool_use_lifo"] = True
    kwargs["query_cache_size"] = 1200
    kwargs["connect_args"] = {
        "connect_timeout": 3,
    }
    return kwargs


def _engine():
    url = get_settings().database_url
    return create_engine(url, **_engine_kwargs(url))


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

_read_engine = None
ReadSessionLocal = None


def _read_factory():
    global _read_engine, ReadSessionLocal
    url = (get_settings().database_read_url or "").strip()
    if not url:
        return SessionLocal
    if ReadSessionLocal is None:
        _read_engine = create_engine(url, **_engine_kwargs(url))
        ReadSessionLocal = sessionmaker(bind=_read_engine, autoflush=False, autocommit=False, class_=Session)
    return ReadSessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_read() -> Generator[Session, None, None]:
    """Read-mostly queries. Same as primary unless DATABASE_READ_URL is set.

    Replica reads are eventually consistent; list/dashboard/public data may lag writes.
    """
    db = _read_factory()()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
