"""Compare restored DB to backup manifest. Hard PASS/FAIL. Never writes to any DB."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def _load_manifest_mod():
    path = ROOT / "ops" / "prod_dr_manifest.py"
    spec = importlib.util.spec_from_file_location("prod_dr_manifest", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _looks_prod(url: str, normalize) -> bool:
    host = (urlparse(normalize(url)).hostname or "").lower()
    if host in {"127.0.0.1", "localhost"}:
        return False
    markers = ("rds.amazonaws.com", "neon.tech", "supabase.co", "azure.com", "cloudsql")
    return any(m in host for m in markers)


def compare(tables, expected: dict, actual: dict) -> dict:
    mismatches = []
    exp_counts = expected.get("row_counts") or {}
    act_counts = actual.get("row_counts") or {}
    exp_fp = expected.get("fingerprints") or {}
    act_fp = actual.get("fingerprints") or {}
    exp_spot = expected.get("spot_checks") or {}
    act_spot = actual.get("spot_checks") or {}

    for table in tables:
        if exp_counts.get(table, -1) < 0 and act_counts.get(table, -1) < 0:
            continue
        if exp_counts.get(table) != act_counts.get(table):
            mismatches.append(
                {
                    "table": table,
                    "field": "row_count",
                    "expected": exp_counts.get(table),
                    "actual": act_counts.get(table),
                }
            )
        if exp_fp.get(table) != act_fp.get(table):
            mismatches.append(
                {
                    "table": table,
                    "field": "fingerprint",
                    "expected": exp_fp.get(table),
                    "actual": act_fp.get(table),
                }
            )
        e_spot = exp_spot.get(table) or {}
        a_spot = act_spot.get(table) or {}
        for key in ("min_id", "max_id"):
            if e_spot.get(key) != a_spot.get(key):
                mismatches.append(
                    {
                        "table": table,
                        "field": f"spot_{key}",
                        "expected": e_spot.get(key),
                        "actual": a_spot.get(key),
                    }
                )
    return {
        "match": len(mismatches) == 0,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:50],
    }


def functional_http(base_url: str) -> dict:
    import urllib.error
    import urllib.request

    checks = {}
    for path in ("/api/live", "/api/ready"):
        url = base_url.rstrip("/") + path
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="replace")[:500]
                checks[path] = {"ok": 200 <= resp.status < 300, "status": resp.status, "body": body}
        except urllib.error.HTTPError as exc:
            checks[path] = {"ok": False, "status": exc.code, "body": str(exc)[:300]}
        except Exception as exc:  # noqa: BLE001
            checks[path] = {"ok": False, "status": None, "body": str(exc)[:300]}
    return checks


def functional_login(base_url: str, email: str, password: str) -> dict:
    import json as _json
    import urllib.error
    import urllib.request

    url = base_url.rstrip("/") + "/api/auth/login"
    data = _json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:800]
            return {"ok": 200 <= resp.status < 300, "status": resp.status, "body": body}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "body": str(exc)[:300]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "body": str(exc)[:300]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify isolated restore against backup manifest")
    parser.add_argument("--manifest", required=True, help="Path to pre-dump manifest JSON")
    parser.add_argument("--database-url", default=os.environ.get("RESTORE_DATABASE_URL", ""))
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_prod_dr_verify.json"))
    parser.add_argument("--app-base-url", default=os.environ.get("PROD_DR_APP_BASE_URL", ""))
    parser.add_argument("--require-login", action="store_true")
    parser.add_argument("--allow-prod-url", action="store_true", help="Dangerous; do not use for drills")
    args = parser.parse_args()

    mod = _load_manifest_mod()

    if not args.database_url:
        print("FAIL: --database-url or RESTORE_DATABASE_URL required", file=sys.stderr)
        return 2

    if not args.allow_prod_url and _looks_prod(args.database_url, mod._normalize_url):
        print("FAIL: refusing to verify against a production-looking URL", file=sys.stderr)
        return 3

    expected = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    from sqlalchemy import create_engine

    engine = create_engine(mod._normalize_url(args.database_url), pool_pre_ping=True)
    try:
        actual = mod.build_manifest(engine, phase="post_restore")
    finally:
        engine.dispose()

    comparison = compare(mod.TABLES, expected, actual)
    functional = {}
    login = None
    if args.app_base_url:
        functional = functional_http(args.app_base_url)
        email = os.environ.get("PROD_DR_VERIFY_EMAIL", "")
        password = os.environ.get("PROD_DR_VERIFY_PASSWORD", "")
        if email and password:
            login = functional_login(args.app_base_url, email, password)
        elif args.require_login:
            login = {"ok": False, "status": None, "body": "PROD_DR_VERIFY_EMAIL/PASSWORD not set"}

    http_ok = True
    if args.app_base_url:
        http_ok = all(v.get("ok") for v in functional.values())
    login_ok = True if login is None else bool(login.get("ok"))

    passed = bool(comparison["match"] and http_ok and login_ok)
    report = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "manifest_match": comparison["match"],
        "mismatch_count": comparison["mismatch_count"],
        "mismatches": comparison["mismatches"],
        "expected_row_counts": expected.get("row_counts"),
        "actual_row_counts": actual.get("row_counts"),
        "expected_database_bytes": expected.get("database_bytes"),
        "actual_database_bytes": actual.get("database_bytes"),
        "functional_http": functional,
        "functional_login": login,
        "writes_to_production": False,
        "isolated_verification": True,
    }
    out = Path(args.out)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": report["verdict"],
                "pass": passed,
                "mismatch_count": report["mismatch_count"],
                "out": str(out),
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
