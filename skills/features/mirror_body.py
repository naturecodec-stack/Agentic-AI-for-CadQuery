NAME = "mirror_body"
DESCRIPTION = "Create a symmetric body by building half and mirroring — L-bracket, symmetric enclosure, symmetric clip"
PARAMETERS = {
    "base_shape":   {"type": "str",   "default": "bracket", "desc": "bracket | fin | clip | custom_half"},
    "mirror_plane": {"type": "str",   "default": "XZ",      "desc": "XZ | YZ | XY"},
    "width":        {"type": "float", "default": 60.0, "unit": "mm"},
    "height":       {"type": "float", "default": 40.0, "unit": "mm"},
    "depth":        {"type": "float", "default": 5.0,  "unit": "mm"},
    "fillet_r":     {"type": "float", "default": 2.0,  "unit": "mm"},
    "hole_d":       {"type": "float", "default": 5.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

shape   = "{base_shape}"
plane   = "{mirror_plane}"
w       = {width}
h       = {height}
d       = {depth}
fil_r   = {fillet_r}
hole_d  = {hole_d}

hw = w / 2

if shape == "fin":
    # Triangular fin — half then mirror
    half = (cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(hw, 0)
        .lineTo(0, h)
        .close()
        .extrude(d))

elif shape == "clip":
    # C-clip half
    half = (cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(hw, 0)
        .lineTo(hw, d)
        .lineTo(d, d)
        .lineTo(d, h - d)
        .lineTo(hw, h - d)
        .lineTo(hw, h)
        .lineTo(0, h)
        .close()
        .extrude(d))

else:  # bracket
    # L-shaped bracket half
    base_half = cq.Workplane("XY").box(hw, d, d).translate((hw/2, 0, d/2))
    wall = cq.Workplane("XY").box(d, d, h).translate((d/2, 0, h/2))
    half = base_half.union(wall)
    if hole_d > 0:
        half = (half
            .faces(">Z").workplane()
            .pushPoints([(hw * 0.6, 0)])
            .hole(hole_d))

# Mirror
result = half.mirror(plane)

if fil_r > 0:
    try:
        result = result.edges("|Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        base_shape=str(params.get("base_shape", "bracket")),
        mirror_plane=str(params.get("mirror_plane", "XZ")),
        width=float(params.get("width", 60.0)),
        height=float(params.get("height", 40.0)),
        depth=float(params.get("depth", 5.0)),
        fillet_r=float(params.get("fillet_r", 2.0)),
        hole_d=float(params.get("hole_d", 5.0)),
    )
