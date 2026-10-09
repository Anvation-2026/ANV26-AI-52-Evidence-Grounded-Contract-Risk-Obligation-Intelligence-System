from playbook_loader import load_playbook


def detect_missing_clauses(clauses):
    """
    Detect playbook-required clause categories that are
    completely missing from the contract.

    Args:
        clauses: List of segmented contract clauses.

    Returns:
        List of missing clause findings.
    """

    rules = load_playbook()

    detected_categories = set()

    for clause in clauses:
        clause_type = clause.get(
            "clause_type",
            "Other"
        )

        if clause_type:
            normalized_category = (
                clause_type
                .strip()
                .upper()
                .replace(" ", "_")
            )

            detected_categories.add(
                normalized_category
            )

    missing = []

    for rule in rules:

        rule_category = (
            rule["category"]
            .strip()
            .upper()
            .replace(" ", "_")
        )

        if rule_category not in detected_categories:

            missing.append(
                {
                    "section": None,
                    "clause_type": rule_category,
                    "page": None,

                    "evidence_text": (
                        "No corresponding clause "
                        "detected in the contract."
                    ),

                    "rule_id": rule["rule_id"],
                    "category": rule["category"],
                    "requirement": rule["requirement"],

                    "expected_value": (
                        rule["requirement"]
                    ),

                    "actual_value": None,

                    "classification": "MISSING",
                    "severity": rule["severity"],

                    "explanation": (
                        f"The contract does not contain "
                        f"a clearly identifiable "
                        f"{rule_category.replace('_', ' ').title()} "
                        f"clause required by the playbook."
                    ),

                    "suggested_action": (
                        f"Add a {rule_category.replace('_', ' ').title()} "
                        f"clause that satisfies the playbook requirement."
                    ),

                    "evidence_found": False
                }
            )

    return missing


if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("MISSING CLAUSE DETECTION TEST")
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

    missing_clauses = detect_missing_clauses(
        test_clauses
    )

    print(
        f"\nTotal missing clauses: "
        f"{len(missing_clauses)}"
    )

    for number, finding in enumerate(
        missing_clauses,
        start=1
    ):

        print("\n" + "-" * 70)
        print(
            f"MISSING CLAUSE {number}"
        )
        print("-" * 70)

        print(
            f"Rule: {finding['rule_id']}"
        )

        print(
            f"Category: {finding['category']}"
        )

        print(
            f"Classification: {finding['classification']}"
        )

        print(
            f"Severity: {finding['severity']}"
        )

        print(
            f"Evidence Found: "
            f"{finding['evidence_found']}"
        )

        print(
            f"Evidence: "
            f"{finding['evidence_text']}"
        )

        print(
            f"Explanation: "
            f"{finding['explanation']}"
        )

        print(
            f"Suggested Action: "
            f"{finding['suggested_action']}"
        )