"""
Tests for Gremlin language processor.
"""

from pygments.lexers import GroovyLexer

from graphsh.lang import GremlinProcessor


def test_validate_query():
    """Test query validation."""
    processor = GremlinProcessor()

    # Valid queries
    is_valid = processor.validate("g.V().limit(5)")
    assert is_valid is True

    is_valid = processor.validate("g.V().has('name', 'Alice')")
    assert is_valid is True

    # Invalid queries
    is_valid = processor.validate("g.V(.limit(5)")
    assert is_valid is False

    is_valid = processor.validate("V().limit(5)")
    assert is_valid is False


def test_get_syntax_lexer():
    """Test syntax lexer."""
    processor = GremlinProcessor()
    lexer = processor.get_syntax_lexer()
    assert lexer is GroovyLexer

