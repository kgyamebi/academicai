"""Validate Grafana dashboard JSON + Prometheus alert rules; optional live stack check."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAFANA = ROOT / "ops" / "grafana"
RULES = ROOT / "ops" / "prometheus" / "alert-rules.yml"


def validate_dashboards() -> list[str]:
    errors = []
    for path in sorted(GRAFANA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.name}: root must be object")
            continue
        if "panels" not in data and "rows" not in data and "templating" not in data:
            # Grafana 7+ often uses panels; some use schemaVersion only
            if "schemaVersion" not in data and "title" not in data:
                errors.append(f"{path.name}: missing Grafana dashboard keys")
    return errors


def validate_alert_rules() -> list[str]:
    errors = []
    text = RULES.read_text(encoding="utf-8")
    if "groups:" not in text:
        errors.append("alert-rules.yml missing groups:")
    if "expr:" not in text:
        errors.append("alert-rules.yml missing expr:")
    # Prefer pyyaml if available
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if not isinstance(data, dict) or "groups" not in data:
            errors.append("alert-rules.yml failed YAML groups parse")
        else:
            for group in data["groups"]:
                for rule in group.get("rules") or []:
                    if "alert" in rule and "expr" not in rule:
                        errors.append(f"rule {rule.get('alert')} missing expr")
    except ImportError:
        pass
    return errors


def optional_live_check() -> dict:
    out = {"prometheus": None, "grafana": None}
    for name, url in (("prometheus", "http://127.0.0.1:9090/-/ready"), ("grafana", "http://127.0.0.1:3001/api/health")):
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                out[name] = resp.status
        except Exception as exc:  # noqa: BLE001
            out[name] = f"unreachable:{exc.__class__.__name__}"
    return out


def main() -> int:
    errors = validate_dashboards() + validate_alert_rules()
    live = optional_live_check()
    report = {
        "pass": not errors,
        "dashboard_count": len(list(GRAFANA.glob("*.json"))),
        "errors": errors,
        "live_stack": live,
        "note": "Live prometheus/grafana status is optional; syntax validation is required.",
    }
    out = ROOT / "ops" / "cert_observability_validate.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
