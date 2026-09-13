#!/usr/bin/env python3
"""Local SMTP sink for development — no Docker / no vendor credentials.

Listens on SMTP (default 1025), stores .eml files under ops/evidence/mail/,
and prints subject lines. Point the API at it:

  EMAIL_PROVIDER=smtp
  SMTP_HOST=127.0.0.1
  SMTP_PORT=1025
  SMTP_TLS=disabled
  SMTP_USER=
  SMTP_PASSWORD=
  EMAIL_FROM=noreply@academiccheck.local
  EMAIL_SMTP_PROBE_ON_STARTUP=true

Usage:
  python ops/local_smtp_sink.py
  python ops/local_smtp_sink.py --port 1025 --dir ops/evidence/mail
"""

from __future__ import annotations

import argparse
import asyncio
import email
import email.policy
from datetime import datetime, timezone
from pathlib import Path


class _SinkSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, out_dir: Path):
        self.reader = reader
        self.writer = writer
        self.out_dir = out_dir
        self.mail_from = ""
        self.rcpt: list[str] = []
        self.data_mode = False
        self.buffer = bytearray()

    async def _send(self, line: str) -> None:
        self.writer.write((line + "\r\n").encode("utf-8"))
        await self.writer.drain()

    async def run(self) -> None:
        peer = self.writer.get_extra_info("peername")
        await self._send("220 academiccheck-local-smtp ESMTP ready")
        try:
            while True:
                raw = await self.reader.readline()
                if not raw:
                    break
                if self.data_mode:
                    if raw == b".\r\n" or raw == b".\n":
                        await self._store()
                        self.data_mode = False
                        self.buffer.clear()
                        self.mail_from = ""
                        self.rcpt = []
                        await self._send("250 OK queued as local-sink")
                    else:
                        # Dot-stuffing undo
                        if raw.startswith(b".."):
                            raw = raw[1:]
                        self.buffer.extend(raw)
                    continue

                line = raw.decode("utf-8", errors="replace").strip()
                upper = line.upper()
                if upper.startswith("EHLO") or upper.startswith("HELO"):
                    await self._send("250-academiccheck-local-smtp")
                    await self._send("250-SIZE 10485760")
                    await self._send("250 HELP")
                elif upper.startswith("MAIL FROM:"):
                    self.mail_from = line.split(":", 1)[-1].strip()
                    await self._send("250 OK")
                elif upper.startswith("RCPT TO:"):
                    self.rcpt.append(line.split(":", 1)[-1].strip())
                    await self._send("250 OK")
                elif upper == "DATA":
                    self.data_mode = True
                    self.buffer.clear()
                    await self._send("354 End data with <CR><LF>.<CR><LF>")
                elif upper == "RSET":
                    self.mail_from = ""
                    self.rcpt = []
                    self.buffer.clear()
                    await self._send("250 OK")
                elif upper == "NOOP":
                    await self._send("250 OK")
                elif upper == "QUIT":
                    await self._send("221 Bye")
                    break
                else:
                    await self._send("502 Command not implemented")
        finally:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
            _ = peer

    async def _store(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.out_dir / f"{stamp}.eml"
        path.write_bytes(bytes(self.buffer))
        subject = "(no subject)"
        try:
            msg = email.message_from_bytes(bytes(self.buffer), policy=email.policy.default)
            subject = str(msg.get("Subject") or subject)
            to_hdr = str(msg.get("To") or ",".join(self.rcpt))
        except Exception:  # noqa: BLE001
            to_hdr = ",".join(self.rcpt)
        print(f"[smtp-sink] saved {path.name}  to={to_hdr}  subject={subject}")


async def _main(host: str, port: int, out_dir: Path) -> None:
    async def _on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _SinkSession(reader, writer, out_dir).run()

    server = await asyncio.start_server(_on_connect, host, port)
    sockets = ", ".join(str(s.getsockname()) for s in server.sockets or [])
    print(f"AcademicCheck local SMTP sink listening on {sockets}")
    print(f"Saving messages to {out_dir.resolve()}")
    print("API tip: EMAIL_PROVIDER=smtp SMTP_HOST=127.0.0.1 SMTP_PORT=%s SMTP_TLS=disabled" % port)
    async with server:
        await server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="Local SMTP sink for AcademicCheck AI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument(
        "--dir",
        default=str(Path(__file__).resolve().parents[1] / "ops" / "evidence" / "mail"),
        help="Directory for .eml files",
    )
    args = parser.parse_args()
    try:
        asyncio.run(_main(args.host, args.port, Path(args.dir)))
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
