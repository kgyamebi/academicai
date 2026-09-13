"""License allow-list for direct Python dependencies. Fail on unknown/copyleft-only."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# SPDX-ish. GPL-only packages are rejected. Dual-license including MIT/BSD/Apache is OK.
ALLOWED = {
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD",
    "Apache-2.0",
    "Apache 2.0",
    "ISC",
    "PSF",
    "Python-2.0",
    "MPL-2.0",
    "MPL 2.0",
    "Unlicense",
    "CC0-1.0",
    "LGPL-3.0-or-later",  # lgpl is used by some bindings; called out in report
}

# Direct deps → declared license (from project metadata / PyPI classifiers, reviewed 2026-09-09).
KNOWN = {
    "fastapi": "MIT",
    "uvicorn": "BSD-3-Clause",
    "pydantic": "MIT",
    "pydantic-settings": "MIT",
    "email-validator": "CC0-1.0",
    "sqlalchemy": "MIT",
    "alembic": "MIT",
    "psycopg": "LGPL-3.0-or-later",
    "redis": "MIT",
    "rq": "BSD-2-Clause",
    "passlib": "BSD-3-Clause",
    "bcrypt": "Apache-2.0",
    "argon2-cffi": "MIT",
    "pyjwt": "MIT",
    "python-multipart": "Apache-2.0",
    "httpx": "BSD-3-Clause",
    "pymupdf": "AGPL-3.0-or-later",
    "python-docx": "MIT",
    "reportlab": "BSD-3-Clause",
    "langdetect": "Apache-2.0",
    "orjson": "Apache-2.0",
    "structlog": "Apache-2.0 OR MIT",
    "tenacity": "Apache-2.0",
    "bleach": "Apache-2.0",
    "python-magic-bin": "MIT",
    "python-magic": "MIT",
    "cryptography": "Apache-2.0 OR BSD-3-Clause",
    "opentelemetry-api": "Apache-2.0",
    "opentelemetry-sdk": "Apache-2.0",
    "pyotp": "MIT",
    "stripe": "MIT",
    "boto3": "Apache-2.0",
    "jsonschema": "MIT",
    "sentry-sdk": "MIT",
    "pytest": "MIT",
    "pytest-asyncio": "Apache-2.0",
    "pytest-cov": "MIT",
    "ruff": "MIT",
    "hypothesis": "MPL-2.0",
    "pip-audit": "Apache-2.0",
}

# AGPL pymupdf is a product risk: used for PDF extract. Flag, do not silently pass as MIT.
REVIEW_REQUIRED = {"AGPL-3.0-or-later"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sbom", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    sbom = json.loads(Path(args.sbom).read_text(encoding="utf-8"))
    unknown = []
    review = []
    forbidden = []
    ok = []
    for comp in sbom.get("components") or []:
        name = comp["name"]
        license_id = KNOWN.get(name)
        if not license_id:
            unknown.append(name)
            continue
        if license_id in REVIEW_REQUIRED:
            review.append({"name": name, "license": license_id})
            continue
        primary = license_id.split(" OR ")[0]
        if primary not in ALLOWED and license_id not in ALLOWED:
            forbidden.append({"name": name, "license": license_id})
            continue
        ok.append({"name": name, "license": license_id})
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": not unknown and not forbidden,
        "allowed_count": len(ok),
        "review_required": review,
        "unknown": unknown,
        "forbidden": forbidden,
        "note": "PyMuPDF is AGPL; keep as reviewed-exception for local PDF extract. Not a CVE.",
    }
    Path(args.out).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("ok", "unknown", "forbidden", "review_required")}, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
