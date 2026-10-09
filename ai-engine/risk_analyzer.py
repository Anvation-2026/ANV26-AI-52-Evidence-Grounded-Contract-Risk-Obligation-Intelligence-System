import re


CLASSIFICATIONS = {
    "STANDARD": "STANDARD",
    "RISKY": "RISKY",
    "MISSING": "MISSING",
    "AMBIGUOUS": "AMBIGUOUS",
}


def extract_days(text):
    """
    Extract a number of days from contract text.

    Examples:
        30 days
        15 business days
        60 calendar days

    Returns:
        int | None
    """

    patterns = [
        r"(\d+)\s+business\s+days?",
        r"(\d+)\s+calendar\s+days?",
        r"(\d+)\s+days?"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return int(match.group(1))

    return None


def extract_years(text):
    """
    Extract a number of years from contract text.

    Examples:
        2 years
        5 years
        two years

    Returns:
        int | None
    """

    numeric_match = re.search(
        r"(\d+)\s+years?",
        text,
        re.IGNORECASE
    )

    if numeric_match:
        return int(numeric_match.group(1))

    word_numbers = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10
    }

    for word, number in word_numbers.items():
        if re.search(
            rf"\b{word}\s+years?\b",
            text,
            re.IGNORECASE
        ):
            return number

    return None


def result(
    classification,
    severity,
    expected_value,
    actual_value,
    evidence_found,
    evidence_text,
    explanation,
    suggested_action
):
    """
    Create a consistent risk-analysis result.
    """

    return {
        "classification": classification,
        "severity": severity,
        "expected_value": expected_value,
        "actual_value": actual_value,
        "evidence_found": evidence_found,
        "evidence_text": evidence_text,
        "explanation": explanation,
        "suggested_action": suggested_action
    }


# ============================================================
# PAYMENT
# ============================================================

def analyze_payment_clause(clause, rule):
    evidence = clause["text"]

    actual_days = extract_days(evidence)
    expected_days = 30

    if actual_days is None:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="No more than 30 days",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "A payment clause was found, but the payment "
                "period could not be determined."
            ),
            suggested_action=(
                "Specify a clear payment period of no more "
                "than 30 days from the invoice date."
            )
        )

    if actual_days > expected_days:
        return result(
            classification=CLASSIFICATIONS["RISKY"],
            severity=rule["severity"],
            expected_value="No more than 30 days",
            actual_value=f"{actual_days} days",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                f"The contract requires payment within "
                f"{actual_days} days, exceeding the playbook "
                f"maximum of {expected_days} days."
            ),
            suggested_action=(
                "Reduce the payment period to 30 days or less."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value="No more than 30 days",
        actual_value=f"{actual_days} days",
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            f"The contract specifies payment within "
            f"{actual_days} days, satisfying the maximum "
            f"payment period of 30 days."
        ),
        suggested_action=(
            "No change required."
        )
    )


# ============================================================
# TERMINATION
# ============================================================

def analyze_termination_clause(clause, rule):
    evidence = clause["text"]

    actual_days = extract_days(evidence)
    expected_days = 30

    if actual_days is None:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="At least 30 days",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The termination clause was found, but "
                "a clear notice period could not be determined."
            ),
            suggested_action=(
                "Specify an explicit termination notice period "
                "of at least 30 days."
            )
        )

    if actual_days < expected_days:
        return result(
            classification=CLASSIFICATIONS["RISKY"],
            severity=rule["severity"],
            expected_value="At least 30 days",
            actual_value=f"{actual_days} days",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                f"The contract provides only {actual_days} days "
                f"of termination notice, which is below the "
                f"playbook requirement of {expected_days} days."
            ),
            suggested_action=(
                "Increase the termination notice period "
                "to at least 30 days."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value="At least 30 days",
        actual_value=f"{actual_days} days",
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            f"The contract provides {actual_days} days of "
            f"termination notice, satisfying the minimum "
            f"requirement of {expected_days} days."
        ),
        suggested_action=(
            "No change required."
        )
    )


# ============================================================
# LIABILITY
# ============================================================

def analyze_liability_clause(clause, rule):
    evidence = clause["text"]

    cap_patterns = [
        r"liability\s+cap",
        r"cap\s+on\s+liability",
        r"maximum\s+liability",
        r"aggregate\s+liability",
        r"total\s+liability",
        r"limited\s+to",
        r"limitation\s+of\s+liability"
    ]

    cap_found = any(
        re.search(pattern, evidence, re.IGNORECASE)
        for pattern in cap_patterns
    )

    if not cap_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Clearly defined liability limitation or cap",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "A liability clause was found, but a clearly "
                "defined liability limitation or cap could "
                "not be identified."
            ),
            suggested_action=(
                "Define a clear limitation or maximum liability cap."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value="Clearly defined liability limitation or cap",
        actual_value="Liability limitation/cap identified",
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            "The clause contains language indicating a "
            "defined limitation or cap on liability."
        ),
        suggested_action=(
            "No immediate change required. Verify that the "
            "cap is commercially appropriate."
        )
    )


