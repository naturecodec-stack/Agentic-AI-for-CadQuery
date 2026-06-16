NAME = "helical_gear"
DESCRIPTION = "Create a helical gear using cq_gears library — smoother and quieter than spur gears"
PARAMETERS = {
    "module":        {"type": "float", "default": 1.0,  "desc": "gear module (tooth size)"},
    "teeth_number":  {"type": "int",   "default": 20},
    "width":         {"type": "float", "default": 8.0,  "unit": "mm"},
    "helix_angle":   {"type": "float", "default": 15.0, "desc": "helix angle in degrees"},
    "bore_d":        {"type": "float", "default": 5.0,  "unit": "mm", "desc": "shaft bore diameter"},
    "hand":          {"type": "str",   "default": "right", "desc": "right | left hand helix"},
}

TEMPLATE = """import cadquery as cq

try:
    from cq_gears import HelicalGear
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module       = {module}
teeth_number = {teeth_number}
width        = {width}
helix_angle  = {helix_angle}
bore_d       = {bore_d}
hand         = "{hand}"

gear = HelicalGear(
    module=module,
    teeth_number=teeth_number,
    width=width,
    helix_angle=helix_angle,
    bore_d=bore_d,
    hand=hand,
)
result = gear.build()
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        teeth_number=int(params.get("teeth_number", 20)),
        width=float(params.get("width", 8.0)),
        helix_angle=float(params.get("helix_angle", 15.0)),
        bore_d=float(params.get("bore_d", 5.0)),
        hand=str(params.get("hand", "right")),
    )
