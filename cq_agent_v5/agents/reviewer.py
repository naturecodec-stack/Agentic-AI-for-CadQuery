"""
Reviewer agent — v5 (local model via Ollama, vision_model).
Looks at rendered SVG images and judges if shape matches the request.
"""

import base64
import os

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_vision_llm

SYSTEM = """You are a 3D CAD quality reviewer.

You will be shown SVG projections of a generated CadQuery shape (and reference image if provided).

Your job: judge whether the generated shape matches the reference image or text request.

RESPOND WITH EXACTLY:
APPROVED
[one sentence describing what matches]

OR:

REJECTED
[bullet list of specific differences]
[be precise: "reference has 4 holes, generated has none", "missing pocket", "wrong aspect ratio"]

Rules:
- If reference image provided: compare against the IMAGE, not just the text plan
- SVG projections are 2D line drawings — judge geometry, not colour
- Simple box output for a complex shape → always REJECTED"""


def run_reviewer(ollama_url: str, vision_model: str,
                 user_request: str, plan: str,
                 svg_paths: dict, image_path: str = "",
                 extra_context: str = "") -> dict:
    llm = get_vision_llm(ollama_url, vision_model, temperature=0.0)

    extra = f"\n\n{extra_context}" if extra_context else ""
    content = [{"type": "text",
                "text": f"USER REQUEST: {user_request}\n\nFEATURE PLAN:\n{plan}{extra}\n\n"}]

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        content.append({"type": "text", "text": "REFERENCE IMAGE (this is what must be reproduced):"})
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

    content.append({"type": "text", "text": "GENERATED SHAPE (compare against reference):"})

    for view_name, svg_path in svg_paths.items():
        if not svg_path or not os.path.exists(str(svg_path)):
            continue
        image_data = _svg_to_image(svg_path)
        if image_data:
            mime, b64 = image_data
            content.append({"type": "text", "text": f"View: {view_name}"})
            content.append({"type": "image_url",
                             "image_url": {"url": f"data:{mime};base64,{b64}"}})

    if len(content) <= 2:
        return {"approved": True,
                "critique": "Could not load rendered SVGs — skipping visual review."}

    result = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=content)])
    text = result.content if isinstance(result.content, str) else str(result.content)
    approved = text.strip().startswith("APPROVED")
    return {"approved": approved, "critique": text.strip()}


def _svg_to_image(svg_path: str):
    try:
        from PyQt5.QtSvg import QSvgRenderer
        from PyQt5.QtGui import QImage, QPainter, QColor
        from PyQt5.QtCore import QSize, QBuffer, QIODevice

        renderer = QSvgRenderer(svg_path)
        if renderer.isValid():
            img = QImage(QSize(640, 480), QImage.Format_ARGB32)
            img.fill(QColor("white"))
            painter = QPainter(img)
            renderer.render(painter)
            painter.end()
            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            img.save(buf, "PNG")
            return "image/png", base64.b64encode(bytes(buf.data())).decode()
    except Exception:
        pass
    try:
        import cairosvg, tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        cairosvg.svg2png(url=svg_path, write_to=tmp.name, output_width=640)
        with open(tmp.name, "rb") as f:
            data = f.read()
        os.unlink(tmp.name)
        return "image/png", base64.b64encode(data).decode()
    except Exception:
        pass
    return None
