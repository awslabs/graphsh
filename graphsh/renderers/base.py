"""
Base renderer for GraphSh.
"""

from typing import Dict, Any, List
from rich.console import Console

console = Console()


class ResultRenderer:
    """Base class for result renderers."""

    def render(self, results: List[Dict[str, Any]]) -> str:
        """Render results for display.

        Args:
            results: Query results.

        Returns:
            str: Rendered results.
        """
        # Base implementation returns string representation
        return str(results)

    def display_results(self, results: List[Dict[str, Any]], **kwargs) -> None:
        """Format and print results.

        Args:
            results: Query results.
            **kwargs: Additional rendering options.
        """
        if not results:
            console.print("No results.")
            return

        # Process results through the graph formatter
        from graphsh.models.graph import (
            format_graph_element,
            GraphNode,
            GraphEdge,
            GraphPath,
            GraphValue,
        )

        processed_results = []
        for result in results:
            # Handle graph objects directly
            if isinstance(result, (GraphNode, GraphEdge, GraphPath, GraphValue)):
                processed_results.append({"result": format_graph_element(result)})
            # Handle dictionaries
            elif isinstance(result, dict):
                processed_result = {}
                for key, value in result.items():
                    processed_result[key] = format_graph_element(value)
                processed_results.append(processed_result)
            # Handle other types
            else:
                processed_results.append({"result": format_graph_element(result)})

        rendered = self.render(processed_results)
        console.print(rendered)
