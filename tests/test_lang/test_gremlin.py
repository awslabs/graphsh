"""
Tests for Gremlin language processor.
"""

import pytest
from pygments.lexers import GroovyLexer

from graphsh.lang import GremlinProcessor


def test_validate_query():
    """Test query validation."""
    processor = GremlinProcessor()

    # Valid queries
    is_valid, error = processor.validate_query("g.V().limit(5)")
    assert is_valid is True
    assert error is None

    is_valid, error = processor.validate_query("g.V().has('name', 'Alice')")
    assert is_valid is True
    assert error is None

    # Invalid queries
    is_valid, error = processor.validate_query("g.V(.limit(5)")
    assert is_valid is False
    assert "Unbalanced parentheses" in error

    is_valid, error = processor.validate_query("V().limit(5)")
    assert is_valid is False
    assert "typically start with" in error


def test_get_completion_suggestions():
    """Test completion suggestions."""
    processor = GremlinProcessor()

    # Test completion after 'g.'
    suggestions = processor.get_completion_suggestions("g.", 2)
    assert "V()" in suggestions
    assert "E()" in suggestions

    # Test completion after 'g.V().'
    suggestions = processor.get_completion_suggestions("g.V().", 6)
    assert "has()" in suggestions
    assert "values()" in suggestions


def test_get_syntax_lexer():
    """Test syntax lexer."""
    processor = GremlinProcessor()
    lexer = processor.get_syntax_lexer()
    assert lexer is GroovyLexer


def test_process_results():
    """Test result processing."""
    processor = GremlinProcessor()

    # Sample raw results
    raw_results = [
        {"id": "1", "label": "person", "properties": {"name": "Alice", "age": 30}},
        {"id": "2", "label": "person", "properties": {"name": "Bob", "age": 25}},
    ]

    # Process results
    processed = processor.process_results(raw_results)

    # For now, processor just returns raw results
    assert processed == raw_results