# ============================================================
# INDEMNIFICATION
# ============================================================

def analyze_indemnification_clause(clause, rule):
    evidence = clause["text"]

    indemnification_found = bool(
        re.search(
            r"\bindemnif(y|ies|ication|ied)?\b",
            evidence,
            re.IGNORECASE
        )
    )

    responsible_party_found = bool(
        re.search(
            r"\b(supplier|customer|client|company|party|parties)\b",
            evidence,
            re.IGNORECASE
        )
    )

    claims_found = bool(
        re.search(
            r"\b(claim|claims|loss|losses|damages|liabilities|expenses)\b",
            evidence,
            re.IGNORECASE
        )
    )

    if not indemnification_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Defined indemnification obligation",
            actual_value="No indemnification language identified",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The clause does not contain clear "
                "indemnification language."
            ),
            suggested_action=(
                "Add a clearly defined indemnification obligation."
            )
        )

    if not responsible_party_found or not claims_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value=(
                "Responsible party and covered claims"
            ),
            actual_value=(
                "Incomplete indemnification details"
            ),
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "Indemnification language exists, but the "
                "responsible party or covered claims are not "
                "clearly identifiable."
            ),
            suggested_action=(
                "Clearly identify the responsible party and "
                "the claims, losses, or damages covered."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value=(
            "Responsible party and covered claims"
        ),
        actual_value=(
            "Indemnification obligation identified"
        ),
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            "The clause contains an indemnification obligation "
            "with identifiable parties and covered claims."
        ),
        suggested_action=(
            "No immediate change required."
        )
    )


# ============================================================
# CONFIDENTIALITY
# ============================================================

def analyze_confidentiality_clause(clause, rule):
    evidence = clause["text"]

    protection_found = bool(
        re.search(
            r"\b(confidential|confidentiality|protect|disclose|disclosure)\b",
            evidence,
            re.IGNORECASE
        )
    )

    survival_found = bool(
        re.search(
            r"\b(survive|survival|termination)\b",
            evidence,
            re.IGNORECASE
        )
    )

    actual_years = extract_years(evidence)

    if not protection_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Confidential information must be protected",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The clause does not clearly establish "
                "confidentiality protection."
            ),
            suggested_action=(
                "Add clear confidentiality protections."
            )
        )

    if not survival_found or actual_years is None:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Confidentiality survives for at least 2 years",
            actual_value="Survival period unclear",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "Confidentiality protection exists, but the "
                "required post-termination survival period "
                "could not be established."
            ),
            suggested_action=(
                "Specify that confidentiality obligations "
                "survive termination for at least 2 years."
            )
        )

    if actual_years < 2:
        return result(
            classification=CLASSIFICATIONS["RISKY"],
            severity=rule["severity"],
            expected_value="At least 2 years",
            actual_value=f"{actual_years} years",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                f"The confidentiality obligation survives "
                f"for only {actual_years} years, below the "
                f"required minimum of 2 years."
            ),
            suggested_action=(
                "Increase the confidentiality survival period "
                "to at least 2 years."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value="At least 2 years",
        actual_value=f"{actual_years} years",
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            f"The confidentiality obligation survives for "
            f"{actual_years} years, satisfying the minimum "
            f"requirement of 2 years."
        ),
        suggested_action="No change required."
    )


# ============================================================
# INTELLECTUAL PROPERTY
# ============================================================

def analyze_ip_clause(clause, rule):
    evidence = clause["text"]

    ownership_found = bool(
        re.search(
            r"\b(own|ownership|owned|assign|assignment|title)\b",
            evidence,
            re.IGNORECASE
        )
    )

    rights_found = bool(
        re.search(
            r"\b(right|rights|license|licence|licensed|use|usage)\b",
            evidence,
            re.IGNORECASE
        )
    )

    if not ownership_found and not rights_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Defined IP ownership or permitted rights",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The clause does not clearly specify "
                "intellectual property ownership or usage rights."
            ),
            suggested_action=(
                "Clearly define ownership or permitted rights "
                "for intellectual property created under the agreement."
            )
        )

    if ownership_found or rights_found:
        return result(
            classification=CLASSIFICATIONS["STANDARD"],
            severity="LOW",
            expected_value="Defined IP ownership or permitted rights",
            actual_value="IP ownership/rights language identified",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The clause contains language indicating "
                "intellectual property ownership or permitted rights."
            ),
            suggested_action=(
                "No immediate change required. Verify that "
                "the ownership and usage rights are sufficiently specific."
            )
        )


