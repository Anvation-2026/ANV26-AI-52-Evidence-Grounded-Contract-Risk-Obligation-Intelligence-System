import re


CLAUSE_TYPES = {
    "payment": "Payment",
    "termination": "Termination",
    "liability": "Liability",
    "indemnification": "Indemnification",
    "confidentiality": "Confidentiality",
    "intellectual property rights": "Intellectual Property",
    "intellectual property": "Intellectual Property",
    "data protection": "Data Protection",
    "data privacy": "Data Protection",
    "governing law": "Governing Law",
}


def detect_clause_type(heading):
    """
    Detect the contract clause type from a section heading.
    """

    heading_lower = heading.lower().strip()

    for keyword, clause_type in CLAUSE_TYPES.items():
        if keyword in heading_lower:
            return clause_type

    return "Other"


def is_page_header_or_footer(text):
    """
    Detect common page headers/footers that should not become
    part of contract clause evidence.
    """

    text_lower = text.strip().lower()

    if re.match(r"^sample contract - page \d+$", text_lower):
        return True

    return False


def is_section_heading(text):
    """
    Detect common numbered contract section headings.

    Examples:
        1. Payment
        2. Termination
        8.2 Termination
        10.3 Governing Law
    """

    text = text.strip()

    pattern = r"^\d+(?:\.\d+)*\.?\s+.+$"

    return bool(re.match(pattern, text))


def extract_section_number(heading):
    """
    Extract the section number from a heading.
    """

    match = re.match(
        r"^(\d+(?:\.\d+)*)\.?\s+",
        heading.strip()
    )

    if match:
        return match.group(1)

    return None


def segment_contract_pages(pages):
    """
    Convert page-level extracted text into structured clauses.

    Expected input:

    [
        {
            "page": 1,
            "text": "..."
        },
        ...
    ]

    Returns:

    [
        {
            "section": "1",
            "clause_type": "Payment",
            "page": 1,
            "text": "..."
        }
    ]
    """

    clauses = []

    current_section = None
    current_clause_type = "Other"
    current_page = None
    current_text = []

    def save_current_clause():
        if not current_text:
            return

        text = " ".join(current_text).strip()

        if not text:
            return

        clauses.append(
            {
                "section": current_section,
                "clause_type": current_clause_type,
                "page": current_page,
                "text": text,
            }
        )

    for page_data in pages:

        page_number = page_data["page"]
        page_text = page_data["text"]

        lines = page_text.splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                continue

            # Ignore known page headers/footers
            if is_page_header_or_footer(line):
                continue

            # Detect a new contract section
            if is_section_heading(line):

                save_current_clause()

                current_section = extract_section_number(line)
                current_clause_type = detect_clause_type(line)
                current_page = page_number
                current_text = []

                continue

            # Add text to the current clause
            if current_section is not None:
                current_text.append(line)

    # Save the final clause
    save_current_clause()

    return clauses