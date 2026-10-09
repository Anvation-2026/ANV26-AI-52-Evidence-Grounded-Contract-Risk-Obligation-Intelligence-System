# =============================================================
# AI SUPPORTING DOCUMENT SUGGESTER
# =============================================================

DOCUMENT_SUGGESTIONS = {

    "LIABILITY": [
        "Liability Insurance Certificate",
        "Professional Indemnity Policy",
        "Existing Liability Agreement"
    ],

    "INDEMNIFICATION": [
        "Indemnification Agreement",
        "Insurance Certificate",
        "Existing Indemnity Policy"
    ],

    "CONFIDENTIALITY": [
        "Non-Disclosure Agreement (NDA)",
        "Confidentiality Agreement",
        "Information Security Policy"
    ],

    "INTELLECTUAL_PROPERTY": [
        "Intellectual Property Assignment Agreement",
        "IP Ownership Agreement",
        "IP License Agreement"
    ],

    "DATA_PROTECTION": [
        "Data Processing Agreement (DPA)",
        "Privacy Policy",
        "Information Security / Data Protection Policy"
    ],

    "GOVERNING_LAW": [
        "Jurisdiction Agreement",
        "Applicable Law Policy",
        "Existing Contract Governing-Law Clause"
    ],

    "PAYMENT": [
        "Invoice",
        "Payment Schedule",
        "Purchase Order"
    ],

    "TERMINATION": [
        "Termination Notice",
        "Termination Agreement",
        "Contract Termination Policy"
    ]
}


# =============================================================
# DOCUMENT SUGGESTION
# =============================================================

def suggest_supporting_documents(finding):

    category = finding.get(
        "category",
        ""
    )

    category = (
        category
        .strip()
        .upper()
        .replace(" ", "_")
    )

    return DOCUMENT_SUGGESTIONS.get(
        category,
        []
    )


# =============================================================
# BUILD SUPPORTING DOCUMENT REPORT
# =============================================================

def build_supporting_document_report(findings):

    suggestions = []

    for finding in findings:

        classification = finding.get(
            "classification",
            ""
        )

        classification = (
            classification
            .strip()
            .upper()
        )

        # Supporting documents are mainly useful
        # for clauses requiring attention.
        if classification not in {
            "MISSING",
            "RISKY",
            "AMBIGUOUS"
        }:
            continue

        documents = suggest_supporting_documents(
            finding
        )

        if not documents:
            continue

        suggestions.append(
            {
                "rule_id": finding.get(
                    "rule_id"
                ),

                "category": finding.get(
                    "category"
                ),

                "classification": classification,

                "severity": finding.get(
                    "severity"
                ),

                "suggested_documents": documents,

                "reason": finding.get(
                    "explanation",
                    ""
                )
            }
        )

    # IMPORTANT:
    # Always return total_suggestions.
    return {
        "suggestions": suggestions,
        "total_suggestions": len(suggestions)
    }


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("AI SUPPORTING DOCUMENT SUGGESTION TEST")
    print("=" * 70)

    test_findings = [

        {
            "rule_id": "LIAB-001",
            "category": "LIABILITY",
            "classification": "MISSING",
            "severity": "HIGH",
            "explanation": (
                "Liability clause is missing."
            )
        },

        {
            "rule_id": "CONF-001",
            "category": "CONFIDENTIALITY",
            "classification": "MISSING",
            "severity": "MEDIUM",
            "explanation": (
                "Confidentiality clause is missing."
            )
        },

        {
            "rule_id": "DATA-001",
            "category": "DATA_PROTECTION",
            "classification": "MISSING",
            "severity": "HIGH",
            "explanation": (
                "Data protection clause is missing."
            )
        }
    ]

    report = build_supporting_document_report(
        test_findings
    )

    print(
        f"\nTotal suggestion categories: "
        f"{report['total_suggestions']}"
    )

    for suggestion in report["suggestions"]:

        print("\n" + "-" * 70)

        print(
            f"Rule: {suggestion['rule_id']}"
        )

        print(
            f"Category: {suggestion['category']}"
        )

        print(
            f"Classification: "
            f"{suggestion['classification']}"
        )

        print(
            f"Severity: "
            f"{suggestion['severity']}"
        )

        print(
            "Suggested Documents:"
        )

        for document in suggestion[
            "suggested_documents"
        ]:

            print(
                f"  - {document}"
            )