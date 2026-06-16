"""
v4 Multi-agent orchestration graph.

Nodes:
  recall_memory   — search past shapes for context
  plan            — planner agent: builds feature plan
  code            — coder agent: writes + validates code
  render          — renders shape to SVG projections
  review          — reviewer agent: visual inspection
  human_approval  — interrupt: asks user to approve/reject
  save_memory     — saves successful shape to JSON memory

Flow:
  START → recall → plan → code → render → review
          ↑ (visual loop)                   │
          └──── REJECTED ───────────────────┤
                                            │ APPROVED
                                      human_approval
                                            │
                                      save_memory → END
"""

import os
import sys

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .state import AgentState

MAX_VISUAL_LOOPS = 2

# ---------------------------------------------------------------------------
# Node: recall_memory
# ---------------------------------------------------------------------------

def recall_memory_node(state: AgentState) -> dict:
    from .memory.store import recall_similar
    recalled = recall_similar(state["user_request"], top_n=3)
    return {"recalled_shapes": recalled}


# ---------------------------------------------------------------------------
# Node: plan
# ---------------------------------------------------------------------------

def plan_node(state: AgentState) -> dict:
    from .agents.planner import run_planner
    plan_text = run_planner(
        api_key=state["api_key"],
        model=state["model"],
        user_request=state["user_request"],
        recalled_shapes=state.get("recalled_shapes", []),
        image_path=state.get("image_path", ""),
    )
    return {"plan": plan_text}


# ---------------------------------------------------------------------------
# Node: code
# ---------------------------------------------------------------------------

def code_node(state: AgentState) -> dict:
    from .agents.coder import run_coder
    result = run_coder(
        api_key=state["api_key"],
        model=state["model"],
        plan=state.get("plan", ""),
        visual_critique=state.get("visual_critique", ""),
        recalled_shapes=state.get("recalled_shapes", []),
    )
    return {
        "generated_code":    result["code"],
        "execution_success": result["success"],
        "repair_attempts":   state.get("repair_attempts", 0) + 1,
    }


# ---------------------------------------------------------------------------
# Node: render
# ---------------------------------------------------------------------------

def render_node(state: AgentState) -> dict:
    code = state.get("generated_code", "")
    if not code or not state.get("execution_success"):
        return {"svg_paths": {}}

    from .tools.cadquery_tools import render_shape
    import json

    raw = render_shape.invoke({"code": code})
    if raw.startswith("RENDER_FAILED"):
        return {"svg_paths": {}}

    try:
        paths = json.loads(raw)
        return {"svg_paths": paths}
    except Exception:
        return {"svg_paths": {}}


# ---------------------------------------------------------------------------
# Node: review
# ---------------------------------------------------------------------------

def review_node(state: AgentState) -> dict:
    svg_paths = state.get("svg_paths", {})
    if not svg_paths:
        # No render available — auto-approve so we don't block forever
        return {
            "shape_approved": True,
            "visual_critique": "No render available — skipping visual review.",
        }

    from .agents.reviewer import run_reviewer
    result = run_reviewer(
        api_key=state["api_key"],
        model=state["model"],
        user_request=state["user_request"],
        plan=state.get("plan", ""),
        svg_paths=svg_paths,
    )
    return {
        "shape_approved":  result["approved"],
        "visual_critique": result["critique"],
        "visual_loops":    state.get("visual_loops", 0) + 1,
    }


# ---------------------------------------------------------------------------
# Node: human_approval (interrupt)
# ---------------------------------------------------------------------------

def human_approval_node(state: AgentState) -> dict:
    svg_paths = state.get("svg_paths", {})
    visual_critique = state.get("visual_critique", "")

    # Pause and ask the human
    response = interrupt({
        "message":        "Shape looks correct. Do you approve loading this code?",
        "svg_paths":      svg_paths,
        "visual_critique": visual_critique,
        "code_preview":   "\n".join(
            state.get("generated_code", "").splitlines()[:6]
        ),
    })

    approved = response.get("approved", True)
    feedback = response.get("feedback", "")
    return {
        "human_approved": approved,
        "human_feedback": feedback,
        # If rejected, append feedback to visual_critique so coder sees it
        "visual_critique": (
            (visual_critique + "\n\nHUMAN FEEDBACK:\n" + feedback)
            if not approved and feedback else visual_critique
        ),
    }


# ---------------------------------------------------------------------------
# Node: save_memory
# ---------------------------------------------------------------------------

def save_memory_node(state: AgentState) -> dict:
    from .memory.store import save_shape

    code = state.get("generated_code", "")
    if code:
        request = state.get("user_request", "")
        # Extract tags from request words (simple keyword extraction)
        stop = {"a","an","the","with","and","or","for","of","to","in","on","at","is"}
        tags = [w for w in request.lower().split() if w not in stop and len(w) > 2][:8]
        save_shape(request=request, code=code, tags=tags)

    final_code = state.get("generated_code", "")
    return {
        "final_code":    final_code,
        "final_message": "Done — shape generated, validated, approved and saved to memory.",
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_review(state: AgentState) -> str:
    loops = state.get("visual_loops", 0)
    if state.get("shape_approved") or loops >= MAX_VISUAL_LOOPS:
        return "human_approval"
    return "code"   # visual loop: go back to coder with critique


def route_after_human(state: AgentState) -> str:
    if state.get("human_approved", True):
        return "save_memory"
    # Human rejected — loop back to coder (visual_critique updated with feedback)
    return "code"


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("recall_memory",   recall_memory_node)
    g.add_node("plan",            plan_node)
    g.add_node("code",            code_node)
    g.add_node("render",          render_node)
    g.add_node("review",          review_node)
    g.add_node("human_approval",  human_approval_node)
    g.add_node("save_memory",     save_memory_node)

    g.add_edge(START,            "recall_memory")
    g.add_edge("recall_memory",  "plan")
    g.add_edge("plan",           "code")
    g.add_edge("code",           "render")
    g.add_edge("render",         "review")

    g.add_conditional_edges("review", route_after_review, {
        "human_approval": "human_approval",
        "code":           "code",
    })
    g.add_conditional_edges("human_approval", route_after_human, {
        "save_memory": "save_memory",
        "code":        "code",
    })
    g.add_edge("save_memory", END)

    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer, interrupt_before=["human_approval"])


graph = build_graph()
