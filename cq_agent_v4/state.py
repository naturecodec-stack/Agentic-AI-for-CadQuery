from typing import Annotated
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Full state for the v4 multi-agent pipeline."""

    # --- Input ---
    user_request: str
    image_path: str
    api_key: str
    model: str

    # --- Memory ---
    recalled_shapes: list          # similar past shapes loaded at startup

    # --- Planning ---
    plan: str                      # feature plan from planner agent

    # --- Coding ---
    generated_code: str
    execution_success: bool
    execution_error: str
    repair_attempts: int

    # --- Visual feedback ---
    svg_paths: dict                # {"isometric": path, "front": path, "top": path}
    visual_critique: str           # reviewer's written assessment
    visual_loops: int              # how many times we've looped back from reviewer
    shape_approved: bool           # reviewer says shape looks correct

    # --- Human approval ---
    human_approved: bool           # human clicked Approve
    human_feedback: str            # human typed feedback (if rejected)

    # --- Output ---
    final_code: str
    final_message: str
