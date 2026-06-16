NAME = "planetary_gear"
DESCRIPTION = "Create a planetary gear set (sun + planets + ring) using cq_gears"
PARAMETERS = {
    "module":          {"type": "float", "default": 1.0},
    "sun_teeth":       {"type": "int",   "default": 16, "desc": "sun gear teeth"},
    "planet_teeth":    {"type": "int",   "default": 16, "desc": "planet gear teeth"},
    "n_planets":       {"type": "int",   "default": 3,  "desc": "number of planet gears"},
    "width":           {"type": "float", "default": 6.0, "unit": "mm"},
    "bore_d":          {"type": "float", "default": 4.0, "unit": "mm"},
    "show_assembled":  {"type": "bool",  "default": True},
}

TEMPLATE = """import cadquery as cq
import math

try:
    from cq_gears import SpurGear, RingGear, PlanetaryGearSet
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module       = {module}
sun_teeth    = {sun_teeth}
planet_teeth = {planet_teeth}
n_planets    = {n_planets}
width        = {width}
bore_d       = {bore_d}
assembled    = {show_assembled}

try:
    # Use PlanetaryGearSet if available
    pg = PlanetaryGearSet(
        module=module,
        sun_teeth_number=sun_teeth,
        planet_teeth_number=planet_teeth,
        n_planets=n_planets,
        width=width,
        bore_d=bore_d,
    )
    result = pg.build()
except Exception:
    # Fallback: just show the sun gear
    sun = SpurGear(module=module, teeth_number=sun_teeth, width=width, bore_d=bore_d)
    result = sun.build()

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        sun_teeth=int(params.get("sun_teeth", 16)),
        planet_teeth=int(params.get("planet_teeth", 16)),
        n_planets=int(params.get("n_planets", 3)),
        width=float(params.get("width", 6.0)),
        bore_d=float(params.get("bore_d", 4.0)),
        show_assembled=bool(params.get("show_assembled", True)),
    )
