NAME = "cone"
DESCRIPTION = "Create a cone or frustum (truncated cone) by lofting between two circles"
PARAMETERS = {
    "radius_bottom": {"type": "float", "default": 30.0, "unit": "mm"},
    "radius_top":    {"type": "float", "default": 0.0,  "unit": "mm", "desc": "0 = sharp point"},
    "height":        {"type": "float", "default": 50.0, "unit": "mm"},
    "hollow":        {"type": "bool",  "default": False, "desc": "hollow cone with wall_thickness"},
    "wall_thickness":{"type": "float", "default": 2.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

r_bot = {radius_bottom}
r_top = {radius_top}
h     = {height}
hollow = {hollow}
wall_t = {wall_thickness}

r_top_actual = max(r_top, 0.01)  # avoid degenerate loft

result = (
    cq.Workplane("XY")
    .circle(r_bot)
    .workplane(offset=h)
    .circle(r_top_actual)
    .loft()
)

if hollow and wall_t > 0:
    inner = (
        cq.Workplane("XY")
        .circle(max(r_bot - wall_t, 0.5))
        .workplane(offset=h - wall_t)
        .circle(max(r_top_actual - wall_t, 0.5))
        .loft()
    )
    result = result.cut(inner)

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        radius_bottom=float(params.get("radius_bottom", 30.0)),
        radius_top=float(params.get("radius_top", 0.0)),
        height=float(params.get("height", 50.0)),
        hollow=bool(params.get("hollow", False)),
        wall_thickness=float(params.get("wall_thickness", 2.0)),
    )
