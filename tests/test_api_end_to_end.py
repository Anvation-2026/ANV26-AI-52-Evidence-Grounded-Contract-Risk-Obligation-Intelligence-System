import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["DATABASE_URL"] = f"sqlite:///{(ROOT / 'tests' / 'api_test.db').as_posix()}"
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app


def test_upload_analyze_trace_obligations_and_version_comparison():
    client = TestClient(app)
    # Workspace endpoints require authentication. Confirm protection, then create an account and sign in.
    unauthenticated = client.get("/contracts")
    assert unauthenticated.status_code == 401
    email = f"e2e-{time.time_ns()}@example.test"
    registered = client.post("/auth/register", json={"name": "E2E Reviewer", "email": email, "password": "Review12345"})
    assert registered.status_code == 201, registered.text
    login = client.post("/auth/login", json={"email": email, "password": "Review12345"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    health = client.get("/health")
    assert health.status_code == 200 and health.json()["status"] == "healthy"
    demo = client.post("/contracts/demo/sample")
    assert demo.status_code == 200, demo.text
    demo_id = demo.json()["contract"]["id"]

    # A different account must not list, read, analyze, compare, or delete this user's contract.
    second_email = f"isolated-{time.time_ns()}@example.test"
    second_registered = client.post("/auth/register", json={"name": "Second Reviewer", "email": second_email, "password": "Review67890"})
    assert second_registered.status_code == 201, second_registered.text
    first_token = token
    second_token = client.post("/auth/login", json={"email": second_email, "password": "Review67890"}).json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {second_token}"})
    assert all(item["id"] != demo_id for item in client.get("/contracts").json()["contracts"])
    assert client.get(f"/contracts/{demo_id}/dashboard").status_code == 404
    assert client.post(f"/contracts/{demo_id}/analyze").status_code == 404
    assert client.delete(f"/contracts/{demo_id}").status_code == 404
    client.headers.update({"Authorization": f"Bearer {first_token}"})

    demo_analysis = client.post(f"/contracts/{demo_id}/analyze")
    assert demo_analysis.status_code == 200, demo_analysis.text
    demo_audit = client.get(f"/contracts/{demo_id}/audit")
    assert demo_audit.status_code == 200 and any(e["type"] == "DEMO_CONTRACT_LOADED" for e in demo_audit.json()["events"])
    assert client.delete(f"/contracts/{demo_id}").status_code == 200

    rules = client.get("/contracts/playbook/rules")
    assert rules.status_code == 200 and len(rules.json()["rules"]) >= 8
    payment_rule = next(rule for rule in rules.json()["rules"] if rule["rule_id"] == "PAYMENT-001")
    updated_rule = client.put(f"/contracts/playbook/rules/PAYMENT-001", json={"requirement": payment_rule["requirement"], "description": payment_rule["description"], "severity": payment_rule["severity"]})
    assert updated_rule.status_code == 200 and updated_rule.json()["requires_reanalysis"] is True
    invalid_rule = client.put("/contracts/playbook/rules/PAYMENT-001", json={"severity": "CRITICAL"})
    assert invalid_rule.status_code == 400

    # PDF upload path is also exercised end-to-end.
    pdf_fixture = ROOT / "contracts" / "test_contract.pdf"
    with pdf_fixture.open("rb") as handle:
        pdf_upload = client.post("/contracts/upload", data={"contract_name": "PDF Smoke Test"}, files={"file": ("test_contract.pdf", handle, "application/pdf")})
    assert pdf_upload.status_code == 200, pdf_upload.text
    pdf_id = pdf_upload.json()["contract"]["id"]
    pdf_analysis = client.post(f"/contracts/{pdf_id}/analyze")
    assert pdf_analysis.status_code == 200, pdf_analysis.text
    assert client.delete(f"/contracts/{pdf_id}").status_code == 200

    fixture = ROOT / "contracts" / "demo_vendor_agreement.docx"
    with fixture.open("rb") as handle:
        uploaded = client.post(
            "/contracts/upload",
            data={"contract_name": "E2E Synthetic Contract"},
            files={"file": ("demo_vendor_agreement.docx", handle, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert uploaded.status_code == 200, uploaded.text
    v1_id = uploaded.json()["contract"]["id"]

    analyzed = client.post(f"/contracts/{v1_id}/analyze")
    assert analyzed.status_code == 200, analyzed.text
    report = analyzed.json()
    assert report["summary"]["finding_count"] >= 8
    payment = next(item for item in report["findings"] if item["rule_id"] == "PAYMENT-001")
    assert payment["status"] == "RISKY"
    assert any(item["status"] == "CONFLICTING" for item in report["findings"])
    dashboard = client.get(f"/contracts/{v1_id}/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["risk_summary"]["conflicting"] >= 1
    trace = client.get(f"/contracts/{v1_id}/findings/{payment['id']}/trace")
    assert trace.status_code == 200, trace.text
    assert trace.json()["playbook_rule"]["rule_id"] == "PAYMENT-001"
    assert trace.json()["assessment"]["evidence"]

    # Reviewer workflow, audit trail and PDF export are exercised end-to-end.
    reviewed = client.post(f"/contracts/{v1_id}/findings/{payment['id']}/review", json={"status": "REVIEWED", "note": "Checked against payment playbook", "reviewer": "Test reviewer"})
    assert reviewed.status_code == 200 and reviewed.json()["status"] == "REVIEWED"
    review_actions = client.get(f"/contracts/{v1_id}/review-actions")
    assert review_actions.status_code == 200 and review_actions.json()["actions"][0]["status"] == "REVIEWED"
    audit = client.get(f"/contracts/{v1_id}/audit")
    assert audit.status_code == 200
    assert any(event["type"] == "ANALYSIS_COMPLETED" for event in audit.json()["events"])
    pdf_report = client.get(f"/contracts/{v1_id}/report.pdf")
    assert pdf_report.status_code == 200 and pdf_report.headers["content-type"].startswith("application/pdf")
    assert pdf_report.content.startswith(b"%PDF")

    obligations = client.post(f"/contracts/{v1_id}/obligations")
    assert obligations.status_code == 200, obligations.text
    assert obligations.json()["summary"]["obligation_count"] >= 1

    generated = client.post(f"/contracts/{v1_id}/generate-v2")
    assert generated.status_code == 200, generated.text
    v2_id = generated.json()["new_contract"]["id"]
    compare = client.get(f"/contracts/{v1_id}/compare-v2")
    assert compare.status_code == 200, compare.text
    assert compare.json()["summary"]["modified"] >= 1
    risk_compare = client.get(f"/contracts/{v1_id}/risk-comparison", params={"v2_contract_id": v2_id})
    assert risk_compare.status_code == 200, risk_compare.text
    # Cleanup records/files recursively so test runs are repeatable and tidy.
    deleted = client.delete(f"/contracts/{v1_id}")
    assert deleted.status_code == 200, deleted.text
    assert v2_id in deleted.json()["deleted_contract_ids"]
    assert client.get(f"/contracts/{v2_id}/dashboard").status_code == 404
    from app.database.connection import SessionLocal
    from app.models import AuditEvent, ReviewAction
    cleanup_db = SessionLocal()
    try:
        deleted_ids = deleted.json()["deleted_contract_ids"]
        assert cleanup_db.query(AuditEvent).filter(AuditEvent.contract_id.in_(deleted_ids)).count() == 0
        assert cleanup_db.query(ReviewAction).filter(ReviewAction.contract_id.in_(deleted_ids)).count() == 0
    finally:
        cleanup_db.close()


def test_auth_validation_upload_validation_and_cross_account_resource_isolation():
    """Regression coverage for auth failures, unsafe uploads, and nested resource access."""
    client = TestClient(app)
    suffix = str(time.time_ns())
    first_email = f"security-a-{suffix}@example.test"
    second_email = f"security-b-{suffix}@example.test"

    first_register = client.post("/auth/register", json={"name": "Security Reviewer A", "email": first_email, "password": "SecurePass123"})
    assert first_register.status_code == 201, first_register.text
    assert client.post("/auth/register", json={"name": "Security Reviewer A", "email": first_email.upper(), "password": "SecurePass123"}).status_code == 409
    assert client.post("/auth/login", json={"email": first_email, "password": "WrongPassword123"}).status_code == 401
    first_token = first_register.json()["access_token"]

    second_register = client.post("/auth/register", json={"name": "Security Reviewer B", "email": second_email, "password": "OtherSecure456"})
    assert second_register.status_code == 201, second_register.text
    second_token = second_register.json()["access_token"]

    # Create a contract for each account and analyze both to populate nested resources.
    client.headers.update({"Authorization": f"Bearer {first_token}"})
    first_demo = client.post("/contracts/demo/sample")
    assert first_demo.status_code == 200, first_demo.text
    first_id = first_demo.json()["contract"]["id"]
    first_analysis = client.post(f"/contracts/{first_id}/analyze")
    assert first_analysis.status_code == 200, first_analysis.text
    first_finding_id = first_analysis.json()["findings"][0]["id"]
    first_v2 = client.post(f"/contracts/{first_id}/generate-v2")
    assert first_v2.status_code == 200, first_v2.text
    first_v2_id = first_v2.json()["new_contract"]["id"]

    client.headers.update({"Authorization": f"Bearer {second_token}"})
    second_demo = client.post("/contracts/demo/sample")
    assert second_demo.status_code == 200, second_demo.text
    second_id = second_demo.json()["contract"]["id"]
    second_analysis = client.post(f"/contracts/{second_id}/analyze")
    assert second_analysis.status_code == 200, second_analysis.text

    # Every nested resource under another user's contract must be unavailable.
    foreign_paths = [
        ("GET", f"/contracts/{first_id}/intelligence"),
        ("GET", f"/contracts/{first_id}/audit"),
        ("GET", f"/contracts/{first_id}/review-actions"),
        ("GET", f"/contracts/{first_id}/report.pdf"),
        ("POST", f"/contracts/{first_id}/obligations"),
        ("POST", f"/contracts/{first_id}/generate-v2"),
        ("GET", f"/contracts/{first_id}/compare-v2"),
        ("GET", f"/contracts/{first_id}/findings/{first_finding_id}/trace"),
        ("POST", f"/contracts/{first_id}/findings/{first_finding_id}/review"),
    ]
    for method, path in foreign_paths:
        response = client.request(method, path, json={"status": "REVIEWED", "note": "unauthorized test"} if method == "POST" and "review" in path else None)
        assert response.status_code == 404, f"{method} {path}: expected 404, got {response.status_code} {response.text}"

    # A user cannot smuggle another account's version through a query parameter.
    cross_compare = client.get(f"/contracts/{second_id}/risk-comparison", params={"v2_contract_id": first_v2_id})
    assert cross_compare.status_code == 404, cross_compare.text

    # Upload validation rejects disguised invalid files with clear client errors.
    bad_pdf = client.post("/contracts/upload", data={"contract_name": "Invalid PDF"}, files={"file": ("fake.pdf", b"not a pdf", "application/pdf")})
    assert bad_pdf.status_code == 400, bad_pdf.text
    bad_docx = client.post("/contracts/upload", data={"contract_name": "Invalid DOCX"}, files={"file": ("fake.docx", b"not a docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert bad_docx.status_code == 400, bad_docx.text
    unsupported = client.post("/contracts/upload", data={"contract_name": "Unsupported"}, files={"file": ("fake.txt", b"text", "text/plain")})
    assert unsupported.status_code == 400, unsupported.text

    # Remove created records to keep repeat runs deterministic and tidy.
    assert client.delete(f"/contracts/{second_id}").status_code == 200
    client.headers.update({"Authorization": f"Bearer {first_token}"})
    assert client.delete(f"/contracts/{first_id}").status_code == 200
