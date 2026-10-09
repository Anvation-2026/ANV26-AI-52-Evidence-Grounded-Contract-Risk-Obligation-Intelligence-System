# Evidence-Grounded Contract Risk & Obligation Intelligence

A local-first MVP for reviewing PDF/DOCX contracts against a defined playbook. It returns clause-linked findings, missing-provision checks, obligation inventory, and clause/version diffs. It is a decision-support prototype, not legal advice or autonomous approval.

## Quick start (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for API docs. In another terminal, serve the frontend from the repository root with `py -m http.server 5500`; open `http://127.0.0.1:5500/frontend/`. If the frontend API URL is configured elsewhere, set it to `http://127.0.0.1:8000` in `frontend/app.js`.

The default database is SQLite at `backend/data/contract_risk.db` so the MVP can run without a MySQL server. For MySQL, set `USE_MYSQL=true` and configure `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME` in `.env`.

The core install intentionally keeps the API lightweight. To enable the optional embedding/vector AI pipeline, install `backend/requirements-ai.txt`; the first run may need internet access to download the sentence-transformer model. If those optional dependencies/model are unavailable, the API continues using deterministic playbook analysis.

## Test

From repository root:

```powershell
python -m pip install -r backend/requirements.txt
python -m pytest -q
```

The tests include known-answer synthetic cases for risky/ambiguous/missing findings, conflicting periods, traceability and renumbered clause comparisons.

## Review flow

1. Upload a PDF or DOCX (15 MB limit; signature/content validation is applied).
2. Analyze it against `playbook/rules.json`.
3. Inspect each finding's source clause, rule ID, expected/actual values and suggested action.
4. Review the obligation register and compare contract versions.
5. Treat every result and generated edit as a recommendation requiring human review.

## Limitations

Clause extraction is text-based and currently relies on document layout/numbered headings for best segmentation. Scanned PDFs may require OCR; low-quality extraction should be manually reviewed. The deterministic rules are a starter playbook, not universal legal standards. A keyword match does not prove complete compliance. Redline generation is intentionally conservative and only edits recognized patterns; unsupported changes remain for human review.

## Professional review workspace additions

- **Executive overview:** dashboard risk profile and severity/status counts are populated from persisted analysis results.
- **Evidence quality:** the trace panel identifies whether a direct source excerpt and playbook rule are linked. A missing excerpt is surfaced rather than silently treated as verified evidence.
- **Findings workbench:** search findings by category/rule/evidence and filter by status or severity.
- **Reviewer workflow:** mark findings as reviewed or action-required; action-required decisions accept a reviewer note and are persisted in the database.
- **Audit trail:** contract upload, analysis, demo loading, version creation, reviewer actions and report export are recorded in `audit_events`.
- **Demo contract:** use **Load demo agreement** to create a fresh record from the bundled synthetic agreement, analyze it and extract obligations.
- **Exports:** export a PDF review report with risk findings, evidence, expected/actual values, suggested actions, review status, obligations and a human-review disclaimer. Export obligations to CSV from the dashboard.
- **Version comparison:** the existing comparison screen remains the place to inspect clause additions, removals and modifications, alongside risk changes.

The dashboard's existing visual language and navigation are retained; additions use the same dark surfaces, emerald accent and compact controls.

### Extra test coverage

The API integration test checks demo-contract creation, persisted reviewer actions, audit events, a valid PDF response, authentication failures, malformed uploads, cross-account nested-resource access, and cleanup of audit/review records when a contract is deleted. The report uses ReportLab, included in `backend/requirements.txt`.


## Login and registration

The frontend starts at `frontend/auth.html`. Users can create an account or sign in. Passwords are stored as salted PBKDF2-SHA256 hashes, and contract/playbook API requests require a signed bearer token. Tokens expire after eight hours. Set a unique, long `AUTH_SECRET` in `.env` for stable sessions before sharing or deploying the application. If omitted, a random in-memory signing secret is generated for local development and all sessions are invalidated when the backend restarts. The local static frontend stores the bearer token in browser local storage for this hackathon prototype; do not use this authentication design for sensitive production deployment without moving to an appropriately secured session/cookie architecture and applying HTTPS. Each contract and generated version is owned by the authenticated account. API middleware checks ownership on contract-specific routes, list results are scoped to the signed-in user, and cross-account access returns 404. Existing database rows from earlier versions are migrated with a null owner and are deliberately hidden until explicitly reassigned.

Use the frontend static server as usual, and open `auth.html` first. The backend auth endpoints are `POST /auth/register`, `POST /auth/login`, and protected workspace APIs use `Authorization: Bearer <access_token>`.

### Tenant isolation and evaluation

- Every new contract, bundled demo contract and generated V2 is associated with the signed-in user. Contract-specific routes enforce ownership centrally; list responses are owner-scoped. Cross-account access tests cover list, read, analyze and delete attempts.
- Legacy contract rows are not automatically assigned to the first user. They remain hidden until an administrator explicitly migrates ownership.
- Run `python -m pytest -q` from the repository root for deterministic risk, traceability, comparison, auth-isolation and API end-to-end checks. The tests use synthetic fixtures and do not claim general legal-domain accuracy.
- Use `AUTH_SECRET` and `CORS_ORIGINS` in `.env` for local configuration. Production deployment additionally requires HTTPS, secure session design, deployment-specific CORS origins, database backups and security review.

### Reproducible synthetic benchmark

Run `python scripts/evaluate_synthetic.py` from the repository root. The benchmark evaluates 12 hand-labelled synthetic cases across standard, risky, missing, ambiguous and conflicting outcomes. The current rule implementation matches all 12 expected labels on this small benchmark. This is only a deterministic regression smoke test: the cases are authored to exercise known rule paths and do **not** estimate real-world legal accuracy, generalization, or production safety. Add independently labelled contracts and report false positives/false negatives before making any broader accuracy claim.

### Final demo checklist

1. Start the API and frontend using the quick-start commands.
2. Register a new user and sign in.
3. Load the synthetic demo agreement and run analysis.
4. Open a finding and verify its source quotation and rule ID.
5. Review obligations, save a reviewer action, and inspect the audit trail.
6. Generate/compare a version and check the actual text diff and risk changes.
7. Export and open the PDF/CSV files.
8. Register a second user and verify that the first user's contracts do not appear and direct contract URLs/API IDs return 404.
9. Test a malformed/oversized upload and confirm a clear error message.
