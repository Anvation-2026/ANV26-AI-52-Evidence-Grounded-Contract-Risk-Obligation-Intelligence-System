\
import json
import re
from pathlib import Path

PLAYBOOK_PATH = Path(__file__).resolve().parents[3] / "playbook" / "rules.json"


def load_playbook():
    data = json.loads(PLAYBOOK_PATH.read_text(encoding="utf-8-sig"))
    return data["rules"] if isinstance(data, dict) else data


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _days(text):
    match = re.search(r"\b(\d+)\s*(?:business\s+|calendar\s+)?days?\b", text, re.I)
    return int(match.group(1)) if match else None


def _has(text, phrases):
    return any(phrase in text for phrase in phrases)


def _finding(rule, status, clause=None, expected=None, actual=None, reason="", action=""):
    text = (clause or {}).get("clause_text") or (clause or {}).get("text")
    return {
        "clause_id": (clause or {}).get("id"),
        "clause_number": (clause or {}).get("clause_number") or (clause or {}).get("section"),
        "clause_title": (clause or {}).get("clause_title"),
        "page_number": (clause or {}).get("page_number") or (clause or {}).get("page"),
        "rule_id": rule["rule_id"], "category": rule["category"],
        "status": status, "classification": status,
        "severity": rule.get("severity", "MEDIUM") if status != "STANDARD" else "LOW",
        "evidence": text if text else "No corresponding source clause was detected.",
        "expected": expected or rule.get("requirement"), "actual": actual,
        "reason": reason, "recommended_action": action,
        "evidence_found": bool(text), "source_type": "contract_clause" if text else "absence_check",
        "confidence": "high" if text and status in {"STANDARD", "RISKY"} else "review_required"
    }


def _evaluate(rule, clause):
    text = normalize_text((clause.get("clause_text") or clause.get("text") or "") + " " + (clause.get("clause_title") or ""))
    cat = normalize_text(rule.get("category"))
    if not text:
        return None
    if cat == "payment":
        if not _has(text, ["payment", "pay ", "paid", "invoice", "remit"]): return None
        days = _days(text)
        if days is None:
            return _finding(rule, "AMBIGUOUS", clause, "Payment within 30 days", "Period not measurable", "A payment-related clause exists, but a measurable payment period was not found.", "Specify an explicit payment period and its trigger, such as within 30 days of receipt of a valid invoice.")
        if days > 30:
            return _finding(rule, "RISKY", clause, "No more than 30 days", f"{days} days", f"The stated payment period ({days} days) exceeds the playbook maximum of 30 days.", "Consider revising the period to 30 days or less, subject to reviewer approval.")
        return _finding(rule, "STANDARD", clause, "No more than 30 days", f"{days} days", f"The stated payment period ({days} days) meets the playbook's 30-day maximum.", "No change indicated by this rule; reviewer should confirm the trigger and exceptions.")
    if cat == "termination":
        if not _has(text, ["terminat", "terminate", "termination"]): return None
        days = _days(text)
        if days is None:
            return _finding(rule, "AMBIGUOUS", clause, "At least 30 days", "Period not measurable", "Termination is mentioned but no measurable notice period was found.", "Specify a clear notice period and whether it applies to each termination pathway.")
        if days < 30:
            return _finding(rule, "RISKY", clause, "At least 30 days", f"{days} days", f"The stated notice period ({days} days) is below the playbook minimum of 30 days.", "Consider revising the notice period to at least 30 days, subject to reviewer approval.")
        return _finding(rule, "STANDARD", clause, "At least 30 days", f"{days} days", f"The stated notice period ({days} days) meets the playbook minimum.", "Confirm that all termination pathways are covered consistently.")
    phrase_map = {
        "liability": ["liability", "liable", "limitation of liability"],
        "indemnification": ["indemnif", "indemnity"],
        "confidentiality": ["confidential", "non-disclosure", "nondisclosure"],
        "ip ownership": ["intellectual property", "ip ownership", "proprietary rights", "work product"],
        "data protection": ["data protection", "personal data", "privacy", "data processing"],
        "governing law": ["governing law", "laws of", "jurisdiction"]
    }
    phrases = phrase_map.get(cat, [cat])
    if not _has(text, phrases): return None
    if cat == "liability":
        cap = re.search(r"(?:liability|aggregate liability|liabilities)[^.;]{0,100}(?:shall not exceed|limited to|capped at|maximum of)\s+([^.;]+)", text, re.I)
        if not cap:
            return _finding(rule, "RISKY", clause, "An explicit liability cap", "Liability language found; cap not identified", "A liability-related provision exists, but an explicit cap could not be verified from this clause.", "Review whether the agreement defines a clear monetary cap, its calculation basis, and any exceptions.")
        return _finding(rule, "STANDARD", clause, "An explicit liability cap", cap.group(1).strip(), "A candidate cap expression was found; human review should verify scope and carve-outs.", "Verify the cap amount, covered claims, and exclusions against the playbook.")
    if cat == "governing law" and not _has(text, ["governed by the laws", "governed by laws", "laws of", "governing law"]):
        return _finding(rule, "AMBIGUOUS", clause, rule.get("requirement"), "Jurisdiction mention only", "A jurisdiction-related phrase exists but governing-law wording is unclear.", "State the governing law expressly and separately specify venue if required.")
    body = normalize_text(clause.get("clause_text") or clause.get("text") or "")
    quality_checks = {
        "confidentiality": (["shall keep", "shall protect", "shall not disclose", "must protect", "must not disclose", "keep confidential", "protect confidential"], "Confirm that the clause defines protected information, permitted disclosures and an express non-disclosure/protection duty."),
        "indemnification": (["indemnify and hold harmless", "indemnify", "indemnification for", "indemnity for"], "Specify the indemnifying party, covered claims/losses, procedure and any limitations."),
        "ip ownership": (["owned by", "ownership of", "assign", "assigned to", "vest in", "shall own", "intellectual property rights in"], "Specify ownership of pre-existing and newly created IP, assignment mechanics and relevant licences."),
        "data protection": (["shall protect", "shall process", "data controller", "data processor", "security measures", "personal data shall", "comply with applicable data protection"], "Define each party's data role, permitted processing, security, incident notice and deletion/return duties as applicable.")
    }
    if cat in quality_checks and not _has(body, quality_checks[cat][0]):
        return _finding(rule, "AMBIGUOUS", clause, rule.get("requirement"), "Operative requirement not verified", f"A {rule.get('category')} reference exists but a clear operative duty could not be verified.", quality_checks[cat][1])
    return _finding(rule, "STANDARD", clause, rule.get("requirement"), "Relevant operative provision detected", f"A {rule.get('category')} provision with relevant operative wording was located. This limited rule check does not establish complete legal sufficiency.", "Review the full provision against the complete playbook requirement; keyword presence is not proof of complete compliance.")


