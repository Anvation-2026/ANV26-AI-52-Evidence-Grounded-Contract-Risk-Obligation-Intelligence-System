from pathlib import Path

from pdf_extractor import extract_pdf_pages
from docx_extractor import extract_docx_paragraphs
from clause_segmenter import segment_contract_pages
from semantic_matcher import SemanticMatcher
from risk_analyzer import analyze_clause

from evidence_trace import (
    build_evidence_finding,
    build_evidence_report
)

from vector_store import VectorStore
from missing_clause_detector import detect_missing_clauses

from key_point_extractor import (
    build_key_point_report
)

from risk_summary import (
    build_risk_summary
)

from supporting_document_suggester import (
    build_supporting_document_report
)


class ContractPipeline:

    def __init__(self):

        print("Initializing Contract AI Pipeline...")

        # -----------------------------------------------------
        # Semantic matcher
        # -----------------------------------------------------

        self.matcher = SemanticMatcher()

        # -----------------------------------------------------
        # Vector database
        # -----------------------------------------------------

        self.vector_store = VectorStore()

        print("Pipeline initialized successfully.")

    # =========================================================
    # CONTRACT EXTRACTION
    # =========================================================

    def extract_contract(self, file_path):

        path = Path(file_path)

        if not path.exists():

            raise FileNotFoundError(
                f"Contract not found: {file_path}"
            )

        # -----------------------------------------------------
        # PDF
        # -----------------------------------------------------

        if path.suffix.lower() == ".pdf":

            return extract_pdf_pages(
                str(path)
            )

        # -----------------------------------------------------
        # DOCX
        # -----------------------------------------------------

        elif path.suffix.lower() == ".docx":

            paragraphs = extract_docx_paragraphs(
                str(path)
            )

            # Normalize DOCX output to the same
            # structure used by PDF extraction.

            return [
                {
                    "page": item["paragraph"],
                    "text": item["text"]
                }
                for item in paragraphs
            ]

        # -----------------------------------------------------
        # Unsupported format
        # -----------------------------------------------------

        else:

            raise ValueError(
                "Only PDF and DOCX files are supported."
            )

    # =========================================================
    # MAIN ANALYSIS PIPELINE
    # =========================================================

    def analyze(self, file_path):

        print("\n" + "=" * 70)
        print("CONTRACT AI ANALYSIS PIPELINE")
        print("=" * 70)

        # =====================================================
        # STEP 1: EXTRACTION
        # =====================================================

        print("\n[1/9] Extracting contract...")

        pages = self.extract_contract(
            file_path
        )

        print(
            f"Extracted {len(pages)} "
            f"pages/paragraphs."
        )

        # =====================================================
        # STEP 2: CLAUSE SEGMENTATION
        # =====================================================

        print("\n[2/9] Segmenting clauses...")

        clauses = segment_contract_pages(
            pages
        )

        print(
            f"Detected {len(clauses)} clauses."
        )

        # =====================================================
        # STEP 3: CHROMADB STORAGE
        # =====================================================

        print(
            "\n[3/9] Storing clauses in ChromaDB..."
        )

        self.vector_store.add_clauses(
            clauses
        )

        # =====================================================
        # STEP 4: SEMANTIC PLAYBOOK MATCHING
        # =====================================================

        print(
            "\n[4/9] Matching clauses with playbook..."
        )

        findings = []

        for clause in clauses:

            matches = self.matcher.match_clause(
                clause,
                top_k=3
            )

            # Only process rules that passed
            # semantic + category matching.

            matched_rules = [
                match
                for match in matches
                if match.get("matched")
            ]

            for rule in matched_rules:

                print(
                    f"  Section "
                    f"{clause.get('section')} "
                    f"-> "
                    f"{rule.get('rule_id')}"
                )

                # -------------------------------------------------
                # RISK ANALYSIS
                # -------------------------------------------------

                risk_result = analyze_clause(
                    clause,
                    rule
                )

                # -------------------------------------------------
                # EVIDENCE TRACEABILITY
                # -------------------------------------------------

                finding = build_evidence_finding(
                    clause=clause,
                    rule=rule,
                    risk_result=risk_result
                )

                findings.append(
                    finding
                )

        # =====================================================
        # STEP 5: MISSING CLAUSE DETECTION
        # =====================================================

        print(
            "\n[5/9] Detecting missing clauses..."
        )

        missing_clauses = detect_missing_clauses(
            clauses
        )

        for missing in missing_clauses:

            print(
                f"  Missing -> "
                f"{missing.get('rule_id')}"
            )

        # Add missing clauses to findings.

        findings.extend(
            missing_clauses
        )

        # =====================================================
        # STEP 6: AI KEY POINT EXTRACTION
        # =====================================================

        print(
            "\n[6/9] Extracting AI key points..."
        )

        key_point_report = build_key_point_report(
            clauses=clauses,
            findings=findings
        )

        key_points = key_point_report.get(
            "key_points",
            []
        )

        total_key_points = len(
            key_points
        )

        print(
            f"Generated "
            f"{total_key_points} "
            f"key points."
        )

        # =====================================================
        # STEP 7: RISK SUMMARY
        # =====================================================

        print(
            "\n[7/9] Generating risk summary..."
        )

        risk_summary = build_risk_summary(
            findings
        )

        # Safely read values from risk summary.

        high_risk = risk_summary.get(
            "high_risk",
            0
        )

        medium_risk = risk_summary.get(
            "medium_risk",
            0
        )

        low_risk = risk_summary.get(
            "low_risk",
            0
        )

        print(
            f"High Risk       : "
            f"{high_risk}"
        )

        print(
            f"Medium Risk     : "
            f"{medium_risk}"
        )

        print(
            f"Low Risk        : "
            f"{low_risk}"
        )

        # =====================================================
        # STEP 8: SUPPORTING DOCUMENT SUGGESTIONS
        # =====================================================

        print(
            "\n[8/9] Generating supporting "
            "document suggestions..."
        )

        supporting_document_report = (
            build_supporting_document_report(
                findings
            )
        )

        supporting_suggestions = (
            supporting_document_report.get(
                "suggestions",
                []
            )
        )

        # IMPORTANT:
        # Calculate this directly so the pipeline does
        # not fail even if the helper module changes.

        total_suggestions = len(
            supporting_suggestions
        )

        print(
            f"Generated "
            f"{total_suggestions} "
            f"supporting document "
            f"suggestion categories."
        )

        # =====================================================
        # STEP 9: FINAL REPORT
        # =====================================================

        print(
            "\n[9/9] Building final report..."
        )

        report = build_evidence_report(
            findings
        )

        # -----------------------------------------------------
        # Basic contract information
        # -----------------------------------------------------

        report["contract"] = str(
            file_path
        )

        report["total_clauses"] = len(
            clauses
        )

        # -----------------------------------------------------
        # Key points
        # -----------------------------------------------------

        report["key_points"] = (
            key_points
        )

        report["total_key_points"] = (
            total_key_points
        )

        # -----------------------------------------------------
        # Risk summary
        # -----------------------------------------------------

        report["risk_summary"] = (
            risk_summary
        )

        # -----------------------------------------------------
        # Supporting document suggestions
        # -----------------------------------------------------

        report[
            "supporting_document_suggestions"
        ] = supporting_suggestions

        report[
            "total_supporting_document_suggestions"
        ] = total_suggestions

        return report


