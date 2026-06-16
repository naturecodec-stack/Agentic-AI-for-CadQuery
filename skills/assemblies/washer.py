NAME = "washer"
DESCRIPTION = "Create a washer using cq_warehouse fastener library"
PARAMETERS = {
    "size":          {"type": "str", "default": "M8"},
    "fastener_type": {"type": "str", "default": "iso7089"},
}

TEMPLATE = """import cadquery as cq
from cq_warehouse.fastener import PlainWasher

result = PlainWasher(
    size="{size}",
    fastener_type="{fastener_type}"
)
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        size=params.get("size", "M8"),
        fastener_type=params.get("fastener_type", "iso7089"),
    )
