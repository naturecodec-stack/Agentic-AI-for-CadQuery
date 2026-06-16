NAME = "torus"
DESCRIPTION = "Create a torus (donut / ring shape) by revolving a circle around an axis"
PARAMETERS = {
    "major_radius": {"type": "float", "default": 30.0, "unit": "mm", "desc": "distance from centre of tube to centre of torus"},
    "minor_radius": {"type": "float", "default": 8.0,  "unit": "mm", "desc": "radius of the tube cross-section"},
    "angle":        {"type": "float", "default": 360.0,"desc": "sweep angle (360 = full torus)"},
}

TEMPLATE = """import cadquery as cq

major_r = {major_radius}
minor_r = {minor_radius}
angle   = {angle}

result = (
    cq.Workplane("XZ")
    .center(major_r, 0)
    .circle(minor_r)
    .revolve(angle, (0, 0, 0), (0, 1, 0))
)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        major_radius=float(params.get("major_radius", 30.0)),
        minor_radius=float(params.get("minor_radius", 8.0)),
        angle=float(params.get("angle", 360.0)),
    )
