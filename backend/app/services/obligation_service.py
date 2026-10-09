import re


ACTION_PATTERNS = [
    r"\bdeliver\b",
    r"\bprovide\b",
    r"\bsubmit\b",
    r"\bpay(?:able|ment|ments)?\b",
    r"\bmaintain\b",
    r"\bnotify\b",
    r"\binform\b",
    r"\bdisclose\b",
    r"\bprotect\b",
    r"\bcomply\b",
    r"\bindemnify\b",
    r"\breturn\b",
    r"\bcomplete\b",
    r"\bperform\b",
    r"\bexecute\b",
    r"\bkeep\b",
    r"\bensure\b",
    r"\bremit\b",
    r"\breport\b",
    r"\bcooperate\b",
]

OBLIGATION_LANGUAGE = re.compile(
    r"\b(?:shall|must|is required to|are required to|"
    r"will|agrees to|undertakes to|is responsible for|"
    r"are responsible for|is payable|are payable|"
    r"must be|shall be)\b",
    re.IGNORECASE,
)

PARTY_PATTERN = re.compile(
    r"\b(?:the\s+)?(Buyer|Supplier|Customer|Vendor|Company|"
    r"Provider|Contractor|Client|Seller|Service Provider|"
    r"Recipient|Licensee|Licensor|Employer|Employee|"
    r"Disclosing Party|Receiving Party|each party|both parties|"
    r"the parties)\b",
    re.IGNORECASE,
)

DEADLINE_PATTERN = re.compile(
    r"\b(?:within|no later than|at least|not less than|"
    r"before|by)\s+\d+\s+"
    r"(?:business\s+days?|calendar\s+days?|days?|hours?|"
    r"weeks?|months?|years?)\b",
    re.IGNORECASE,
)


def extract_actor(text: str):
    match = PARTY_PATTERN.search(text)
    if not match:
        return "Contracting party (unspecified)"
    return match.group(0).strip()


def extract_deadline(text: str):
    match = DEADLINE_PATTERN.search(text)
    return match.group(0).strip() if match else None


def extract_trigger(text: str):
    match = re.search(
        r"\b(?:upon|after|following|on receipt of|"
        r"from receipt of)\s+([^.;]+)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def extract_action(text: str):
    match = OBLIGATION_LANGUAGE.search(text)
    if match:
        action = text[match.end():].strip(" :,-")
        action = re.split(
            r"\b(?:within|no later than|before|by)\s+\d+\s+"
            r"(?:business\s+days?|calendar\s+days?|days?|hours?|"
            r"weeks?|months?|years?)\b",
            action,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" .;,:")
        return action or text.strip()

    # Recognize direct payment clauses such as:
    # "Invoices are payable within 75 days."
    match = re.search(r"\b(?:is|are)\s+payable\b", text, re.IGNORECASE)
    if match:
        return text[match.start():].strip(" .;,:")
    return None


def is_actionable_obligation(text: str):
    lower = text.lower()

    excluded = [
        "shall not exceed",
        "shall remain the property",
        "shall be governed",
        "shall have jurisdiction",
        "constitutes the entire agreement",
    ]
    if any(pattern in lower for pattern in excluded):
        return False

    has_action = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in ACTION_PATTERNS
    )
    has_obligation_language = bool(OBLIGATION_LANGUAGE.search(text))
    has_payable_language = bool(
        re.search(r"\b(?:is|are)\s+payable\b", text, re.IGNORECASE)
    )
    return has_action and (has_obligation_language or has_payable_language)


def extract_obligation_from_clause(clause):
    text = (clause.get("clause_text") or "").strip()
    if not text or not is_actionable_obligation(text):
        return None

    action = extract_action(text)
    if not action:
        return None

    return {
        "clause_id": clause.get("id"),
        "clause_number": clause.get("clause_number"),
        "clause_title": clause.get("clause_title"),
        "actor": extract_actor(text),
        "action": action,
        "deadline": extract_deadline(text),
        "trigger_condition": extract_trigger(text),
        "evidence": text,
    }


def extract_obligations(clauses):
    obligations = []
    seen = set()

    for clause in clauses:
        obligation = extract_obligation_from_clause(clause)
        if not obligation:
            continue

        # Avoid duplicate records while preserving clause-level evidence.
        key = (
            obligation["clause_id"],
            obligation["evidence"].casefold(),
        )
        if key not in seen:
            seen.add(key)
            obligations.append(obligation)

    return obligations