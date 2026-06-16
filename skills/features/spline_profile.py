NAME = "spline_profile"
DESCRIPTION = "Extrude a closed spline profile into a solid — organic blobs, custom cross-sections, freeform shapes"
PARAMETERS = {
    "profile_shape": {"type": "str",   "default": "teardrop", "desc": "teardrop | leaf | blob | star | custom"},
    "width":         {"type": "float", "default": 40.0, "unit": "mm"},
    "height":        {"type": "float", "default": 60.0, "unit": "mm"},
    "extrude_depth": {"type": "float", "default": 15.0, "unit": "mm"},
    "symmetric":     {"type": "bool",  "default": True},
    "fillet_r":      {"type": "float", "default": 0.0,  "unit": "mm", "desc": "top/bottom edge fillet"},
}

TEMPLATE = """import cadquery as cq
import math

shape   = "{profile_shape}"
w       = {width}
h       = {height}
depth   = {extrude_depth}
sym     = {symmetric}
fil_r   = {fillet_r}

hw = w / 2
hh = h / 2

if shape == "leaf":
    pts = [
        (0,    hh),
        (hw,   hh * 0.4),
        (hw * 0.8, 0),
        (hw,   -hh * 0.4),
        (0,    -hh),
        (-hw,  -hh * 0.4),
        (-hw * 0.8, 0),
        (-hw,  hh * 0.4),
        (0,    hh),
    ]

elif shape == "star":
    outer_r = hw
    inner_r = hw * 0.45
    n_points = 5
    pts = []
    for i in range(n_points * 2 + 1):
        r = outer_r if i % 2 == 0 else inner_r
        a = math.radians(90 + i * 180 / n_points)
        pts.append((r * math.cos(a) * w / h, r * math.sin(a)))
    pts.append(pts[0])

elif shape == "blob":
    # Irregular organic blob
    angles = [0, 45, 90, 135, 180, 225, 270, 315, 360]
    radii  = [hw, hw*0.75, hh, hw*0.85, hw*0.9, hw*0.7, hh*0.95, hw*0.8, hw]
    pts = [(radii[i] * math.cos(math.radians(angles[i])),
            radii[i] * math.sin(math.radians(angles[i])))
           for i in range(len(angles))]

else:  # teardrop (default)
    pts = [
        (0,     hh),
        (hw,    hh * 0.1),
        (hw * 0.6, -hh * 0.5),
        (0,    -hh),
        (-hw * 0.6, -hh * 0.5),
        (-hw,   hh * 0.1),
        (0,     hh),
    ]

result = (cq.Workplane("XY")
    .spline(pts, includeCurrent=False)
    .close()
    .extrude(depth))

if fil_r > 0:
    try:
        result = result.faces(">Z").edges().fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        profile_shape=str(params.get("profile_shape", "teardrop")),
        width=float(params.get("width", 40.0)),
        height=float(params.get("height", 60.0)),
        extrude_depth=float(params.get("extrude_depth", 15.0)),
        symmetric=bool(params.get("symmetric", True)),
        fillet_r=float(params.get("fillet_r", 0.0)),
    )
