# Architecture and evidence flow

1. **Document intake** validates extension, size and file signature/container structure; stores bytes under an opaque server-generated filename.
2. **Extraction** produces clause text, section identifiers and page references where available. DOCX paragraph page positions are not reliably available in the current parser.
3. **Playbook evaluation** reads stable rules from `playbook/rules.json`. Deterministic checks are authoritative for supported measurable requirements; unknown or insufficient evidence should remain ambiguous.
4. **Coverage** creates a missing finding when no relevant source clause is detected, explicitly caveated as a detection result in case extraction was incomplete.
5. **Conflict scan** compares multiple clauses for differing measurable payment/termination periods and preserves both quotations.
6. **Persistence** stores contracts, clauses, findings and obligations in SQLAlchemy-backed storage.
7. **Traceability** links a finding to its clause ID when a single source clause exists; cross-clause conflicts preserve both clauses in the evidence text and clause identifiers.
8. **Version comparison** matches by section number first and then title/text similarity, returns additions/removals/modifications and token-level differences. Similarity matching is heuristic and must be verified by a reviewer.

## Status semantics

- `STANDARD`: a supported check passed; does not certify legal sufficiency.
- `RISKY`: a supported check failed or a required element (such as an explicit liability cap) could not be verified despite relevant clause language.
- `MISSING`: no relevant clause was detected; this is not conclusive if extraction failed.
- `AMBIGUOUS`: relevant wording exists but the rule cannot be evaluated reliably.
- `CONFLICTING`: two or more source clauses contain different measurable periods for the same concept.

## Security and scope

The prototype has no autonomous approval. Uploaded contracts may contain sensitive information; run locally, restrict access, and do not upload confidential documents to a public demo. For production, add authentication/authorization, retention controls, audit events, antivirus scanning, OCR and stronger database migrations.
