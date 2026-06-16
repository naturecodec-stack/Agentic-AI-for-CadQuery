NAME = "spline_path_sweep"
DESCRIPTION = "Sweep a circular or rectangular profile along a smooth spline path — pipes, tubes, curved rods, cables"
PARAMETERS = {
    "profile":       {"type": "str",   "default": "circle", "desc": "circle | rect"},
    "profile_r":     {"type": "float", "default": 4.0,  "unit": "mm", "desc": "radius (circle) or half-width (rect)"},
    "profile_h":     {"type": "float", "default": 6.0,  "unit": "mm", "desc": "height for rect profile"},
    "path_shape":    {"type": "str",   "default": "s_curve", "desc": "s_curve | wave | arc | spiral"},
    "path_length":   {"type": "float", "default": 100.0, "unit": "mm"},
    "path_amplitude":{"type": "float", "default": 20.0, "unit": "mm", "desc": "side-to-side amplitude"},
    "num_waves":     {"type": "int",   "default": 2,    "desc": "number of wave cycles (wave shape only)"},
    "isFrenet":      {"type": "bool",  "default": True, "desc": "Frenet frame — keeps profile perpendicular to path"},
}

TEMPLATE = """import cadquery as cq
import math

profile      = "{profile}"
pr           = {profile_r}
ph           = {profile_h}
path_shape   = "{path_shape}"
path_len     = {path_length}
amplitude    = {path_amplitude}
num_waves    = {num_waves}
use_frenet   = {isFrenet}

# --- Build path control points ---
if path_shape == "wave":
    steps = num_waves * 8
    pts = [(path_len * i / steps,
            amplitude * math.sin(2 * math.pi * num_waves * i / steps))
           for i in range(steps + 1)]

elif path_shape == "arc":
    steps = 20
    radius = path_len / math.pi
    pts = [(radius * math.sin(math.pi * i / steps),
            radius * (1 - math.cos(math.pi * i / steps)))
           for i in range(steps + 1)]

elif path_shape == "spiral":
    steps = 24
    pts = []
    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps
        r = amplitude * i / steps
        pts.append((r * math.cos(angle), r * math.sin(angle)))

else:  # s_curve (default)
    pts = [
        (0, 0),
        (path_len * 0.2, amplitude * 0.5),
        (path_len * 0.4, amplitude),
        (path_len * 0.5, 0),
        (path_len * 0.6, -amplitude),
        (path_len * 0.8, -amplitude * 0.5),
        (path_len, 0),
    ]

# --- Build path wire ---
path = cq.Workplane("XY").spline(pts)

# --- Build profile ---
if profile == "rect":
    face = cq.Workplane("YZ").rect(pr * 2, ph)
else:
    face = cq.Workplane("YZ").circle(pr)

# --- Sweep ---
result = face.sweep(path, isFrenet=use_frenet)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        profile=str(params.get("profile", "circle")),
        profile_r=float(params.get("profile_r", 4.0)),
        profile_h=float(params.get("profile_h", 6.0)),
        path_shape=str(params.get("path_shape", "s_curve")),
        path_length=float(params.get("path_length", 100.0)),
        path_amplitude=float(params.get("path_amplitude", 20.0)),
        num_waves=int(params.get("num_waves", 2)),
        isFrenet=bool(params.get("isFrenet", True)),
    )