# =============================================================
# REPORT PRINTING
# =============================================================

def print_report(report):

    print("\n")

    print("=" * 70)
    print("FINAL CONTRACT RISK REPORT")
    print("=" * 70)

    # =========================================================
    # CONTRACT INFORMATION
    # =========================================================

    print(
        f"\nContract: "
        f"{report.get('contract')}"
    )

    print(
        f"Total clauses: "
        f"{report.get('total_clauses', 0)}"
    )

    print(
        f"Total findings: "
        f"{report.get('total_findings', 0)}"
    )

    # =========================================================
    # RISK SUMMARY
    # =========================================================

    risk_summary = report.get(
        "risk_summary",
        {}
    )

    print("\n")
    print("=" * 70)
    print("RISK SUMMARY")
    print("=" * 70)

    print(
        f"High Risk       : "
        f"{risk_summary.get('high_risk', 0)}"
    )

    print(
        f"Medium Risk     : "
        f"{risk_summary.get('medium_risk', 0)}"
    )

    print(
        f"Low Risk        : "
        f"{risk_summary.get('low_risk', 0)}"
    )

    print("\nClassification")
    print("-" * 70)

    print(
        f"Standard        : "
        f"{risk_summary.get('standard', 0)}"
    )

    print(
        f"Risky           : "
        f"{risk_summary.get('risky', 0)}"
    )

    print(
        f"Ambiguous       : "
        f"{risk_summary.get('ambiguous', 0)}"
    )

    print(
        f"Missing         : "
        f"{risk_summary.get('missing', 0)}"
    )

    # =========================================================
    # KEY POINTS
    # =========================================================

    print("\n")
    print("=" * 70)
    print("CONTRACT KEY POINTS")
    print("=" * 70)

    key_points = report.get(
        "key_points",
        []
    )

    if key_points:

        for number, point in enumerate(
            key_points,
            start=1
        ):

            print(
                f"{number}. {point}"
            )

    else:

        print(
            "No key points generated."
        )

    # =========================================================
    # SUPPORTING DOCUMENT SUGGESTIONS
    # =========================================================

    print("\n")
    print("=" * 70)
    print("AI SUPPORTING DOCUMENT SUGGESTIONS")
    print("=" * 70)

    suggestions = report.get(
        "supporting_document_suggestions",
        []
    )

    print(
        f"\nTotal suggestion categories: "
        f"{len(suggestions)}"
    )

    if not suggestions:

        print(
            "\nNo supporting documents required."
        )

    else:

        for suggestion in suggestions:

            print(
                "\n" + "-" * 70
            )

            print(
                f"Rule: "
                f"{suggestion.get('rule_id')}"
            )

            print(
                f"Category: "
                f"{suggestion.get('category')}"
            )

            print(
                f"Classification: "
                f"{suggestion.get('classification')}"
            )

            print(
                f"Severity: "
                f"{suggestion.get('severity')}"
            )

            print(
                "Reason: "
                f"{suggestion.get('reason', '')}"
            )

            print(
                "Suggested Documents:"
            )

            for document in suggestion.get(
                "suggested_documents",
                []
            ):

                print(
                    f"  - {document}"
                )

    # =========================================================
    # FINDINGS
    # =========================================================

    findings = report.get(
        "findings",
        []
    )

    if not findings:

        print(
            "\nNo matched findings detected."
        )

        return

    print("\n")
    print("=" * 70)
    print("DETAILED FINDINGS")
    print("=" * 70)

    for number, finding in enumerate(
        findings,
        start=1
    ):

        print(
            "\n" + "-" * 70
        )

        print(
            f"FINDING {number}"
        )

        print(
            "-" * 70
        )

        print(
            f"Section: "
            f"{finding.get('section')}"
        )

        print(
            f"Clause Type: "
            f"{finding.get('clause_type')}"
        )

        print(
            f"Page: "
            f"{finding.get('page')}"
        )

        print(
            f"Rule: "
            f"{finding.get('rule_id')}"
        )

        print(
            f"Category: "
            f"{finding.get('category')}"
        )

        print(
            f"Classification: "
            f"{finding.get('classification')}"
        )

        print(
            f"Severity: "
            f"{finding.get('severity')}"
        )

        print(
            f"Expected: "
            f"{finding.get('expected_value')}"
        )

        print(
            f"Actual: "
            f"{finding.get('actual_value')}"
        )

        print(
            f"Evidence Found: "
            f"{finding.get('evidence_found')}"
        )

        print(
            f"Evidence: "
            f"{finding.get('evidence_text')}"
        )

        print(
            f"Explanation: "
            f"{finding.get('explanation')}"
        )

        print(
            f"Suggested Action: "
            f"{finding.get('suggested_action')}"
        )


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    contract_path = (
        "contracts/test_contract.pdf"
    )

    pipeline = ContractPipeline()

    report = pipeline.analyze(
        contract_path
    )

    print_report(
        report
    )