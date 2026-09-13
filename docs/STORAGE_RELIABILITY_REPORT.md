# Storage Reliability Report — AcademicCheck AI

Date: 2026-09-07  
Code: `storage.py`, `validation.py`. Chaos `storage_kill`: **not_run**. Throughput: `cert_storage_results.json` (not DR).

| Control | Status | Proven? |
| --- | --- | --- |
| Upload verification | Magic/size/dangerous stems; 15 MB cap | Pytest upload failures |
| Object verification | **No** content hash stored | **FAIL** checksum |
| Replication readiness | None | **FAIL** |
| Safe deletion | Path traversal rejected; unlink/S3 delete | Pytest path; guest purge on reaper |
| Versioning | Not configured | **FAIL** |
| Signed URL | Requires S3 keys; 300s default | **Unrun** |
| Storage cleanup | Guest `expires_at` purge with reaper | Pytest; needs workers |

## Validations requested

| Test | Result |
| --- | --- |
| Upload failures | Pytest 400 on extract crash / over cap / garbage PDF |
| Storage outages | **Not run** |
| Corrupted uploads | Pytest maps to 400 / security error |
| Large files | Rejected over 15 MB — not a reliability soak |

DB restore restores `documents` **rows**, not bytes.

## Verdict

**FAIL** object-storage reliability certification. **PASS** upload validation pytest + local 10k round-trip (separate scale cert).
