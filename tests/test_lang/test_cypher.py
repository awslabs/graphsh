"""
Tests for Cypher language processor.
"""

import pytest
from pygments.lexers import CypherLexer

from graphsh.lang.cypher import CypherProcessor


@pytest.fixture
def processor():
    """Create a Cypher processor."""
    return CypherProcessor()


def test_validate_query_valid(processor):
    """Test validating valid Cypher queries."""
    # Simple MATCH query
    query = """
    MATCH (p:Person)
    WHERE p.name = 'Alice'
    RETURN p.name, p.age
    """
    is_valid = processor.validate(query)
    assert is_valid is True

    # CREATE query
    query = """
    CREATE (p:Person {name: 'Alice', age: 30})
    RETURN p
    """
    is_valid = processor.validate(query)
    assert is_valid is True

    # MERGE query
    query = """
    MERGE (p:Person {name: 'Alice'})
    ON CREATE SET p.created = timestamp()
    RETURN p
    """
    is_valid = processor.validate(query)
    assert is_valid is True


def test_validate_query_invalid(processor):
    """Test validating invalid Cypher queries."""
    # Unbalanced parentheses
    query = """
    MATCH (p:Person
    WHERE p.name = 'Alice'
    RETURN p
    """
    is_valid = processor.validate(query)
    assert is_valid is False

def test_get_syntax_lexer(processor):
    """Test getting syntax lexer."""
    lexer = processor.get_syntax_lexer()
    assert lexer is CypherLexer
