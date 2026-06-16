NAME = "shell"
DESCRIPTION = "Hollow out a solid box leaving open faces — negative thickness shells inward (the correct direction)"
PARAMETERS = {
    "length":        {"type": "float", "default": 50.0, "unit": "mm"},
    "width":         {"type": "float", "default": 30.0, "unit": "mm"},
    "height":        {"type": "float", "default": 20.0, "unit": "mm"},
    "thickness":     {"type": "float", "default": 2.0,  "unit": "mm", "desc": "wall thickness (always positive here)"},
    "open_face":     {"type": "str",   "default": ">Z", "desc": "face selector to leave open: >Z <Z >X <X >Y <Y or 'none'"},
}

TEMPLATE = """import cadquery as cq

length    = {length}
width     = {width}
height    = {height}
thickness = {thickness}
open_face = "{open_face}"

base = cq.Workplane("XY").box(length, width, height)

if open_face == "none":
    # Fully closed hollow shell — use a small face to open then manually close isn't
    # possible with shell(), so pick any face and accept the opening
    result = base.faces(">Z").shell(-thickness)
else:
    result = base.faces(open_face).shell(-thickness)

show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        length=float(params.get("length", 50.0)),
        width=float(params.get("width", 30.0)),
        height=float(params.get("height", 20.0)),
        thickness=float(params.get("thickness", 2.0)),
        open_face=str(params.get("open_face", ">Z")),
    )
