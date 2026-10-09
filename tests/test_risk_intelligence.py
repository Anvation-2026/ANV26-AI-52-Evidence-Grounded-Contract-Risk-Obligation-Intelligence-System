import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.risk_service import analyze_clauses
from app.services.diff_service import compare_clauses

class Clause:
    def __init__(self, number, title, text):
        self.clause_number=number; self.clause_title=title; self.clause_text=text; self.page_number=1

def by_rule(findings, rule):
    return next(x for x in findings if x["rule_id"] == rule and x["status"] != "CONFLICTING")

def test_payment_risky_and_traceable():
    findings=analyze_clauses([{"id":7,"clause_number":"4.2","clause_title":"Payment","clause_text":"Customer shall pay invoices within 60 days of receipt.","page_number":2}])
    item=by_rule(findings,"PAYMENT-001")
    assert item["status"] == "RISKY" and item["clause_id"] == 7 and "60 days" in item["evidence"]

def test_payment_ambiguous():
    findings=analyze_clauses([{"clause_number":"4","clause_title":"Payment","clause_text":"Customer shall pay promptly."}])
    assert by_rule(findings,"PAYMENT-001")["status"] == "AMBIGUOUS"

def test_missing_liability_cap_not_standard_by_heading_alone():
    findings=analyze_clauses([{"clause_number":"8","clause_title":"Limitation of Liability","clause_text":"Each party may be liable for losses."}])
    assert by_rule(findings,"LIABILITY-001")["status"] == "RISKY"

def test_absent_provision_is_missing():
    findings=analyze_clauses([{"clause_number":"1","clause_title":"Payment","clause_text":"Payment within 30 days."}])
    assert by_rule(findings,"DATA-001")["status"] == "MISSING"

def test_conflicting_periods_are_reported_with_both_sources():
    clauses=[{"clause_number":"4.1","clause_title":"Payment","clause_text":"Invoices are payable within 30 days."},{"clause_number":"9.2","clause_title":"Payment exception","clause_text":"All invoices must be paid within 60 days."}]
    findings=analyze_clauses(clauses)
    conflicts=[x for x in findings if x["status"] == "CONFLICTING" and x["rule_id"] == "PAYMENT-001"]
    assert conflicts and "4.1" in conflicts[0]["evidence"] and "9.2" in conflicts[0]["evidence"]

def test_comparison_matches_renumbered_clause():
    old=[Clause("4","Payment","Payment shall be made within 60 days.")]
    new=[Clause("7","Payment","Payment shall be made within 30 days.")]
    changes=compare_clauses(old,new)
    assert len(changes)==1 and changes[0]["change_type"] == "MODIFIED"
    assert "60" in changes[0]["inline_diff"]["removed"] and "30" in changes[0]["inline_diff"]["added"]

def test_comparison_detects_added_and_removed():
    changes=compare_clauses([Clause("1","Old","old content")],[Clause("2","New","brand new clause")])
    assert any(x["change_type"] == "ADDED" for x in changes)
    assert any(x["change_type"] == "REMOVED" for x in changes)


def test_synthetic_benchmark_known_answers():
    import json
    benchmark_path = ROOT / "evaluation" / "synthetic_benchmark.json"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    for case in benchmark["cases"]:
        clauses = case.get("clauses") or [case["clause"]]
        findings = analyze_clauses(clauses)
        if case["expected"] == "CONFLICTING":
            match = next((item for item in findings if item["rule_id"] == case["rule_id"] and item["status"] == "CONFLICTING"), None)
        else:
            match = next((item for item in findings if item["rule_id"] == case["rule_id"] and item["status"] != "CONFLICTING"), None)
        assert match is not None, f"No result for benchmark case {case['id']}"
        assert match["status"] == case["expected"], f"{case['id']}: expected {case['expected']}, got {match['status']}"
