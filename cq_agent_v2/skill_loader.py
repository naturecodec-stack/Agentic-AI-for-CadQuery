import os
import json
import importlib.util


SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")


def load_registry() -> list:
    registry_path = os.path.join(SKILLS_DIR, "skill_registry.json")
    with open(registry_path) as f:
        return json.load(f)


def _find_skill_entry(skill_name: str, registry: list) -> dict:
    for entry in registry:
        if entry["name"] == skill_name:
            return entry
    return None


def load_skill(skill_name: str):
    """Load a skill module by name (supports subfolder paths) and return it."""
    registry = load_registry()
    entry = _find_skill_entry(skill_name, registry)

    if entry:
        rel_path = entry["file"]  # e.g. "sketch_primitives/point.py" or "box.py"
    else:
        rel_path = f"{skill_name}.py"  # fallback: flat file

    skill_path = os.path.join(SKILLS_DIR, rel_path)
    if not os.path.exists(skill_path):
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    spec   = importlib.util.spec_from_file_location(skill_name, skill_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_registry_summary() -> str:
    """Return a text summary of all skills for use in prompts."""
    registry = load_registry()
    lines = []
    for skill in registry:
        lines.append(f"- {skill['name']}: {skill['description']}")
    return "\n".join(lines)