NAME = "bolt"
DESCRIPTION = "Create a hex head bolt using cq_warehouse fastener library"
PARAMETERS = {
    "size":          {"type": "str",   "default": "M8-1.25"},
    "length":        {"type": "float", "default": 30.0, "unit": "mm"},
    "fastener_type": {"type": "str",   "default": "iso4017"},
    "simple":        {"type": "bool",  "default": False},
}

TEMPLATE = """import cadquery as cq
from cq_warehouse.fastener import HexHeadScrew

result = HexHeadScrew(
    size="{size}",
    length={length},
    fastener_type="{fastener_type}",
    simple={simple}
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        size=params.get("size", "M8-1.25"),
        length=params.get("length", 30.0),
        fastener_type=params.get("fastener_type", "iso4017"),
        simple=params.get("simple", False),
    )
