import os
import sys

# Ensure v3 root is on the path so nodes can import state/llm/skill_loader
sys.path.insert(0, os.path.dirname(__file__))

from langgraph.graph import StateGraph, END, START

from state import AgentState
from nodes.planning import planning_node
from nodes.skill_selection import skill_selection_node
from nodes.code_generation import code_generation_node
from nodes.execute import execute_node, MAX_REPAIR_ATTEMPTS
from nodes.repair import repair_node


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_execute(state: AgentState) -> str:
    """Branch after execution: succeed → end, retry → repair, exhausted → end."""
    if state["execution_success"]:
        return "end"
    if state["repair_attempts"] < MAX_REPAIR_ATTEMPTS:
        return "repair"
    return "end"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("plan",         planning_node)
    builder.add_node("skill_select", skill_selection_node)
    builder.add_node("codegen",      code_generation_node)
    builder.add_node("execute",      execute_node)
    builder.add_node("repair",       repair_node)

    builder.add_edge(START,          "plan")
    builder.add_edge("plan",         "skill_select")
    builder.add_edge("skill_select", "codegen")
    builder.add_edge("codegen",      "execute")

    builder.add_conditional_edges(
        "execute",
        route_after_execute,
        {"repair": "repair", "end": END},
    )

    builder.add_edge("repair", "execute")   # repair loops back to execute

    return builder.compile()


graph = build_graph()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_graph(
    user_request: str,
    image_path: str,
    api_key: str,
    model: str,
) -> AgentState:
    """Run the full agent graph and return the final state."""
    initial: AgentState = {
        "user_request":     user_request,
        "image_path":       image_path,
        "api_key":          api_key,
        "model":            model,
        "plan":             "",
        "selected_skill":   "",
        "extracted_params": {},
        "generated_code":   "",
        "execution_success": False,
        "execution_error":  "",
        "repair_attempts":  0,
        "repair_history":   [],
        "final_message":    "",
    }
    return graph.invoke(initial)


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CadQuery AI Agent v3 (LangGraph)")
    parser.add_argument("request", help="CAD request, e.g. 'a 50x30x10 box with a 5mm hole'")
    parser.add_argument("--api-key", required=True, help="Google Gemini API key")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--image", default="", help="Optional image path")
    args = parser.parse_args()

    result = run_graph(args.request, args.image, args.api_key, args.model)

    print("\n" + "=" * 60)
    print(result["final_message"])
    print("=" * 60)
    print(result["generated_code"])
