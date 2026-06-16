NAME = "spline_transition"
DESCRIPTION = "Smooth spline transition between two different cross-sections — round to square, circle to rectangle"
PARAMETERS = {
    "bottom_shape":  {"type": "str",   "default": "circle", "desc": "circle | square | rect | hex"},
    "top_shape":     {"type": "str",   "default": "square",  "desc": "circle | square | rect | hex"},
    "bottom_size":   {"type": "float", "default": 40.0, "unit": "mm", "desc": "diameter or width"},
    "top_size":      {"type": "float", "default": 30.0, "unit": "mm"},
    "height":        {"type": "float", "default": 50.0, "unit": "mm"},
    "num_sections":  {"type": "int",   "default": 8,    "desc": "smoothness of transition"},
    "twist_angle":   {"type": "float", "default": 0.0,  "desc": "twist top relative to bottom (degrees)"},
}

TEMPLATE = """import cadquery as cq
import math

bot_shape  = "{bottom_shape}"
top_shape  = "{top_shape}"
bot_size   = {bottom_size}
top_size   = {top_size}
h          = {height}
sections   = {num_sections}
twist      = {twist_angle}

def shape_pts(shape, size, angle_offset=0, n=24):
    \"\"\"Generate polygon approximation points for a shape.\"\"\"
    pts = []
    r = size / 2
    if shape == "circle":
        for i in range(n + 1):
            a = math.radians(360 * i / n + angle_offset)
            pts.append((r * math.cos(a), r * math.sin(a)))
    elif shape == "hex":
        for i in range(6 + 1):
            a = math.radians(60 * i + 30 + angle_offset)
            pts.append((r * math.cos(a), r * math.sin(a)))
    elif shape == "rect":
        hw, hh = size / 2, size * 0.6 / 2
        pts = [( hw,  hh), (-hw,  hh), (-hw, -hh), ( hw, -hh), ( hw,  hh)]
    else:  # square
        hw = size / 2
        pts = [( hw,  hw), (-hw,  hw), (-hw, -hw), ( hw, -hw), ( hw,  hw)]
    return pts

# Build loft through interpolated sections
wp = cq.Workplane("XY")

for i in range(sections + 1):
    t = i / sections
    z_off = h * t / sections if i > 0 else 0

    # Interpolate size
    size = bot_size + (top_size - bot_size) * t
    # Interpolate twist
    angle = twist * t

    # Interpolate shape (use more circle-like pts at 0, more target shape at 1)
    if t < 0.5:
        pts = shape_pts(bot_shape, size, angle)
    else:
        pts = shape_pts(top_shape, size, angle)

    if i == 0:
        wp = wp.spline(pts).close()
    else:
        wp = wp.workplane(offset=h / sections).spline(pts).close()

result = wp.loft(ruled=False)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        bottom_shape=str(params.get("bottom_shape", "circle")),
        top_shape=str(params.get("top_shape", "square")),
        bottom_size=float(params.get("bottom_size", 40.0)),
        top_size=float(params.get("top_size", 30.0)),
        height=float(params.get("height", 50.0)),
        num_sections=int(params.get("num_sections", 8)),
        twist_angle=float(params.get("twist_angle", 0.0)),
    )
