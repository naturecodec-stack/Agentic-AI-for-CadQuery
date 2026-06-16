"""
Skill library tools — identical in purpose to v3 but importable standalone.
"""

import json
import os
import sys

from langchain_core.tools import tool

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cq_agent_v2", "skills")


def _load_registry() -> list:
    path = os.path.join(SKILLS_DIR, "skill_registry.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_skill(skill_name: str):
    import importlib.util
    registry = _load_registry()
    entry = next((e for e in registry if e["name"] == skill_name), None)
    rel = entry["file"] if entry else f"{skill_name}.py"
    skill_path = os.path.join(SKILLS_DIR, rel)
    if not os.path.exists(skill_path):
        raise FileNotFoundError(skill_path)
    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------

@tool
def plan_shape(features: str) -> str:
    """Record a structured feature plan BEFORE writing any code.

    Call this FIRST after understanding the request.
    List every geometric feature the final shape must have.
    This plan is your contract — your code MUST implement ALL items.

    Args:
        features: newline-separated list of required features.
    """
    lines = [l.strip() for l in features.strip().splitlines() if l.strip()]
    if not lines:
        return "ERROR: features list is empty."
    plan = "\n".join(f"  [x] {l}" for l in lines)
    return (
        f"PLAN CONFIRMED ({len(lines)} features):\n{plan}\n\n"
        "Your code MUST implement every item above. "
        "Do NOT simplify or omit any feature to make the code pass."
    )


@tool
def search_skills(query: str) -> str:
    """Search the skill library by keyword.

    Args:
        query: keyword e.g. "gear", "bracket", "thread", "pocket"
    """
    registry = _load_registry()
    q = query.lower()
    matches = [
        s for s in registry
        if q in s["name"].lower()
        or q in s["description"].lower()
        or any(q in kw.lower() for kw in s.get("keywords", []))
    ]
    if not matches:
        return f"No skills found for '{query}'. Use list_skills() to see all."
    return "\n".join(f"- {s['name']}: {s['description']}" for s in matches)


@tool
def list_skills() -> str:
    """List all 27 available CadQuery skill templates."""
    registry = _load_registry()
    return "\n".join(f"- {s['name']}: {s['description']}" for s in registry)


@tool
def use_skill(skill_name: str, params_json: str) -> str:
    """Render a skill template with given parameters.

    Args:
        skill_name:  exact name from list_skills() or search_skills()
        params_json: JSON string of params, e.g. '{"width": 50, "height": 30}'
                     Use '{}' for all defaults.
    """
    try:
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        skill = _load_skill(skill_name)
        code = skill.render(params)
        return f"Skill '{skill_name}' rendered. Code:\n\n{code}"
    except json.JSONDecodeError as e:
        return f"ERROR: params_json is not valid JSON — {e}"
    except FileNotFoundError:
        return f"ERROR: skill '{skill_name}' not found. Use list_skills() to see valid names."
    except Exception as e:
        return f"ERROR rendering skill '{skill_name}': {e}"
