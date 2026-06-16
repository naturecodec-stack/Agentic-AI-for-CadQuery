NAME = "airfoil"
DESCRIPTION = "Generate a NACA 4-digit airfoil wing section using spline interpolation"
PARAMETERS = {
    "naca":          {"type": "str",   "default": "2412", "desc": "4-digit NACA code e.g. 0012, 2412, 4415"},
    "chord":         {"type": "float", "default": 100.0, "unit": "mm", "desc": "chord length"},
    "span":          {"type": "float", "default": 60.0,  "unit": "mm", "desc": "wing span (extrude depth)"},
    "n_points":      {"type": "int",   "default": 40,    "desc": "points per surface (more = smoother)"},
    "te_gap":        {"type": "float", "default": 0.5,   "unit": "mm", "desc": "trailing edge thickness (0=sharp)"},
    "twist_deg":     {"type": "float", "default": 0.0,   "desc": "washout twist angle along span"},
}

TEMPLATE = """import cadquery as cq
import math

naca    = "{naca}"
chord   = {chord}
span    = {span}
n_pts   = {n_points}
te_gap  = {te_gap}
twist   = {twist_deg}

# Parse NACA 4-digit
m  = int(naca[0]) / 100.0   # max camber ratio
p  = int(naca[1]) / 10.0    # max camber position ratio
tc = int(naca[2:]) / 100.0  # thickness ratio

def naca_coords(n):
    upper, lower = [], []
    for i in range(n + 1):
        # Cosine spacing for better LE resolution
        x = 0.5 * (1 - math.cos(math.pi * i / n))

        # Thickness distribution (NACA 4-digit formula)
        yt = (tc / 0.2) * (
            0.2969 * math.sqrt(x)
            - 0.1260 * x
            - 0.3516 * x ** 2
            + 0.2843 * x ** 3
            - 0.1015 * x ** 4
        )

        # Camber line and gradient
        if p > 0 and x < p:
            yc   = (m / p ** 2) * (2 * p * x - x ** 2)
            dyc  = (2 * m / p ** 2) * (p - x)
        elif p > 0:
            yc   = (m / (1 - p) ** 2) * (1 - 2 * p + 2 * p * x - x ** 2)
            dyc  = (2 * m / (1 - p) ** 2) * (p - x)
        else:
            yc, dyc = 0.0, 0.0

        theta = math.atan(dyc)
        xu = (x  - yt * math.sin(theta)) * chord
        yu = (yc + yt * math.cos(theta)) * chord
        xl = (x  + yt * math.sin(theta)) * chord
        yl = (yc - yt * math.cos(theta)) * chord

        upper.append((xu, yu))
        lower.append((xl, yl))

    return upper, lower

upper_pts, lower_pts = naca_coords(n_pts)

# Build closed profile: upper surface → lower surface (reversed) → close
# Shift so LE is at origin
all_pts = upper_pts + lower_pts[-2:0:-1]

# Add trailing edge thickness if requested
if te_gap > 0:
    all_pts[0]  = (all_pts[0][0],   te_gap / 2)
    all_pts[-1] = (all_pts[-1][0], -te_gap / 2)

result = (cq.Workplane("XY")
    .spline(all_pts)
    .close()
    .extrude(span))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        naca=str(params.get("naca", "2412")),
        chord=float(params.get("chord", 100.0)),
        span=float(params.get("span", 60.0)),
        n_points=int(params.get("n_points", 40)),
        te_gap=float(params.get("te_gap", 0.5)),
        twist_deg=float(params.get("twist_deg", 0.0)),
    )
