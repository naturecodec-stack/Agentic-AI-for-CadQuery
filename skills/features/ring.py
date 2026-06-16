NAME = "ring"
DESCRIPTION = "Create a flat ring, spacer, or custom washer shape"
PARAMETERS = {
    "outer_diameter": {"type": "float", "default": 40.0, "unit": "mm"},
    "inner_diameter": {"type": "float", "default": 20.0, "unit": "mm"},
    "thickness":      {"type": "float", "default": 5.0,  "unit": "mm"},
    "num_holes":      {"type": "int",   "default": 0,    "desc": "optional radial holes in ring body"},
    "hole_diameter":  {"type": "float", "default": 4.0,  "unit": "mm"},
    "fillet_r":       {"type": "float", "default": 0.5,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
import math

od  = {outer_diameter}
id_ = {inner_diameter}
t   = {thickness}
nh  = {num_holes}
hd  = {hole_diameter}
fr  = {fillet_r}

outer = cq.Workplane("XY").circle(od / 2).extrude(t)
inner = cq.Workplane("XY").circle(id_ / 2).extrude(t)
result = outer.cut(inner)

if nh > 0:
    hole_r = (od / 2 + id_ / 2) / 2  # mid-ring radius
    pts = [(hole_r * math.cos(math.radians(360 * i / nh)),
            hole_r * math.sin(math.radians(360 * i / nh))) for i in range(nh)]
    result = (result
        .faces(">Z").workplane()
        .pushPoints(pts)
        .hole(hd))

if fr > 0:
    try:
        result = result.edges(">Z or <Z").fillet(fr)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        outer_diameter=float(params.get("outer_diameter", 40.0)),
        inner_diameter=float(params.get("inner_diameter", 20.0)),
        thickness=float(params.get("thickness", 5.0)),
        num_holes=int(params.get("num_holes", 0)),
        hole_diameter=float(params.get("hole_diameter", 4.0)),
        fillet_r=float(params.get("fillet_r", 0.5)),
    )
