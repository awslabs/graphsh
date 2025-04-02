"""
Cypher language processor for GraphSh.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pygments.lexers import CypherLexer

from graphsh.lang.base import LanguageProcessor

logger = logging.getLogger(__name__)


class CypherProcessor(LanguageProcessor):
    """Cypher language processor."""

    def __init__(self):
        """Initialize Cypher processor."""
        super().__init__()
        # Core Cypher clauses
        self.clauses = [
            "MATCH",
            "RETURN",
            "WITH",
            "WHERE",
            "CREATE",
            "MERGE",
            "DELETE",
            "REMOVE",
            "SET",
            "OPTIONAL MATCH",
            "DETACH DELETE",
            "FOREACH",
            "CALL",
            "YIELD",
            "UNWIND",
        ]

        # Operators and keywords
        self.operators = [
            "AND",
            "OR",
            "XOR",
            "NOT",
            "IN",
            "STARTS WITH",
            "ENDS WITH",
            "CONTAINS",
            "IS NULL",
            "IS NOT NULL",
            "=",
            "<>",
            "<",
            ">",
            "<=",
            ">=",
            "+",
            "-",
            "*",
            "/",
        ]

        # Functions by category
        self.aggregation_functions = [
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "collect",
            "stDev",
            "stDevP",
            "percentileDisc",
            "percentileCont",
        ]

        self.string_functions = [
            "toString",
            "trim",
            "left",
            "right",
            "lower",
            "upper",
            "substring",
            "replace",
            "reverse",
            "split",
            "size",
        ]

        self.numeric_functions = [
            "toInteger",
            "toFloat",
            "abs",
            "ceil",
            "floor",
            "round",
            "sign",
            "rand",
            "sqrt",
        ]

        self.list_functions = [
            "size",
            "reverse",
            "head",
            "last",
            "tail",
            "range",
            "reduce",
            "extract",
            "filter",
            "all",
            "any",
            "none",
            "single",
        ]

        self.predicate_functions = ["exists", "isEmpty", "isNaN"]

        # Common patterns and relationships
        self.node_patterns = [
            "()",
            "(n)",
        ]

        self.relationship_patterns = [
            "-->",
            "<--",
            "--",
            "-[r]->",
            "<-[r]-",
            "-[r]-",
        ]

        # Common property keys and labels
        self.common_labels = []

        self.common_properties = []

        self.common_relationships = []

        # Flow control
        self.flow_control = [
            "SKIP",
            "LIMIT",
            "ORDER BY",
            "ASC",
            "DESC",
            "UNION",
            "UNION ALL",
        ]

        # Combine all keywords for general completion
        self.all_keywords = (
            self.clauses
            + self.operators
            + self.flow_control
            + ["AS", "ON", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END"]
        )

        # Set of keywords for case-insensitive matching
        self.keywords = {k.upper() for k in self.all_keywords}

    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate Cypher query.

        Args:
            query: Query string.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Basic validation - check for balanced braces and parentheses
        if not self._check_balanced_braces(query):
            return False, "Unbalanced braces, brackets, or parentheses"

        # Check for required keywords
        if not re.search(r"\b(MATCH|CREATE|MERGE|RETURN|CALL)\b", query, re.IGNORECASE):
            return (
                False,
                "Missing required clause (MATCH, CREATE, MERGE, RETURN, or CALL)",
            )

        # More advanced validation would require a full Cypher parser
        return True, None

    def _get_context(self, text_before_cursor: str) -> str:
        """Determine the current context based on the text before cursor.

        Args:
            text_before_cursor: Text up to the cursor position.

        Returns:
            str: The identified context.
        """
        context_patterns = [
            (r"MATCH\s*\([^)]*$", "NODE_PATTERN"),
            (r"\[([^]]*)?$", "RELATIONSHIP_PATTERN"),
            (r"WHERE\s+[^=]*$", "WHERE_CLAUSE"),
            (r"\bRETURN\s+[\w\s,]*$", "RETURN_CLAUSE"),
            (r"\bWHERE\s+[\w\s.]*$", "WHERE_CONDITION"),
            (r"\bORDER\s+BY\s+[\w\s,]*$", "ORDER_BY"),
            (r"\w+\($", "FUNCTION_CALL"),
        ]

        for pattern, context in context_patterns:
            if re.search(pattern, text_before_cursor, re.IGNORECASE):
                return context
        return "DEFAULT"

    def _get_suggestions_by_context(
        self, context: str, current_word: str = ""
    ) -> List[str]:
        """Get suggestions based on the current context and word.

        Args:
            context: The current context.
            current_word: The current word being typed.

        Returns:
            List[str]: List of suggestions.
        """
        context_handlers = {
            "NODE_PATTERN": lambda: [f":{label}" for label in self.common_labels],
            "RELATIONSHIP_PATTERN": lambda: [
                f":{rel}" for rel in self.common_relationships
            ],
            "WHERE_CLAUSE": lambda: self.common_properties,
            "RETURN_CLAUSE": lambda: self._filter_suggestions(
                self.aggregation_functions + ["DISTINCT"] + self.common_properties,
                current_word,
            ),
            "WHERE_CONDITION": lambda: self._filter_suggestions(
                self.operators
                + self.predicate_functions
                + ["AND", "OR", "NOT", "IN", "IS NULL", "IS NOT NULL"],
                current_word,
            ),
            "ORDER_BY": lambda: self._filter_suggestions(["ASC", "DESC"], current_word),
            "FUNCTION_CALL": lambda: self._filter_suggestions(
                self.string_functions
                + self.numeric_functions
                + self.list_functions
                + self.predicate_functions,
                current_word,
            ),
            "DEFAULT": lambda: self._get_default_suggestions(current_word),
        }
        return context_handlers.get(context, lambda: [])()

    def _filter_suggestions(self, suggestions: List[str], prefix: str) -> List[str]:
        """Filter suggestions based on prefix.

        Args:
            suggestions: List of possible suggestions.
            prefix: Prefix to filter by.

        Returns:
            List[str]: Filtered suggestions.
        """
        return [s for s in suggestions if s.lower().startswith(prefix.lower())]

    def _get_default_suggestions(self, current_word: str) -> List[str]:
        """Get default suggestions when no specific context is matched.

        Args:
            current_word: The current word being typed.

        Returns:
            List[str]: List of default suggestions.
        """
        suggestions = []

        # Add matching keywords
        suggestions.extend(self._filter_suggestions(self.all_keywords, current_word))

        # Add matching functions
        all_functions = (
            self.aggregation_functions
            + self.string_functions
            + self.numeric_functions
            + self.list_functions
            + self.predicate_functions
        )
        suggestions.extend(self._filter_suggestions(all_functions, current_word))

        # Add matching property keys if appropriate
        if "." in current_word:
            node_alias, prop_prefix = current_word.split(".")
            suggestions.extend(
                f"{node_alias}.{prop}"
                for prop in self.common_properties
                if prop.lower().startswith(prop_prefix.lower())
            )

        return suggestions

    def get_completion_suggestions(self, text: str, cursor_position: int) -> List[str]:
        """Get completion suggestions for Cypher.

        Args:
            text: Current text.
            cursor_position: Cursor position.

        Returns:
            List[str]: Completion suggestions.
        """
        text_before_cursor = text[:cursor_position]

        if not text_before_cursor.strip():
            return []

        word_match = re.search(r"[\w:]+$", text_before_cursor)
        if not word_match:
            context = self._get_context(text_before_cursor)
            return self._get_suggestions_by_context(context)

        current_word = word_match.group(0)
        text_before_word = text_before_cursor[: -len(current_word)]
        context = self._get_context(text_before_word)

        return self._get_suggestions_by_context(context, current_word)

    def get_syntax_lexer(self):
        """Get syntax lexer for Cypher.

        Returns:
            CypherLexer: Cypher lexer.
        """
        return CypherLexer

    def process_results(self, results: Any) -> List[Dict[str, Any]]:
        """Process Cypher query results.

        Args:
            results: Raw query results.

        Returns:
            List[Dict[str, Any]]: Processed results.
        """
        # Handle different result formats
        if isinstance(results, dict) and "columns" in results and "data" in results:
            # Neo4j HTTP API format
            rows = []
            columns = results.get("columns", [])

            for record in results.get("data", []):
                if "row" in record:
                    row_data = record["row"]
                    row = {columns[i]: row_data[i] for i in range(len(columns))}
                    rows.append(row)

            return rows
        elif isinstance(results, list) and all(isinstance(r, dict) for r in results):
            # Already processed or simple format
            return results
        elif hasattr(results, "records") and callable(getattr(results, "records")):
            # Neo4j Python driver Result object
            records = results.records()
            rows = []

            for record in records:
                row = {}
                for key in record.keys():
                    row[key] = self._process_neo4j_value(record[key])
                rows.append(row)

            return rows
        else:
            # Unknown format, return as is
            logger.warning(f"Unknown Cypher result format: {type(results)}")
            if isinstance(results, dict):
                # For test compatibility, convert to string representation
                return [{"result": str(results)}]
            return [{"result": str(results)}]

    def _process_neo4j_value(self, value: Any) -> Any:
        """Process Neo4j value.

        Args:
            value: Neo4j value.

        Returns:
            Any: Processed value.
        """
        # Handle Neo4j types
        if hasattr(value, "id") and hasattr(value, "labels"):
            # Node
            node = {
                "id": value.id,
                "labels": list(value.labels),
                "properties": dict(value),
            }
            return node
        elif hasattr(value, "id") and hasattr(value, "type"):
            # Relationship
            rel = {
                "id": value.id,
                "type": value.type,
                "properties": dict(value),
                "start": value.start_node.id if hasattr(value, "start_node") else None,
                "end": value.end_node.id if hasattr(value, "end_node") else None,
            }
            return rel
        elif (
            hasattr(value, "start")
            and hasattr(value, "end")
            and hasattr(value, "segments")
        ):
            # Path
            return {
                "start": self._process_neo4j_value(value.start),
                "end": self._process_neo4j_value(value.end),
                "length": len(value.relationships),
                "segments": [
                    {
                        "start": self._process_neo4j_value(segment.start),
                        "relationship": self._process_neo4j_value(segment.relationship),
                        "end": self._process_neo4j_value(segment.end),
                    }
                    for segment in value.segments
                ],
            }
        elif isinstance(value, list):
            return [self._process_neo4j_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._process_neo4j_value(v) for k, v in value.items()}
        else:
            # Primitive value
            return value

    def _check_balanced_braces(self, query: str) -> bool:
        """Check if braces, brackets, and parentheses are balanced.

        Args:
            query: Query string.

        Returns:
            bool: True if balanced.
        """
        stack = []
        brackets = {"{": "}", "(": ")", "[": "]"}

        for char in query:
            if char in brackets.keys():
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return False
                opening = stack.pop()
                if char != brackets[opening]:
                    return False

        return len(stack) == 0

    def validate(self, query: str) -> bool:
        """Validate Cypher query.

        Args:
            query: Query string.

        Returns:
            bool: True if query is valid, False otherwise.
        """
        # Basic validation - check for balanced parentheses and braces
        if not self._check_balanced_symbols(query):
            return False

        # For now, we'll just do basic validation
        # In a real implementation, we might use a proper parser
        return True

    def _check_balanced_symbols(self, query: str) -> bool:
        """Check if parentheses and braces are balanced.

        Args:
            query: Query string.

        Returns:
            bool: True if balanced, False otherwise.
        """
        stack = []
        brackets = {"(": ")", "{": "}", "[": "]"}

        for char in query:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return False
                opening = stack.pop()
                if char != brackets[opening]:
                    return False

        return len(stack) == 0
