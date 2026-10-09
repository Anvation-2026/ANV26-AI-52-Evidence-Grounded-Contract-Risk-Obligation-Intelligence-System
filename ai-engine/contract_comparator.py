import re
from difflib import SequenceMatcher

from playbook_loader import load_playbook


def normalize_text(text):
    """
    Normalize text for comparison.
    """
    return " ".join(
        text.strip().lower().split()
    )


def calculate_similarity(text1, text2):
    """
    Calculate similarity between two clause texts.
    """

    return round(
        SequenceMatcher(
            None,
            normalize_text(text1),
            normalize_text(text2)
        ).ratio(),
        4
    )


def extract_days(text):
    """
    Extract a number followed by 'day' or 'days'.
    """

    match = re.search(
        r"\b(\d+)\s*days?\b",
        text.lower()
    )

    if match:
        return int(match.group(1))

    return None


def get_rule_for_category(category):
    """
    Find the playbook rule for a clause category.
    """

    normalized_category = (
        category
        .strip()
        .upper()
        .replace(" ", "_")
    )

    rules = load_playbook()

    for rule in rules:

        rule_category = (
            rule["category"]
            .strip()
            .upper()
            .replace(" ", "_")
        )

        if rule_category == normalized_category:
            return rule

    return None


def analyze_risk_change(
    category,
    old_text,
    new_text,
    change_type
):
    """
    Determine the risk impact of a contract version change
    using the existing playbook rules.
    """

    rule = get_rule_for_category(
        category
    )

    if not rule:

        return {
            "risk_impact": "UNKNOWN",
            "severity": "LOW",
            "reason": (
                "No corresponding playbook "
                "rule was found."
            ),
            "suggested_action": (
                "Review the clause manually."
            )
        }

    category_normalized = (
        category
        .strip()
        .upper()
        .replace(" ", "_")
    )

    # ---------------------------------------------------------
    # ADDED CLAUSE
    # ---------------------------------------------------------

    if change_type == "ADDED":

        return {
            "risk_impact": "POSITIVE",
            "severity": rule["severity"],
            "reason": (
                f"The {category_normalized.replace('_', ' ').title()} "
                "clause has been added to the new contract."
            ),
            "suggested_action": (
                "Verify that the added clause fully satisfies "
                "the playbook requirement."
            )
        }

    # ---------------------------------------------------------
    # REMOVED CLAUSE
    # ---------------------------------------------------------

    if change_type == "REMOVED":

        return {
            "risk_impact": "INCREASED",
            "severity": rule["severity"],
            "reason": (
                f"The required {category_normalized.replace('_', ' ').title()} "
                "clause was removed from the new contract."
            ),
            "suggested_action": (
                f"Restore the {category_normalized.replace('_', ' ').title()} "
                "clause and ensure it satisfies the playbook requirement."
            )
        }

    # ---------------------------------------------------------
    # MODIFIED CLAUSE
    # ---------------------------------------------------------

    if change_type == "MODIFIED":

        old_days = extract_days(
            old_text
        )

        new_days = extract_days(
            new_text
        )

        # -----------------------------------------------------
        # PAYMENT
        # -----------------------------------------------------

        if category_normalized == "PAYMENT":

            if new_days is not None:

                if new_days > 30:

                    return {
                        "risk_impact": "INCREASED",
                        "severity": rule["severity"],
                        "reason": (
                            f"Payment period increased to "
                            f"{new_days} days, exceeding the "
                            "playbook maximum of 30 days."
                        ),
                        "suggested_action": (
                            "Reduce the payment period to "
                            "30 days or less."
                        )
                    }

                if (
                    old_days is not None
                    and new_days < old_days
                ):

                    return {
                        "risk_impact": "DECREASED",
                        "severity": "LOW",
                        "reason": (
                            f"Payment period decreased from "
                            f"{old_days} days to {new_days} days."
                        ),
                        "suggested_action": (
                            "No immediate change required."
                        )
                    }

                return {
                    "risk_impact": "NO_SIGNIFICANT_CHANGE",
                    "severity": "LOW",
                    "reason": (
                        f"Payment period changed to "
                        f"{new_days} days and remains within "
                        "the playbook maximum of 30 days."
                    ),
                    "suggested_action": (
                        "No immediate change required."
                    )
                }

        # -----------------------------------------------------
        # TERMINATION
        # -----------------------------------------------------

        if category_normalized == "TERMINATION":

            if new_days is not None:

                if new_days < 30:

                    return {
                        "risk_impact": "INCREASED",
                        "severity": rule["severity"],
                        "reason": (
                            f"Termination notice decreased to "
                            f"{new_days} days, below the "
                            "playbook minimum of 30 days."
                        ),
                        "suggested_action": (
                            "Increase the termination notice "
                            "period to at least 30 days."
                        )
                    }

                if (
                    old_days is not None
                    and new_days > old_days
                ):

                    return {
                        "risk_impact": "DECREASED",
                        "severity": "LOW",
                        "reason": (
                            f"Termination notice increased "
                            f"from {old_days} days to "
                            f"{new_days} days."
                        ),
                        "suggested_action": (
                            "No immediate change required."
                        )
                    }

                return {
                    "risk_impact": "NO_SIGNIFICANT_CHANGE",
                    "severity": "LOW",
                    "reason": (
                        f"Termination notice is now "
                        f"{new_days} days and satisfies "
                        "the playbook minimum."
                    ),
                    "suggested_action": (
                        "No immediate change required."
                    )
                }

        # -----------------------------------------------------
        # OTHER CLAUSES
        # -----------------------------------------------------

        return {
            "risk_impact": "REVIEW_REQUIRED",
            "severity": rule["severity"],
            "reason": (
                "The clause was modified. The change should "
                "be reviewed against the playbook requirement."
            ),
            "suggested_action": (
                "Review the modified clause against the "
                "applicable playbook requirement."
            )
        }

    # ---------------------------------------------------------
    # UNCHANGED
    # ---------------------------------------------------------

    return {
        "risk_impact": "NO_CHANGE",
        "severity": "LOW",
        "reason": (
            "The clause remains unchanged between "
            "contract versions."
        ),
        "suggested_action": (
            "No change required."
        )
    }


