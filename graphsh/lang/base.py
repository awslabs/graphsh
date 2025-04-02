"""
Base language processor for GraphSh.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class LanguageProcessor(ABC):
    """Base class for query language processors."""

    @abstractmethod
    def validate_query(self, query_string: str) -> Tuple[bool, Optional[str]]:
        """Validate query syntax.

        Args:
            query_string: Query string to validate.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_completion_suggestions(self, text: str, cursor_position: int) -> List[str]:
        """Get completion suggestions for text at cursor position.

        Args:
            text: Current input text.
            cursor_position: Cursor position in text.

        Returns:
            List[str]: Completion suggestions.
        """
        pass

    @abstractmethod
    def get_syntax_lexer(self):
        """Get syntax lexer for highlighting.

        Returns:
            Any: Pygments lexer class.
        """
        pass

    @abstractmethod
    def process_results(
        self, raw_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process raw results into standardized format.

        Args:
            raw_results: Raw query results.

        Returns:
            List[Dict[str, Any]]: Processed results.
        """
        pass
