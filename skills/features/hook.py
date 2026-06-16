NAME = "hook"
DESCRIPTION = "Create a wall hook or S-hook for hanging objects"
PARAMETERS = {
    "hook_type":     {"type": "str",   "default": "wall", "desc": "wall | s_hook"},
    "wire_diameter": {"type": "float", "default": 5.0,  "unit": "mm"},
    "hook_radius":   {"type": "float", "default": 15.0, "unit": "mm", "desc": "bend radius"},
    "hook_depth":    {"type": "float", "default": 40.0, "unit": "mm", "desc": "how far hook extends"},
    "back_height":   {"type": "float", "default": 50.0, "unit": "mm", "desc": "wall mount back plate height"},
    "back_width":    {"type": "float", "default": 30.0, "unit": "mm"},
    "back_thickness":{"type": "float", "default": 5.0,  "unit": "mm"},
    "mount_hole_d":  {"type": "float", "default": 4.5,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
import math

htype  = "{hook_type}"
wd     = {wire_diameter}
hr     = {hook_radius}
hd     = {hook_depth}
bh     = {back_height}
bw     = {back_width}
bt     = {back_thickness}
mhd    = {mount_hole_d}

if htype == "s_hook":
    # S-hook: two semicircular bends
    pts = []
    steps = 18
    for i in range(steps + 1):
        a = math.radians(i * 180 / steps)
        pts.append((hr * math.sin(a), hr * math.cos(a) + hr))
    for i in range(steps + 1):
        a = math.radians(180 + i * 180 / steps)
        pts.append((hr * math.sin(a), hr * math.cos(a) - hr))

    spine = (cq.Workplane("XY")
        .polyline(pts)
        .close())
    result = spine.sweep(cq.Workplane("XY").circle(wd / 2))
else:
    # Wall hook: back plate + curved hook arm
    back = cq.Workplane("XY").box(bw, bt, bh)

    # Hook arm sweeps forward then curves down
    arm_pts = [
        (0, 0),
        (hd * 0.6, 0),
        (hd, -hd * 0.3),
        (hd, -hd * 0.7),
    ]
    arm = (cq.Workplane("XZ")
        .spline(arm_pts, includeCurrent=False))
    arm_profile = cq.Workplane("XY").circle(wd / 2)
    arm_solid = arm_profile.sweep(arm)
    arm_solid = arm_solid.translate((0, bt / 2, 0))

    result = back.union(arm_solid)

    # Mounting holes
    if mhd > 0:
        result = (result
            .faces(">Y").workplane()
            .pushPoints([(0, bh / 4), (0, -bh / 4)])
            .hole(mhd, depth=bt))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        hook_type=str(params.get("hook_type", "wall")),
        wire_diameter=float(params.get("wire_diameter", 5.0)),
        hook_radius=float(params.get("hook_radius", 15.0)),
        hook_depth=float(params.get("hook_depth", 40.0)),
        back_height=float(params.get("back_height", 50.0)),
        back_width=float(params.get("back_width", 30.0)),
        back_thickness=float(params.get("back_thickness", 5.0)),
        mount_hole_d=float(params.get("mount_hole_d", 4.5)),
    )
