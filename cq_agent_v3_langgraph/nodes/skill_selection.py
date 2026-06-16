import json
from state import AgentState
from llm import call_llm
from skill_loader import get_registry_summary

SYSTEM = """You are a CadQuery skill matcher.

You will be given a user's CAD request and a geometric analysis of it.
You have a SMALL list of specialized skills for operations where exact syntax matters most:

{registry}

IMPORTANT: Default to "generic" unless the request CLEARLY and SPECIFICALLY matches
one of the specialized skills above (e.g. bolts/nuts/washers, counterbore/countersink holes,
hole patterns, helix/springs, multi-section lofts/sweeps, assemblies with constraints,
or file import/export).

For ALL general shapes (boxes, cylinders, brackets, vases, custom profiles, etc.) — use "generic".

Respond ONLY with valid JSON:
{{
  "skill": "skill_name_or_generic",
  "confidence": "high/medium/low",
  "reason": "brief reason",
  "params": {{ }}
}}

If skill is "generic", params can be empty {{}}.
"""


def skill_selection_node(state: AgentState) -> dict:
    print("[2/5] Selecting skill...")

    system = SYSTEM.format(registry=get_registry_summary())
    user = (
        f"User request: {state['user_request']}\n\n"
        f"Geometric analysis:\n{state['plan']}\n\n"
        f"Does this match a specialized skill, or should it be generic?"
    )

    response = call_llm(state["api_key"], state["model"], system, user)
    response = response.strip()
    if response.startswith("```"):
        lines = [l for l in response.splitlines() if not l.startswith("```")]
        response = "\n".join(lines).strip()

    try:
        data = json.loads(response)
        skill = data.get("skill", "generic")
        params = data.get("params", {})
        print(f"  Skill: {skill} (confidence: {data.get('confidence', '?')})")
        print(f"  Reason: {data.get('reason', '')}")
    except Exception as e:
        print(f"  Parse error: {e} — falling back to generic")
        skill, params = "generic", {}

    return {"selected_skill": skill, "extracted_params": params}
