"""
Planner agent — v5 (local model via Ollama).
Uses text_model with tool calling. Does NOT receive raw image
(local vision+tool-calling models are rare) — relies on dimension hints instead.
"""

import inspect

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm
from .dimension_extractor import format_hints_for_planner

SYSTEM = """You are a CadQuery 3D CAD planning expert.

Your job: produce a complete, exact feature plan so the coder can reproduce the shape precisely.

You have access to:
  plan_shape(features)   — call this to commit to the feature list

DIMENSION HINTS (pre-extracted): These are measured/inferred sizes — USE THEM.
Do not invent different dimensions. If hints say 80mm wide, plan 80mm wide.

ASSEMBLY CONTEXT: If multi-part assembly detected, plan each part separately.

STEPS:
1. Read the dimension hints carefully — use those exact sizes
2. Build a complete feature list: every body, hole, pocket, fillet, thread
3. Call plan_shape() with the complete feature list
4. Reply with ONE sentence summarising the plan

RULES:
- Exact over approximate
- Do NOT omit features. Do NOT add features not described
- Do NOT write any CadQuery code — that is the coder's job"""


def run_planner(ollama_url: str, text_model: str, user_request: str,
                recalled_shapes: list, image_path: str = "",
                dimension_hints: dict = None,
                assembly_context: str = "") -> str:
    from langgraph.prebuilt import create_react_agent
    from ..tools.skill_tools import plan_shape

    llm = get_text_llm(ollama_url, text_model, temperature=0.1)
    system_msg = SystemMessage(content=SYSTEM)

    params = inspect.signature(create_react_agent).parameters
    kwargs = {"prompt": system_msg} if "prompt" in params else \
             {"state_modifier": system_msg} if "state_modifier" in params else {}
    agent = create_react_agent(llm, [plan_shape], **kwargs)

    memory_ctx = ""
    if recalled_shapes:
        memory_ctx = "\n\nSIMILAR PAST SHAPES FROM MEMORY:\n"
        for s in recalled_shapes:
            memory_ctx += f"- {s['request']}  Tags: {', '.join(s.get('tags', []))}\n"

    dim_ctx = ""
    if dimension_hints:
        dim_ctx = "\n\n" + format_hints_for_planner(dimension_hints)

    asm_ctx = f"\n\n{assembly_context}" if assembly_context else ""

    text = f"User request: {user_request}{memory_ctx}{dim_ctx}{asm_ctx}"
    result = agent.invoke({"messages": [HumanMessage(content=text)]})
    msgs = result.get("messages", [])

    from langchain_core.messages import AIMessage
    for msg in reversed(msgs):
        if isinstance(msg, AIMessage):
            c = msg.content
            return c if isinstance(c, str) else str(c)
    return "Plan completed."
