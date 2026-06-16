NAME = "grid_holes"
DESCRIPTION = "Create a plate with a rectangular grid array of holes"
PARAMETERS = {
    "length":        {"type": "float", "default": 80.0, "unit": "mm"},
    "width":         {"type": "float", "default": 60.0, "unit": "mm"},
    "height":        {"type": "float", "default": 8.0,  "unit": "mm"},
    "hole_diameter": {"type": "float", "default": 5.0,  "unit": "mm"},
    "x_spacing":     {"type": "float", "default": 20.0, "unit": "mm"},
    "y_spacing":     {"type": "float", "default": 20.0, "unit": "mm"},
    "x_count":       {"type": "int",   "default": 3},
    "y_count":       {"type": "int",   "default": 2},
}

TEMPLATE = """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box({length}, {width}, {height})
    .faces(">Z")
    .workplane()
    .rarray({x_spacing}, {y_spacing}, {x_count}, {y_count})
    .hole({hole_diameter})
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        length=params.get("length", 80.0),
        width=params.get("width", 60.0),
        height=params.get("height", 8.0),
        hole_diameter=params.get("hole_diameter", 5.0),
        x_spacing=params.get("x_spacing", 20.0),
        y_spacing=params.get("y_spacing", 20.0),
        x_count=params.get("x_count", 3),
        y_count=params.get("y_count", 2),
    )
