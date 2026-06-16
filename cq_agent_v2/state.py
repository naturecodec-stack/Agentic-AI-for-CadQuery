from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentState:
    # Input
    user_request: str = ""
    image_path:   str = ""

    # Planning
    plan: str = ""

    # Skill selection
    selected_skill: str = ""        # skill name e.g. "box", "bolt"
    extracted_params: dict = field(default_factory=dict)

    # Code
    generated_code: str = ""

    # Execution
    execution_success: bool = False
    execution_error:   str  = ""
    repair_attempts:   int  = 0
    repair_history:    list = field(default_factory=list)

    # Final
    final_message: str = ""
