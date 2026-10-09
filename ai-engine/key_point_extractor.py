from typing import List, Dict, Any


def extract_key_points(
    clauses: List[Dict[str, Any]],
    findings: List[Dict[str, Any]] | None = None
) -> List[str]:
    """
    Extract concise, evidence-grounded key points
    from contract clauses and risk findings.

    Key points are generated only from information
    available in the contract analysis.
    """

    key_points = []

    # ---------------------------------------------------------
    # 1. CONTRACT CLAUSE KEY POINTS
    # ---------------------------------------------------------

    for clause in clauses:

        clause_type = clause.get(
            "clause_type",
            "Other"
        )

        text = clause.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        key_points.append(
            f"{clause_type}: {text}"
        )

    # ---------------------------------------------------------
    # 2. RISK / MISSING CLAUSE KEY POINTS
    # ---------------------------------------------------------

    if findings:

        for finding in findings:

            classification = finding.get(
                "classification"
            )

            if classification == "MISSING":

                category = finding.get(
                    "category",
                    "Unknown"
                )

                key_points.append(
                    f"Missing {category.replace('_', ' ').title()} clause: "
                    f"{finding.get('requirement', '')}"
                )

            elif classification == "RISKY":

                category = finding.get(
                    "category",
                    "Unknown"
                )

                explanation = finding.get(
                    "explanation",
                    ""
                )

                key_points.append(
                    f"Risk identified in "
                    f"{category.replace('_', ' ').title()}: "
                    f"{explanation}"
                )

    return key_points


def build_key_point_report(
    clauses: List[Dict[str, Any]],
    findings: List[Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    """
    Build a structured key-point report.
    """

    key_points = extract_key_points(
        clauses,
        findings
    )

    return {
        "total_key_points": len(key_points),
        "key_points": key_points
    }


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("AI KEY POINT EXTRACTION TEST")
    print("=" * 70)

    test_clauses = [
        {
            "section": "1",
            "clause_type": "Payment",
            "page": 1,
            "text": (
                "The Customer shall pay the Supplier "
                "within 30 days of receiving an invoice."
            )
        },
        {
            "section": "2",
            "clause_type": "Termination",
            "page": 2,
            "text": (
                "Either party may terminate this agreement "
                "by providing 30 days written notice."
            )
        }
    ]

    test_findings = [
        {
            "classification": "MISSING",
            "category": "LIABILITY",
            "requirement": (
                "Liability should include a clearly defined "
                "limitation or liability cap."
            )
        },
        {
            "classification": "MISSING",
            "category": "CONFIDENTIALITY",
            "requirement": (
                "Confidential information must be protected."
            )
        }
    ]

    report = build_key_point_report(
        clauses=test_clauses,
        findings=test_findings
    )

    print(
        f"\nTotal key points: "
        f"{report['total_key_points']}"
    )

    print("\n" + "-" * 70)
    print("KEY POINTS")
    print("-" * 70)

    for number, point in enumerate(
        report["key_points"],
        start=1
    ):
        print(
            f"{number}. {point}"
        )