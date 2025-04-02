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
    is_valid, error = processor.validate_query(query)
    assert is_valid is True
    assert error is None

    # CREATE query
    query = """
    CREATE (p:Person {name: 'Alice', age: 30})
    RETURN p
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is True
    assert error is None

    # MERGE query
    query = """
    MERGE (p:Person {name: 'Alice'})
    ON CREATE SET p.created = timestamp()
    RETURN p
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is True
    assert error is None


def test_validate_query_invalid(processor):
    """Test validating invalid Cypher queries."""
    # Missing required clause
    query = """
    (p:Person)
    WHERE p.name = 'Alice'
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is False
    assert "Missing required clause" in error

    # Unbalanced parentheses
    query = """
    MATCH (p:Person
    WHERE p.name = 'Alice'
    RETURN p
    """
    is_valid, error = processor.validate_query(query)
    assert is_valid is False
    assert "Unbalanced" in error


def test_get_completion_suggestions(processor):
    """Test getting completion suggestions."""
    # Suggest keywords
    suggestions = processor.get_completion_suggestions("MAT", 3)
    assert "MATCH" in suggestions

    # Suggest after partial keyword
    suggestions = processor.get_completion_suggestions("MATCH (p:Person) RET", 19)
    assert "RETURN" in suggestions

    # No suggestions for empty input
    suggestions = processor.get_completion_suggestions("", 0)
    assert len(suggestions) == 0


def test_get_syntax_lexer(processor):
    """Test getting syntax lexer."""
    lexer = processor.get_syntax_lexer()
    assert lexer is CypherLexer


def test_process_results_neo4j_http_format(processor):
    """Test processing results in Neo4j HTTP API format."""
    # Neo4j HTTP API format
    results = {
        "columns": ["p.name", "p.age"],
        "data": [{"row": ["Alice", 30]}, {"row": ["Bob", 25]}],
    }

    processed = processor.process_results(results)

    assert len(processed) == 2
    assert processed[0]["p.name"] == "Alice"
    assert processed[0]["p.age"] == 30
    assert processed[1]["p.name"] == "Bob"
    assert processed[1]["p.age"] == 25


def test_process_results_simple_list(processor):
    """Test processing results as simple list."""
    # Already processed results
    results = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    processed = processor.process_results(results)

    assert processed == results
    assert len(processed) == 2
    assert processed[0]["name"] == "Alice"
    assert processed[1]["name"] == "Bob"


def test_process_neo4j_value_node(processor):
    """Test processing Neo4j node value."""

    # Create a mock Neo4j node
    class MockNode:
        def __init__(self, id, labels, properties):
            self.id = id
            self.labels = labels
            self._properties = properties

        def __iter__(self):
            return iter(self._properties.items())

        def items(self):
            return self._properties.items()

    # Create a node
    node = MockNode(1, ["Person"], {"name": "Alice", "age": 30})

    # Process the node
    processed = processor._process_neo4j_value(node)

    # Check the result
    assert processed["id"] == 1
    assert processed["labels"] == ["Person"]
    assert processed["properties"]["name"] == "Alice"
    assert processed["properties"]["age"] == 30


def test_process_neo4j_value_relationship(processor):
    """Test processing Neo4j relationship value."""

    # Create a mock Neo4j relationship
    class MockRelationship:
        def __init__(self, id, type, properties, start_id, end_id):
            self.id = id
            self.type = type
            self._properties = properties
            self.start_node = MockNode(start_id)
            self.end_node = MockNode(end_id)

        def __iter__(self):
            return iter(self._properties.items())

        def items(self):
            return self._properties.items()

    # Create a mock node for relationship endpoints
    class MockNode:
        def __init__(self, id):
            self.id = id

    # Create a relationship
    rel = MockRelationship(1, "KNOWS", {"since": 2020}, 101, 102)

    # Process the relationship
    processed = processor._process_neo4j_value(rel)

    # Check the result
    assert processed["id"] == 1
    assert processed["type"] == "KNOWS"
    assert processed["properties"]["since"] == 2020
    assert processed["start"] == 101
    assert processed["end"] == 102


def test_process_neo4j_value_path(processor):
    """Test processing Neo4j path value."""

    # Create mock classes for Neo4j path
    class MockPath:
        def __init__(self, start, end, relationships, segments):
            self.start = start
            self.end = end
            self.relationships = relationships
            self.segments = segments

    class MockSegment:
        def __init__(self, start, relationship, end):
            self.start = start
            self.relationship = relationship
            self.end = end

    class MockNode:
        def __init__(self, id, labels=None, properties=None):
            self.id = id
            self.labels = labels or []
            self._properties = properties or {}

        def __iter__(self):
            return iter(self._properties.items())

    class MockRelationship:
        def __init__(self, id, type):
            self.id = id
            self.type = type
            self._properties = {}

        def __iter__(self):
            return iter(self._properties.items())

    # Create nodes and relationships
    start_node = MockNode(1, ["Person"], {"name": "Alice"})
    middle_node = MockNode(2, ["Person"], {"name": "Bob"})
    end_node = MockNode(3, ["Person"], {"name": "Charlie"})

    rel1 = MockRelationship(101, "KNOWS")
    rel2 = MockRelationship(102, "KNOWS")

    # Create segments
    segment1 = MockSegment(start_node, rel1, middle_node)
    segment2 = MockSegment(middle_node, rel2, end_node)

    # Create path
    path = MockPath(start_node, end_node, [rel1, rel2], [segment1, segment2])

    # Process the path
    processed = processor._process_neo4j_value(path)

    # Check the result
    assert processed["length"] == 2
    assert processed["start"]["id"] == 1
    assert processed["end"]["id"] == 3
    assert len(processed["segments"]) == 2
    assert processed["segments"][0]["start"]["id"] == 1
    assert processed["segments"][0]["relationship"]["id"] == 101
    assert processed["segments"][0]["end"]["id"] == 2
    assert processed["segments"][1]["start"]["id"] == 2
    assert processed["segments"][1]["relationship"]["id"] == 102
    assert processed["segments"][1]["end"]["id"] == 3


def test_process_neo4j_value_primitive(processor):
    """Test processing primitive values."""
    # Test primitive values
    assert processor._process_neo4j_value(123) == 123
    assert processor._process_neo4j_value("test") == "test"
    assert processor._process_neo4j_value(True) is True
    assert processor._process_neo4j_value(None) is None

    # Test list
    assert processor._process_neo4j_value([1, 2, 3]) == [1, 2, 3]

    # Test dict
    assert processor._process_neo4j_value({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_check_balanced_braces(processor):
    """Test checking for balanced braces."""
    # Balanced braces
    assert processor._check_balanced_braces("MATCH (p:Person) RETURN p") is True
    assert (
        processor._check_balanced_braces("MATCH (p:Person {name: 'Alice'}) RETURN p")
        is True
    )
    assert (
        processor._check_balanced_braces(
            "MATCH (p:Person)-[r:KNOWS]->(f:Person) RETURN p, r, f"
        )
        is True
    )

    # Unbalanced braces
    assert processor._check_balanced_braces("MATCH (p:Person RETURN p") is False
    assert processor._check_balanced_braces("MATCH (p:Person) RETURN p]") is False
    assert processor._check_balanced_braces("MATCH {p:Person}) RETURN p") is False
