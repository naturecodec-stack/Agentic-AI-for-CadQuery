from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Full state for the v5 local-model multi-agent pipeline."""

    # --- Input ---
    user_request: str
    image_path: str
    ollama_url: str          # e.g. "http://localhost:11434"
    text_model: str          # tool-calling model, e.g. "qwen2.5-coder:7b"
    vision_model: str        # vision model, e.g. "llava:7b"

    # --- Memory ---
    recalled_shapes: list          # similar past shapes loaded at startup

    # --- Dimension extraction ---
    dimension_hints: dict          # structured dimensions extracted before planning

    # --- Assembly decomposition ---
    is_assembly: bool              # True if input has multiple parts
    sub_shapes: list               # list of part descriptions from decomposer

    # --- Planning ---
    plan: str                      # feature plan from planner agent

    # --- Skill selection ---
    skill_recommendations: list    # ranked skill templates from skill_selector

    # --- Coding ---
    generated_code: str
    execution_success: bool
    execution_error: str
    repair_attempts: int
    repair_used: bool              # True if repair_specialist was activated

    # --- Code review ---
    code_critic_feedback: str      # logical mismatch feedback from code_critic
    critic_loops: int              # how many times code_critic sent back to coder

    # --- Visual feedback ---
    svg_paths: dict                # {"isometric": path, "front": path, "top": path}
    dimension_validation: dict     # proportion analysis from dimension_validator
    visual_critique: str           # reviewer's written assessment
    visual_loops: int              # how many times we've looped back from reviewer
    shape_approved: bool           # reviewer says shape looks correct

    # --- Mode ---
    visual_review: bool            # False = fast mode (skip render/review/approval)

    # --- Human approval ---
    human_approved: bool           # human clicked Approve
    human_feedback: str            # human typed feedback (if rejected)

    # --- Output ---
    final_code: str
    final_message: str
