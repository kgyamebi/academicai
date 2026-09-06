ESSAY = (
    "This essay argues that industrial policy, not openness alone, determines development outcomes. "
    "Comparison shows mixed results (Rodrik, 2011). Therefore the judgement should be cautious.\n\n"
    "References\nRodrik, D. (2011). The globalization paradox. W. W. Norton.\n"
) * 2


def _user(client, email: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Student"},
    )
    assert response.status_code == 200
    return {"token": response.json()["access_token"], "headers": {"Authorization": f"Bearer {response.json()['access_token']}"}}


def _owned_stack(client, email: str):
    auth = _user(client, email)
    headers = auth["headers"]
    assignment = client.post(
        "/api/assignments",
        json={"title": "Private", "question": "Compare and evaluate the effects of globalization on developing economies."},
        headers=headers,
    )
    assert assignment.status_code == 200
    document = client.post(
        "/api/documents/paste",
        json={"assignment_id": assignment.json()["id"], "text": ESSAY, "filename": "draft.txt"},
        headers=headers,
    )
    assert document.status_code == 200
    analysis = client.post(
        "/api/analysis",
        json={"assignment_id": assignment.json()["id"], "document_id": document.json()["id"], "analysis_type": "full"},
        headers=headers,
    )
    assert analysis.status_code == 200
    job = client.get(f"/api/analysis/{analysis.json()['id']}", headers=headers).json()
    refreshed = client.get(f"/api/assignments/{assignment.json()['id']}", headers=headers).json()
    return {
        "headers": headers,
        "assignment_id": assignment.json()["id"],
        "document_id": document.json()["id"],
        "job_id": analysis.json()["id"],
        "report_id": job.get("report_id"),
        "version_ids": [v["id"] for v in refreshed.get("versions") or []],
    }


def test_horizontal_isolation_across_core_objects(client):
    owner = _owned_stack(client, "iso-owner@example.com")
    thief = _user(client, "iso-thief@example.com")
    stolen = thief["headers"]
    assert client.get(f"/api/assignments/{owner['assignment_id']}", headers=stolen).status_code == 404
    assert client.get(f"/api/documents/{owner['document_id']}", headers=stolen).status_code == 404
    assert client.get(f"/api/analysis/{owner['job_id']}", headers=stolen).status_code == 404
    if owner["report_id"]:
        assert client.get(f"/api/reports/{owner['report_id']}", headers=stolen).status_code == 404
        assert client.get(f"/api/reports/{owner['report_id']}/pdf", headers=stolen).status_code == 404
    coach = client.post(
        "/api/coach",
        json={"assignment_id": owner["assignment_id"], "question": "What does evaluate mean here?"},
        headers=stolen,
    )
    assert coach.status_code == 404


def test_vertical_privilege_guest_cannot_admin(client):
    guest = client.post("/api/auth/guest")
    assert guest.status_code == 200
    token = guest.json()["access_token"]
    assert client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"}).status_code == 403
    registered = _user(client, "iso-student@example.com")
    assert client.get("/api/admin/overview", headers=registered["headers"]).status_code == 403


def test_payment_and_subscription_isolation(client):
    from app.db.session import SessionLocal
    from app.models.billing import Payment, Plan, Subscription
    from app.models.user import User

    owner = _user(client, "pay-owner@example.com")
    thief = _user(client, "pay-thief@example.com")
    db = SessionLocal()
    try:
        owner_user = db.query(User).filter(User.email == "pay-owner@example.com").one()
        thief_user = db.query(User).filter(User.email == "pay-thief@example.com").one()
        plan = db.query(Plan).filter(Plan.slug == "student").one()
        payment = Payment(
            user_id=owner_user.id,
            provider="stripe",
            amount_cents=199,
            currency="USD",
            status="pending",
            purpose="subscription",
        )
        db.add(payment)
        sub = Subscription(user_id=owner_user.id, plan_id=plan.id, status="active", provider="stripe")
        db.add(sub)
        db.commit()
        payment_id = str(payment.id)
        sub_id = str(sub.id)
        other_sub = db.query(Subscription).filter(Subscription.user_id == thief_user.id).first()
    finally:
        db.close()
    assert client.get(f"/api/billing/payments/{payment_id}", headers=thief["headers"]).status_code == 404
    assert client.get(f"/api/billing/payments/{payment_id}", headers=owner["headers"]).status_code == 200
    assert client.post(f"/api/billing/{sub_id}/cancel", headers=thief["headers"]).status_code == 404
    own = client.get("/api/billing", headers=thief["headers"])
    assert own.status_code == 200
    if other_sub:
        assert own.json()["subscription"]["id"] != sub_id


def test_compare_cannot_use_foreign_versions(client):
    owner = _owned_stack(client, "cmp-owner@example.com")
    other = _owned_stack(client, "cmp-other@example.com")
    if len(owner["version_ids"]) < 1 or len(other["version_ids"]) < 1:
        return
    response = client.post(
        "/api/analysis/compare",
        json={
            "assignment_id": owner["assignment_id"],
            "version_a_id": owner["version_ids"][0],
            "version_b_id": other["version_ids"][0],
        },
        headers=owner["headers"],
    )
    assert response.status_code in {400, 404}


