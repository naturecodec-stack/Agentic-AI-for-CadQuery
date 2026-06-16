NAME = "cable_clip"
DESCRIPTION = "Create a cable management clip that snaps over a wire or cable bundle"
PARAMETERS = {
    "cable_diameter": {"type": "float", "default": 8.0,  "unit": "mm"},
    "wall_thickness": {"type": "float", "default": 2.0,  "unit": "mm"},
    "clip_width":     {"type": "float", "default": 10.0, "unit": "mm"},
    "base_height":    {"type": "float", "default": 5.0,  "unit": "mm"},
    "mount_hole_d":   {"type": "float", "default": 3.5,  "unit": "mm", "desc": "screw hole diameter (0=none)"},
    "gap_width":      {"type": "float", "default": 5.0,  "unit": "mm", "desc": "snap-in opening width"},
}

TEMPLATE = """import cadquery as cq
import math

cd  = {cable_diameter}
wt  = {wall_thickness}
cw  = {clip_width}
bh  = {base_height}
mhd = {mount_hole_d}
gap = {gap_width}

r_outer = cd / 2 + wt
r_inner = cd / 2

# Outer and inner cylinders for the clip body
outer = cq.Workplane("XY").circle(r_outer).extrude(cw)
inner = cq.Workplane("XY").circle(r_inner).extrude(cw)
clip_ring = outer.cut(inner)

# Cut the opening gap at the top
gap_cut = (cq.Workplane("XY")
    .box(gap, r_outer * 2 + 1, cw)
    .translate((0, r_outer / 2 + 0.5, cw / 2)))
clip_ring = clip_ring.cut(gap_cut)

# Base/mounting tab
base = (cq.Workplane("XY")
    .box(r_outer * 2 + wt * 2, bh, cw)
    .translate((0, -(r_outer + bh / 2), cw / 2)))
result = clip_ring.union(base)

# Mounting hole through base
if mhd > 0:
    result = (result
        .faces(">Z").workplane()
        .pushPoints([(0, -(r_outer + bh / 2))])
        .hole(mhd))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        cable_diameter=float(params.get("cable_diameter", 8.0)),
        wall_thickness=float(params.get("wall_thickness", 2.0)),
        clip_width=float(params.get("clip_width", 10.0)),
        base_height=float(params.get("base_height", 5.0)),
        mount_hole_d=float(params.get("mount_hole_d", 3.5)),
        gap_width=float(params.get("gap_width", 5.0)),
    )
