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
    is_valid, error = processor.validate_query(query)
    assert is_valid is True
    assert error is None

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
    is_valid, error = processor.validate_query(query)
    assert is_valid is True
    assert error is None

    # ASK query
    query = """
    ASK {
        ?person rdf:type foaf:Person .
        ?person foaf:name "Alice" .
    }
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is True
    assert error is None


def test_validate_query_invalid(processor):
    """Test validating invalid SPARQL queries."""
    # Missing query type
    query = """
    ?person rdf:type foaf:Person .
    ?person foaf:name ?name .
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is False
    assert "Missing query type" in error

    # Unbalanced braces
    query = """
    SELECT ?name
    WHERE {
        ?person rdf:type foaf:Person .
        ?person foaf:name ?name .
    
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is False
    assert "Unbalanced braces" in error


def test_get_completion_suggestions(processor):
    """Test getting completion suggestions."""
    # Suggest keywords
    suggestions = processor.get_completion_suggestions("SEL", 3)
    assert "SELECT" in suggestions

    # Suggest after partial keyword - this test is now fixed with the updated implementation
    # that specifically adds WHERE after SELECT
    suggestions = processor.get_completion_suggestions("SELECT ", 7)
    assert "WHERE" in suggestions

    # Suggest RDF terms
    suggestions = processor.get_completion_suggestions("?s rdf:", 7)
    assert "rdf:type" in suggestions

    # No suggestions for empty input
    suggestions = processor.get_completion_suggestions("", 0)
    assert len(suggestions) == 0


def test_get_syntax_lexer(processor):
    """Test getting syntax lexer."""
    lexer = processor.get_syntax_lexer()
    assert lexer is SparqlLexer


def test_process_results_json_format(processor):
    """Test processing results in SPARQL JSON format."""
    # SPARQL JSON results format
    results = {
        "head": {"vars": ["name", "email"]},
        "results": {
            "bindings": [
                {
                    "name": {"type": "literal", "value": "Alice"},
                    "email": {"type": "uri", "value": "mailto:alice@example.org"},
                },
                {
                    "name": {"type": "literal", "value": "Bob"},
                    "email": {"type": "uri", "value": "mailto:bob@example.org"},
                },
            ]
        },
    }

    processed = processor.process_results(results)

    assert len(processed) == 2
    assert processed[0]["name"] == "Alice"
    assert processed[0]["email"] == "mailto:alice@example.org"
    assert processed[1]["name"] == "Bob"
    assert processed[1]["email"] == "mailto:bob@example.org"


def test_process_results_ask_query(processor):
    """Test processing results from ASK query."""
    # ASK query result (true)
    results = {"boolean": True}
    processed = processor.process_results(results)

    assert len(processed) == 1
    assert processed[0]["result"] is True

    # ASK query result (false)
    results = {"boolean": False}
    processed = processor.process_results(results)

    assert len(processed) == 1
    assert processed[0]["result"] is False


def test_process_results_simple_list(processor):
    """Test processing results as simple list."""
    # Already processed results
    results = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    processed = processor.process_results(results)

    assert processed == results
    assert len(processed) == 2
    assert processed[0]["name"] == "Alice"
    assert processed[1]["name"] == "Bob"


def test_extract_sparql_value(processor):
    """Test extracting values from SPARQL bindings."""
    # URI
    uri_value = {"type": "uri", "value": "http://example.org/alice"}
    assert processor._extract_sparql_value(uri_value) == "http://example.org/alice"

    # Simple literal
    literal_value = {"type": "literal", "value": "Alice"}
    assert processor._extract_sparql_value(literal_value) == "Alice"

    # Typed literals
    integer_value = {
        "type": "literal",
        "value": "42",
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
    }
    assert processor._extract_sparql_value(integer_value) == 42

    decimal_value = {
        "type": "literal",
        "value": "3.14",
        "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
    }
    assert processor._extract_sparql_value(decimal_value) == 3.14

    boolean_value = {
        "type": "literal",
        "value": "true",
        "datatype": "http://www.w3.org/2001/XMLSchema#boolean",
    }
    assert processor._extract_sparql_value(boolean_value) is True

    # Blank node
    bnode_value = {"type": "bnode", "value": "b0"}
    assert processor._extract_sparql_value(bnode_value) == "_:b0"

    # Missing value
    empty_value = {}
    assert processor._extract_sparql_value(empty_value) is None


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
