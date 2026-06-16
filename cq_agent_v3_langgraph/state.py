from typing import TypedDict


class AgentState(TypedDict):
    # inputs
    user_request: str
    image_path: str
    api_key: str
    model: str

    # planning
    plan: str

    # skill selection
    selected_skill: str
    extracted_params: dict

    # code
    generated_code: str

    # execution
    execution_success: bool
    execution_error: str
    repair_attempts: int
    repair_history: list

    # output
    final_message: str
