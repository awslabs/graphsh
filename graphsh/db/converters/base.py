"""
Base converter class for database adapters.

This module provides the base class for all database-specific converters
that transform native database formats to GraphSh models.
"""

from typing import Any, Dict, List


class BaseConverter:
    """Base class for all database converters."""

    @staticmethod
    def convert_value(value: Any) -> Any:
        """Convert a database value to a GraphSh model.

        Args:
            value: Database value

        Returns:
            Any: Converted value
        """
        raise NotImplementedError("Subclasses must implement convert_value")

    @staticmethod
    def convert_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database result to GraphSh models.

        Args:
            result: Database result

        Returns:
            Dict[str, Any]: Converted result
        """
        raise NotImplementedError("Subclasses must implement convert_result")

    @staticmethod
    def convert_results(results: Any) -> List[Any]:
        """Convert database results to GraphSh models.

        Args:
            results: Database results

        Returns:
            List[Any]: Converted results
        """
        raise NotImplementedError("Subclasses must implement convert_results")
