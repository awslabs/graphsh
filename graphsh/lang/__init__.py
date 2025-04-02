"""
Language processors for GraphSh.
"""

from graphsh.lang.base import LanguageProcessor
from graphsh.lang.gremlin import GremlinProcessor
from graphsh.lang.sparql import SparqlProcessor
from graphsh.lang.cypher import CypherProcessor

__all__ = [
    "LanguageProcessor",
    "GremlinProcessor",
    "SparqlProcessor",
    "CypherProcessor",
    "get_language_processor",
]


def get_language_processor(language):
    """Get language processor by language name.

    Args:
        language: Language name.

    Returns:
        LanguageProcessor: Language processor instance.

    Raises:
        ValueError: If language is not supported.
    """
    language = language.lower()

    if language == "gremlin":
        return GremlinProcessor()
    elif language == "sparql":
        return SparqlProcessor()
    elif language in ["cypher", "opencypher"]:
        return CypherProcessor()
    else:
        raise ValueError(f"Unsupported language: {language}")
