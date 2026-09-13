"""Static Dockerfile + compose network policy audit."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    backend = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    frontend = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    prod = (ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    checks = {
        "backend_non_root": "USER 10001" in backend,
        "backend_slim_base": "python:3.12-slim" in backend,
        "backend_no_dotenv_copy": "COPY .env" not in backend,
        "frontend_non_root": "USER 10001" in frontend,
        "frontend_npm_ci": "npm ci" in frontend,
        "prod_no_host_postgres": re.search(r"\d+:5432", prod) is None,
        "prod_no_host_redis": re.search(r"\d+:6379", prod) is None,
    }
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": all(checks.values()),
        "checks": checks,
    }
    out = ROOT / "ops" / "cert_dockerfile_hardening.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