def compare_clauses(
    old_clauses,
    new_clauses
):
    """
    Compare clauses between two contract versions.
    """

    old_by_type = {}

    for clause in old_clauses:

        clause_type = clause.get(
            "clause_type",
            "Other"
        ).strip().upper()

        old_by_type.setdefault(
            clause_type,
            []
        ).append(clause)

    new_by_type = {}

    for clause in new_clauses:

        clause_type = clause.get(
            "clause_type",
            "Other"
        ).strip().upper()

        new_by_type.setdefault(
            clause_type,
            []
        ).append(clause)

    all_categories = (
        set(old_by_type.keys())
        | set(new_by_type.keys())
    )

    changes = []

    for category in sorted(
        all_categories
    ):

        old_items = old_by_type.get(
            category,
            []
        )

        new_items = new_by_type.get(
            category,
            []
        )

        # -----------------------------------------------------
        # ADDED
        # -----------------------------------------------------

        if not old_items:

            for new_clause in new_items:

                risk = analyze_risk_change(
                    category,
                    "",
                    new_clause.get(
                        "text",
                        ""
                    ),
                    "ADDED"
                )

                changes.append(
                    {
                        "change_type": "ADDED",
                        "clause_type": new_clause.get(
                            "clause_type"
                        ),
                        "old_clause": None,
                        "new_clause": new_clause,
                        "similarity": None,
                        **risk
                    }
                )

            continue

        # -----------------------------------------------------
        # REMOVED
        # -----------------------------------------------------

        if not new_items:

            for old_clause in old_items:

                risk = analyze_risk_change(
                    category,
                    old_clause.get(
                        "text",
                        ""
                    ),
                    "",
                    "REMOVED"
                )

                changes.append(
                    {
                        "change_type": "REMOVED",
                        "clause_type": old_clause.get(
                            "clause_type"
                        ),
                        "old_clause": old_clause,
                        "new_clause": None,
                        "similarity": None,
                        **risk
                    }
                )

            continue

        # -----------------------------------------------------
        # EXISTING CATEGORY
        # -----------------------------------------------------

        used_new_indexes = set()

        for old_clause in old_items:

            best_index = None
            best_similarity = -1

            for index, new_clause in enumerate(
                new_items
            ):

                if index in used_new_indexes:
                    continue

                similarity = calculate_similarity(
                    old_clause.get(
                        "text",
                        ""
                    ),
                    new_clause.get(
                        "text",
                        ""
                    )
                )

                if similarity > best_similarity:

                    best_similarity = similarity
                    best_index = index

            if best_index is not None:

                used_new_indexes.add(
                    best_index
                )

                new_clause = new_items[
                    best_index
                ]

                old_text = old_clause.get(
                    "text",
                    ""
                )

                new_text = new_clause.get(
                    "text",
                    ""
                )

                if normalize_text(
                    old_text
                ) == normalize_text(
                    new_text
                ):

                    change_type = "UNCHANGED"

                else:

                    change_type = "MODIFIED"

                risk = analyze_risk_change(
                    category,
                    old_text,
                    new_text,
                    change_type
                )

                changes.append(
                    {
                        "change_type": change_type,
                        "clause_type": old_clause.get(
                            "clause_type"
                        ),
                        "old_clause": old_clause,
                        "new_clause": new_clause,
                        "similarity": best_similarity,
                        **risk
                    }
                )

        # -----------------------------------------------------
        # EXTRA NEW CLAUSES
        # -----------------------------------------------------

        for index, new_clause in enumerate(
            new_items
        ):

            if index not in used_new_indexes:

                risk = analyze_risk_change(
                    category,
                    "",
                    new_clause.get(
                        "text",
                        ""
                    ),
                    "ADDED"
                )

                changes.append(
                    {
                        "change_type": "ADDED",
                        "clause_type": new_clause.get(
                            "clause_type"
                        ),
                        "old_clause": None,
                        "new_clause": new_clause,
                        "similarity": None,
                        **risk
                    }
                )

    return changes


