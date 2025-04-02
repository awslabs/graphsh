"""
Table renderer for GraphSh.
"""

from typing import Dict, Any, List, Union
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

from graphsh.renderers.base import ResultRenderer


class TableRenderer(ResultRenderer):
    """Table renderer."""

    def render(self, results: List[Dict[str, Any]]) -> Union[str, Table, Panel, Tree]:
        """Render results as table.

        Args:
            results: Query results.

        Returns:
            Union[str, Table, Panel, Tree]: Rendered results.
        """
        if not results:
            return "No results"

        # Handle case where results is a single item that contains an array
        if len(results) == 1 and any(isinstance(v, list) for v in results[0].values()):
            # Find the array field
            array_field = None
            array_data = None
            for key, value in results[0].items():
                if isinstance(value, list) and value:
                    array_field = key
                    array_data = value
                    break

            if array_field and array_data:
                # Convert array to list of dictionaries
                if all(isinstance(item, dict) for item in array_data):
                    # Already a list of dictionaries
                    return self.render(array_data)
                else:
                    # Create a list of dictionaries with a single field
                    return self.render([{array_field: item} for item in array_data])

        return self._render_as_table(results)

    def _render_as_table(self, results: List[Dict[str, Any]]) -> Table:
        """Render results as a generic table."""
        table = Table(box=box.ROUNDED)

        # Add columns
        if results:
            columns = list(results[0].keys())
            for column in columns:
                table.add_column(column, style="cyan")

            # Add rows
            for row in results:
                values = [str(row.get(column, "")) for column in columns]
                table.add_row(*values)

        return table
