"""
Real LangGraph tools for the CadQuery AI agent.

Tools:
  plan_shape        — commit to a feature list before writing code
  execute_cadquery  — run code headlessly, return SUCCESS or error
  list_skills       — show the skill registry
  search_skills     — keyword search over the registry
  use_skill         — render a skill template with given params
"""

import json
import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_code(code: str) -> tuple[bool, str]:
    """Run code headlessly (show_object commented out). Return (success, error)."""
    headless = code.replace("show_object(", "#show_object(")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(headless)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def plan_shape(features: str) -> str:
    """Record a structured feature plan BEFORE writing any code.

    Call this FIRST, right after understanding the user's request.
    List every geometric feature the final shape must have.
    This plan is your contract — your code MUST implement ALL items.

    Args:
        features: newline-separated list of required features, e.g.
            "L-shaped body: 80x40x5mm vertical plate + 80x30x5mm horizontal base
             4x mounting holes dia=4mm at corners
             gusset triangle between vertical and horizontal plates
             3mm fillet on all outer edges"

    Returns:
        The confirmed plan, which you must honour in your code.
    """
    lines = [l.strip() for l in features.strip().splitlines() if l.strip()]
    if not lines:
        return "ERROR: features list is empty — describe what needs to be built."
    plan = "\n".join(f"  [x] {l}" for l in lines)
    return (
        f"PLAN CONFIRMED ({len(lines)} features):\n{plan}\n\n"
        "Your code MUST implement every item above. "
        "Do NOT simplify or omit any feature to make the code pass."
    )


@tool
def execute_cadquery(code: str) -> str:
    """Execute CadQuery Python code headlessly to verify it runs without errors.

    Returns 'SUCCESS' if the code is valid and runs cleanly.
    Returns the full error traceback if it fails.

    ALWAYS call this after writing or modifying code.
    If it fails, read the error, fix the code, and call again.
    Repeat until SUCCESS — do not give up before 3 attempts.
    """
    success, error = _run_code(code)
    if success:
        return "SUCCESS — code is valid and ready for the editor."
    return f"FAILED:\n{error.strip()}"


@tool
def list_skills() -> str:
    """List all available CadQuery skill templates with their names and descriptions.

    Call this first to check if a pre-built template already exists for the
    requested shape (bracket, gear, thread, enclosure, etc.).
    If a matching skill exists, use use_skill() to get the base code.
    """
    from skill_loader import get_registry_summary
    return get_registry_summary()


@tool
def search_skills(query: str) -> str:
    """Search the skill library by keyword and return matching skills.

    Args:
        query: keyword to search, e.g. "gear", "thread", "bracket", "pocket", "hole"

    Returns matching skill names and descriptions, or a message if none found.
    """
    from skill_loader import load_registry
    registry = load_registry()
    q = query.lower()
    matches = [
        s for s in registry
        if q in s["name"].lower()
        or q in s["description"].lower()
        or any(q in kw.lower() for kw in s.get("keywords", []))
    ]
    if not matches:
        return f"No skills found for '{query}'. Use list_skills() to see everything available."
    return "\n".join(f"- {s['name']}: {s['description']}" for s in matches)


@tool
def use_skill(skill_name: str, params_json: str) -> str:
    """Render a CadQuery skill template with the given parameters.

    Returns the complete Python code from the template.
    After calling this, always run execute_cadquery() to validate the result.

    Args:
        skill_name:  exact name from list_skills() or search_skills()
        params_json: JSON string of parameters, e.g.
                     '{"major_diameter": 8, "pitch": 1.25, "length": 20}'
                     Use '{}' to render with all defaults.
    """
    from skill_loader import load_skill
    try:
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        skill = load_skill(skill_name)
        code = skill.render(params)
        return f"Skill '{skill_name}' rendered. Code:\n\n{code}"
    except json.JSONDecodeError as e:
        return f"ERROR: params_json is not valid JSON — {e}"
    except FileNotFoundError:
        return f"ERROR: skill '{skill_name}' not found. Use list_skills() to see valid names."
    except Exception as e:
        return f"ERROR rendering skill '{skill_name}': {e}"
