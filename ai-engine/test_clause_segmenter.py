from pathlib import Path
from pdf_extractor import extract_pdf_pages
from clause_segmenter import segment_contract_pages

def test_segment_pdf_fixture():
    path = Path(__file__).resolve().parents[1] / "contracts" / "test_contract.pdf"
    clauses = segment_contract_pages(extract_pdf_pages(str(path)))
    assert clauses
    assert any(item.get("clause_type") == "Payment" for item in clauses)
