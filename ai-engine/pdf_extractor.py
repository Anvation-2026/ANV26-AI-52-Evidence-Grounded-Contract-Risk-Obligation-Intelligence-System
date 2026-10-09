from pathlib import Path
import pymupdf


def extract_pdf_pages(pdf_path: str) -> list[dict]:
    """
    Extract text from a PDF while preserving page numbers.

    Returns:
        [
            {
                "page": 1,
                "text": "..."
            },
            ...
        ]
    """

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_file}")

    if pdf_file.suffix.lower() != ".pdf":
        raise ValueError("The provided file must be a PDF.")

    pages = []

    document = pymupdf.open(pdf_file)

    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )
    finally:
        document.close()

    return pages


if __name__ == "__main__":
    print("PDF extractor module loaded successfully.")