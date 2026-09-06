from app.core.csrf import enforce_csrf
from app.db.session import SessionLocal
from app.models.user import User
from app.services.documents.validation import DocumentSecurityError, validate_upload
from app.services.entitlements import assert_can_analyze, monthly_quota_exhausted


class _Req:
    def __init__(self, method="POST", path="/api/assignments", cookies=None, headers=None):
        self.method = method
        self.url = type("U", (), {"path": path})()
        self.cookies = cookies or {}
        self.headers = headers or {}


def test_csrf_rejects_cookie_session_without_header():
    try:
        enforce_csrf(
            _Req(
                cookies={"ac_access": "token", "ac_csrf": "abc"},
                headers={},
            )
        )
    except Exception as exc:
        assert getattr(exc, "status_code", 0) == 403
        return
    raise AssertionError("CSRF should reject a cookie mutation without X-CSRF-Token")


def test_csrf_allows_bearer_and_safe_methods():
    enforce_csrf(_Req(method="GET", cookies={"ac_access": "token"}))
    enforce_csrf(_Req(headers={"authorization": "Bearer abc"}, cookies={"ac_access": "token"}))


def test_upload_rejects_executable_disguise():
    try:
        validate_upload("payload.exe", b"MZ\x90\x00not-a-pdf")
    except DocumentSecurityError:
        return
    raise AssertionError("Executables must be rejected")


def test_upload_accepts_plain_text():
    validated = validate_upload("draft.txt", b"This is a short academic draft used for validation.", "text/plain")
    assert validated.extension == ".txt"


def test_entitlements_block_oversize_and_rubric_on_free(client):
    client.post(
        "/api/auth/register",
        json={"email": "entitle@example.com", "password": "password12", "full_name": "Ent"},
    )
    db = SessionLocal()
    user = db.query(User).filter(User.email == "entitle@example.com").one()
    try:
        assert_can_analyze(db, user, 5_000_000, "full")
        raise AssertionError("Oversize documents must be rejected")
    except Exception as exc:
        assert getattr(exc, "status_code", 0) == 402
    try:
        assert_can_analyze(db, user, 200, "rubric")
        raise AssertionError("Free plan must not receive rubric analysis")
    except Exception as exc:
        assert getattr(exc, "status_code", 0) == 402
    assert monthly_quota_exhausted(db, user) in {True, False}
    db.close()


def test_recovery_validation_counts_after_owned_write(client):
    from sqlalchemy import func, select

    from app.models.analysis import AnalysisJob, AnalysisReport
    from app.models.assignment import Assignment
    from app.models.document import Document
    from tests.test_isolation import _owned_stack

    owner = _owned_stack(client, "recover@example.com")
    db = SessionLocal()
    counts = {
        "assignments": db.scalar(select(func.count(Assignment.id))) or 0,
        "documents": db.scalar(select(func.count(Document.id))) or 0,
        "jobs": db.scalar(select(func.count(AnalysisJob.id))) or 0,
        "reports": db.scalar(select(func.count(AnalysisReport.id))) or 0,
    }
    db.close()
    assert counts["assignments"] >= 1
    assert counts["documents"] >= 1
    assert counts["jobs"] >= 1
    if owner["report_id"]:
        assert counts["reports"] >= 1
