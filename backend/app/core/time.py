from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def is_past(value: datetime | None, *, now: datetime | None = None) -> bool:
    aware = as_utc(value)
    if aware is None:
        return False
    return aware < (now or utcnow())
