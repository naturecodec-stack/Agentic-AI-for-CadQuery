"""
Dimension Validator — v5 (local model via Ollama, vision_model).
"""

import base64
import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_vision_llm

SYSTEM = """You are a CAD Dimension Validator.

You see: (1) REFERENCE IMAGE and (2) RENDERED SVG of the generated shape.

YOUR ONLY JOB: Compare proportions NUMERICALLY. Do NOT comment on feature presence.

MEASURE: overall width:height ratio, relative feature sizes, depth ratio.

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "proportions_match": false,
  "ref_width_height": 2.1,
  "gen_width_height": 3.4,
  "ref_feature_ratio": 0.12,
  "gen_feature_ratio": 0.09,
  "corrections": [
    "Shape is ~60% too wide — reduce width or increase height"
  ],
  "confidence": "high|medium|low",
  "notes": ""
}

If proportions match: {"proportions_match": true, "corrections": [], "confidence": "medium"}
If no reference image: {"proportions_match": true, "corrections": [], "confidence": "low"}"""


def run_dimension_validator(ollama_url: str, vision_model: str,
                             svg_paths: dict, image_path: str = "",
                             dimension_hints: dict = None) -> dict:
    if not image_path or not os.path.exists(image_path) or not svg_paths:
        return {"proportions_match": True, "corrections": [], "confidence": "low"}

    llm = get_vision_llm(ollama_url, vision_model, temperature=0.0)

    def _encode(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp",
                "svg": "image/svg+xml"}.get(ext, "image/png")
        return b64, mime

    content = [{"type": "text", "text": "IMAGE 1 — REFERENCE (target proportions):"}]
    try:
        b64, mime = _encode(image_path)
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    except Exception:
        return {"proportions_match": True, "corrections": [], "confidence": "low"}

    svg_path = (svg_paths.get("isometric") or svg_paths.get("front") or
                next(iter(svg_paths.values()), None))
    if svg_path and os.path.exists(str(svg_path)):
        content.append({"type": "text", "text": "IMAGE 2 — GENERATED SHAPE:"})
        try:
            b64, mime = _encode(str(svg_path))
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        except Exception:
            pass

    if dimension_hints:
        o = dimension_hints.get("overall", {})
        if o.get("width_mm"):
            content.append({"type": "text",
                             "text": f"Target dimensions: {o['width_mm']}x{o['height_mm']}x{o['depth_mm']}mm"})

    content.append({"type": "text", "text": "Compare proportions and report mismatches."})

    result = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=content)])
    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip())
    except Exception:
        return {"proportions_match": True, "corrections": [], "confidence": "low"}


def format_dimension_corrections(data: dict) -> str:
    if not data or data.get("proportions_match") or not data.get("corrections"):
        return ""
    lines = [
        "=== DIMENSION VALIDATOR: PROPORTION MISMATCH ===",
        f"Confidence: {data.get('confidence', '?')}",
    ]
    rw = data.get("ref_width_height")
    gw = data.get("gen_width_height")
    if rw and gw:
        lines.append(f"Width:Height — target {rw:.2f}:1, generated {gw:.2f}:1")
    for fix in data.get("corrections", []):
        lines.append(f"  RESIZE: {fix}")
    lines.append("=== ADJUST DIMENSIONS TO MATCH TARGET ===")
    return "\n".join(lines)
