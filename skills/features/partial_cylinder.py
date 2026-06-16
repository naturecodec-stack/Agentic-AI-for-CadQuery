NAME = "partial_cylinder"
DESCRIPTION = "Create a partial cylinder, arc solid, or curved wall segment"
PARAMETERS = {
    "radius":       {"type": "float", "default": 40.0, "unit": "mm"},
    "height":       {"type": "float", "default": 30.0, "unit": "mm"},
    "arc_angle":    {"type": "float", "default": 180.0,"desc": "sweep angle in degrees (360=full cylinder)"},
    "start_angle":  {"type": "float", "default": 0.0,  "desc": "start angle in degrees"},
    "wall_thickness":{"type":"float", "default": 0.0,  "unit": "mm", "desc": "0 = solid, >0 = hollow curved wall"},
    "fillet_r":     {"type": "float", "default": 1.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
import math

r       = {radius}
h       = {height}
arc     = {arc_angle}
start   = {start_angle}
wall_t  = {wall_thickness}
fil_r   = {fillet_r}

if arc >= 360:
    # Full cylinder
    result = cq.Workplane("XY").cylinder(h, r)
    if wall_t > 0:
        result = result.cut(
            cq.Workplane("XY").cylinder(h, max(r - wall_t, 1)))
else:
    # Partial cylinder via revolve
    if wall_t > 0:
        # Hollow arc wall: rectangle profile revolved
        profile = (cq.Workplane("XZ")
            .moveTo(r - wall_t, 0)
            .lineTo(r,          0)
            .lineTo(r,          h)
            .lineTo(r - wall_t, h)
            .close())
    else:
        # Solid sector: triangle/pie profile revolved
        profile = (cq.Workplane("XZ")
            .moveTo(0, 0)
            .lineTo(r, 0)
            .lineTo(r, h)
            .lineTo(0, h)
            .close())

    result = profile.revolve(arc, (0, 0, 0), (0, 0, 1))

    # Rotate to start angle
    if start != 0:
        result = result.rotate((0, 0, 0), (0, 0, 1), start)

if fil_r > 0:
    try:
        result = result.edges(">Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        radius=float(params.get("radius", 40.0)),
        height=float(params.get("height", 30.0)),
        arc_angle=float(params.get("arc_angle", 180.0)),
        start_angle=float(params.get("start_angle", 0.0)),
        wall_thickness=float(params.get("wall_thickness", 0.0)),
        fillet_r=float(params.get("fillet_r", 1.0)),
    )
