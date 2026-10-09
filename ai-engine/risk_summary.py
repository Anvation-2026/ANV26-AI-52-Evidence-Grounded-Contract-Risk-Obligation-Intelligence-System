from collections import Counter
from typing import List, Dict, Any


def build_risk_summary(
    findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build a summary of contract risk findings.

    Counts:
    - Severity
    - Classification
    """

    severity_counts = Counter()
    classification_counts = Counter()

    for finding in findings:

        severity = finding.get(
            "severity",
            "UNKNOWN"
        )

        classification = finding.get(
            "classification",
            "UNKNOWN"
        )

        severity_counts[severity] += 1
        classification_counts[classification] += 1

    return {
        "high_risk": severity_counts.get(
            "HIGH",
            0
        ),

        "medium_risk": severity_counts.get(
            "MEDIUM",
            0
        ),

        "low_risk": severity_counts.get(
            "LOW",
            0
        ),

        "standard": classification_counts.get(
            "STANDARD",
            0
        ),

        "risky": classification_counts.get(
            "RISKY",
            0
        ),

        "ambiguous": classification_counts.get(
            "AMBIGUOUS",
            0
        ),

        "missing": classification_counts.get(
            "MISSING",
            0
        )
    }


def print_risk_summary(
    summary: Dict[str, Any]
):
    """
    Print a human-readable risk summary.
    """

    print("\n" + "=" * 70)
    print("RISK SUMMARY")
    print("=" * 70)

    print(
        f"High Risk       : "
        f"{summary['high_risk']}"
    )

    print(
        f"Medium Risk     : "
        f"{summary['medium_risk']}"
    )

    print(
        f"Low Risk        : "
        f"{summary['low_risk']}"
    )

    print("\nClassification")
    print("-" * 70)

    print(
        f"Standard        : "
        f"{summary['standard']}"
    )

    print(
        f"Risky           : "
        f"{summary['risky']}"
    )

    print(
        f"Ambiguous       : "
        f"{summary['ambiguous']}"
    )

    print(
        f"Missing         : "
        f"{summary['missing']}"
    )


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("RISK SUMMARY TEST")
    print("=" * 70)

    test_findings = [
        {
            "classification": "STANDARD",
            "severity": "LOW"
        },
        {
            "classification": "STANDARD",
            "severity": "LOW"
        },
        {
            "classification": "MISSING",
            "severity": "HIGH"
        },
        {
            "classification": "MISSING",
            "severity": "HIGH"
        },
        {
            "classification": "MISSING",
            "severity": "MEDIUM"
        }
    ]

    summary = build_risk_summary(
        test_findings
    )

    print_risk_summary(
        summary
    )