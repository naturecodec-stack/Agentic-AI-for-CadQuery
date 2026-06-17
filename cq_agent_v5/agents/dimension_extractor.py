"""
Dimension Extractor — v5 (local model via Ollama).
Vision model used when image provided; text model for text-only.
"""

import base64
import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm, get_vision_llm

SYSTEM_WITH_IMAGE = """You are a CAD dimension extraction specialist.

You are given an image of a 3D shape. No scale bar may be present.

YOUR ONLY JOB: Extract every visible dimension, proportion, and feature count.

RULES:
- Study overall proportions first (width:height:depth ratios)
- Count EVERY visible feature: holes, ribs, slots, fillets, steps, pockets
- If no scale reference: estimate absolute mm based on what the part looks like in real life
- Be specific about positions: "4 holes at corners, ~10% from each edge"
- Never say "unknown" — always give a best estimate with confidence level

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "has_image": true,
  "overall": {
    "width_mm": 80,
    "height_mm": 40,
    "depth_mm": 5,
    "width_height_ratio": 2.0,
    "confidence": "medium"
  },
  "features": [
    {
      "type": "hole",
      "count": 4,
      "size_mm": 4.5,
      "depth_mm": null,
      "position": "corners, ~8mm from edges",
      "notes": ""
    }
  ],
  "shape_type": "bracket",
  "notes": ""
}"""

SYSTEM_WITHOUT_IMAGE = """You are a CAD dimension extraction specialist.

You are given a TEXT description of a shape. No image is provided.

YOUR ONLY JOB: Extract explicit dimensions and infer missing ones.

ENGINEERING STANDARDS:
- M3=3mm, M4=4mm, M5=5mm, M6=6mm, M8=8mm, M10=10mm
- Arduino=68x53mm, Raspberry Pi=85x56mm, standard PCB=60x40mm
- Bracket thickness=4-6mm, fillet=1-3mm small / 3-8mm large

INFER FROM SHAPE TYPE (when not stated):
- small bracket: ~80x40x5mm
- enclosure: ~100x60x40mm
- gear: module=1-2, 20-40 teeth

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "has_image": false,
  "overall": {
    "width_mm": 80,
    "height_mm": 40,
    "depth_mm": 5,
    "confidence": "medium"
  },
  "features": [
    {
      "type": "hole",
      "count": 4,
      "size_mm": 4.5,
      "position": "corners",
      "source": "inferred"
    }
  ],
  "explicit_dimensions": [],
  "inferred_dimensions": ["width 80mm", "height 40mm"],
  "shape_type": "bracket",
  "notes": ""
}"""


def run_dimension_extractor(ollama_url: str, text_model: str, vision_model: str,
                             user_request: str, image_path: str = "") -> dict:
    """Extract dimensions from image or text. Returns hints dict."""
    has_image = bool(image_path and os.path.exists(image_path))

    if has_image:
        llm = get_vision_llm(ollama_url, vision_model, temperature=0.0)
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        content = [
            {"type": "text",
             "text": f"USER REQUEST: {user_request}\n\nAnalyse this image and extract all dimensions:"},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
        system = SYSTEM_WITH_IMAGE
    else:
        llm = get_text_llm(ollama_url, text_model, temperature=0.0)
        content = [{"type": "text",
                    "text": f"USER REQUEST: {user_request}\n\nExtract all dimensions from this text description:"}]
        system = SYSTEM_WITHOUT_IMAGE

    result = llm.invoke([SystemMessage(content=system), HumanMessage(content=content)])
    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {
            "has_image": has_image,
            "overall": {"width_mm": None, "height_mm": None, "depth_mm": None, "confidence": "low"},
            "features": [],
            "notes": raw[:400],
        }


def format_hints_for_planner(hints: dict) -> str:
    if not hints:
        return ""
    lines = ["=== DIMENSION EXTRACTOR OUTPUT ==="]
    overall = hints.get("overall", {})
    if overall.get("width_mm"):
        lines.append(f"Overall size: {overall.get('width_mm')}mm (W) x "
                     f"{overall.get('height_mm')}mm (H) x "
                     f"{overall.get('depth_mm')}mm (D)  "
                     f"[confidence: {overall.get('confidence', '?')}]")
    if hints.get("shape_type"):
        lines.append(f"Shape type: {hints['shape_type']}")
    for f in hints.get("features", []):
        src = f" [{f.get('source', '')}]" if f.get("source") else ""
        size = f", size={f.get('size_mm')}mm" if f.get("size_mm") else ""
        pos = f", at: {f.get('position')}" if f.get("position") else ""
        lines.append(f"  - {f.get('count', 1)}x {f.get('type')}{size}{pos}{src}")
    if hints.get("notes"):
        lines.append(f"Notes: {hints['notes']}")
    lines.append("=== USE THESE DIMENSIONS IN YOUR PLAN ===")
    return "\n".join(lines)
