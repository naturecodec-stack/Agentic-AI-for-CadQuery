NAME = "polar_array"
DESCRIPTION = "Create a disc or ring with features arranged in a polar/circular pattern using polarArray"
PARAMETERS = {
    "body_type":     {"type": "str",   "default": "disc",  "desc": "disc | ring | plate"},
    "outer_radius":  {"type": "float", "default": 50.0, "unit": "mm"},
    "inner_radius":  {"type": "float", "default": 15.0, "unit": "mm", "desc": "ring bore (disc ignored)"},
    "thickness":     {"type": "float", "default": 8.0,  "unit": "mm"},
    "feature":       {"type": "str",   "default": "hole",  "desc": "hole | slot | pocket | boss"},
    "feature_size":  {"type": "float", "default": 6.0,  "unit": "mm"},
    "feature_depth": {"type": "float", "default": 5.0,  "unit": "mm"},
    "pattern_radius":{"type": "float", "default": 35.0, "unit": "mm", "desc": "radius of the feature circle"},
    "count":         {"type": "int",   "default": 6},
    "start_angle":   {"type": "float", "default": 0.0},
}

TEMPLATE = """import cadquery as cq

btype    = "{body_type}"
r_outer  = {outer_radius}
r_inner  = {inner_radius}
t        = {thickness}
feat     = "{feature}"
fs       = {feature_size}
fd       = {feature_depth}
pr       = {pattern_radius}
count    = {count}
start_a  = {start_angle}

# Body
if btype == "ring":
    outer = cq.Workplane("XY").circle(r_outer).extrude(t)
    inner = cq.Workplane("XY").circle(r_inner).extrude(t)
    result = outer.cut(inner)
elif btype == "plate":
    result = cq.Workplane("XY").box(r_outer * 2, r_outer * 2, t)
else:  # disc
    result = cq.Workplane("XY").circle(r_outer).extrude(t)

# Apply feature in polar array
wp = result.faces(">Z").workplane().polarArray(pr, start_a, 360, count)

if feat == "hole":
    result = wp.hole(fs)
elif feat == "slot":
    result = wp.slot2D(fs * 2, fs, 0).cutBlind(-min(fd, t))
elif feat == "boss":
    import math
    for i in range(count):
        a = math.radians(start_a + 360 * i / count)
        x = pr * math.cos(a)
        y = pr * math.sin(a)
        boss = (cq.Workplane("XY")
            .circle(fs / 2).extrude(fd)
            .translate((x, y, t / 2)))
        result = result.union(boss)
else:  # pocket
    result = wp.rect(fs, fs).cutBlind(-min(fd, t * 0.8))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        body_type=str(params.get("body_type", "disc")),
        outer_radius=float(params.get("outer_radius", 50.0)),
        inner_radius=float(params.get("inner_radius", 15.0)),
        thickness=float(params.get("thickness", 8.0)),
        feature=str(params.get("feature", "hole")),
        feature_size=float(params.get("feature_size", 6.0)),
        feature_depth=float(params.get("feature_depth", 5.0)),
        pattern_radius=float(params.get("pattern_radius", 35.0)),
        count=int(params.get("count", 6)),
        start_angle=float(params.get("start_angle", 0.0)),
    )
