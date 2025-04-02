"""
Gremlin language processor for GraphSh.
"""

from typing import Any, Dict, List, Optional, Tuple

from pygments.lexers import GroovyLexer

from graphsh.lang.base import LanguageProcessor


class GremlinProcessor(LanguageProcessor):
    """Processor for Gremlin query language."""

    def __init__(self):
        """Initialize Gremlin processor."""
        super().__init__()
        # Common Gremlin steps and methods
        self.traversal_source_methods = ["V", "E", "addV", "addE", "inject"]
        self.vertex_steps = [
            "out",
            "in",
            "both",
            "outE",
            "inE",
            "bothE",
            "outV",
            "inV",
            "bothV",
            "toV",
            "otherV",
            "order",
            "properties",
            "values",
            "valueMap",
            "has",
            "hasNot",
            "hasLabel",
            "hasId",
            "hasKey",
            "hasValue",
            "is",
            "not",
            "filter",
            "and",
            "or",
            "where",
            "choose",
            "optional",
            "union",
            "coalesce",
            "repeat",
            "until",
            "emit",
            "times",
            "branch",
            "path",
            "tree",
            "map",
            "flatMap",
            "identity",
            "constant",
            "id",
            "label",
            "sack",
            "loops",
            "project",
            "select",
            "unfold",
            "fold",
            "count",
            "sum",
            "max",
            "min",
            "mean",
            "group",
            "groupCount",
            "limit",
            "tail",
            "range",
            "skip",
            "sample",
            "dedup",
            "sideEffect",
            "store",
            "aggregate",
            "subgraph",
            "barrier",
            "index",
            "cap",
            "as",
            "by",
            "from",
            "to",
            "option",
            "match",
            "sack",
            "local",
            "pageRank",
            "peerPressure",
            "connectedComponent",
            "shortestPath",
            "cyclicPath",
            "simplePath",
            "tree",
            "drop",
            "property",
            "element",
        ]
        self.edge_steps = [
            "outV",
            "inV",
            "bothV",
            "otherV",
            "valueMap",
            "properties",
            "values",
            "has",
            "hasNot",
            "hasLabel",
            "hasId",
            "hasKey",
            "hasValue",
            "is",
            "not",
            "filter",
            "drop",
            "property",
            "element",
        ]
        self.common_property_keys = [
            "id",
            "name",
            "label",
            "type",
            "value",
            "weight",
            "timestamp",
            "date",
            "created",
            "updated",
            "title",
            "description",
            "age",
            "status",
            "category",
        ]
        self.common_labels = [
            "person",
            "user",
            "product",
            "category",
            "order",
            "item",
            "review",
            "comment",
            "post",
            "tag",
            "friend",
            "follows",
            "created",
            "rated",
            "purchased",
            "contains",
            "belongs_to",
        ]

    def validate(self, query_string: str) -> bool:
        """Validate Gremlin query syntax.

        Args:
            query_string: Query string to validate.

        Returns:
            bool: True if query is valid, False otherwise.
        """
        # For now, just do basic validation
        result, _ = self.validate_query(query_string)
        return result

    def get_completion_suggestions(self, text: str, cursor_position: int) -> List[str]:
        """Get completion suggestions for Gremlin.

        Args:
            text: Current input text.
            cursor_position: Cursor position in text.

        Returns:
            List[str]: Completion suggestions.
        """
        # Extract text up to cursor position
        text_before_cursor = text[:cursor_position]

        # If we're at the beginning of the query
        if not text_before_cursor.strip():
            return ["g."]

        # Basic completion for common Gremlin methods
        if text_before_cursor.endswith("."):
            # Get the part before the dot
            parts = text_before_cursor.split(".")
            prefix = parts[-2] if len(parts) > 1 else ""

            if prefix == "g" or text_before_cursor == ".":
                return [f"{m}()" for m in self.traversal_source_methods]
            elif any(method in prefix for method in ["V", "E", "addV", "addE"]):
                return [f"{step}()" for step in self.vertex_steps]
            elif any(step in prefix for step in ["outE", "inE", "bothE"]):
                return [f"{step}()" for step in self.edge_steps]
            return []

        # If we're in the middle of typing a method after a dot
        dot_pos = text_before_cursor.rfind(".")
        if dot_pos >= 0 and dot_pos < cursor_position - 1:
            # Get the part before the dot
            prefix = ""
            for i in range(dot_pos - 1, -1, -1):
                if i < 0 or not (
                    text_before_cursor[i].isalnum() or text_before_cursor[i] in "._()"
                ):
                    break
                prefix = text_before_cursor[i] + prefix

            # Get the partial method name after the dot
            partial_method = text_before_cursor[dot_pos + 1 :]

            # Suggest methods based on the prefix
            if prefix == "g":
                methods = [f"{m}()" for m in self.traversal_source_methods]
                return [m for m in methods if m.startswith(partial_method)]
            elif any(method in prefix for method in ["V", "E", "addV", "addE"]):
                methods = [f"{step}()" for step in self.vertex_steps]
                return [m for m in methods if m.startswith(partial_method)]
            elif any(step in prefix for step in ["outE", "inE", "bothE"]):
                methods = [f"{step}()" for step in self.edge_steps]
                return [m for m in methods if m.startswith(partial_method)]

        # If we're inside a method's parentheses
        open_paren_pos = text_before_cursor.rfind("(")
        close_paren_pos = text_before_cursor.rfind(")")

        if open_paren_pos > close_paren_pos:
            # We're inside a method's parameters
            method_name = ""
            for i in range(open_paren_pos - 1, -1, -1):
                if not text_before_cursor[i].isalnum():
                    break
                method_name = text_before_cursor[i] + method_name

            # Suggest parameters based on method
            if method_name in ["has", "hasLabel"]:
                # Suggest common labels or property keys
                partial = (
                    text_before_cursor[open_paren_pos + 1 :]
                    .strip()
                    .strip("'")
                    .strip('"')
                )
                if method_name == "hasLabel":
                    return [
                        f"'{label}'"
                        for label in self.common_labels
                        if label.startswith(partial)
                    ]
                else:
                    return [
                        f"'{key}'"
                        for key in self.common_property_keys
                        if key.startswith(partial)
                    ]

        # If nothing else matches, return empty list
        return []

    def get_syntax_lexer(self):
        """Get syntax lexer for highlighting.

        Returns:
            Any: Pygments lexer class.
        """
        return GroovyLexer

    def process_results(
        self, raw_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process Gremlin results into standardized format.

        Args:
            raw_results: Raw Gremlin results.

        Returns:
            List[Dict[str, Any]]: Processed results.
        """
        # For now, just return the raw results
        # In a more complete implementation, we would normalize different result types
        return raw_results

    def validate_query(self, query_string: str) -> Tuple[bool, Optional[str]]:
        """Validate Gremlin query syntax.

        Args:
            query_string: Query string to validate.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Basic validation - check for balanced parentheses
        if query_string.count("(") != query_string.count(")"):
            return False, "Unbalanced parentheses"

        # Check for common Gremlin starting points
        if not query_string.strip().startswith(("g.", "graph.")):
            return False, "Gremlin queries typically start with 'g.' or 'graph.'"

        return True, None
