"""Google and Microsoft OAuth (authorization code + PKCE)."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger
from app.core.security import create_token, decode_token
from app.core.time import utcnow
from app.models.user import OAuthAccount, User
from app.services.auth import _ensure_free_subscription, get_role
from app.services.security_events import record_security_event

log = get_logger("oauth")

PROVIDERS = ("google", "microsoft")
OAUTH_STATE_COOKIE = "ac_oauth_state"
OAUTH_NEXT_COOKIE = "ac_oauth_next"


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: str


@dataclass(frozen=True)
class OAuthProfile:
    provider: str
    subject: str
    email: str
    email_verified: bool
    full_name: str
    raw: dict[str, Any]


def configured_providers() -> list[str]:
    settings = get_settings()
    out: list[str] = []
    if settings.google_oauth_client_id.strip() and settings.google_oauth_client_secret.strip():
        out.append("google")
    if settings.microsoft_oauth_client_id.strip() and settings.microsoft_oauth_client_secret.strip():
        out.append("microsoft")
    return out


def _provider_config(provider: str) -> ProviderConfig:
    settings = get_settings()
    name = provider.lower().strip()
    if name == "google":
        if not (settings.google_oauth_client_id and settings.google_oauth_client_secret):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google sign-in is not configured.")
        return ProviderConfig(
            name="google",
            client_id=settings.google_oauth_client_id.strip(),
            client_secret=settings.google_oauth_client_secret.strip(),
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            scopes="openid email profile",
        )
    if name == "microsoft":
        if not (settings.microsoft_oauth_client_id and settings.microsoft_oauth_client_secret):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Microsoft sign-in is not configured.")
        return ProviderConfig(
            name="microsoft",
            client_id=settings.microsoft_oauth_client_id.strip(),
            client_secret=settings.microsoft_oauth_client_secret.strip(),
            authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            userinfo_url="https://graph.microsoft.com/v1.0/me",
            scopes="openid email profile User.Read offline_access",
        )
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown sign-in provider.")


def redirect_uri(provider: str) -> str:
    settings = get_settings()
    base = (settings.oauth_redirect_base or "").strip()
    if not base:
        api = (settings.app_api_url or "").strip().rstrip("/")
        # Prefer public web origin when API URL is loopback (common Docker/Caddy setup).
        if not api or "127.0.0.1" in api or "localhost" in api or api.startswith("http://0.0.0.0"):
            base = (settings.app_web_url or "").strip().rstrip("/")
        else:
            base = api
    base = base.rstrip("/")
    return f"{base}/api/auth/oauth/{provider}/callback"


def issue_oauth_state(*, provider: str, code_verifier: str, next_path: str) -> str:
    return create_token(
        "oauth",
        "oauth_state",
        extra={"provider": provider, "cv": code_verifier, "next": next_path},
    )


def parse_oauth_state(state: str, *, provider: str) -> dict[str, str]:
    try:
        payload = decode_token(state)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sign-in session expired. Try again.") from exc
    if payload.get("typ") != "oauth_state" or payload.get("sub") != "oauth" or payload.get("provider") != provider:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid sign-in state.")
    cv = str(payload.get("cv") or "")
    if not cv:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid sign-in state.")
    next_path = str(payload.get("next") or "/app/dashboard")
    return {"code_verifier": cv, "next": _safe_next(next_path)}


def _safe_next(path: str) -> str:
    if not path.startswith("/") or path.startswith("//") or "://" in path:
        return "/app/dashboard"
    return path


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = hashlib.sha256(verifier.encode("ascii")).digest()
    import base64

    challenge_b64 = base64.urlsafe_b64encode(challenge).rstrip(b"=").decode("ascii")
    return verifier, challenge_b64


def build_authorize_url(provider: str, *, state: str, code_challenge: str) -> str:
    cfg = _provider_config(provider)
    params = {
        "client_id": cfg.client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri(provider),
        "scope": cfg.scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if provider == "google":
        params["access_type"] = "online"
        params["prompt"] = "select_account"
    if provider == "microsoft":
        params["response_mode"] = "query"
    return f"{cfg.authorize_url}?{urlencode(params)}"


def exchange_code(provider: str, *, code: str, code_verifier: str) -> OAuthProfile:
    cfg = _provider_config(provider)
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri(provider),
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "code_verifier": code_verifier,
    }
    with httpx.Client(timeout=20.0) as client:
        token_res = client.post(cfg.token_url, data=data, headers={"Accept": "application/json"})
        if token_res.status_code >= 400:
            log.warning("oauth_token_failed", provider=provider, status=token_res.status_code, body=token_res.text[:300])
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not complete social sign-in.")
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not complete social sign-in.")
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        info_res = client.get(cfg.userinfo_url, headers=headers)
        if info_res.status_code >= 400:
            log.warning("oauth_userinfo_failed", provider=provider, status=info_res.status_code, body=info_res.text[:300])
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not load your profile from the provider.")
        profile = info_res.json()
    return _normalize_profile(provider, profile)


def _normalize_profile(provider: str, profile: dict[str, Any]) -> OAuthProfile:
    if provider == "google":
        email = str(profile.get("email") or "").strip().lower()
        subject = str(profile.get("sub") or "").strip()
        verified = bool(profile.get("email_verified"))
        name = str(profile.get("name") or "").strip()
    else:
        email = str(profile.get("mail") or profile.get("userPrincipalName") or profile.get("email") or "").strip().lower()
        # Prefer stable Azure AD object id
        subject = str(profile.get("id") or profile.get("sub") or "").strip()
        verified = bool(email)  # Graph me requires authenticated account
        name = str(profile.get("displayName") or profile.get("name") or "").strip()
        # Strip #EXT# guest UPNs to email-like if needed
        if email and "#ext#" in email:
            email = email.split("#ext#")[0].replace("_", "@", 1)
    if not subject:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provider did not return a stable user id.")
    if not email or "@" not in email:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Your account did not share an email address. Allow email access and try again.",
        )
    return OAuthProfile(
        provider=provider,
        subject=subject,
        email=email,
        email_verified=verified,
        full_name=name[:200],
        raw=profile,
    )


def upsert_oauth_user(
    db: Session,
    profile: OAuthProfile,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[User, bool]:
    """Return (user, created). Links existing email accounts; marks verified when IdP asserts it."""
    link = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == profile.provider,
            OAuthAccount.provider_subject == profile.subject,
        )
    )
    if link:
        user = db.get(User, link.user_id)
        if not user or user.deleted_at is not None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not available.")
        if user.is_suspended or not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not active.")
        link.email = profile.email
        link.email_verified = profile.email_verified
        link.raw_profile = json.dumps(profile.raw)[:8000]
        if profile.email_verified and not user.email_verified_at:
            user.email_verified_at = utcnow()
            user.pending_email = None
        if profile.full_name and not user.full_name:
            user.full_name = profile.full_name
        user.last_login_at = utcnow()
        user.is_guest = False
        record_security_event(db, "oauth_login", user_id=user.id, ip_address=ip, user_agent=user_agent, details=profile.provider)
        return user, False

    existing = db.scalar(select(User).where(User.email == profile.email, User.deleted_at.is_(None)))
    created = False
    if existing and not existing.is_guest:
        user = existing
        if user.is_suspended or not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not active.")
    else:
        user = existing or User(email=profile.email)
        user.email = profile.email
        user.full_name = profile.full_name or user.full_name or ""
        user.is_guest = False
        user.is_active = True
        user.password_hash = user.password_hash  # keep if converting guest with password
        if not user.role:
            user.role = get_role(db, "student")
        created = existing is None or bool(existing and existing.is_guest)
        db.add(user)
        db.flush()
        _ensure_free_subscription(db, user)
        record_security_event(
            db,
            "account_created",
            user_id=user.id,
            ip_address=ip,
            user_agent=user_agent,
            details=f"oauth:{profile.provider}",
        )

    if profile.email_verified:
        user.email_verified_at = user.email_verified_at or utcnow()
        user.pending_email = None
    if profile.full_name and not user.full_name:
        user.full_name = profile.full_name
    user.last_login_at = utcnow()
    if not user.role:
        user.role = get_role(db, "student")

    db.add(
        OAuthAccount(
            user_id=user.id,
            provider=profile.provider,
            provider_subject=profile.subject,
            email=profile.email,
            email_verified=profile.email_verified,
            raw_profile=json.dumps(profile.raw)[:8000],
        )
    )
    record_security_event(
        db,
        "oauth_linked" if not created else "oauth_login",
        user_id=user.id,
        ip_address=ip,
        user_agent=user_agent,
        details=profile.provider,
    )
    return user, created
