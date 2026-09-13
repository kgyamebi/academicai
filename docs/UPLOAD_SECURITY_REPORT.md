# Upload Security Report — AcademicCheck AI

Date: 2026-09-09  
Evidence: `test_document_security.py`, validation module.

| Control | Status |
| --- | --- |
| Extension + MIME allow-list | Yes |
| Magic / signature checks | Yes |
| Size / page / extract limits | Yes |
| Zip bomb / DOCX macro-OLE / PDF JS-Launch | Yes |
| Polyglot / double extension | Yes |
| Path traversal on storage keys | Yes |
| Quarantine bucket | **No** — fail-closed reject (not stored) |
| ClamAV | Optional (`CLAMAV_HOST`); mandatory = HAL-12 |

**PASS filter suite.** **FAIL** malware quarantine pipeline / mandatory AV as enterprise claim.
