# UPLOAD_ANALYSIS_FAILURE_VALIDATION

**Measured:** 2026-09-13  
**Scope:** User-visible failure paths (no feature work)

## Matrix

| Scenario | Expected UX | Actual (code review) | Status |
| --- | --- | --- | --- |
| Invalid upload type | Inline reject message | Dropzone reject messaging | Pass (lab) |
| Large upload | Clear size error | API validation + client message | Pass (lab) |
| Corrupt / unreadable file | extraction_error surfaced | CheckExperience polls extraction_error | Pass (lab) |
| Worker unavailable | Fail with retry / dashboard | enqueue returns false; job fails; ritual failed + Try again | Pass (code) |
| Analysis timeout | No infinite spinner | 120s poll ceiling → failed + dashboard hint | Pass (code) |
| Lost connection mid-poll | Clear next step | Catch → failed + dashboard/retry copy | Pass (code) |
| Storage failure | Ready/storage false on staging | Ready now includes `storage` when deep | Pass (code); host unproven |

## Improvements applied this pass

- AnalysisRitual failed copy: explicit **Try again / dashboard**, no spinning-screen ambiguity.

## Remaining

Host staging proof with Redis down / worker kill still requires Docker or cloud staging.
