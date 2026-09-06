import time

import httpx

api = "http://127.0.0.1:8000"
web = "http://127.0.0.1:3000"
c = httpx.Client(timeout=60)

health = c.get(f"{api}/api/health")
print("health", health.status_code, health.json())
home = c.get(web)
print("home", home.status_code, len(home.text))

guest = c.post(f"{api}/api/auth/guest").json()
token = guest["access_token"]
h = {"Authorization": f"Bearer {token}"}

question = "Compare and evaluate the effects of globalization on developing economies."
essay = """
Introduction
Globalization has changed trade, labour and policy in many developing economies. This essay argues that globalization has expanded market access, but the gains are uneven because bargaining power and industrial policy differ across states.

Trade and growth
Trade openness is associated with faster export growth in several developing economies (Rodrik, 2011). This suggests that access to markets can raise output, but it does not prove that every country benefits equally.

Labour and inequality
However, wage gains are often concentrated in urban export sectors. Critics argue that rural households may see weaker gains. The comparison therefore matters more than a single national average.

Evaluation
Overall, globalization appears beneficial where states can bargain and upgrade industry, and more limited where policy capacity is weak.

Conclusion
Based on the comparison above, globalization should not be judged as uniformly good or bad for developing economies.

References
Rodrik, D. (2011). The globalization paradox. W. W. Norton.
""" * 2

assignment = c.post(
    f"{api}/api/assignments",
    headers=h,
    json={
        "title": "Globalization essay",
        "question": question,
        "academic_level": "undergraduate",
        "citation_style": "apa7",
    },
).json()
print("assignment", assignment["id"], assignment["question_analysis"].get("command_words"))

document = c.post(
    f"{api}/api/documents/paste",
    headers=h,
    json={"assignment_id": assignment["id"], "text": essay, "filename": "draft.txt"},
).json()
print("document words", document["word_count"])

job = c.post(
    f"{api}/api/analysis",
    headers=h,
    json={"assignment_id": assignment["id"], "document_id": document["id"], "analysis_type": "full"},
).json()
print("job", job)

status = {}
for _ in range(30):
    status = c.get(f"{api}/api/analysis/{job['id']}", headers=h).json()
    print("status", status["status"], status["stage"])
    if status["status"] in {"completed", "failed"}:
        break
    time.sleep(0.3)

assert status.get("status") == "completed", status
report = c.get(f"{api}/api/reports/{status['report_id']}", headers=h).json()
print("score", report["overall_score"])
print("disclaimer_ok", "not an official" in report["disclaimer"].lower())
print("strengths", report["strengths"])
print("weakest", report["weakest_area"].get("category"))
print("priority", report["priority_actions"][:2])

essay2 = essay + "\n\nThis revision strengthens the thesis: developing economies gain from globalization mainly when industrial policy can convert trade access into capability upgrading.\n"
document2 = c.post(
    f"{api}/api/documents/paste",
    headers=h,
    json={"assignment_id": assignment["id"], "text": essay2, "filename": "draft2.txt"},
).json()
job2 = c.post(
    f"{api}/api/analysis",
    headers=h,
    json={"assignment_id": assignment["id"], "document_id": document2["id"], "analysis_type": "full"},
).json()
status2 = {}
for _ in range(30):
    status2 = c.get(f"{api}/api/analysis/{job2['id']}", headers=h).json()
    if status2["status"] in {"completed", "failed"}:
        break
    time.sleep(0.3)
print("draft2", status2["status"], status2.get("report_id"))

workspace = c.get(f"{api}/api/assignments/{assignment['id']}", headers=h).json()
compare = c.post(
    f"{api}/api/analysis/compare",
    headers=h,
    json={
        "assignment_id": assignment["id"],
        "version_a_id": workspace["versions"][0]["id"],
        "version_b_id": workspace["versions"][-1]["id"],
    },
).json()
print("compare", compare.get("draft_1"), "->", compare.get("draft_2"))

pdf = c.get(f"{api}/api/reports/{status['report_id']}/pdf", headers=h)
print("pdf", pdf.status_code, pdf.headers.get("content-type"), len(pdf.content))

other = c.post(
    f"{api}/api/auth/register",
    json={"email": "iso2@example.com", "password": "password12", "full_name": "Iso"},
).json()
stolen = c.get(
    f"{api}/api/assignments/{assignment['id']}",
    headers={"Authorization": f"Bearer {other['access_token']}"},
)
print("isolation", stolen.status_code)

dashboard = c.get(f"{api}/api/dashboard", headers=h).json()
print("dashboard", dashboard["assignments"], dashboard["plan"])

for path in ("/check", "/pricing", "/features", "/help"):
    page = c.get(f"{web}{path}")
    print("page", path, page.status_code)
