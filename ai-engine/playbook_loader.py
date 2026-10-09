import json
from pathlib import Path


def load_playbook():
    """
    Load the shared project playbook.

    Supports both:
    1. A JSON list of rules
    2. An object containing a 'rules' list
    """

    project_root = Path(__file__).resolve().parents[1]

    playbook_path = project_root / "playbook" / "rules.json"

    if not playbook_path.exists():
        raise FileNotFoundError(
            f"Playbook not found: {playbook_path}"
        )

    with open(playbook_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Existing project format:
    # {
    #     "rules": [...]
    # }
    if isinstance(data, dict) and isinstance(data.get("rules"), list):
        return data["rules"]

    # AI-engine format:
    # [...]
    if isinstance(data, list):
        return data

    raise ValueError(
        "Playbook must contain a JSON list of rules "
        "or an object containing a 'rules' list."
    )