def build_comparison_report(
    old_clauses,
    new_clauses
):
    """
    Build complete risk-aware comparison report.
    """

    changes = compare_clauses(
        old_clauses,
        new_clauses
    )

    summary = {
        "added": 0,
        "removed": 0,
        "modified": 0,
        "unchanged": 0,
        "risk_increased": 0,
        "risk_decreased": 0
    }

    for change in changes:

        change_type = change[
            "change_type"
        ].lower()

        if change_type in summary:

            summary[
                change_type
            ] += 1

        if change[
            "risk_impact"
        ] == "INCREASED":

            summary[
                "risk_increased"
            ] += 1

        elif change[
            "risk_impact"
        ] == "DECREASED":

            summary[
                "risk_decreased"
            ] += 1

    return {
        "old_total_clauses": len(
            old_clauses
        ),
        "new_total_clauses": len(
            new_clauses
        ),
        "total_changes": (
            summary["added"]
            + summary["removed"]
            + summary["modified"]
        ),
        "summary": summary,
        "changes": changes
    }


def print_comparison_report(
    report
):

    print("\n")
    print("=" * 70)
    print("RISK-AWARE CONTRACT VERSION COMPARISON")
    print("=" * 70)

    print(
        f"\nOld contract clauses: "
        f"{report['old_total_clauses']}"
    )

    print(
        f"New contract clauses: "
        f"{report['new_total_clauses']}"
    )

    print(
        f"Total changes: "
        f"{report['total_changes']}"
    )

    print("\n" + "-" * 70)
    print("SUMMARY")
    print("-" * 70)

    print(
        f"Added:          "
        f"{report['summary']['added']}"
    )

    print(
        f"Removed:        "
        f"{report['summary']['removed']}"
    )

    print(
        f"Modified:       "
        f"{report['summary']['modified']}"
    )

    print(
        f"Unchanged:      "
        f"{report['summary']['unchanged']}"
    )

    print(
        f"Risk Increased: "
        f"{report['summary']['risk_increased']}"
    )

    print(
        f"Risk Decreased: "
        f"{report['summary']['risk_decreased']}"
    )

    for number, change in enumerate(
        report["changes"],
        start=1
    ):

        print("\n" + "-" * 70)

        print(
            f"CHANGE {number}: "
            f"{change['change_type']}"
        )

        print("-" * 70)

        print(
            f"Clause Type: "
            f"{change['clause_type']}"
        )

        print(
            f"Similarity: "
            f"{change['similarity']}"
        )

        print(
            f"Risk Impact: "
            f"{change['risk_impact']}"
        )

        print(
            f"Severity: "
            f"{change['severity']}"
        )

        if change["old_clause"]:

            print("\nOLD VERSION:")

            print(
                change["old_clause"].get(
                    "text",
                    ""
                )
            )

        if change["new_clause"]:

            print("\nNEW VERSION:")

            print(
                change["new_clause"].get(
                    "text",
                    ""
                )
            )

        print(
            f"\nReason: "
            f"{change['reason']}"
        )

        print(
            f"Suggested Action: "
            f"{change['suggested_action']}"
        )


if __name__ == "__main__":

    # =========================================================
    # CONTRACT VERSION 1
    # =========================================================

    old_contract = [

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

    # =========================================================
    # CONTRACT VERSION 2
    # =========================================================

    new_contract = [

        {
            "section": "1",
            "clause_type": "Payment",
            "page": 1,
            "text": (
                "The Customer shall pay the Supplier "
                "within 60 days of receiving an invoice."
            )
        },

        {
            "section": "2",
            "clause_type": "Termination",
            "page": 2,
            "text": (
                "Either party may terminate this agreement "
                "by providing 7 days written notice."
            )
        },

        {
            "section": "3",
            "clause_type": "Confidentiality",
            "page": 3,
            "text": (
                "Confidential information shall remain "
                "protected for two years after termination."
            )
        }
    ]

    report = build_comparison_report(
        old_contract,
        new_contract
    )

    print_comparison_report(
        report
    )