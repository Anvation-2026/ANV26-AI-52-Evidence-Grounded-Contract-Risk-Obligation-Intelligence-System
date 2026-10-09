from pathlib import Path
from docx import Document


def extract_docx_paragraphs(file_path):
    """
    Extract non-empty paragraphs from a DOCX contract.

    Returns:
        list[dict]: Each item contains paragraph number and text.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    if path.suffix.lower() != ".docx":
        raise ValueError("The input file must be a .docx file.")

    document = Document(path)

    paragraphs = []

    for index, paragraph in enumerate(document.paragraphs, start=1):
        text = paragraph.text.strip()

        if text:
            paragraphs.append(
                {
                    "paragraph": index,
                    "text": text
                }
            )

    return paragraphs


if __name__ == "__main__":
    print("DOCX extractor module loaded successfully.")