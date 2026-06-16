"""
Planner agent — analyses the user request, checks memory, calls plan_shape.
Returns a structured feature plan the coder must follow.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

SYSTEM = """You are a CadQuery 3D CAD planning expert.

Your job: analyse the user's shape request and produce a complete feature plan.

You have access to:
  plan_shape(features)   — call this to commit to the feature list

STEPS:
1. Read the user request carefully.
2. If recalled_shapes are provided, note any similar past solutions.
3. Break the request into every geometric feature needed (body dimensions,
   holes, fillets, gussets, threads, pockets, text, etc.).
4. Call plan_shape() with the complete feature list.
5. After plan_shape returns, reply with ONE sentence summarising the plan.

RULES:
- Be specific with dimensions when stated (e.g. "4x M4 holes at corners, 10mm from edge")
- Do NOT write any CadQuery code — that's the coder's job.
- Do NOT omit features to simplify. If the user asked for it, plan it."""


def run_planner(api_key: str, model: str, user_request: str,
                recalled_shapes: list, image_path: str = "") -> str:
    """Run the planner agent. Returns the plan text."""
    from langgraph.prebuilt import create_react_agent
    from ..tools.skill_tools import plan_shape
    import inspect, base64, os

    llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0.1)
    system_msg = SystemMessage(content=SYSTEM)

    params = inspect.signature(create_react_agent).parameters
    kwargs = {"prompt": system_msg} if "prompt" in params else \
             {"state_modifier": system_msg} if "state_modifier" in params else {}
    agent = create_react_agent(llm, [plan_shape], **kwargs)

    # Build context message
    memory_ctx = ""
    if recalled_shapes:
        memory_ctx = "\n\nSIMILAR PAST SHAPES FROM MEMORY:\n"
        for s in recalled_shapes:
            memory_ctx += f"- Request: {s['request']}\n  Tags: {', '.join(s.get('tags', []))}\n"

    content = [{"type": "text", "text": f"User request: {user_request}{memory_ctx}"}]

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        content.append({"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}})

    result = agent.invoke({"messages": [HumanMessage(content=content)]})
    msgs = result.get("messages", [])

    # Return the last AI text
    for msg in reversed(msgs):
        from langchain_core.messages import AIMessage
        if isinstance(msg, AIMessage):
            c = msg.content
            return c if isinstance(c, str) else str(c)
    return "Plan completed."
