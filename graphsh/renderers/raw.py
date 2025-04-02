"""
Raw renderer for GraphSh.
"""

from typing import Dict, Any, List
from graphsh.renderers.base import ResultRenderer


class RawRenderer(ResultRenderer):
    """Raw renderer that shows the returned payload as is."""

    def render(self, results: List[Dict[str, Any]]) -> str:
        """Render results as raw output.

        Args:
            results: Query results.

        Returns:
            str: Rendered results.
        """
        if not results:
            return "No results"

        # Simply return the raw results
        return str(results)
