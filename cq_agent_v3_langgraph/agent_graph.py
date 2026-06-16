"""
Tool-calling CadQuery agent built on LangGraph's create_react_agent.

The LLM autonomously decides when to call each tool:
  list_skills / search_skills  → discover available templates
  use_skill                    → render a template as starting code
  execute_cadquery             → validate code; LLM sees error and self-repairs

Requires:
  pip install langchain-google-genai langgraph langchain-core
"""

import base64
import os
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from tools import execute_cadquery, list_skills, plan_shape, search_skills, use_skill

ALL_TOOLS = [plan_shape, search_skills, list_skills, use_skill, execute_cadquery]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert CadQuery programmer and 3D CAD AI assistant.
Your job: generate COMPLETE, ACCURATE CadQuery code — every feature the user asked for, nothing left out.

═══ MANDATORY WORKFLOW ═══
STEP 1 — PLAN:  Call plan_shape(features) listing EVERY geometric feature required.
                This is your contract. You cannot skip or simplify ANY item in the plan.

STEP 2 — SKILLS: Call search_skills(query) for key shape words (e.g. "bracket", "gear", "pocket").
                  If a match: call use_skill(name, params_json) to get a code base.
                  If no match: write from scratch.

STEP 3 — CODE:  Write the complete CadQuery script implementing ALL plan items.
                Never take shortcuts to make code simpler. If the plan says "fillet edges",
                there must be .fillet() in the code. If it says "4 mounting holes", code
                must have 4 holes, not 0.

STEP 4 — VALIDATE: Call execute_cadquery(code) to check for Python/CadQuery errors.
                    If FAILED: fix the specific error — do NOT remove features to make it pass.
                    Repeat up to 5 times. Try a different construction approach on attempt 3+.

STEP 5 — DONE:  When execute_cadquery returns SUCCESS, reply:
                "Done — [one sentence describing what was built]"
                Do NOT print the code again.

═══ ANTI-SIMPLIFICATION RULE ═══
NEVER produce a plain box, cylinder, or minimal shape when the user asked for something
more complex. If the user asked for a bracket with holes, gusset, and fillets — all THREE
must appear in the final code. Validation success on a simplified shape is WRONG.

═══ CADQUERY PATTERNS ═══
# Multi-body union (L-bracket, T-shape, frames):
  plate1 = cq.Workplane("XY").box(w, h, t)
  plate2 = cq.Workplane("XZ").box(w, d, t).translate((0, 0, t/2))
  result = plate1.union(plate2)

# Holes on a face:
  result = result.faces(">Z").workplane().pushPoints([(x1,y1),(x2,y2)]).hole(dia)

# Pocket (blind cavity):
  result = result.faces(">Z").workplane().rect(pw, ph).cutBlind(-depth)

# Fillet/chamfer (ALWAYS last, after all booleans):
  result = result.edges("|Z").fillet(r)          # vertical edges only
  result = result.edges(">Z or <Z").fillet(r)    # top/bottom face edges
  result = result.fillet(r)                       # all edges (use cautiously)

# Stepped shaft:
  result = cq.Workplane("XY").circle(r1).extrude(h1)
  result = result.faces(">Z").workplane().circle(r2).extrude(h2)

# Tag before boolean (preserves face selectors):
  body = cq.Workplane("XY").box(50,30,10).tag("base")
  result = body.cut(cq.Workplane("XY").cylinder(8, 5))

# Shell (hollow, inward):
  result = cq.Workplane("XY").box(60,40,30).faces(">Z").shell(-2)

# Gusset / rib triangle:
  gusset = (cq.Workplane("XZ")
    .moveTo(0, 0).lineTo(gw, 0).lineTo(0, gh).close()
    .extrude(gt))
  result = body.union(gusset)

# Text emboss:
  result = result.faces(">Z").workplane().text("ABC", 8, 1)

# Revolve (lathe shape):
  result = (cq.Workplane("XZ")
    .polyline([(0,0),(r,0),(r,h1),(r2,h2),(0,h2)]).close()
    .revolve())

