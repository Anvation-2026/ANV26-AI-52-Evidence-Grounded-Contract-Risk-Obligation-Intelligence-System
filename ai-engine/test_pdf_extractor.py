from pathlib import Path
from pdf_extractor import extract_pdf_pages

def test_extract_pdf_pages_fixture():
    path = Path(__file__).resolve().parents[1] / "contracts" / "test_contract.pdf"
    pages = extract_pdf_pages(str(path))
    assert pages and pages[0]["page"] == 1
    assert "PAYMENT" in pages[0]["text"].upper()
