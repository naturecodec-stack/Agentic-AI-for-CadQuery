NAME = "rectangular_array"
DESCRIPTION = "Create a plate with a rectangular grid array of holes, bosses, or cut pockets using rarray"
PARAMETERS = {
    "plate_length":  {"type": "float", "default": 120.0, "unit": "mm"},
    "plate_width":   {"type": "float", "default": 80.0,  "unit": "mm"},
    "plate_thickness":{"type":"float", "default": 8.0,   "unit": "mm"},
    "feature":       {"type": "str",   "default": "hole", "desc": "hole | boss | pocket | slot"},
    "feature_size":  {"type": "float", "default": 6.0,   "unit": "mm", "desc": "hole diameter or boss diameter"},
    "feature_depth": {"type": "float", "default": 5.0,   "unit": "mm", "desc": "pocket/blind hole depth"},
    "x_spacing":     {"type": "float", "default": 25.0,  "unit": "mm"},
    "y_spacing":     {"type": "float", "default": 20.0,  "unit": "mm"},
    "x_count":       {"type": "int",   "default": 4},
    "y_count":       {"type": "int",   "default": 3},
    "fillet_r":      {"type": "float", "default": 2.0,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

pl   = {plate_length}
pw   = {plate_width}
pt   = {plate_thickness}
feat = "{feature}"
fs   = {feature_size}
fd   = {feature_depth}
xs   = {x_spacing}
ys   = {y_spacing}
nx   = {x_count}
ny   = {y_count}
fil_r = {fillet_r}

result = cq.Workplane("XY").box(pl, pw, pt)

wp = result.faces(">Z").workplane().rarray(xs, ys, nx, ny)

if feat == "hole":
    result = wp.hole(fs)
elif feat == "boss":
    # Cut the bosses out of a union
    boss_h = fd
    for xi in range(nx):
        for yi in range(ny):
            x = -xs * (nx - 1) / 2 + xi * xs
            y = -ys * (ny - 1) / 2 + yi * ys
            boss = (cq.Workplane("XY")
                .circle(fs / 2).extrude(boss_h)
                .translate((x, y, pt / 2)))
            result = result.union(boss)
elif feat == "slot":
    result = wp.slot2D(fs * 2, fs, 0).cutBlind(-fd)
else:  # pocket
    result = wp.rect(fs, fs).cutBlind(-fd)

if fil_r > 0:
    try:
        result = result.edges("|Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        plate_length=float(params.get("plate_length", 120.0)),
        plate_width=float(params.get("plate_width", 80.0)),
        plate_thickness=float(params.get("plate_thickness", 8.0)),
        feature=str(params.get("feature", "hole")),
        feature_size=float(params.get("feature_size", 6.0)),
        feature_depth=float(params.get("feature_depth", 5.0)),
        x_spacing=float(params.get("x_spacing", 25.0)),
        y_spacing=float(params.get("y_spacing", 20.0)),
        x_count=int(params.get("x_count", 4)),
        y_count=int(params.get("y_count", 3)),
        fillet_r=float(params.get("fillet_r", 2.0)),
    )
