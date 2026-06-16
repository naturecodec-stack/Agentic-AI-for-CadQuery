import os
import json
import importlib.util

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")


def load_registry() -> list:
    registry_path = os.path.join(SKILLS_DIR, "skill_registry.json")
    with open(registry_path) as f:
        return json.load(f)


def _find_skill_entry(skill_name: str, registry: list) -> dict | None:
    for entry in registry:
        if entry["name"] == skill_name:
            return entry
    return None


def load_skill(skill_name: str):
    registry = load_registry()
    entry = _find_skill_entry(skill_name, registry)
    rel_path = entry["file"] if entry else f"{skill_name}.py"

    skill_path = os.path.join(SKILLS_DIR, rel_path)
    if not os.path.exists(skill_path):
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_registry_summary() -> str:
    registry = load_registry()
    return "\n".join(f"- {s['name']}: {s['description']}" for s in registry)
