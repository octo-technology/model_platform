"""
Demo projects templates for quick filling during demonstrations.
Contains realistic AI project examples for French companies and public organizations.
Private company names are anonymized, public organizations remain as-is.
"""

import json
import random
from pathlib import Path


def _load_demo_projects() -> list[dict]:
    json_path = Path(__file__).parent / "demo_projects.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


DEMO_PROJECTS = _load_demo_projects()


def get_random_demo_project() -> dict:
    return random.choice(DEMO_PROJECTS).copy()
