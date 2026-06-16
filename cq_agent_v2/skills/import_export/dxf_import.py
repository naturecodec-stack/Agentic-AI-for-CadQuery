NAME = "dxf_import"
DESCRIPTION = "Import a 2D DXF file and extrude it into a 3D solid"
PARAMETERS = {
    "dxf_path":  {"type": "str",   "default": "C:/path/to/file.dxf"},
    "depth":     {"type": "float", "default": 5.0,  "unit": "mm", "desc": "extrusion depth"},
    "layer":     {"type": "str",   "default": "",   "desc": "DXF layer name to import (empty = all)"},
    "tolerance": {"type": "float", "default": 0.1,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
from cadquery import importers

dxf_path  = r"{dxf_path}"
depth     = {depth}
layer     = "{layer}"
tolerance = {tolerance}

if layer:
    dxf = importers.importDXF(dxf_path, tol=tolerance, include=[layer])
else:
    dxf = importers.importDXF(dxf_path, tol=tolerance)

result = dxf.wires().toPending().extrude(depth)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        dxf_path=str(params.get("dxf_path", "C:/path/to/file.dxf")),
        depth=float(params.get("depth", 5.0)),
        layer=str(params.get("layer", "")),
        tolerance=float(params.get("tolerance", 0.1)),
    )
