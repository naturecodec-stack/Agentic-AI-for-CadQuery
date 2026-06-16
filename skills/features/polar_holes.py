NAME = "polar_holes"
DESCRIPTION = "Create a circular plate or disc with holes arranged in a polar/circular pattern"
PARAMETERS = {
    "plate_radius":  {"type": "float", "default": 40.0, "unit": "mm"},
    "plate_height":  {"type": "float", "default": 8.0,  "unit": "mm"},
    "hole_diameter": {"type": "float", "default": 5.0,  "unit": "mm"},
    "hole_count":    {"type": "int",   "default": 6},
    "hole_radius":   {"type": "float", "default": 28.0, "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle({plate_radius})
    .extrude({plate_height})
    .faces(">Z")
    .workplane()
    .polarArray({hole_radius}, 0, 360, {hole_count})
    .hole({hole_diameter})
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        plate_radius=params.get("plate_radius", 40.0),
        plate_height=params.get("plate_height", 8.0),
        hole_diameter=params.get("hole_diameter", 5.0),
        hole_count=params.get("hole_count", 6),
        hole_radius=params.get("hole_radius", 28.0),
    )
