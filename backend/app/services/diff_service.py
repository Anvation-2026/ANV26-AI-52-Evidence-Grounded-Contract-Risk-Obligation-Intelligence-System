import difflib
import re


def _norm(value):
    return re.sub(r"\W+", " ", (value or "").lower()).strip()


def _identity(clause):
    return (clause.clause_number or "").strip().lower()


def compare_clauses(v1_clauses, v2_clauses):
    old_remaining = list(v1_clauses)
    new_remaining = list(v2_clauses)
    pairs = []
    # Match stable section numbers first.
    for old in list(old_remaining):
        key = _identity(old)
        match = next((new for new in new_remaining if key and _identity(new) == key), None)
        if match is not None:
            pairs.append((old, match))
            old_remaining.remove(old); new_remaining.remove(match)
    # Then match title or near-identical text, allowing renumbered clauses.
    for old in list(old_remaining):
        old_title = _norm(old.clause_title)
        old_text = _norm(old.clause_text)
        best, best_score = None, 0.0
        for new in new_remaining:
            title_score = difflib.SequenceMatcher(None, old_title, _norm(new.clause_title)).ratio() if old_title else 0
            text_score = difflib.SequenceMatcher(None, old_text, _norm(new.clause_text)).ratio() if old_text else 0
            score = max(title_score if title_score > .72 else 0, text_score)
            if score > best_score:
                best, best_score = new, score
        if best is not None and best_score >= .68:
            pairs.append((old, best)); old_remaining.remove(old); new_remaining.remove(best)
    changes = []
    for old, new in pairs:
        before, after = old.clause_text or "", new.clause_text or ""
        kind = "UNCHANGED" if before == after else "MODIFIED"
        changes.append({
            "clause_number": new.clause_number or old.clause_number,
            "clause_title": new.clause_title or old.clause_title,
            "change_type": kind, "before": before, "after": after,
            "diff": list(difflib.ndiff(before.split(), after.split())) if kind == "MODIFIED" else [],
            "inline_diff": {"removed": [x[2:] for x in difflib.ndiff(before.split(), after.split()) if x.startswith("- ")], "added": [x[2:] for x in difflib.ndiff(before.split(), after.split()) if x.startswith("+ ")]},
            "risk_impact": "REVIEW CHANGE" if kind == "MODIFIED" else "NO CHANGE",
            "matched_by": "section_or_similarity"
        })
    for new in new_remaining:
        changes.append({"clause_number": new.clause_number, "clause_title": new.clause_title, "change_type": "ADDED", "before": None, "after": new.clause_text, "diff": [], "inline_diff": {"removed": [], "added": (new.clause_text or "").split()}, "risk_impact": "REVIEW CHANGE", "matched_by": "unmatched_new_clause"})
    for old in old_remaining:
        changes.append({"clause_number": old.clause_number, "clause_title": old.clause_title, "change_type": "REMOVED", "before": old.clause_text, "after": None, "diff": [], "inline_diff": {"removed": (old.clause_text or "").split(), "added": []}, "risk_impact": "HIGH - CLAUSE REMOVED", "matched_by": "unmatched_old_clause"})
    return changes
