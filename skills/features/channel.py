NAME = "channel"
DESCRIPTION = "Create a U-channel, C-channel, or L-angle structural profile extrusion"
PARAMETERS = {
    "profile":    {"type": "str",   "default": "U",   "desc": "U | C | L"},
    "width":      {"type": "float", "default": 40.0,  "unit": "mm", "desc": "outer width"},
    "height":     {"type": "float", "default": 25.0,  "unit": "mm", "desc": "flange height"},
    "thickness":  {"type": "float", "default": 3.0,   "unit": "mm", "desc": "wall thickness"},
    "length":     {"type": "float", "default": 100.0, "unit": "mm"},
    "fillet_r":   {"type": "float", "default": 1.5,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

profile   = "{profile}"
w  = {width}
h  = {height}
t  = {thickness}
ln = {length}
fr = {fillet_r}

if profile == "L":
    # L angle: horizontal flange + vertical flange
    horiz = cq.Workplane("XY").box(w, ln, t).translate((0, 0, t/2))
    vert  = cq.Workplane("XY").box(t, ln, h).translate((-w/2 + t/2, 0, t + h/2))
    result = horiz.union(vert)
elif profile == "C":
    # C-channel: web + two flanges (open at front)
    web   = cq.Workplane("XY").box(t, ln, h).translate((-w/2 + t/2, 0, h/2))
    top   = cq.Workplane("XY").box(w, ln, t).translate((0, 0, h - t/2))
    bot   = cq.Workplane("XY").box(w, ln, t).translate((0, 0, t/2))
    result = web.union(top).union(bot)
else:  # U channel
    left  = cq.Workplane("XY").box(t, ln, h).translate((-w/2 + t/2, 0, h/2))
    right = cq.Workplane("XY").box(t, ln, h).translate(( w/2 - t/2, 0, h/2))
    base  = cq.Workplane("XY").box(w, ln, t).translate((0, 0, t/2))
    result = left.union(right).union(base)

if fr > 0:
    try:
        result = result.edges("|Y").fillet(fr)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        profile=str(params.get("profile", "U")),
        width=float(params.get("width", 40.0)),
        height=float(params.get("height", 25.0)),
        thickness=float(params.get("thickness", 3.0)),
        length=float(params.get("length", 100.0)),
        fillet_r=float(params.get("fillet_r", 1.5)),
    )
