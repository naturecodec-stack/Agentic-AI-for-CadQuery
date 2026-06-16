NAME = "cbore_hole"
DESCRIPTION = "Create a box with a counterbored hole (wider at top, narrower through)"
PARAMETERS = {
    "length":          {"type": "float", "default": 60.0, "unit": "mm"},
    "width":           {"type": "float", "default": 60.0, "unit": "mm"},
    "height":          {"type": "float", "default": 20.0, "unit": "mm"},
    "diameter":        {"type": "float", "default": 6.0,  "unit": "mm"},
    "cbore_diameter":  {"type": "float", "default": 11.0, "unit": "mm"},
    "cbore_depth":     {"type": "float", "default": 5.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box({length}, {width}, {height})
    .faces(">Z")
    .workplane()
    .cboreHole({diameter}, {cbore_diameter}, {cbore_depth})
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        length=params.get("length", 60.0),
        width=params.get("width", 60.0),
        height=params.get("height", 20.0),
        diameter=params.get("diameter", 6.0),
        cbore_diameter=params.get("cbore_diameter", 11.0),
        cbore_depth=params.get("cbore_depth", 5.0),
    )
