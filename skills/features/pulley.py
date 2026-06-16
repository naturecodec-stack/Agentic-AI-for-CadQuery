NAME = "pulley"
DESCRIPTION = "Create a V-groove or flat belt pulley with hub and bore"
PARAMETERS = {
    "outer_diameter": {"type": "float", "default": 60.0,  "unit": "mm"},
    "groove_depth":   {"type": "float", "default": 6.0,   "unit": "mm"},
    "groove_angle":   {"type": "float", "default": 40.0,  "desc": "V-groove angle in degrees (0 = flat)"},
    "width":          {"type": "float", "default": 20.0,  "unit": "mm"},
    "hub_diameter":   {"type": "float", "default": 20.0,  "unit": "mm"},
    "hub_height":     {"type": "float", "default": 30.0,  "unit": "mm"},
    "bore_diameter":  {"type": "float", "default": 8.0,   "unit": "mm"},
    "num_spokes":     {"type": "int",   "default": 0,     "desc": "0 = solid disc, >0 = spoked"},
    "fillet_r":       {"type": "float", "default": 1.0,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
import math

od   = {outer_diameter}
gd   = {groove_depth}
ga   = {groove_angle}
w    = {width}
hd   = {hub_diameter}
hh   = {hub_height}
bore = {bore_diameter}
spokes = {num_spokes}
fil_r  = {fillet_r}

r = od / 2

# Rim profile (revolve around Z axis)
half_w = w / 2
groove_r = r - gd

if ga > 0:
    groove_top_offset = gd * math.tan(math.radians(ga / 2))
    profile_pts = [
        (hd/2, -hh/2),
        (hd/2,  hh/2),
        (r,     hh/2),
        (r,     half_w),
        (groove_r + groove_top_offset, half_w),
        (groove_r, 0),
        (groove_r + groove_top_offset, -half_w),
        (r,    -half_w),
        (r,    -hh/2),
    ]
else:
    profile_pts = [
        (hd/2, -hh/2),
        (hd/2,  hh/2),
        (r,     hh/2),
        (r,     half_w),
        (groove_r, half_w),
        (groove_r, -half_w),
        (r,    -half_w),
        (r,    -hh/2),
    ]

result = (
    cq.Workplane("XZ")
    .polyline(profile_pts)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# Central bore
if bore > 0:
    result = result.faces(">Z").workplane().hole(bore, depth=hh)

if fil_r > 0:
    try:
        result = result.edges(">Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        outer_diameter=float(params.get("outer_diameter", 60.0)),
        groove_depth=float(params.get("groove_depth", 6.0)),
        groove_angle=float(params.get("groove_angle", 40.0)),
        width=float(params.get("width", 20.0)),
        hub_diameter=float(params.get("hub_diameter", 20.0)),
        hub_height=float(params.get("hub_height", 30.0)),
        bore_diameter=float(params.get("bore_diameter", 8.0)),
        num_spokes=int(params.get("num_spokes", 0)),
        fillet_r=float(params.get("fillet_r", 1.0)),
    )