═══ IMPORTS & CONVENTIONS ═══
- import cadquery as cq          (always)
- result = ...                   (final shape always named `result`)
- show_object(result)            (always last line)
- Numbers: use floats (10.0 not 10 for dimensions where precision matters)"""


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------

def build_agent(api_key: str, model: str):
    import inspect

    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.1,
    )

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    params = inspect.signature(create_react_agent).parameters

    # Parameter name changed across LangGraph versions:
    #   0.1.x → messages_modifier
    #   0.2.x → state_modifier
    #   0.3.x → prompt
    if "prompt" in params:
        return create_react_agent(llm, ALL_TOOLS, prompt=system_msg)
    elif "state_modifier" in params:
        return create_react_agent(llm, ALL_TOOLS, state_modifier=system_msg)
    elif "messages_modifier" in params:
        return create_react_agent(llm, ALL_TOOLS, messages_modifier=system_msg)
    else:
        return create_react_agent(llm, ALL_TOOLS)


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

def _build_human_message(user_request: str, image_path: str) -> HumanMessage:
    """Build a HumanMessage, with base64 image embedded if provided."""
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png",  "webp": "image/webp",
        }.get(ext, "image/png")
        return HumanMessage(content=[
            {"type": "text",      "text": user_request},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
        ])
    return HumanMessage(content=user_request)


def extract_final_code(messages: list) -> str:
    """Scan message history for the last code that execute_cadquery reported SUCCESS on."""
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        # Find a ToolMessage that says SUCCESS
        if isinstance(msg, ToolMessage) and "SUCCESS" in str(msg.content):
            # Walk back to find the AIMessage whose tool_call triggered this
            tool_call_id = getattr(msg, "tool_call_id", None)
            for j in range(i - 1, -1, -1):
                prev = messages[j]
                if isinstance(prev, AIMessage) and prev.tool_calls:
                    for tc in prev.tool_calls:
                        if tc.get("name") == "execute_cadquery":
                            if tool_call_id is None or tc.get("id") == tool_call_id:
                                return tc["args"].get("code", "")
    return ""


# ---------------------------------------------------------------------------
# Public entry point (used by CLI and widget)
# ---------------------------------------------------------------------------

def run_agent(
    user_request: str,
    image_path: str,
    api_key: str,
    model: str,
) -> dict:
    """Run the tool-calling agent synchronously.

    Returns:
        {
            "code":          str   — final working CadQuery code (empty if failed),
            "success":       bool,
            "final_message": str   — last AI message text,
            "messages":      list  — full message history,
        }
    """
    agent = build_agent(api_key, model)
    human_msg = _build_human_message(user_request, image_path)

    result = agent.invoke({"messages": [human_msg]})
    messages = result.get("messages", [])

    code = extract_final_code(messages)

    # Fallback: if no SUCCESS found, check last AIMessage for embedded code
    if not code:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = msg.content if isinstance(msg.content, str) else ""
                if "import cadquery" in content:
                    import re
                    match = re.search(
                        r"```python\s*(import cadquery[\s\S]*?)```", content
                    )
                    if match:
                        code = match.group(1).strip()
                    break

    final_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                )
            final_msg = str(content)
            break

    return {
        "code":          code,
        "success":       bool(code),
        "final_message": final_msg,
        "messages":      messages,
    }


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CadQuery tool-calling agent")
    parser.add_argument("request", help="e.g. 'a 50x30x10 box with a 5mm hole'")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--model", default="gemini-2.0-flash")
    parser.add_argument("--image", default="")
    args = parser.parse_args()

    # Ensure v3 dir is on path for skill_loader
    v3_dir = os.path.dirname(__file__)
    if v3_dir not in sys.path:
        sys.path.insert(0, v3_dir)

    result = run_agent(args.request, args.image, args.api_key, args.model)
    print("\n" + "=" * 60)
    print("SUCCESS" if result["success"] else "FAILED")
    print("=" * 60)
    print(result["code"] or result["final_message"])
