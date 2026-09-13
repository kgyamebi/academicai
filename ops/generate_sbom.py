"""Generate a CycloneDX-lite SBOM from pinned requirements (direct + extras)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"^([A-Za-z0-9_.\-]+)(\[[^\]]+\])?==([^;#\s]+)")


def parse_requirements(path: Path) -> list[dict]:
    comps = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        req, _, marker = line.partition(";")
        m = PIN.match(req.strip())
        if not m:
            raise SystemExit(f"Unpinned or unparsable requirement: {raw!r}")
        comps.append(
            {
                "type": "library",
                "name": m.group(1),
                "version": m.group(3),
                "purl": f"pkg:pypi/{m.group(1).lower()}@{m.group(3)}",
                "extra": (m.group(2) or "").strip("[]"),
                "marker": marker.strip(),
            }
        )
    return comps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    req = Path(args.requirements)
    comps = parse_requirements(req)
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "component": {"name": "academiccheck-backend", "type": "application"},
            "tools": [{"name": "ops/generate_sbom.py", "version": "1"}],
            "note": "Direct pins from requirements.txt. Transitives are enumerated by pip-audit/CI Trivy.",
        },
        "components": comps,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} components={len(comps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
