NAME = "offset_profile"
DESCRIPTION = "Create a shape from an offset 2D profile — thick outlines, frames, gaskets, border shapes"
PARAMETERS = {
    "base_shape":    {"type": "str",   "default": "rect",  "desc": "rect | circle | hexagon | triangle"},
    "outer_size":    {"type": "float", "default": 60.0, "unit": "mm"},
    "offset_amount": {"type": "float", "default": -8.0, "unit": "mm", "desc": "negative=inward, positive=outward"},
    "height":        {"type": "float", "default": 5.0,  "unit": "mm"},
    "corner_radius": {"type": "float", "default": 4.0,  "unit": "mm", "desc": "for rect shape"},
    "fillet_r":      {"type": "float", "default": 1.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

bshape  = "{base_shape}"
os_     = {outer_size}
ofs     = {offset_amount}
h       = {height}
cr      = {corner_radius}
fil_r   = {fillet_r}

r = os_ / 2

if bshape == "circle":
    outer = cq.Workplane("XY").circle(r).extrude(h)
    if ofs < 0:
        inner = cq.Workplane("XY").circle(max(r + ofs, 1)).extrude(h)
        result = outer.cut(inner)
    else:
        result = cq.Workplane("XY").circle(r + ofs).extrude(h).cut(
            cq.Workplane("XY").circle(r).extrude(h))

elif bshape == "hexagon":
    outer = cq.Workplane("XY").polygon(6, os_).extrude(h)
    if ofs < 0:
        inner = cq.Workplane("XY").polygon(6, max(os_ + ofs * 2, 1)).extrude(h)
        result = outer.cut(inner)
    else:
        result = cq.Workplane("XY").polygon(6, os_ + abs(ofs) * 2).extrude(h).cut(outer)

elif bshape == "triangle":
    import math
    tri_r = os_ / math.sqrt(3)
    outer = cq.Workplane("XY").polygon(3, os_).extrude(h)
    if ofs < 0:
        inner = cq.Workplane("XY").polygon(3, max(os_ + ofs * 2, 1)).extrude(h)
        result = outer.cut(inner)
    else:
        result = outer

else:  # rect
    outer = cq.Workplane("XY").rect(os_, os_).extrude(h)
    inner_s = max(os_ + ofs * 2, 1)
    inner = cq.Workplane("XY").rect(inner_s, inner_s).extrude(h)
    if ofs < 0:
        result = outer.cut(inner)
    else:
        result = cq.Workplane("XY").rect(os_ - ofs * 2, os_ - ofs * 2).extrude(h).cut(outer)
        result = outer  # fallback

if fil_r > 0:
    try:
        result = result.edges("|Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        base_shape=str(params.get("base_shape", "rect")),
        outer_size=float(params.get("outer_size", 60.0)),
        offset_amount=float(params.get("offset_amount", -8.0)),
        height=float(params.get("height", 5.0)),
        corner_radius=float(params.get("corner_radius", 4.0)),
        fillet_r=float(params.get("fillet_r", 1.0)),
    )
