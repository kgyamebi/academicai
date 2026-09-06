import time
from uuid import uuid4

import httpx
import jwt

API = "http://127.0.0.1:8000"
c = httpx.Client(timeout=20)

print("admin", c.post(f"{API}/api/auth/login", json={"email": "admin@academiccheck.ai", "password": "ChangeMeAdmin123!"}).status_code)
print("webhook_nosig", c.post(f"{API}/api/billing/payments/webhook", content=b"{}").status_code, c.post(f"{API}/api/billing/payments/webhook", content=b"{}").json())
print(
    "webhook_spoof",
    c.post(
        f"{API}/api/billing/payments/webhook",
        content=b'{"id":"x"}',
        headers={"Stripe-Signature": "t=1,v1=ab"},
    ).status_code,
)
g = c.post(f"{API}/api/auth/guest").json()
h = {"Authorization": "Bearer " + g["access_token"]}
print("openapi", c.get(f"{API}/api/docs").status_code, c.get(f"{API}/api/openapi.json").status_code)
print(
    "exe",
    c.post(
        f"{API}/api/documents/upload",
        headers=h,
        files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
    ).status_code,
)
print(
    "fakepdf",
    c.post(
        f"{API}/api/documents/upload",
        headers=h,
        files={"file": ("a.pdf", b"nope", "application/pdf")},
    ).status_code,
)
print("empty", c.post(f"{API}/api/documents/upload", headers=h, files={"file": ("a.txt", b"", "text/plain")}).status_code)
tok = jwt.encode({"sub": (g.get("user") or {}).get("id", "x"), "typ": "access", "exp": int(time.time()) + 99}, key="", algorithm="none")
print("alg_none", c.get(f"{API}/api/dashboard", headers={"Authorization": "Bearer " + tok}).status_code)
print("refresh_as_access", c.get(f"{API}/api/dashboard", headers={"Authorization": "Bearer " + g["refresh_token"]}).status_code)
print("admin_as_guest", c.get(f"{API}/api/admin/overview", headers=h).status_code)

email = f"r{uuid4().hex[:8]}@ex.com"
reg = c.post(f"{API}/api/auth/register", json={"email": email, "password": "password12", "full_name": "R"}).json()
rh = {"Authorization": "Bearer " + reg["access_token"]}
asg = c.post(f"{API}/api/assignments", headers=rh, json={"title": "t", "question": "Compare and evaluate trade."}).json()
doc = c.post(
    f"{API}/api/documents/paste",
    headers=rh,
    json={"assignment_id": asg["id"], "text": "This essay argues that trade matters because evidence from Rodrik, 2011 shows mixed gains. " * 20, "filename": "d.txt"},
).json()
an = c.post(f"{API}/api/analysis", headers=rh, json={"assignment_id": asg["id"], "document_id": doc["id"]})
print("registered_analysis", an.status_code, an.json())

asg2 = c.post(f"{API}/api/assignments", headers=h, json={"title": "g", "question": "Compare and evaluate trade."}).json()
doc2 = c.post(
    f"{API}/api/documents/paste",
    headers=h,
    json={"assignment_id": asg2["id"], "text": "This essay argues that trade matters because evidence from Rodrik, 2011 shows mixed gains. " * 20, "filename": "d.txt"},
).json()
an2 = c.post(f"{API}/api/analysis", headers=h, json={"assignment_id": asg2["id"], "document_id": doc2["id"]})
print("guest_analysis", an2.status_code, an2.json())

# checkout
print("checkout", c.post(f"{API}/api/billing/checkout", headers=rh, json={"plan_slug": "student", "provider": "stripe"}).json())
print("plan_after", c.get(f"{API}/api/billing", headers=rh).json()["plan"]["slug"])