# ============================================================
# DATA PROTECTION
# ============================================================

def analyze_data_protection_clause(clause, rule):
    evidence = clause["text"]

    data_found = bool(
        re.search(
            r"\b(data|personal data|personal information|sensitive data|privacy)\b",
            evidence,
            re.IGNORECASE
        )
    )

    responsibility_found = bool(
        re.search(
            r"\b(protect|protection|secure|security|safeguard|responsible|responsibility)\b",
            evidence,
            re.IGNORECASE
        )
    )

    if not data_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Data protection responsibilities",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The clause does not clearly address "
                "personal or sensitive data protection."
            ),
            suggested_action=(
                "Add clear data protection responsibilities."
            )
        )

    if not responsibility_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Data protection responsibilities",
            actual_value="Data mentioned but responsibility unclear",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "Data is referenced, but the responsibility "
                "for protecting it is not clearly defined."
            ),
            suggested_action=(
                "Clearly define responsibilities for protecting "
                "personal and sensitive data."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value="Data protection responsibilities",
        actual_value="Protection responsibility identified",
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            "The clause addresses data protection and "
            "identifies protection responsibilities."
        ),
        suggested_action="No immediate change required."
    )


# ============================================================
# GOVERNING LAW
# ============================================================

def analyze_governing_law_clause(clause, rule):
    evidence = clause["text"]

    law_found = bool(
        re.search(
            r"\b(governing law|laws of|law of|applicable law)\b",
            evidence,
            re.IGNORECASE
        )
    )

    jurisdiction_found = bool(
        re.search(
            r"\b(jurisdiction|courts of|court of|venue)\b",
            evidence,
            re.IGNORECASE
        )
    )

    if not law_found and not jurisdiction_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Governing law and jurisdiction",
            actual_value=None,
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The clause does not clearly specify "
                "governing law or jurisdiction."
            ),
            suggested_action=(
                "Specify the governing law and jurisdiction."
            )
        )

    if law_found and not jurisdiction_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Governing law and jurisdiction",
            actual_value="Governing law identified; jurisdiction unclear",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The governing law is identified, but "
                "the jurisdiction is not clearly specified."
            ),
            suggested_action=(
                "Add the applicable jurisdiction."
            )
        )

    if jurisdiction_found and not law_found:
        return result(
            classification=CLASSIFICATIONS["AMBIGUOUS"],
            severity=rule["severity"],
            expected_value="Governing law and jurisdiction",
            actual_value="Jurisdiction identified; governing law unclear",
            evidence_found=True,
            evidence_text=evidence,
            explanation=(
                "The jurisdiction is identified, but "
                "the governing law is not clearly specified."
            ),
            suggested_action=(
                "Add the applicable governing law."
            )
        )

    return result(
        classification=CLASSIFICATIONS["STANDARD"],
        severity="LOW",
        expected_value="Governing law and jurisdiction",
        actual_value="Both identified",
        evidence_found=True,
        evidence_text=evidence,
        explanation=(
            "The clause specifies both governing law "
            "and jurisdiction."
        ),
        suggested_action="No change required."
    )


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_clause(clause, rule):
    """
    Analyze a contract clause against a matched playbook rule.

    Deterministic analysis is used wherever the requirement
    can be reliably checked using Python rules.
    """

    category = rule["category"].upper()

    analyzers = {
        "PAYMENT": analyze_payment_clause,
        "TERMINATION": analyze_termination_clause,
        "LIABILITY": analyze_liability_clause,
        "INDEMNIFICATION": analyze_indemnification_clause,
        "CONFIDENTIALITY": analyze_confidentiality_clause,
        "INTELLECTUAL_PROPERTY": analyze_ip_clause,
        "DATA_PROTECTION": analyze_data_protection_clause,
        "GOVERNING_LAW": analyze_governing_law_clause,
    }

    analyzer = analyzers.get(category)

    if analyzer:
        return analyzer(clause, rule)

    return result(
        classification=CLASSIFICATIONS["AMBIGUOUS"],
        severity=rule["severity"],
        expected_value=rule["requirement"],
        actual_value=None,
        evidence_found=True,
        evidence_text=clause["text"],
        explanation=(
            f"Deterministic analysis is not implemented "
            f"for category {category}."
        ),
        suggested_action=(
            "Review this clause against the playbook requirement."
        )
    )


