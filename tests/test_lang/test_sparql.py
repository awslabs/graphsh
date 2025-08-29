"""
Tests for SPARQL language processor.
"""

import pytest
from pygments.lexers import SparqlLexer

from graphsh.lang.sparql import SparqlProcessor


@pytest.fixture
def processor():
    """Create a SPARQL processor."""
    return SparqlProcessor()


def test_validate_query_valid(processor):
    """Test validating valid SPARQL queries."""
    # Simple SELECT query
    query = """
    SELECT ?name ?email
    WHERE {
        ?person rdf:type foaf:Person .
        ?person foaf:name ?name .
        ?person foaf:mbox ?email .
    }
    """
    is_valid = processor.validate(query)
    assert is_valid is True

    # CONSTRUCT query
    query = """
    CONSTRUCT {
        ?person a foaf:Person .
        ?person foaf:name ?name .
    }
    WHERE {
        ?person rdf:type ex:User .
        ?person ex:username ?name .
    }
    """
    is_valid = processor.validate(query)
    assert is_valid is True

    # ASK query
    query = """
    ASK {
        ?person rdf:type foaf:Person .
        ?person foaf:name "Alice" .
    }
    """
    is_valid = processor.validate(query)
    assert is_valid is True


def test_validate_query_invalid(processor):
    """Test validating invalid SPARQL queries."""
    # Unbalanced braces
    query = """
    SELECT ?name
    WHERE {
        ?person rdf:type foaf:Person .
        ?person foaf:name ?name .
    
    """
    is_valid = processor.validate(query)
    assert is_valid is False


def test_get_syntax_lexer(processor):
    """Test getting syntax lexer."""
    lexer = processor.get_syntax_lexer()
    assert lexer is SparqlLexer


def test_check_balanced_braces(processor):
    """Test checking for balanced braces."""
    # Balanced braces
    assert processor._check_balanced_braces("SELECT * WHERE { ?s ?p ?o }") is True
    assert (
        processor._check_balanced_braces(
            "SELECT * WHERE { ?s ?p ?o . FILTER(?o > 10) }"
        )
        is True
    )
    assert (
        processor._check_balanced_braces("SELECT * WHERE { ?s ?p ?o . { ?s a ?type } }")
        is True
    )

    # Unbalanced braces
    assert processor._check_balanced_braces("SELECT * WHERE { ?s ?p ?o") is False
    assert processor._check_balanced_braces("SELECT * WHERE } ?s ?p ?o }") is False
    assert processor._check_balanced_braces("SELECT * WHERE { ?s ?p ?o } }") is False
