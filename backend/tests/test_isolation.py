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
