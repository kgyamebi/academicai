"""Fail CI if security scanners are swallowed (|| true / continue-on-error)."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# Security-relevant command patterns that must not be followed by || true.
BLOCKED = (
    r"pip-audit[^&\n]*\|\|\s*true",
    r"npm audit[^&\n]*\|\|\s*true",
    r"trivy[^&\n]*\|\|\s*true",
    r"pip-licenses[^&\n]*\|\|\s*true",
)


def main() -> int:
    problems: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"continue-on-error:\s*true", text):
            problems.append(f"{path.name}: continue-on-error: true")
        for pat in BLOCKED:
            if re.search(pat, text):
                problems.append(f"{path.name}: swallowed scanner ({pat})")
        if path.name == "ci.yml" and "|| true" in text and "pip-audit" in text:
            # Any remaining pip-audit || true
            if re.search(r"pip-audit.*\|\|\s*true", text):
                problems.append("ci.yml: pip-audit still uses || true")
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": not problems,
        "problems": problems,
        "threshold": "any known CVE (pip-audit); npm audit --audit-level=high; trivy HIGH+",
    }
    out = ROOT / "ops" / "cert_ci_security_gates.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
