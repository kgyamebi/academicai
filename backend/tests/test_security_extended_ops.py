"""Pins, SBOM, license allow-list, CI fail-closed, container/network static proofs."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_python_requirements_are_pinned():
    text = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        req = line.split(";", 1)[0].strip()
        assert "==" in req, f"unpinned: {raw}"
        assert ">=" not in req and "~=" not in req


def test_frontend_package_json_has_no_caret_ranges():
    text = (ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
    assert '"^' not in text
    assert '"~' not in text


def test_ci_does_not_swallow_pip_audit():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert re.search(r"pip-audit[^\n]*\|\|\s*true", ci) is None
    assert "pip-audit -r requirements.txt" in ci


def test_generate_sbom_and_license_scan(tmp_path):
    import subprocess
    import sys

    sbom = tmp_path / "sbom.json"
    lic = tmp_path / "lic.json"
    subprocess.check_call(
        [sys.executable, str(ROOT / "ops" / "generate_sbom.py"), "--requirements", str(ROOT / "backend" / "requirements.txt"), "--out", str(sbom)]
    )
    subprocess.check_call(
        [sys.executable, str(ROOT / "ops" / "license_scan.py"), "--sbom", str(sbom), "--out", str(lic)]
    )
    data = __import__("json").loads(sbom.read_text(encoding="utf-8"))
    names = {c["name"] for c in data["components"]}
    assert "fastapi" in names and "cryptography" in names
    assert __import__("json").loads(lic.read_text(encoding="utf-8"))["ok"] is True


def test_backend_dockerfile_drops_root():
    text = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "USER 10001" in text
    assert "python:3.12-slim" in text
    assert "COPY .env" not in text


def test_frontend_dockerfile_drops_root_and_uses_npm_ci():
    text = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    assert "USER 10001" in text
    assert "npm ci" in text
    assert '"start"' in text


def test_prod_compose_does_not_publish_db_or_redis():
    text = (ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    # Host port publish looks like "5432:5432" or "6379:6379".
    assert re.search(r'["\']\d+:5432["\']', text) is None
    assert re.search(r'["\']\d+:6379["\']', text) is None
    assert "postgres:" in text and "redis:" in text
