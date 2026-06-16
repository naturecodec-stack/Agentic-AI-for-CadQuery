NAME = "gear"
DESCRIPTION = "Generate an involute spur gear with correct tooth profile"
PARAMETERS = {
    "module":          {"type": "float", "default": 1.0,  "unit": "mm",  "desc": "gear module (tooth size)"},
    "num_teeth":       {"type": "int",   "default": 20,                  "desc": "number of teeth"},
    "width":           {"type": "float", "default": 6.0,  "unit": "mm",  "desc": "face width (extrusion depth)"},
    "pressure_angle":  {"type": "float", "default": 20.0, "unit": "deg", "desc": "standard is 20°"},
    "bore_diameter":   {"type": "float", "default": 5.0,  "unit": "mm",  "desc": "central bore (0 = no bore)"},
}

TEMPLATE = """import cadquery as cq
import math

# --- Parameters ---
module         = {module}
num_teeth      = {num_teeth}
width          = {width}
pressure_angle = {pressure_angle}
bore_d         = {bore_diameter}

# --- Involute geometry ---
pa      = math.radians(pressure_angle)
pitch_r = module * num_teeth / 2
base_r  = pitch_r * math.cos(pa)
tip_r   = pitch_r + module
root_r  = pitch_r - 1.25 * module
root_r  = max(root_r, base_r * 0.85)

pitch_angle = 2 * math.pi / num_teeth

def _inv_pt(rb, t):
    return rb * (math.cos(t) + t * math.sin(t)), rb * (math.sin(t) - t * math.cos(t))

def _inv_t(rb, r):
    return math.sqrt(max((r / rb) ** 2 - 1, 0))

# Angular offset so tooth is centred on +Y axis
t_pitch     = _inv_t(base_r, pitch_r)
xp, yp      = _inv_pt(base_r, t_pitch)
phi_pitch   = math.atan2(yp, xp)
half_tooth  = math.pi / num_teeth / 2
offset      = half_tooth - phi_pitch

# Build one flank (root → tip), 12 points
N   = 12
t0  = _inv_t(base_r, max(root_r, base_r))
t1  = _inv_t(base_r, tip_r)

right = []
for i in range(N + 1):
    t     = t0 + (t1 - t0) * i / N
    x, y  = _inv_pt(base_r, t)
    ang   = math.atan2(y, x) + offset
    r     = math.hypot(x, y)
    right.append((r * math.cos(ang), r * math.sin(ang)))

# Mirror for left flank (tip → root order so tooth traces cleanly)
left = [(-x, y) for x, y in right[::-1]]

# Root arc angles for this tooth
ang_root_right = math.atan2(right[0][1], right[0][0])
ang_root_left  = math.atan2(left[-1][1], left[-1][0])

# One tooth profile: gap → left flank → right flank → gap start
one_tooth = (
    [(root_r * math.cos(ang_root_left - pitch_angle),
      root_r * math.sin(ang_root_left - pitch_angle))]
    + left
    + right
    + [(root_r * math.cos(ang_root_right),
        root_r * math.sin(ang_root_right))]
)

# Tile all teeth by rotating
all_pts = []
for i in range(num_teeth):
    a  = i * pitch_angle
    ca = math.cos(a)
    sa = math.sin(a)
    for x, y in one_tooth:
        all_pts.append((x * ca - y * sa, x * sa + y * ca))

# Extrude
result = (
    cq.Workplane("XY")
    .polyline(all_pts)
    .close()
    .extrude(width)
)

if bore_d > 0:
    result = result.faces(">Z").workplane().hole(bore_d)

show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        num_teeth=int(params.get("num_teeth", 20)),
        width=float(params.get("width", 6.0)),
        pressure_angle=float(params.get("pressure_angle", 20.0)),
        bore_diameter=float(params.get("bore_diameter", 5.0)),
    )