if __name__ == "__main__":

    test_cases = [
        {
            "name": "PAYMENT - STANDARD",
            "rule": {
                "rule_id": "PAY-001",
                "category": "PAYMENT",
                "requirement": (
                    "Payment terms must specify a clear payment "
                    "period of no more than 30 days from invoice date."
                ),
                "severity": "MEDIUM"
            },
            "clause": {
                "section": "1",
                "clause_type": "Payment",
                "page": 1,
                "text": (
                    "The Customer shall pay the Supplier "
                    "within 30 days of receiving an invoice."
                )
            }
        },
        {
            "name": "PAYMENT - RISKY",
            "rule": {
                "rule_id": "PAY-001",
                "category": "PAYMENT",
                "requirement": (
                    "Payment terms must specify a clear payment "
                    "period of no more than 30 days from invoice date."
                ),
                "severity": "MEDIUM"
            },
            "clause": {
                "section": "1",
                "clause_type": "Payment",
                "page": 1,
                "text": (
                    "The Customer shall pay the Supplier "
                    "within 60 days of receiving an invoice."
                )
            }
        },
        {
            "name": "TERMINATION - STANDARD",
            "rule": {
                "rule_id": "TERM-001",
                "category": "TERMINATION",
                "requirement": (
                    "Termination for convenience must provide "
                    "at least 30 days written notice."
                ),
                "severity": "HIGH"
            },
            "clause": {
                "section": "2",
                "clause_type": "Termination",
                "page": 2,
                "text": (
                    "Either party may terminate this agreement "
                    "by providing 30 days written notice."
                )
            }
        },
        {
            "name": "TERMINATION - RISKY",
            "rule": {
                "rule_id": "TERM-001",
                "category": "TERMINATION",
                "requirement": (
                    "Termination for convenience must provide "
                    "at least 30 days written notice."
                ),
                "severity": "HIGH"
            },
            "clause": {
                "section": "2",
                "clause_type": "Termination",
                "page": 2,
                "text": (
                    "Either party may terminate this agreement "
                    "by providing 7 days written notice."
                )
            }
        },
        {
            "name": "LIABILITY - STANDARD",
            "rule": {
                "rule_id": "LIAB-001",
                "category": "LIABILITY",
                "requirement": (
                    "Liability should include a clearly defined "
                    "limitation or liability cap."
                ),
                "severity": "HIGH"
            },
            "clause": {
                "section": "3",
                "clause_type": "Liability",
                "page": 3,
                "text": (
                    "The Supplier's aggregate liability under "
                    "this agreement shall be limited to the total "
                    "fees paid during the preceding twelve months."
                )
            }
        },
        {
            "name": "CONFIDENTIALITY - RISKY",
            "rule": {
                "rule_id": "CONF-001",
                "category": "CONFIDENTIALITY",
                "requirement": (
                    "Confidential information must be protected "
                    "and the confidentiality obligation should "
                    "survive termination for at least 2 years."
                ),
                "severity": "MEDIUM"
            },
            "clause": {
                "section": "5",
                "clause_type": "Confidentiality",
                "page": 5,
                "text": (
                    "The parties shall protect confidential "
                    "information. These obligations shall survive "
                    "termination for 1 year."
                )
            }
        },
        {
            "name": "GOVERNING LAW - STANDARD",
            "rule": {
                "rule_id": "LAW-001",
                "category": "GOVERNING_LAW",
                "requirement": (
                    "The contract must specify a governing law "
                    "and jurisdiction."
                ),
                "severity": "MEDIUM"
            },
            "clause": {
                "section": "8",
                "clause_type": "Governing Law",
                "page": 8,
                "text": (
                    "This agreement shall be governed by the laws "
                    "of Karnataka. The courts of Bengaluru shall "
                    "have exclusive jurisdiction."
                )
            }
        }
    ]

    for test_case in test_cases:

        print("\n" + "=" * 60)
        print(f"TEST: {test_case['name']}")
        print("=" * 60)

        analysis = analyze_clause(
            test_case["clause"],
            test_case["rule"]
        )

        print(
            f"Classification: "
            f"{analysis['classification']}"
        )

        print(
            f"Severity: "
            f"{analysis['severity']}"
        )

        print(
            f"Expected: "
            f"{analysis['expected_value']}"
        )

        print(
            f"Actual: "
            f"{analysis['actual_value']}"
        )

        print(
            f"Evidence Found: "
            f"{analysis['evidence_found']}"
        )

        print(
            f"Evidence: "
            f"{analysis['evidence_text']}"
        )

        print(
            f"Explanation: "
            f"{analysis['explanation']}"
        )

        print(
            f"Action: "
            f"{analysis['suggested_action']}"
        )