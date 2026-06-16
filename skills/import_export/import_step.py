NAME = "import_step"
DESCRIPTION = "Import an existing STEP file into CadQuery and optionally translate it"
PARAMETERS = {
    "file_path": {"type": "str",   "default": "input.step"},
    "translate_x": {"type": "float", "default": 0.0, "unit": "mm"},
    "translate_y": {"type": "float", "default": 0.0, "unit": "mm"},
    "translate_z": {"type": "float", "default": 0.0, "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

result = cq.importers.importStep("{file_path}")
result = result.translate(({translate_x}, {translate_y}, {translate_z}))
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        file_path=params.get("file_path", "input.step"),
        translate_x=params.get("translate_x", 0.0),
        translate_y=params.get("translate_y", 0.0),
        translate_z=params.get("translate_z", 0.0),
    )
