"""Basic tests for the agent_skills package."""

import importlib
import pkgutil


def test_all_modules_are_importable():
    import agent_skills

    for name in agent_skills.__all__:
        module = importlib.import_module(f"agent_skills.{name}")
        assert module is not None


def test_example_skill_metadata():
    from agent_skills import example_skill

    assert hasattr(example_skill, "SKILL_METADATA"), "example_skill must expose SKILL_METADATA"
    assert example_skill.SKILL_METADATA["name"] == "example"
