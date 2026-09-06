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


def test_guest_cannot_read_another_users_assignment(client):
    first = client.post("/api/auth/register", json={
        "email": "one@example.com",
        "password": "password12",
        "full_name": "One Student",
    })
    assert first.status_code == 200
    token = first.json()["access_token"]
    created = client.post(
        "/api/assignments",
        json={"title": "Private", "question": "Compare and evaluate the effects of globalization on developing economies."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 200
    assignment_id = created.json()["id"]

    other = client.post("/api/auth/register", json={
        "email": "two@example.com",
        "password": "password12",
        "full_name": "Two Student",
    })
    other_token = other.json()["access_token"]
    stolen = client.get(f"/api/assignments/{assignment_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert stolen.status_code == 404


def test_paste_and_analyze_workflow(client):
    guest = client.post("/api/auth/guest")
    assert guest.status_code == 200
    token = guest.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assignment = client.post(
        "/api/assignments",
        json={
            "title": "Globalization essay",
            "question": "Compare and evaluate the effects of globalization on developing economies.",
            "academic_level": "undergraduate",
            "citation_style": "apa7",
        },
        headers=headers,
    )
    assert assignment.status_code == 200
    assignment_id = assignment.json()["id"]
    document = client.post(
        "/api/documents/paste",
        json={"assignment_id": assignment_id, "text": ESSAY * 2, "filename": "draft.txt"},
        headers=headers,
    )
    assert document.status_code == 200
    analysis = client.post(
        "/api/analysis",
        json={"assignment_id": assignment_id, "document_id": document.json()["id"], "analysis_type": "full"},
        headers=headers,
    )
    assert analysis.status_code == 200
    job = client.get(f"/api/analysis/{analysis.json()['id']}", headers=headers)
    assert job.status_code == 200
    assert job.json()["status"] in {"queued", "processing", "completed"}
    if job.json()["report_id"]:
        report = client.get(f"/api/reports/{job.json()['report_id']}", headers=headers)
        assert report.status_code == 200
        assert "overall_score" in report.json()
        assert "not an official" in report.json()["disclaimer"].lower()
