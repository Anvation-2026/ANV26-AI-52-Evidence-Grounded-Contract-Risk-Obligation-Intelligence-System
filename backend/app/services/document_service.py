from pathlib import Path
import re

import fitz
from docx import Document


def parse_clause_heading(text: str):
    """
    Detect headings such as:
    1. PAYMENT
    2. TERMINATION
    10. GENERAL
    """

    pattern = r"^(\d+(?:\.\d+)*)\.\s+(.+)$"

    match = re.match(pattern, text.strip())

    if match:
        return match.group(1), match.group(2).strip()

    return None, None


def extract_docx_clauses(file_path: str):
    """
    Groups a numbered heading with the paragraph(s) that follow it.

    Example:

    1. PAYMENT
    The Buyer shall make payment within 60 days...

    becomes:

    {
        clause_number: "1",
        clause_title: "PAYMENT",
        clause_text: "The Buyer shall make payment within 60 days..."
    }
    """

    document = Document(file_path)

    clauses = []

    current_number = None
    current_title = None
    current_text = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if not text:
            continue

        clause_number, clause_title = parse_clause_heading(text)

        # New numbered clause detected
        if clause_number:
            # Save previous clause
            if current_number is not None:
                clauses.append({
                    "clause_number": current_number,
                    "clause_title": current_title,
                    "clause_text": " ".join(current_text).strip(),
                    "page_number": None
                })

            current_number = clause_number
            current_title = clause_title
            current_text = []

        else:
            # If we have already found a numbered clause,
            # attach this paragraph to that clause.
            if current_number is not None:
                current_text.append(text)

            else:
                # Content before the first numbered clause.
                clauses.append({
                    "clause_number": None,
                    "clause_title": None,
                    "clause_text": text,
                    "page_number": None
                })

    # Save final clause
    if current_number is not None:
        clauses.append({
            "clause_number": current_number,
            "clause_title": current_title,
            "clause_text": " ".join(current_text).strip(),
            "page_number": None
        })

    return clauses


def extract_pdf_clauses(file_path: str):
    """
    Extract numbered clauses from PDF documents.

    The PDF extractor groups text following a numbered heading
    into the corresponding clause.
    """

    clauses = []

    document = fitz.open(file_path)

    current_number = None
    current_title = None
    current_text = []
    current_page = None

    heading_pattern = r"^(\d+(?:\.\d+)*)\.\s+(.+)$"

    for page_index, page in enumerate(document):

        text = page.get_text("text")

        if not text.strip():
            continue

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines:

            match = re.match(heading_pattern, line)

            if match:

                # Save previous clause
                if current_number is not None:
                    clauses.append({
                        "clause_number": current_number,
                        "clause_title": current_title,
                        "clause_text": " ".join(current_text).strip(),
                        "page_number": current_page
                    })

                current_number = match.group(1)
                current_title = match.group(2).strip()
                current_text = []
                current_page = page_index + 1

            else:

                if current_number is not None:
                    current_text.append(line)

                else:
                    clauses.append({
                        "clause_number": None,
                        "clause_title": None,
                        "clause_text": line,
                        "page_number": page_index + 1
                    })

    # Save final clause
    if current_number is not None:
        clauses.append({
            "clause_number": current_number,
            "clause_title": current_title,
            "clause_text": " ".join(current_text).strip(),
            "page_number": current_page
        })

    document.close()

    return clauses


def extract_clauses(file_path: str):

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_clauses(file_path)

    if extension == ".docx":
        return extract_docx_clauses(file_path)

    raise ValueError("Unsupported file type")