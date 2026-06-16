NAME = "csk_hole"
DESCRIPTION = "Create a box with a countersunk hole (conical recess at top)"
PARAMETERS = {
    "length":       {"type": "float", "default": 60.0, "unit": "mm"},
    "width":        {"type": "float", "default": 60.0, "unit": "mm"},
    "height":       {"type": "float", "default": 20.0, "unit": "mm"},
    "diameter":     {"type": "float", "default": 6.0,  "unit": "mm"},
    "csk_diameter": {"type": "float", "default": 12.0, "unit": "mm"},
    "csk_angle":    {"type": "float", "default": 82.0, "unit": "degrees"},
}

TEMPLATE = """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box({length}, {width}, {height})
    .faces(">Z")
    .workplane()
    .cskHole({diameter}, {csk_diameter}, {csk_angle})
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        length=params.get("length", 60.0),
        width=params.get("width", 60.0),
        height=params.get("height", 20.0),
        diameter=params.get("diameter", 6.0),
        csk_diameter=params.get("csk_diameter", 12.0),
        csk_angle=params.get("csk_angle", 82.0),
    )
