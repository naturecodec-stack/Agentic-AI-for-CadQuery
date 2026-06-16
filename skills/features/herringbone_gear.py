NAME = "herringbone_gear"
DESCRIPTION = "Create a herringbone (double helical) gear using cq_gears — no axial thrust, very smooth"
PARAMETERS = {
    "module":        {"type": "float", "default": 1.0},
    "teeth_number":  {"type": "int",   "default": 20},
    "width":         {"type": "float", "default": 10.0, "unit": "mm"},
    "helix_angle":   {"type": "float", "default": 20.0, "desc": "helix angle per half (degrees)"},
    "bore_d":        {"type": "float", "default": 5.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

try:
    from cq_gears import HerringboneGear
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module       = {module}
teeth_number = {teeth_number}
width        = {width}
helix_angle  = {helix_angle}
bore_d       = {bore_d}

gear = HerringboneGear(
    module=module,
    teeth_number=teeth_number,
    width=width,
    helix_angle=helix_angle,
    bore_d=bore_d,
)
result = gear.build()
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        teeth_number=int(params.get("teeth_number", 20)),
        width=float(params.get("width", 10.0)),
        helix_angle=float(params.get("helix_angle", 20.0)),
        bore_d=float(params.get("bore_d", 5.0)),
    )
