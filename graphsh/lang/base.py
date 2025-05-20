"""
Base language processor for GraphSh.
"""

from abc import ABC, abstractmethod


class LanguageProcessor(ABC):
    """Base class for query language processors."""

    @abstractmethod
    def validate(self, query: str) -> bool:
        """Validate query syntax.

        Args:
            query_string: Query string to validate.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_syntax_lexer(self):
        """Get syntax lexer for highlighting.

        Returns:
            Any: Pygments lexer class.
        """
        pass

