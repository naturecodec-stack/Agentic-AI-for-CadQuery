"""
Coder agent — v5 (local model via Ollama, text_model with tool calling).
Note: does NOT receive raw image (local vision+tools models are rare).
Relies on dimension hints for sizes instead.
"""

import inspect

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from .llm_factory import get_text_llm
from .dimension_extractor import format_hints_for_planner

SYSTEM = """You are an expert CadQuery programmer.

PRIME DIRECTIVE: Implement EVERY feature from the plan. Use the dimension hints for exact sizes.

You have tools:
  search_skills(query)           — find a matching template
  list_skills()                  — see all 71 templates
  use_skill(name, params_json)   — render a template as starting code
  execute_cadquery(code)         — validate code; returns SUCCESS or error

WORKFLOW:
1. Search skills for the main shape keyword.
2. If match: use use_skill() as the base, then extend it.
3. Implement EVERY feature from the plan using the provided dimensions.
4. Call execute_cadquery(code) — fix errors and retry until SUCCESS (max 5 tries).
5. If error: read the EXACT error, fix the root cause. Do NOT remove features.

CADQUERY PATTERNS:
# Multi-body union:
  a = cq.Workplane("XY").box(w, h, t)
  b = cq.Workplane("XZ").box(w, d, t).translate((0, 0, t/2))
  result = a.union(b)

# Holes on face:
  result = result.faces(">Z").workplane().pushPoints(pts).hole(dia)

# Pocket:
  result = result.faces(">Z").workplane().rect(pw, ph).cutBlind(-depth)

# Fillet (ALWAYS last):
  result = result.edges("|Z").fillet(r)

CONVENTIONS:
  import cadquery as cq
  result = ...
  show_object(result)"""


def run_coder(ollama_url: str, text_model: str, plan: str,
              visual_critique: str = "", recalled_shapes: list = None,
              image_path: str = "", dimension_hints: dict = None,
              skill_recommendations: list = None,
              code_critic_feedback: str = "") -> dict:
    from langgraph.prebuilt import create_react_agent
    from ..tools.cadquery_tools import execute_cadquery
    from ..tools.skill_tools import search_skills, list_skills, use_skill

    llm = get_text_llm(ollama_url, text_model, temperature=0.1)
    system_msg = SystemMessage(content=SYSTEM)
    tools = [search_skills, list_skills, use_skill, execute_cadquery]

    params = inspect.signature(create_react_agent).parameters
    kwargs = {"prompt": system_msg} if "prompt" in params else \
             {"state_modifier": system_msg} if "state_modifier" in params else {}
    agent = create_react_agent(llm, tools, **kwargs)

    prompt_parts = [f"FEATURE PLAN (implement ALL of these):\n{plan}"]

    if dimension_hints:
        prompt_parts.append("\n" + format_hints_for_planner(dimension_hints))

    if skill_recommendations:
        from .skill_selector import format_skill_recommendations
        prompt_parts.append("\n" + format_skill_recommendations(skill_recommendations))

    if code_critic_feedback:
        prompt_parts.append(f"\n{code_critic_feedback}")

    if visual_critique:
        prompt_parts.append(f"\nVISUAL REVIEW FEEDBACK (fix these):\n{visual_critique}")

    if recalled_shapes:
        mem = "\nSIMILAR PAST SHAPES:\n"
        for s in (recalled_shapes or [])[:2]:
            mem += f"Request: {s['request']}\nCode:\n{s['code'][:300]}\n---\n"
        prompt_parts.append(mem)

    prompt_parts.append(
        "\nWrite complete CadQuery code implementing ALL features above, "
        "then validate with execute_cadquery."
    )

    result = agent.invoke({"messages": [HumanMessage(content="\n".join(prompt_parts))]})
    messages = result.get("messages", [])
    code = _extract_code(messages)
    error = _extract_last_error(messages) if not code else ""
    return {"code": code, "success": bool(code), "error": error, "messages": messages}


def _extract_last_error(messages: list) -> str:
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            content = str(msg.content)
            if "SUCCESS" not in content and len(content) > 10:
                return content[:500]
    return ""


def _extract_code(messages: list) -> str:
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if isinstance(msg, ToolMessage) and "SUCCESS" in str(msg.content):
            tc_id = getattr(msg, "tool_call_id", None)
            for j in range(i - 1, -1, -1):
                prev = messages[j]
                if isinstance(prev, AIMessage) and prev.tool_calls:
                    for tc in prev.tool_calls:
                        if tc.get("name") == "execute_cadquery":
                            if tc_id is None or tc.get("id") == tc_id:
                                return tc["args"].get("code", "")
    return ""
