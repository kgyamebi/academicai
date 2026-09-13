"""Shared safety guards for production DR backup/restore.

Used by shell wrappers and unit tests. Never connects to a database.
"""

from __future__ import annotations

from urllib.parse import urlparse


CONFIRM_TOKEN = "I_UNDERSTAND_THIS_IS_NOT_PRODUCTION"


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def looks_nonprod_source(url: str) -> bool:
    """True if URL looks like local/dev (refused for production backup certification)."""
    h = _host(url)
    u = url.lower()
    if h in {"127.0.0.1", "localhost"}:
        return True
    if "@postgres:" in u or "@pgbouncer:" in u:
        return True
    if "academiccheck:academiccheck@" in u:
        return True
    return False


def looks_managed_prod_host(url: str) -> bool:
    h = _host(url)
    markers = ("rds.amazonaws.com", "neon.tech", "supabase.co", "azure.com", "cloudsql")
    return any(m in h for m in markers)


def is_loopback_target(url: str) -> bool:
    h = _host(url)
    return h in {"127.0.0.1", "localhost"} or "dr-restore-postgres" in url.lower()


def guard_backup_url(url: str, *, allow_nonprod: bool = False) -> None:
    if not url:
        raise SystemExit("FATAL: PROD_DATABASE_URL is empty")
    if not allow_nonprod and looks_nonprod_source(url):
        raise SystemExit(
            "REFUSED: URL looks non-production. Set ALLOW_NONPROD_BACKUP=1 only for dry-runs."
        )


def guard_restore_url(
    restore_url: str,
    *,
    confirm: str,
    prod_url: str | None = None,
    allow_nonlocal_isolated: bool = False,
) -> None:
    if confirm != CONFIRM_TOKEN:
        raise SystemExit(
            "FATAL: set CONFIRM_ISOLATED_RESTORE=I_UNDERSTAND_THIS_IS_NOT_PRODUCTION"
        )
    if not restore_url:
        raise SystemExit("FATAL: RESTORE_DATABASE_URL is empty")
    if prod_url and restore_url == prod_url:
        raise SystemExit("FATAL: RESTORE_DATABASE_URL equals PROD_DATABASE_URL — refusing.")
    if not is_loopback_target(restore_url) and not allow_nonlocal_isolated:
        raise SystemExit(
            "FATAL: restore URL is not localhost. Use isolated compose or set I_CONFIRM_NONLOCAL_ISOLATED=1."
        )
    if looks_managed_prod_host(restore_url):
        raise SystemExit("FATAL: refuse restoring into a URL that looks like managed production.")


def main_backup() -> None:
    import os

    guard_backup_url(
        os.environ.get("PROD_DATABASE_URL") or os.environ.get("DATABASE_URL") or "",
        allow_nonprod=os.environ.get("ALLOW_NONPROD_BACKUP") == "1",
    )


def main_restore() -> None:
    import os

    guard_restore_url(
        os.environ.get("RESTORE_DATABASE_URL") or "",
        confirm=os.environ.get("CONFIRM_ISOLATED_RESTORE") or "",
        prod_url=os.environ.get("PROD_DATABASE_URL") or None,
        allow_nonlocal_isolated=os.environ.get("I_CONFIRM_NONLOCAL_ISOLATED") == "1",
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or sys.argv[1] not in {"backup", "restore"}:
        print("usage: prod_dr_guards.py backup|restore", file=sys.stderr)
        raise SystemExit(2)
    try:
        if sys.argv[1] == "backup":
            main_backup()
        else:
            main_restore()
    except SystemExit as exc:
        msg = str(exc)
        if msg and msg != "0":
            print(msg, file=sys.stderr)
            raise SystemExit(3) from None
        raise
