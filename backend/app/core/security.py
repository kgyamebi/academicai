import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.config import get_settings

TokenType = Literal["access", "refresh", "verify", "reset", "guest", "mfa_challenge", "mfa_enroll"]

_DUMMY_BCRYPT = bcrypt.hashpw(b"timing-dummy-not-a-real-password", bcrypt.gensalt()).decode("utf-8")
_COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "passw0rd",
    "12345678",
    "123456789",
    "1234567890",
    "qwerty12",
    "qwerty123",
    "letmein1",
    "welcome1",
    "welcome123",
    "admin123",
    "admin1234",
    "changeme",
    "changeme1",
    "academic",
    "academic1",
    "iloveyou1",
    "monkey12",
    "dragon12",
    "master12",
    "login123",
    "abc12345",
    "football1",
    "baseball1",
    "sunshine1",
    "princess1",
    "superman1",
    "trustno1",
    "whatever1",
    "starwars1",
}

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

    _ARGON = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
except Exception:  # noqa: BLE001
    PasswordHasher = None  # type: ignore[misc, assignment]
    InvalidHash = VerificationError = VerifyMismatchError = Exception  # type: ignore[misc, assignment]
    _ARGON = None


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    if _ARGON is not None:
        return _ARGON.hash(password)
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        bcrypt.checkpw(_password_bytes(password), _DUMMY_BCRYPT.encode("utf-8"))
        return False
    if password_hash.startswith("$argon2"):
        if _ARGON is None:
            return False
        try:
            _ARGON.verify(password_hash, password)
            return True
        except (VerifyMismatchError, VerificationError, InvalidHash):
            return False
    try:
        return bcrypt.checkpw(_password_bytes(password), password_hash.encode("utf-8"))
    except ValueError:
        return False


def dummy_password_check(password: str) -> None:
    """Equalize login timing when the account does not exist."""
    verify_password(password, _DUMMY_BCRYPT)


def password_needs_rehash(password_hash: str | None) -> bool:
    if not password_hash or _ARGON is None:
        return False
    if password_hash.startswith("$2"):
        return True
    if password_hash.startswith("$argon2"):
        try:
            return bool(_ARGON.check_needs_rehash(password_hash))
        except Exception:  # noqa: BLE001
            return False
    return False


def assert_password_policy(password: str) -> None:
    """Reject weak and commonly breached passwords (local denylist — not a live HIBP API)."""
    if password.lower() in _COMMON_PASSWORDS:
        raise ValueError("Choose a stronger password.")
    if password.isalpha() or password.isdigit():
        raise ValueError("Password must include letters and numbers.")
    if re.fullmatch(r"(.)\1{7,}", password):
        raise ValueError("Choose a stronger password.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")


def create_token(
    subject: str,
    token_type: TokenType,
    extra: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(minutes=settings.access_token_minutes)
        elif token_type == "refresh":
            expires_delta = timedelta(days=settings.refresh_token_days)
        elif token_type == "verify":
            expires_delta = timedelta(hours=settings.email_verification_hours)
        elif token_type == "guest":
            expires_delta = timedelta(hours=settings.guest_retention_hours)
        else:
            expires_delta = timedelta(hours=settings.password_reset_hours)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    # Explicit allow-list only — rejects alg=none and algorithm confusion.
    allowed = [settings.jwt_algorithm]
    if settings.jwt_algorithm.upper() not in {"HS256", "HS384", "HS512"}:
        raise jwt.InvalidTokenError("Unsupported JWT algorithm configuration.")
    keys = [settings.jwt_secret_key]
    previous = (settings.jwt_secret_previous or "").strip()
    if previous and previous != settings.jwt_secret_key:
        keys.append(previous)
    last_error: Exception | None = None
    for key in keys:
        try:
            return jwt.decode(
                token,
                key,
                algorithms=allowed,
                options={"require": ["exp", "sub", "typ"], "verify_aud": False},
            )
        except jwt.InvalidTokenError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise jwt.InvalidTokenError("Invalid token.")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def new_id() -> UUID:
    return uuid4()