def _category_hint(rule, clause):
    text = normalize_text((clause.get("clause_text") or clause.get("text") or "") + " " + (clause.get("clause_title") or ""))
    cat = normalize_text(rule.get("category"))
    hints = {
        "payment": ["payment", "pay ", "invoice", "remit"],
        "termination": ["terminat"], "liability": ["liability", "liable"],
        "indemnification": ["indemnif", "indemnity"],
        "confidentiality": ["confidential", "non-disclosure", "nondisclosure"],
        "ip ownership": ["intellectual property", "proprietary rights", "work product"],
        "data protection": ["data protection", "personal data", "privacy", "data processing"],
        "governing law": ["governing law", "laws of", "jurisdiction"]
    }
    return _has(text, hints.get(cat, [cat]))


def _detect_conflicts(clauses, rules):
    findings = []
    # Only compare the same concept and report evidence from both clauses.
    for rule in rules:
        cat = normalize_text(rule.get("category"))
        relevant = [c for c in clauses if _category_hint(rule, c)]
        if len(relevant) < 2: continue
        values = []
        for clause in relevant:
            text = clause.get("clause_text") or clause.get("text") or ""
            days = _days(text)
            if days is not None and cat in {"payment", "termination"}:
                values.append((days, clause))
        if len(values) >= 2 and len({v[0] for v in values}) > 1:
            evidence = "\n\n".join(f"Clause ID {c.get('id') or 'not persisted'} | Section {c.get('clause_number') or c.get('section') or 'unnumbered'}: {c.get('clause_text') or c.get('text','')}" for _, c in values)
            findings.append({
                "clause_id": values[0][1].get("id"), "clause_number": ", ".join(str(c.get("clause_number") or c.get("section") or "unnumbered") for _, c in values),
                "clause_title": rule.get("category"), "page_number": None,
                "rule_id": rule["rule_id"], "category": rule["category"], "status": "CONFLICTING", "classification": "CONFLICTING",
                "severity": rule.get("severity", "HIGH"), "evidence": evidence, "expected": rule.get("requirement"),
                "actual": ", ".join(f"{n} days" for n, _ in values),
                "reason": f"Multiple {rule.get('category').lower()} provisions contain different time periods; the applicable obligation is unclear.",
                "recommended_action": "Reconcile the cited provisions and state one consistent rule or clearly define when each period applies.",
                "evidence_found": True, "source_type": "cross_clause_comparison", "confidence": "review_required"
            })
    return findings


def analyze_clauses(clauses):
    rules = load_playbook()
    findings = []
    for rule in rules:
        candidates = [c for c in clauses if _category_hint(rule, c)]
        if not candidates:
            findings.append(_finding(rule, "MISSING", None, rule.get("requirement"), None,
                f"No source clause matching the {rule.get('category')} requirement was detected. This is a detection result, not proof of absence if extraction was incomplete.",
                f"Review the full document for this requirement; if absent, consider adding a provision that satisfies: {rule.get('requirement')}"))
            continue
        evaluated = [_evaluate(rule, c) for c in candidates]
        evaluated = [x for x in evaluated if x]
        if not evaluated:
            findings.append(_finding(rule, "AMBIGUOUS", candidates[0], rule.get("requirement"), "Potential clause detected; no rule-specific evaluation", "Relevant wording was detected but could not be evaluated reliably.", "Manually review this provision against the playbook and confirm the clause category."))
        else:
            # Prefer highest concern when multiple clauses cover a rule; conflict is reported separately.
            priority = {"RISKY": 0, "AMBIGUOUS": 1, "STANDARD": 2, "MISSING": 3}
            findings.append(sorted(evaluated, key=lambda f: priority.get(f["status"], 9))[0])
    findings.extend(_detect_conflicts(clauses, rules))
    return findings
