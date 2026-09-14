"""Email quality validation — syntax, public domain, disposable blocklist, MX/A DNS.

Launch policy: only real, deliverable-looking addresses. Tests (APP_ENV=test) skip
reserved-domain and MX so fixtures can use @example.com / @school.edu without DNS.
"""

from __future__ import annotations

import re
import socket
from functools import lru_cache

from fastapi import HTTPException, status

from app.config import get_settings

# Conservative local-part / domain pattern as a pre-filter before email-validator.
EMAIL_RE = re.compile(
    r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$",
    re.I,
)

RESERVED_LABELS = frozenset(
    {
        "example",
        "test",
        "invalid",
        "localhost",
        "local",
        "internal",
        "lan",
        "home",
        "corp",
        "localdomain",
    }
)

# Common disposable / temporary providers (expand via DISPOSABLE_EMAIL_DOMAINS).
DEFAULT_DISPOSABLE = frozenset(
    {
        "mailinator.com",
        "mailinator.net",
        "mailinator2.com",
        "10minutemail.com",
        "10minutemail.net",
        "tempmail.com",
        "temp-mail.org",
        "temp-mail.io",
        "guerrillamail.com",
        "guerrillamailblock.com",
        "guerrillamail.net",
        "guerrillamail.org",
        "sharklasers.com",
        "grr.la",
        "yopmail.com",
        "yopmail.fr",
        "trashmail.com",
        "trashmail.me",
        "discard.email",
        "mailnesia.com",
        "maildrop.cc",
        "getnada.com",
        "throwaway.email",
        "fakeinbox.com",
        "emailondeck.com",
        "mintemail.com",
        "moakt.com",
        "tmpmail.org",
        "tmpmail.net",
        "mailcatch.com",
        "mailnull.com",
        "spamgourmet.com",
        "mailnesia.com",
        "getairmail.com",
        "tempail.com",
        "tempr.email",
        "discardmail.com",
        "spam4.me",
        "mailforspam.com",
        "trash-mail.com",
        "mytemp.email",
        "emailtemporario.com.br",
        "tmpeml.com",
        "tempinbox.com",
        "mailnesia.com",
        "inboxbear.com",
        "mailpoof.com",
        "guerrillamail.de",
        "spamfree24.org",
        "wegwerfmail.de",
        "trash-mail.at",
        "kurzepost.de",
        "objectmail.com",
        "proxymail.eu",
        "rcpt.at",
        "trashmail.at",
        "trashmail.io",
        "wegwerfadresse.de",
        "tempsky.com",
        "emailfake.com",
        "fakemailgenerator.com",
        "generator.email",
        "mailsac.com",
        "harakirimail.com",
        "mailnesia.com",
        "sharklasers.com",
        "bccto.me",
    }
)

# Common typo domains that often resolve but are almost always user mistakes.
COMMON_TYPO_DOMAINS = frozenset(
    {
        "gail.com",
        "gamil.com",
        "gmial.com",
        "gmal.com",
        "gnail.com",
        "gmaill.com",
        "gmail.con",
        "gmail.co",
        "hotnail.com",
        "hotmai.com",
        "outlok.com",
        "outllok.com",
        "yahooo.com",
        "yaho.com",
    }
)

# Local-parts that are never valid for a student account signup.
BLOCKED_LOCAL_PARTS = frozenset(
    {
        "mailer-daemon",
        "postmaster",
        "abuse",
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "webmaster",
        "hostmaster",
    }
)


@lru_cache
def disposable_domains() -> frozenset[str]:
    settings = get_settings()
    extra = {d.strip().lower() for d in (settings.disposable_email_domains or "").split(",") if d.strip()}
    return frozenset(DEFAULT_DISPOSABLE | extra)


def clear_email_validation_caches() -> None:
    disposable_domains.cache_clear()


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _mx_required() -> bool:
    """Staging/production always require DNS; elsewhere honor EMAIL_VALIDATE_MX (default true)."""
    settings = get_settings()
    if settings.is_staging or settings.is_production:
        return True
    return bool(settings.email_validate_mx)


def assert_email_syntax(email: str) -> str:
    value = normalize_email(email)
    if not value or value.count("@") != 1 or ".." in value or not EMAIL_RE.match(value):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enter a valid email address.")
    local, _, domain = value.partition("@")
    if not local or not domain or len(value) > 254 or len(local) > 64:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enter a valid email address.")
    if local in BLOCKED_LOCAL_PARTS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Use a personal or school email address you can access.",
        )
    try:
        from email_validator import EmailNotValidError, validate_email

        result = validate_email(value, check_deliverability=False)
        return str(result.normalized).lower()
    except EmailNotValidError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enter a valid email address.") from exc
    except ImportError:
        return value


def assert_public_domain(email: str) -> str:
    """Reject reserved / non-public looking domains (Invoice App pattern)."""
    value = assert_email_syntax(email)
    settings = get_settings()
    if settings.app_env == "test":
        return value
    domain = value.split("@", 1)[1]
    labels = [p for p in domain.split(".") if p]
    if len(labels) < 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Use a real email domain, such as Gmail or your school address.",
        )
    tld = labels[-1]
    if len(tld) < 2 or not re.fullmatch(r"[a-z0-9-]{2,63}", tld, re.I):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Use a real email domain, such as Gmail or your school address.",
        )
    if any(label.lower() in RESERVED_LABELS for label in labels):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Use a real email domain, such as Gmail or your school address.",
        )
    return value


def assert_not_disposable(email: str) -> str:
    value = assert_public_domain(email)
    domain = value.split("@", 1)[1].lower()
    if domain in COMMON_TYPO_DOMAINS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "That email domain looks like a typo. Check the spelling (for example gmail.com) and try again.",
        )
    blocked = disposable_domains()
    if domain in blocked or any(domain.endswith("." + d) for d in blocked):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Temporary or disposable email addresses are not allowed. Use a permanent address you control.",
        )
    # Heuristic: obvious temp patterns in domain labels.
    joined = domain.replace("-", "").replace(".", "")
    if any(tok in domain for tok in ("tempmail", "tmpmail", "trashmail", "throwaway", "fakemail", "guerrilla")):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Temporary or disposable email addresses are not allowed. Use a permanent address you control.",
        )
    if "temp" in joined and "mail" in joined:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Temporary or disposable email addresses are not allowed. Use a permanent address you control.",
        )
    return value


def _dns_has_mx_or_a(domain: str) -> bool:
    try:
        import dns.exception
        import dns.resolver

        resolver = dns.resolver.Resolver(configure=True)
        resolver.lifetime = 3.0
        resolver.timeout = 2.0
        for rdtype in ("MX", "A", "AAAA"):
            try:
                answers = resolver.resolve(domain, rdtype)
                if answers:
                    return True
            except (dns.exception.DNSException, OSError, AttributeError, TypeError):
                continue
    except Exception:  # noqa: BLE001 — missing dnspython or broken resolver
        pass
    try:
        socket.getaddrinfo(domain, 25)
        return True
    except OSError:
        return False


def assert_mx_or_a(email: str) -> str:
    """DNS MX/A/AAAA check. Fail-closed when MX is required for this environment."""
    value = assert_not_disposable(email)
    if not _mx_required():
        return value
    domain = value.split("@", 1)[1]
    if not _dns_has_mx_or_a(domain):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "We could not verify that email domain. Check for typos and use an address that can receive mail.",
        )
    return value


def validate_registration_email(email: str) -> str:
    """Full registration / email-change gate — real addresses only."""
    return assert_mx_or_a(email)
