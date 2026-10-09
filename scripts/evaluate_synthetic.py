"""Run a small, reproducible known-answer benchmark for the deterministic rules.

This is a smoke/evaluation aid for the hackathon demo, not a legal accuracy claim.
Run from repository root: python scripts/evaluate_synthetic.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.risk_service import analyze_clauses  # noqa: E402

benchmark = json.loads((ROOT / "evaluation" / "synthetic_benchmark.json").read_text(encoding="utf-8"))
labels = sorted({case["expected"] for case in benchmark["cases"]})
confusion = {label: {pred: 0 for pred in labels} for label in labels}
results = []
for case in benchmark["cases"]:
    clauses = case.get("clauses") or [case["clause"]]
    findings = analyze_clauses(clauses)
    if case["expected"] == "CONFLICTING":
        finding = next((item for item in findings if item["rule_id"] == case["rule_id"] and item["status"] == "CONFLICTING"), None)
    else:
        finding = next((item for item in findings if item["rule_id"] == case["rule_id"] and item["status"] != "CONFLICTING"), None)
    predicted = finding["status"] if finding else "NO_RESULT"
    results.append((case["id"], case["expected"], predicted, case["expected"] == predicted))
    if predicted in labels:
        confusion[case["expected"]][predicted] += 1

correct = sum(row[3] for row in results)
accuracy = correct / len(results) if results else 0.0
print(f"Benchmark: {benchmark['dataset_name']} v{benchmark['version']}")
print(f"Cases: {len(results)} | Exact status matches: {correct} | Accuracy: {accuracy:.1%}")
print("\nPer-case results:")
for case_id, expected, predicted, passed in results:
    print(f"  {'PASS' if passed else 'FAIL'} {case_id}: expected={expected}, predicted={predicted}")
print("\nPer-class precision / recall / F1 (labels with no predictions are reported as 0):")
for label in labels:
    tp = confusion[label][label]
    fp = sum(confusion[actual][label] for actual in labels if actual != label)
    fn = sum(confusion[label][pred] for pred in labels if pred != label)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    print(f"  {label}: precision={precision:.1%}, recall={recall:.1%}, f1={f1:.1%}")
print("\nLIMITATION: Small synthetic dataset, hand-authored expected labels, and narrow rules. Do not present this score as production or general legal accuracy.")
if correct != len(results):
    raise SystemExit(1)
