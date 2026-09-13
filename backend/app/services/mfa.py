"""TOTP MFA for privileged accounts. Secrets stored encrypted at rest."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

import pyotp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_field, encrypt_field
from app.core.security import create_token, decode_token
from app.core.time import utcnow
from app.models.user import User

PRIVILEGED_ROLES = frozenset({"admin", "institution"})
BACKUP_CODE_COUNT = 8


def role_name(user: User) -> str:
    return user.role.name if user.role else "student"


def mfa_required_for_role(user: User) -> bool:
    """Admin/institution must complete MFA when enabled; enrollment is available to all."""
    return role_name(user) in PRIVILEGED_ROLES and bool(user.mfa_enabled)


def setup_totp(db: Session, user: User) -> dict:
    if user.is_guest:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Guests cannot enable MFA.")
    secret = pyotp.random_base32()
    user.mfa_secret_encrypted = encrypt_field(secret)
    user.mfa_enabled = False
    user.mfa_backup_codes_hash = None
    db.flush()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="AcademicCheck AI")
    return {"secret": secret, "otpauth_url": uri, "enabled": False}


def enable_totp(db: Session, user: User, code: str) -> dict:
    secret = decrypt_field(user.mfa_secret_encrypted or "")
    if not secret or secret.startswith("enc:"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Call MFA setup first.")
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid authenticator code.")
    plain_codes = [secrets.token_hex(4) for _ in range(BACKUP_CODE_COUNT)]
    user.mfa_backup_codes_hash = _hash_backup_list(plain_codes)
    user.mfa_enabled = True
    user.mfa_confirmed_at = utcnow()
    db.flush()
    return {"enabled": True, "backup_codes": plain_codes}


def disable_totp(db: Session, user: User, code: str) -> None:
    if not user.mfa_enabled:
        return
    if not verify_user_mfa(user, code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid MFA code.")
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_backup_codes_hash = None
    user.mfa_confirmed_at = None
    db.flush()


def verify_user_mfa(user: User, code: str) -> bool:
    code = (code or "").strip().replace(" ", "")
    secret = decrypt_field(user.mfa_secret_encrypted or "")
    if secret and not secret.startswith("enc:") and pyotp.TOTP(secret).verify(code, valid_window=1):
        return True
    return _consume_backup_code(user, code)


def _hash_backup_list(codes: list[str]) -> str:
    return ",".join(hashlib.sha256(c.encode("utf-8")).hexdigest() for c in codes)


def _consume_backup_code(user: User, code: str) -> bool:
    stored = user.mfa_backup_codes_hash or ""
    if not stored:
        return False
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    parts = stored.split(",")
    if digest not in parts:
        return False
    parts = [p for p in parts if p != digest]
    user.mfa_backup_codes_hash = ",".join(parts) if parts else None
    return True


def issue_mfa_challenge(user: User) -> str:
    return create_token(str(user.id), "mfa_challenge", expires_delta=timedelta(minutes=5))


def issue_mfa_enroll_challenge(user: User) -> str:
    """Short-lived token after password auth so privileged users can enroll MFA without a session."""
    return create_token(str(user.id), "mfa_enroll", expires_delta=timedelta(minutes=10))


def user_from_enroll_token(db: Session, enroll_token: str) -> User:
    from uuid import UUID

    try:
        payload = decode_token(enroll_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA enrollment expired. Sign in again.") from exc
    if payload.get("typ") != "mfa_enroll":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid MFA enrollment token.")
    try:
        user = db.get(User, UUID(str(payload.get("sub"))))
    except (ValueError, TypeError):
        user = None
    if not user or user.deleted_at or user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account unavailable.")
    if role_name(user) not in PRIVILEGED_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Enrollment token is for privileged accounts only.")
    if user.mfa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "MFA is already enabled. Sign in with your authenticator.")
    return user


def complete_mfa_challenge(db: Session, challenge_token: str, code: str) -> User:
    from uuid import UUID

    try:
        payload = decode_token(challenge_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA challenge expired.") from exc
    if payload.get("typ") != "mfa_challenge":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid MFA challenge.")
    try:
        user = db.get(User, UUID(str(payload.get("sub"))))
    except (ValueError, TypeError):
        user = None
    if not user or not user.mfa_enabled:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA is not enabled for this account.")
    if not verify_user_mfa(user, code):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid MFA code.")
    return user


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
