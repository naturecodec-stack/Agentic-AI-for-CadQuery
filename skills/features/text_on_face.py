NAME = "text_on_face"
DESCRIPTION = "Emboss or deboss text on a flat face of a box (cut into surface or raised above it)"
PARAMETERS = {
    "text":        {"type": "str",   "default": "CQ"},
    "font_size":   {"type": "float", "default": 8.0,  "unit": "mm"},
    "depth":       {"type": "float", "default": 1.0,  "unit": "mm", "desc": "positive=emboss, negative=deboss (cut in)"},
    "face":        {"type": "str",   "default": ">Z", "desc": "face selector: >Z <Z >X <X >Y <Y"},
    "box_length":  {"type": "float", "default": 60.0, "unit": "mm"},
    "box_width":   {"type": "float", "default": 30.0, "unit": "mm"},
    "box_height":  {"type": "float", "default": 10.0, "unit": "mm"},
    "font":        {"type": "str",   "default": "Arial"},
}

TEMPLATE = """import cadquery as cq

box_l   = {box_length}
box_w   = {box_width}
box_h   = {box_height}
txt     = "{text}"
fsize   = {font_size}
depth   = {depth}
face    = "{face}"
font    = "{font}"

base = cq.Workplane("XY").box(box_l, box_w, box_h)

if depth >= 0:
    # Embossed: extrude text outward from face
    result = (
        base
        .faces(face).workplane()
        .text(txt, fsize, depth, font=font)
    )
else:
    # Debossed: cut text into face (negative extrude = cut)
    result = (
        base
        .faces(face).workplane()
        .text(txt, fsize, depth, cut=True, font=font)
    )

show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        box_length=float(params.get("box_length", 60.0)),
        box_width=float(params.get("box_width", 30.0)),
        box_height=float(params.get("box_height", 10.0)),
        text=str(params.get("text", "CQ")),
        font_size=float(params.get("font_size", 8.0)),
        depth=float(params.get("depth", 1.0)),
        face=str(params.get("face", ">Z")),
        font=str(params.get("font", "Arial")),
    )
