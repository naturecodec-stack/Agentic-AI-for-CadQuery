NAME = "ellipse"
DESCRIPTION = "Create an ellipse or elliptical tube/cylinder extruded into a solid"
PARAMETERS = {
    "x_radius":   {"type": "float", "default": 30.0, "unit": "mm"},
    "y_radius":   {"type": "float", "default": 20.0, "unit": "mm"},
    "height":     {"type": "float", "default": 15.0, "unit": "mm"},
    "hollow":     {"type": "bool",  "default": False},
    "wall_t":     {"type": "float", "default": 3.0,  "unit": "mm"},
    "fillet_r":   {"type": "float", "default": 0.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

xr     = {x_radius}
yr     = {y_radius}
h      = {height}
hollow = {hollow}
wall_t = {wall_t}
fil_r  = {fillet_r}

result = cq.Workplane("XY").ellipse(xr, yr).extrude(h)

if hollow:
    inner = cq.Workplane("XY").ellipse(max(xr - wall_t, 1), max(yr - wall_t, 1)).extrude(h)
    result = result.cut(inner)

if fil_r > 0:
    try:
        result = result.faces(">Z").edges().fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        x_radius=float(params.get("x_radius", 30.0)),
        y_radius=float(params.get("y_radius", 20.0)),
        height=float(params.get("height", 15.0)),
        hollow=bool(params.get("hollow", False)),
        wall_t=float(params.get("wall_t", 3.0)),
        fillet_r=float(params.get("fillet_r", 0.0)),
    )
