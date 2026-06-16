NAME = "spline_surface"
DESCRIPTION = "Loft between multiple spline profiles at different heights — vases, organic bodies, transition shapes"
PARAMETERS = {
    "shape":      {"type": "str",   "default": "vase",   "desc": "vase | twist | diamond | hourglass"},
    "height":     {"type": "float", "default": 80.0,  "unit": "mm"},
    "max_radius": {"type": "float", "default": 30.0,  "unit": "mm"},
    "min_radius": {"type": "float", "default": 10.0,  "unit": "mm"},
    "num_sections":{"type": "int",  "default": 5,     "desc": "number of loft cross-sections"},
    "hollow":     {"type": "bool",  "default": False},
    "wall_t":     {"type": "float", "default": 2.5,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
import math

shape    = "{shape}"
h        = {height}
r_max    = {max_radius}
r_min    = {min_radius}
sections = {num_sections}
hollow   = {hollow}
wall_t   = {wall_t}

def radius_at(t, shape):
    \"\"\"t = 0..1 from bottom to top\"\"\"
    if shape == "hourglass":
        return r_min + (r_max - r_min) * (2 * abs(t - 0.5)) ** 1.5
    elif shape == "diamond":
        return r_min + (r_max - r_min) * math.sin(math.pi * t)
    elif shape == "twist":
        return r_min + (r_max - r_min) * math.sin(math.pi * t)
    else:  # vase
        return r_min + (r_max - r_min) * math.sin(math.pi * t ** 0.7)

def make_section_pts(r, twist_angle=0, n=12):
    pts = []
    for i in range(n + 1):
        a = math.radians(360 * i / n + twist_angle)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts

# Build loft by sweeping through section profiles
wp = cq.Workplane("XY")

for i in range(sections + 1):
    t = i / sections
    z = h * t
    r = radius_at(t, shape)
    twist = (t * 45) if shape == "twist" else 0
    pts = make_section_pts(r, twist)

    if i == 0:
        wp = wp.spline(pts).close()
    else:
        wp = wp.workplane(offset=(h / sections)).spline(pts).close()

result = wp.loft(ruled=False)

if hollow:
    # Shell inward
    try:
        result = result.faces(">Z").shell(-wall_t)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        shape=str(params.get("shape", "vase")),
        height=float(params.get("height", 80.0)),
        max_radius=float(params.get("max_radius", 30.0)),
        min_radius=float(params.get("min_radius", 10.0)),
        num_sections=int(params.get("num_sections", 5)),
        hollow=bool(params.get("hollow", False)),
        wall_t=float(params.get("wall_t", 2.5)),
    )
