from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = PROJECT_ROOT / "ai-engine"
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

_pipeline = None

def get_ai_pipeline():
    """Load the optional embedding/vector pipeline lazily.

    The application remains usable with deterministic playbook analysis if
    heavyweight model dependencies are not installed or the model is offline.
    """
    global _pipeline
    if _pipeline is None:
        from pipeline import ContractPipeline
        _pipeline = ContractPipeline()
    return _pipeline

def analyze_contract_with_ai(file_path: str):
    return get_ai_pipeline().analyze(file_path)
