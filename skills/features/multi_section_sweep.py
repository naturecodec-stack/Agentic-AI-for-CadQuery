NAME = "multi_section_sweep"
DESCRIPTION = "Loft through multiple cross-section profiles, morphing from a circle to a square"
PARAMETERS = {
    "circle_radius": {"type": "float", "default": 20.0, "unit": "mm"},
    "square_size":   {"type": "float", "default": 30.0, "unit": "mm"},
    "height":        {"type": "float", "default": 50.0, "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle({circle_radius})
    .workplane(offset={height})
    .rect({square_size}, {square_size})
    .loft(ruled=True)
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        circle_radius=params.get("circle_radius", 20.0),
        square_size=params.get("square_size", 30.0),
        height=params.get("height", 50.0),
    )
