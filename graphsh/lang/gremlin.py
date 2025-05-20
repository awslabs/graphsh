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
