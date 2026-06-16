import json
from state import AgentState
from llm import call_llm
from skill_loader import get_registry_summary

SYSTEM = """You are a CadQuery skill matcher.

You will be given a user's CAD request and Gemini's geometric analysis of it.
You have a SMALL list of specialized skills for operations where exact syntax matters most:

{registry}

IMPORTANT: Default to "generic" unless the request CLEARLY and SPECIFICALLY matches
one of the specialized skills above (e.g. bolts/nuts/washers, counterbore/countersink holes,
hole patterns, helix/springs, multi-section lofts/sweeps, assemblies with constraints,
or file import/export).

For ALL general shapes (boxes, cylinders, brackets, vases, custom profiles, etc.) — use "generic".
Gemini already generates these correctly without a template.

Respond ONLY with valid JSON:
{{
  "skill": "skill_name_or_generic",
  "confidence": "high/medium/low",
  "reason": "brief reason",
  "params": {{ }}
}}

If skill is "generic", params can be empty {{}}.
"""


def skill_selection_node(state: AgentState, api_key: str, model: str) -> AgentState:
    print("[2/4] Checking specialized skills...")

    registry_summary = get_registry_summary()
    system = SYSTEM.format(registry=registry_summary)

    user = (
        f"User request: {state.user_request}\n\n"
        f"Geometric analysis:\n{state.plan}\n\n"
        f"Does this match a specialized skill, or should it be generic?"
    )

    response = call_llm(api_key, model, system, user)

    response = response.strip()
    if response.startswith("```"):
        lines = response.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        response = "\n".join(lines).strip()

    try:
        data = json.loads(response)
        state.selected_skill   = data.get("skill", "generic")
        state.extracted_params = data.get("params", {})
        confidence = data.get("confidence", "?")
        reason     = data.get("reason", "")
        print(f"  Skill: {state.selected_skill} (confidence: {confidence})")
        print(f"  Reason: {reason}")
    except Exception as e:
        print(f"  Parse error: {e} — using generic")
        state.selected_skill   = "generic"
        state.extracted_params = {}

    return state
