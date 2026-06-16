NAME = "nut"
DESCRIPTION = "Create a hex nut using cq_warehouse fastener library"
PARAMETERS = {
    "size":          {"type": "str", "default": "M8-1.25"},
    "fastener_type": {"type": "str", "default": "iso4032"},
}

TEMPLATE = """import cadquery as cq
from cq_warehouse.fastener import HexNut

result = HexNut(
    size="{size}",
    fastener_type="{fastener_type}"
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        size=params.get("size", "M8-1.25"),
        fastener_type=params.get("fastener_type", "iso4032"),
    )
