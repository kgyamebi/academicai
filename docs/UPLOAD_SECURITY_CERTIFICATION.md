# Upload Security Certification — AcademicCheck AI

Date: 2026-09-07  
Code: `backend/app/services/documents/validation.py`. Tests: `test_document_security.py`, reliability upload 400s.

| Control | Implemented | Tested | Prod |
| --- | --- | --- | --- |
| MIME allow-list | Yes (warning vs signature) | wrong MIME | PASS repo |
| File signature | PDF `%PDF`, DOCX zip | wrong signature | PASS repo |
| Extension | no `exe.pdf` | double extension | PASS repo |
| Images | **not accepted** | unknown ext | N/A (reject) |
| Archives as primary | DOCX zip only | macros / zip bomb ratio 200 / 2000 entries / 80MB member / 200MB uncompressed | PASS repo |
| Upload quota | `max_upload_mb=15` | over cap | PASS repo |
| Virus scan hook | ClamAV INSTREAM if `CLAMAV_HOST` | not default | PARTIAL; prod fail-closed **if host set and down** |
| Resource limits | size + zip | yes | PASS repo |
| Sandbox | none (in-process parse) | — | FAIL sandbox |
| PDF JS / Launch | reject | javascript test | PASS repo |

**Certification: PASS repository upload filters. FAIL** malware default-on and sandbox.
