from pathlib import Path
from docx_extractor import extract_docx_paragraphs

def test_extract_docx_paragraphs_fixture():
    path = Path(__file__).resolve().parents[1] / "contracts" / "test_contract.docx"
    paragraphs = extract_docx_paragraphs(str(path))
    assert paragraphs
    assert any("PAYMENT" in item["text"].upper() for item in paragraphs)
