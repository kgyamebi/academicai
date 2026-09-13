#!/usr/bin/env python3
"""CLI: encrypt a backup file with BACKUP_ENCRYPTION_KEY (AES-256-GCM)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from backup_crypto import encrypt_file  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: encrypt_backup_file.py src dest", file=sys.stderr)
        return 2
    key = (os.environ.get("BACKUP_ENCRYPTION_KEY") or "").strip()
    if not key:
        print("BACKUP_ENCRYPTION_KEY required", file=sys.stderr)
        return 2
    encrypt_file(Path(sys.argv[1]), Path(sys.argv[2]), key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
