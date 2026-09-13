"""Validate S3 CRR config-as-code. Does not call AWS."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "ops" / "s3_crr_replication.json"


def validate(cfg: dict) -> list[str]:
    errors: list[str] = []
    if cfg.get("live_account_required") is not True:
        errors.append("must declare live_account_required")
    if cfg.get("local_emulator_cannot_prove_crr") is not True:
        errors.append("must declare CRR cannot be proven on MinIO")
    repl = cfg.get("ReplicationConfiguration") or {}
    if not str(repl.get("Role", "")).startswith("arn:aws:iam::"):
        errors.append("Role must be an IAM ARN template")
    rules = repl.get("Rules") or []
    if not rules:
        errors.append("at least one replication rule")
    else:
        rule = rules[0]
        if rule.get("Status") != "Enabled":
            errors.append("rule Status must be Enabled")
        dest = (rule.get("Destination") or {}).get("Bucket", "")
        if not str(dest).startswith("arn:aws:s3:::"):
            errors.append("Destination.Bucket must be an S3 ARN template")
        if not (rule.get("Filter") or {}).get("Prefix"):
            errors.append("Filter.Prefix required")
    if not cfg.get("VersioningRequired"):
        errors.append("VersioningRequired must be true (S3 CRR prerequisite)")
    return errors


def main() -> int:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    errors = validate(cfg)
    payload = {
        "config": "ops/s3_crr_replication.json",
        "syntax_ok": not errors,
        "errors": errors,
        "replication_succeeded": False,
        "reason": "CRR requires two real regional buckets plus IAM. Not executed.",
    }
    out = ROOT / "ops" / "cert_crr_config.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["syntax_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
