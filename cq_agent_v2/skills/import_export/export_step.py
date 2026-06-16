NAME = "export_step"
DESCRIPTION = "Create a box and export it to STEP, STL, or SVG file format"
PARAMETERS = {
    "length":     {"type": "float", "default": 50.0, "unit": "mm"},
    "width":      {"type": "float", "default": 30.0, "unit": "mm"},
    "height":     {"type": "float", "default": 10.0, "unit": "mm"},
    "format":     {"type": "str",   "default": "step", "options": ["step", "stl", "svg"]},
    "output_path": {"type": "str", "default": "output.step"},
}

TEMPLATE = """import cadquery as cq
from cadquery import exporters

result = cq.Workplane("XY").box({length}, {width}, {height})

exporters.export(result, "{output_path}")
show_object(result)
"""


def render(params: dict) -> str:
    fmt = params.get("format", "step")
    output_path = params.get("output_path", f"output.{fmt}")
    return TEMPLATE.format(
        length=params.get("length", 50.0),
        width=params.get("width", 30.0),
        height=params.get("height", 10.0),
        output_path=output_path,
    )
