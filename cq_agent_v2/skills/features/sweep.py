NAME = "sweep"
DESCRIPTION = "Sweep a circular or rectangular profile along a 3D spline path to make a pipe, tube, or curved rod"
PARAMETERS = {
    "profile":        {"type": "str",   "default": "circle", "desc": "circle | rect"},
    "radius":         {"type": "float", "default": 3.0,  "unit": "mm", "desc": "circle radius (profile=circle)"},
    "width":          {"type": "float", "default": 6.0,  "unit": "mm", "desc": "rect width  (profile=rect)"},
    "height":         {"type": "float", "default": 4.0,  "unit": "mm", "desc": "rect height (profile=rect)"},
    "p0":             {"type": "list",  "default": [0, 0, 0],  "desc": "path start  [x,y,z]"},
    "p1":             {"type": "list",  "default": [10, 0, 20], "desc": "path mid   [x,y,z]"},
    "p2":             {"type": "list",  "default": [20, 0, 0],  "desc": "path end   [x,y,z]"},
    "is_frenet":      {"type": "bool",  "default": True},
}

TEMPLATE = """import cadquery as cq

# 3-point 3-D spline path
path = cq.Wire.makeSpline([
    cq.Vector{p0},
    cq.Vector{p1},
    cq.Vector{p2},
])

# Profile perpendicular to path start
profile_type = "{profile}"
if profile_type == "rect":
    profile = cq.Workplane("XY").rect({width}, {height})
else:
    profile = cq.Workplane("XY").circle({radius})

result = profile.sweep(cq.Workplane(obj=path), isFrenet={is_frenet})
show_object(result)
"""


def render(params: dict) -> str:
    def _vec(key, default):
        v = params.get(key, default)
        if isinstance(v, (list, tuple)) and len(v) == 3:
            return f"({v[0]}, {v[1]}, {v[2]})"
        return str(default).replace("[", "(").replace("]", ")")

    return TEMPLATE.format(
        profile=str(params.get("profile", "circle")),
        radius=float(params.get("radius", 3.0)),
        width=float(params.get("width", 6.0)),
        height=float(params.get("height", 4.0)),
        p0=_vec("p0", [0, 0, 0]),
        p1=_vec("p1", [10, 0, 20]),
        p2=_vec("p2", [20, 0, 0]),
        is_frenet=bool(params.get("is_frenet", True)),
    )
