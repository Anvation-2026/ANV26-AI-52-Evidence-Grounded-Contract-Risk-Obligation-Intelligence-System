from typing import Dict, List, Any


def build_evidence_finding(
    clause: Dict[str, Any],
    rule: Dict[str, Any],
    risk_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine contract evidence, playbook rule information,
    and risk analysis into one traceable finding.

    This structure is designed to be consumed later
    by the backend and frontend.
    """

    return {
        "section": clause.get("section"),
        "clause_type": clause.get("clause_type"),
        "page": clause.get("page"),

        # IMPORTANT:
        # This must always come from the actual contract.
        "evidence_text": clause.get("text", ""),

        # Playbook traceability
        "rule_id": rule.get("rule_id"),
        "category": rule.get("category"),
        "requirement": rule.get("requirement"),

        # Comparison
        "expected_value": risk_result.get("expected_value"),
        "actual_value": risk_result.get("actual_value"),

        # Risk result
        "classification": risk_result.get("classification"),
        "severity": risk_result.get("severity"),

        # Explanation and action
        "explanation": risk_result.get("explanation"),
        "suggested_action": risk_result.get("suggested_action"),

        # Evidence validation
        "evidence_found": bool(clause.get("text"))
    }


def build_evidence_report(
    findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build a complete evidence-grounded analysis report.
    """

    return {
        "total_findings": len(findings),
        "findings": findings
    }


if __name__ == "__main__":

    # ---------------------------------------------------------
    # TEST CONTRACT CLAUSE
    # ---------------------------------------------------------

    test_clause = {
        "section": "2",
        "clause_type": "Termination",
        "page": 2,
        "text": (
            "Either party may terminate this agreement "
            "by providing 7 days written notice."
        )
    }

    # ---------------------------------------------------------
    # TEST PLAYBOOK RULE
    # ---------------------------------------------------------

    test_rule = {
        "rule_id": "TERM-001",
        "category": "TERMINATION",
        "requirement": (
            "Termination for convenience must provide "
            "at least 30 days written notice."
        )
    }

    # ---------------------------------------------------------
    # TEST RISK ANALYSIS RESULT
    # ---------------------------------------------------------

    test_risk_result = {
        "classification": "RISKY",
        "severity": "HIGH",
        "expected_value": "At least 30 days",
        "actual_value": "7 days",
        "explanation": (
            "The contract provides only 7 days of termination "
            "notice, which is below the playbook requirement "
            "of 30 days."
        ),
        "suggested_action": (
            "Increase the termination notice period "
            "to at least 30 days."
        )
    }

    # ---------------------------------------------------------
    # BUILD TRACEABLE FINDING
    # ---------------------------------------------------------

    finding = build_evidence_finding(
        clause=test_clause,
        rule=test_rule,
        risk_result=test_risk_result
    )

    # ---------------------------------------------------------
    # BUILD REPORT
    # ---------------------------------------------------------

    report = build_evidence_report([finding])

    print("\n" + "=" * 70)
    print("EVIDENCE TRACEABILITY TEST")
    print("=" * 70)

    for key, value in finding.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 70)
    print("REPORT SUMMARY")
    print("=" * 70)

    print(f"Total findings: {report['total_findings']}")