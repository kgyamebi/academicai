# Encryption Certification — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| Field encryption AES-256-GCM `enc:v2:` | PASS units when key set |
| Secure cookies HttpOnly / SameSite / Secure prod | PASS code |
| JWT HMAC | PASS; previous key rotation supported |
| Backup dump AES-GCM envelope | PASS local crypto (`backup_crypto.py`) |
| TLS 1.3 | **FAIL measured** — edge/host (HAL-19) |
| DB TDE | Provider feature — **unproven** |
| Encrypted assignment/report blobs at rest | Field-level for selected secrets; full corpus = storage/disk encryption **host** |

**PARTIAL PASS** application crypto. **FAIL** end-to-end encryption certification (TLS/TDE/offsite dump custody).