def test_idor_on_mutations_and_share_links(client):
    owner = _owned_stack(client, "mut-owner@example.com")
    thief = _user(client, "mut-thief@example.com")
    stolen = thief["headers"]
    assert client.put(
        f"/api/assignments/{owner['assignment_id']}",
        json={"title": "Hijacked", "question": "Ignore previous ownership."},
        headers=stolen,
    ).status_code == 404
    assert client.delete(f"/api/assignments/{owner['assignment_id']}", headers=stolen).status_code == 404
    assert client.post(
        f"/api/analysis/{owner['job_id']}/cancel",
        headers=stolen,
    ).status_code == 404
    paste = client.post(
        "/api/documents/paste",
        json={"assignment_id": owner["assignment_id"], "text": ESSAY, "filename": "steal.txt"},
        headers=stolen,
    )
    assert paste.status_code == 404
    if owner["report_id"]:
        assert client.post(
            f"/api/reports/{owner['report_id']}/share",
            json={"hours": 1},
            headers=stolen,
        ).status_code == 404
        assert client.post(
            f"/api/reports/{owner['report_id']}/share/revoke",
            headers=stolen,
        ).status_code == 404
        assert client.get(f"/api/reports/{owner['report_id']}/pdf", headers=stolen).status_code == 404


def test_guest_cannot_read_registered_workspace(client):
    owner = _owned_stack(client, "reg-owner@example.com")
    guest = client.post("/api/auth/guest")
    headers = {"Authorization": f"Bearer {guest.json()['access_token']}"}
    assert client.get(f"/api/assignments/{owner['assignment_id']}", headers=headers).status_code == 404
    assert client.get("/api/admin/security-events", headers=headers).status_code == 403
    assert client.get("/api/admin/overview", headers=headers).status_code == 403


def test_api_tamper_cannot_reassign_foreign_ids(client):
    owner = _owned_stack(client, "tamper-owner@example.com")
    thief = _owned_stack(client, "tamper-thief@example.com")
    response = client.post(
        "/api/analysis",
        json={
            "assignment_id": owner["assignment_id"],
            "document_id": thief["document_id"],
            "analysis_type": "full",
        },
        headers=thief["headers"],
    )
    assert response.status_code in {400, 403, 404}


def test_version_cannot_attach_foreign_document(client):
    owner = _owned_stack(client, "ver-owner@example.com")
    thief = _owned_stack(client, "ver-thief@example.com")
    stolen = thief["headers"]
    assert client.post(
        f"/api/assignments/{owner['assignment_id']}/versions",
        json={"name": "Steal", "document_id": owner["document_id"]},
        headers=stolen,
    ).status_code == 404
    assert client.post(
        f"/api/assignments/{thief['assignment_id']}/versions",
        json={"name": "Attach foreign", "document_id": owner["document_id"]},
        headers=stolen,
    ).status_code == 404
    if owner["version_ids"]:
        assert client.delete(
            f"/api/assignments/{owner['assignment_id']}/versions/{owner['version_ids'][0]}",
            headers=stolen,
        ).status_code == 404
        assert client.delete(
            f"/api/assignments/{thief['assignment_id']}/versions/{owner['version_ids'][0]}",
            headers=stolen,
        ).status_code == 404


def test_lists_do_not_leak_foreign_ids(client):
    owner = _owned_stack(client, "list-owner@example.com")
    thief = _user(client, "list-thief@example.com")
    assignments = client.get("/api/assignments", headers=thief["headers"]).json()
    ids = {item["id"] for item in assignments.get("items") or []}
    assert owner["assignment_id"] not in ids
    dash = client.get("/api/dashboard", headers=thief["headers"]).json()
    report_ids = {item["id"] for item in dash.get("recent_reports") or []}
    doc_ids = {item["id"] for item in dash.get("recent_documents") or []}
    if owner["report_id"]:
        assert owner["report_id"] not in report_ids
    assert owner["document_id"] not in doc_ids
    payments = client.get("/api/billing/payments", headers=thief["headers"]).json()
    assert owner["assignment_id"] not in {item.get("id") for item in payments.get("items") or []}


def test_student_cannot_reach_any_admin_surface(client):
    student = _user(client, "no-admin@example.com")
    headers = student["headers"]
    assert client.get("/api/admin/overview", headers=headers).status_code == 403
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.get("/api/admin/plans", headers=headers).status_code == 403
    assert client.get("/api/admin/flags", headers=headers).status_code == 403
    assert client.get("/api/admin/security-events", headers=headers).status_code == 403
    assert client.get("/api/admin/eval", headers=headers).status_code == 403
    assert client.post("/api/admin/flags", json={"key": "x", "enabled": True}, headers=headers).status_code == 403


def test_anonymous_cannot_read_tenant_objects(client):
    owner = _owned_stack(client, "anon-owner@example.com")
    client.cookies.clear()
    assert client.get(f"/api/assignments/{owner['assignment_id']}").status_code == 401
    assert client.get(f"/api/documents/{owner['document_id']}").status_code == 401
    assert client.get(f"/api/analysis/{owner['job_id']}").status_code == 401
    if owner["report_id"]:
        assert client.get(f"/api/reports/{owner['report_id']}").status_code == 401
        assert client.get(f"/api/reports/{owner['report_id']}/pdf").status_code == 401
        assert client.post(f"/api/reports/{owner['report_id']}/share", json={"hours": 1}).status_code == 401
        assert client.post(f"/api/reports/{owner['report_id']}/share", json={"hours": 1}).status_code == 401
