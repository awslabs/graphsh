"""
Factory for creating renderers.
"""

from graphsh.renderers.base import ResultRenderer
from graphsh.renderers.table import TableRenderer
from graphsh.renderers.raw import RawRenderer


def get_renderer(render_type: str) -> ResultRenderer:
    """Get renderer for the specified type.

    Args:
        render_type: Renderer type.

    Returns:
        ResultRenderer: Renderer.

    Raises:
        ValueError: If renderer type is not supported.
    """
    render_type = render_type.lower()
    if render_type == "table":
        return TableRenderer()
    elif render_type == "raw":
        return RawRenderer()
    else:
        raise ValueError(
            f"Unsupported renderer type: {render_type}. Available renderers: table, raw"
        )
