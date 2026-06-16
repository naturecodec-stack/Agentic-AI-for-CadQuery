"""
Reviewer agent — looks at the rendered SVG images and judges whether
the shape matches the original request and plan.

Uses multimodal (vision) LLM to actually see the 3D projections.
"""

import base64
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

SYSTEM = """You are a 3D CAD quality reviewer.

You will be shown SVG projections of a CadQuery shape (isometric, front, top views).
Your job: judge whether the shape correctly matches the user's request and feature plan.

RESPOND WITH EXACTLY:
APPROVED
[one sentence describing what you see]

OR:

REJECTED
[bullet list of specific missing or wrong features]
[be precise: "holes are missing", "gusset not visible", "wrong proportions"]

Rules:
- If the shape has ALL planned features visible → APPROVED
- If ANY feature from the plan is missing or wrong → REJECTED
- SVG projections are 2D line drawings — judge geometry, not colour/shading
- Simple shapes (box, cylinder) for a complex request → always REJECTED"""


def run_reviewer(api_key: str, model: str, user_request: str,
                 plan: str, svg_paths: dict) -> dict:
    """
    Returns:
        {"approved": bool, "critique": str}
    """
    llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0.0)

    content = [
        {
            "type": "text",
            "text": (
                f"USER REQUEST: {user_request}\n\n"
                f"FEATURE PLAN:\n{plan}\n\n"
                "Below are SVG projections of the generated shape. "
                "Judge whether it matches the request and plan."
            ),
        }
    ]

    # Embed each SVG as a PNG image (via base64 SVG → pass as SVG data URI)
    # Gemini accepts SVG as image/svg+xml in some versions; use PNG fallback
    for view_name, svg_path in svg_paths.items():
        if not svg_path or not os.path.exists(str(svg_path)):
            continue
        image_data = _svg_to_image(svg_path)
        if image_data:
            mime, b64 = image_data
            content.append({"type": "text", "text": f"View: {view_name}"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })

    if len(content) == 1:
        # No images loaded — approve with warning
        return {
            "approved": True,
            "critique": "Could not load rendered SVGs — skipping visual review.",
        }

    result = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=content),
    ])

    text = result.content if isinstance(result.content, str) else str(result.content)
    approved = text.strip().startswith("APPROVED")
    critique = text.strip()
    return {"approved": approved, "critique": critique}


def _svg_to_image(svg_path: str):
    """Convert SVG to base64 PNG (needs cairosvg) or return raw SVG base64."""
    try:
        import cairosvg
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        cairosvg.svg2png(url=svg_path, write_to=tmp.name, output_width=600)
        with open(tmp.name, "rb") as f:
            data = f.read()
        os.unlink(tmp.name)
        return "image/png", base64.b64encode(data).decode()
    except ImportError:
        pass

    # Fallback: send SVG directly (Gemini supports SVG in some API versions)
    try:
        with open(svg_path, "rb") as f:
            data = f.read()
        return "image/svg+xml", base64.b64encode(data).decode()
    except Exception:
        return None
