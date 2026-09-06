import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

ESSAY = """
Globalization has changed trade in developing economies. This essay argues that the effects are mixed: export growth often rises, but inequality can widen unless industrial policy is strong.

Comparison
East Asian industrialisers used trade alongside policy, whereas some commodity exporters liberalised without upgrading (Rodrik, 2011). The difference suggests that openness alone does not determine outcomes.

Evaluation
Therefore globalization should be evaluated by distribution and capability, not only by average GDP.

Conclusion
The question is not whether globalization exists, but which effects dominate in which developing economies.

References
Rodrik, D. (2011). The globalization paradox. W. W. Norton.
"""


def _register(client, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Student"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_default_admin_password_is_rejected(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@academiccheck.ai", "password": "ChangeMeAdmin123!"},
    )
    assert response.status_code in {401, 403}


def test_registered_analysis_does_not_crash_on_timezone(client):
    token = _register(client, "reg@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assignment = client.post(
        "/api/assignments",
        json={
            "title": "Registered analysis",
            "question": "Compare and evaluate the effects of globalization on developing economies.",
        },
        headers=headers,
    )
    assert assignment.status_code == 200
    document = client.post(
        "/api/documents/paste",
        json={"assignment_id": assignment.json()["id"], "text": ESSAY * 2, "filename": "draft.txt"},
        headers=headers,
    )
    assert document.status_code == 200
    analysis = client.post(
        "/api/analysis",
        json={"assignment_id": assignment.json()["id"], "document_id": document.json()["id"], "analysis_type": "full"},
        headers=headers,
    )
    assert analysis.status_code == 200
    assert analysis.json()["status"] in {"queued", "processing", "completed"}


def test_cookie_session_without_bearer(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "cookie@example.com", "password": "password12", "full_name": "Cookie User"},
    )
    assert response.status_code == 200
    assert "ac_access" in response.cookies
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "cookie@example.com"


def test_assignment_idor_is_denied(client):
    a = _register(client, "owner@example.com")
    b = _register(client, "other@example.com")
    created = client.post(
        "/api/assignments",
        json={"title": "Secret", "question": "Evaluate industrial policy in Ghana."},
        headers={"Authorization": f"Bearer {a}"},
    )
    stolen = client.get(
        f"/api/assignments/{created.json()['id']}",
        headers={"Authorization": f"Bearer {b}"},
    )
    assert stolen.status_code == 404


def test_document_and_report_idor(client):
    owner = _register(client, "docowner@example.com")
    thief = _register(client, "docthief@example.com")
    assignment = client.post(
        "/api/assignments",
        json={"title": "Owned", "question": "Assess climate policy in Kenya."},
        headers={"Authorization": f"Bearer {owner}"},
    ).json()
    document = client.post(
        "/api/documents/paste",
        json={"assignment_id": assignment["id"], "text": ESSAY * 2, "filename": "draft.txt"},
        headers={"Authorization": f"Bearer {owner}"},
    ).json()
    analysis = client.post(
        "/api/analysis",
        json={"assignment_id": assignment["id"], "document_id": document["id"], "analysis_type": "full"},
        headers={"Authorization": f"Bearer {owner}"},
    ).json()
    job = client.get(f"/api/analysis/{analysis['id']}", headers={"Authorization": f"Bearer {owner}"}).json()
    stolen_doc = client.get(f"/api/documents/{document['id']}", headers={"Authorization": f"Bearer {thief}"})
    stolen_job = client.get(f"/api/analysis/{analysis['id']}", headers={"Authorization": f"Bearer {thief}"})
    assert stolen_doc.status_code == 404
    assert stolen_job.status_code == 404
    if job.get("report_id"):
        stolen_report = client.get(f"/api/reports/{job['report_id']}", headers={"Authorization": f"Bearer {thief}"})
        assert stolen_report.status_code == 404


def test_share_link_requires_password_and_can_be_revoked(client):
    token = _register(client, "share@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assignment = client.post(
        "/api/assignments",
        json={"title": "Share", "question": "Examine rural-urban migration in Ghana."},
        headers=headers,
    ).json()
    document = client.post(
        "/api/documents/paste",
        json={"assignment_id": assignment["id"], "text": ESSAY * 2, "filename": "draft.txt"},
        headers=headers,
    ).json()
    analysis = client.post(
        "/api/analysis",
        json={"assignment_id": assignment["id"], "document_id": document["id"], "analysis_type": "full"},
        headers=headers,
    ).json()
    job = client.get(f"/api/analysis/{analysis['id']}", headers=headers).json()
    if not job.get("report_id"):
        return
    shared = client.post(
        f"/api/reports/{job['report_id']}/share",
        json={"password": "sharepass1", "hours": 2},
        headers=headers,
    )
    assert shared.status_code == 200
    link = shared.json()["token"]
    locked = client.get(f"/api/reports/shared/{link}")
    assert locked.status_code == 401
    opened = client.post(f"/api/reports/shared/{link}", json={"password": "sharepass1"})
    assert opened.status_code == 200
    client.post(f"/api/reports/{job['report_id']}/share/revoke", headers=headers)
    gone = client.post(f"/api/reports/shared/{link}", json={"password": "sharepass1"})
    assert gone.status_code == 404


def test_stripe_webhook_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.post(
        "/api/billing/webhooks/stripe",
        content=b'{"id":"evt_1","type":"checkout.session.completed"}',
        headers={"Stripe-Signature": "t=1,v1=deadbeef"},
    )
    assert response.status_code in {400, 503}
    get_settings.cache_clear()


def test_paystack_webhook_accepts_valid_hmac(client, monkeypatch):
    secret = "paystack_test_secret"
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    body = json.dumps({"event": "charge.failed", "data": {"reference": "ref_1", "metadata": {}}}).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    response = client.post("/api/billing/webhooks/paystack", content=body, headers={"x-paystack-signature": signature})
    assert response.status_code == 200
    get_settings.cache_clear()


def test_openapi_disabled_outside_dev(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()
    from importlib import reload

    from app import main as main_mod

    reload(main_mod)
    assert main_mod.app.docs_url is None
    assert main_mod.app.openapi_url is None
    monkeypatch.setenv("APP_ENV", "test")
    get_settings.cache_clear()
    reload(main_mod)


def test_naive_datetime_helpers():
    from app.core.time import as_utc, is_past

    naive = datetime.utcnow() - timedelta(days=1)
    assert as_utc(naive).tzinfo is UTC
    assert is_past(naive) is True
