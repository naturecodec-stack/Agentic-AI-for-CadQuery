NAME = "bezier_profile"
DESCRIPTION = "Extrude a Bezier curve profile into a solid — smooth custom cross-sections"
PARAMETERS = {
    "profile_type": {"type": "str",   "default": "wave_fin", "desc": "wave_fin | petal | arch | freeform"},
    "width":        {"type": "float", "default": 50.0, "unit": "mm"},
    "height":       {"type": "float", "default": 40.0, "unit": "mm"},
    "depth":        {"type": "float", "default": 10.0, "unit": "mm"},
    "fillet_r":     {"type": "float", "default": 0.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

ptype  = "{profile_type}"
w      = {width}
h      = {height}
depth  = {depth}
fil_r  = {fillet_r}

hw = w / 2
hh = h / 2

if ptype == "petal":
    # Petal shape: two bezier curves meeting at tip and base
    pts_right = [(0, -hh), (hw * 0.8, -hh * 0.3), (hw, 0), (hw * 0.8, hh * 0.3), (0, hh)]
    pts_left  = [(0,  hh), (-hw * 0.8, hh * 0.3), (-hw, 0), (-hw * 0.8, -hh * 0.3), (0, -hh)]
    result = (cq.Workplane("XY")
        .bezier(pts_right)
        .bezier(pts_left)
        .extrude(depth))

elif ptype == "arch":
    # Arch: flat bottom, bezier curved top
    pts_top = [(-hw, 0), (-hw * 0.5, hh * 1.2), (0, hh * 1.4), (hw * 0.5, hh * 1.2), (hw, 0)]
    result = (cq.Workplane("XY")
        .moveTo(-hw, 0)
        .bezier(pts_top)
        .lineTo(hw, 0)
        .lineTo(-hw, 0)
        .close()
        .extrude(depth))

elif ptype == "freeform":
    # Freeform blob using bezier
    ctrl_pts = [
        (0,   hh),
        (hw,  hh * 0.5),
        (hw * 1.2, 0),
        (hw,  -hh * 0.5),
        (hw * 0.3, -hh),
        (-hw * 0.3, -hh),
        (-hw, -hh * 0.5),
        (-hw * 1.2, 0),
        (-hw, hh * 0.5),
        (0,   hh),
    ]
    result = (cq.Workplane("XY")
        .bezier(ctrl_pts)
        .close()
        .extrude(depth))

else:  # wave_fin
    # Wave profile: bezier S-curve extruded into a thin fin
    pts = [
        (-hw, -hh),
        (-hw * 0.3, -hh * 0.3),
        (0,    0),
        (hw * 0.3, hh * 0.3),
        (hw,   hh),
    ]
    result = (cq.Workplane("XY")
        .moveTo(-hw, -hh)
        .bezier(pts)
        .lineTo(hw, -hh)
        .close()
        .extrude(depth))

if fil_r > 0:
    try:
        result = result.edges(">Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        profile_type=str(params.get("profile_type", "wave_fin")),
        width=float(params.get("width", 50.0)),
        height=float(params.get("height", 40.0)),
        depth=float(params.get("depth", 10.0)),
        fillet_r=float(params.get("fillet_r", 0.0)),
    )
