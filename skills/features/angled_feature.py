NAME = "angled_feature"
DESCRIPTION = "Add a feature (hole, slot, pocket) on an angled or tilted workplane — angled holes, chamfered bores"
PARAMETERS = {
    "body_length":   {"type": "float", "default": 80.0,  "unit": "mm"},
    "body_width":    {"type": "float", "default": 50.0,  "unit": "mm"},
    "body_height":   {"type": "float", "default": 30.0,  "unit": "mm"},
    "feature":       {"type": "str",   "default": "hole", "desc": "hole | slot | pocket"},
    "feature_size":  {"type": "float", "default": 8.0,   "unit": "mm"},
    "tilt_axis":     {"type": "str",   "default": "Y",    "desc": "axis to tilt around: X | Y"},
    "tilt_angle":    {"type": "float", "default": 30.0,  "desc": "tilt angle in degrees"},
    "feature_depth": {"type": "float", "default": 20.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

bl = {body_length}
bw = {body_width}
bh = {body_height}
feat   = "{feature}"
fs     = {feature_size}
t_axis = "{tilt_axis}"
t_ang  = {tilt_angle}
fd     = {feature_depth}

# Base body
result = cq.Workplane("XY").box(bl, bw, bh)

# Angled workplane on top face
rotate = (t_ang, 0, 0) if t_axis == "X" else (0, t_ang, 0)

angled_wp = (result
    .faces(">Z")
    .workplane()
    .transformed(rotate=cq.Vector(*rotate)))

if feat == "slot":
    result = angled_wp.slot2D(fs * 2, fs, 0).cutBlind(-fd)
elif feat == "pocket":
    result = angled_wp.rect(fs, fs * 1.5).cutBlind(-fd)
else:  # hole
    result = angled_wp.hole(fs, depth=fd)

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        body_length=float(params.get("body_length", 80.0)),
        body_width=float(params.get("body_width", 50.0)),
        body_height=float(params.get("body_height", 30.0)),
        feature=str(params.get("feature", "hole")),
        feature_size=float(params.get("feature_size", 8.0)),
        tilt_axis=str(params.get("tilt_axis", "Y")),
        tilt_angle=float(params.get("tilt_angle", 30.0)),
        feature_depth=float(params.get("feature_depth", 20.0)),
    )
