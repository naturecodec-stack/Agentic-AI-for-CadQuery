NAME = "helix"
DESCRIPTION = "Create a helical/spring shape by sweeping a circle along a helix path"
PARAMETERS = {
    "pitch":        {"type": "float", "default": 10.0, "unit": "mm"},
    "height":       {"type": "float", "default": 50.0, "unit": "mm"},
    "helix_radius": {"type": "float", "default": 15.0, "unit": "mm"},
    "wire_radius":  {"type": "float", "default": 1.5,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

helix_path = cq.Wire.makeHelix(
    pitch={pitch}, height={height}, radius={helix_radius}
)

result = (
    cq.Workplane("XY")
    .circle({wire_radius})
    .sweep(cq.Workplane(obj=helix_path), isFrenet=True)
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        pitch=params.get("pitch", 10.0),
        height=params.get("height", 50.0),
        helix_radius=params.get("helix_radius", 15.0),
        wire_radius=params.get("wire_radius", 1.5),
    )
