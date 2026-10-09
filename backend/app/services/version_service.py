\
import re


def generate_clause_v2(clause):
    """Suggest limited deterministic edits only where the rule and text match.

    This is a review draft, not an autonomous legal rewrite. Unsupported patterns
    are left unchanged and surfaced for manual review.
    """
    text = clause.clause_text or ""
    revised = text
    title = (clause.clause_title or "").lower()
    if "payment" in title or re.search(r"\b(payment|invoice|payable)\b", text, re.I):
        revised = re.sub(r"\bwithin\s+(?:45|60|75|90|120)\s+days\b", "within 30 days", revised, flags=re.I)
        revised = re.sub(r"\bwithin\s+(\d+)\s+days\b", lambda m: "within 30 days" if int(m.group(1)) > 30 else m.group(0), revised, flags=re.I)
    if "termination" in title or re.search(r"\btermination\b", text, re.I):
        revised = re.sub(r"\b(?:with|upon)\s+(?:7|10|14|15|20)\s+days(?:'|’)??\s*(?:written\s+)?notice\b", "with 30 days written notice", revised, flags=re.I)
        revised = re.sub(r"\b(\d+)\s+days\s+(?:written\s+)?notice\b", lambda m: "30 days written notice" if int(m.group(1)) < 30 else m.group(0), revised, flags=re.I)
    return revised


def generate_contract_v2(clauses):
    revised_clauses = []
    for clause in clauses:
        revised_text = generate_clause_v2(clause)
        revised_clauses.append({
            "clause_number": clause.clause_number,
            "clause_title": clause.clause_title,
            "clause_text": revised_text,
            "page_number": clause.page_number,
            "changed": revised_text != clause.clause_text,
            "revision_type": "SUGGESTED_RULE_BASED_EDIT" if revised_text != clause.clause_text else "UNCHANGED_REVIEW_REQUIRED",
            "requires_human_review": True
        })
    return revised_clauses
