"""
Integration tests for Neo4j adapter.

These tests require a running Neo4j instance.
"""

import re
from io import StringIO
import sys


def capture_stdout(func, *args, **kwargs):
    """Capture stdout during function execution."""
    old_stdout = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output
    try:
        result = func(*args, **kwargs)
        output = captured_output.getvalue()
        return result, output
    finally:
        sys.stdout = old_stdout


def test_neo4j_cypher_query(neo4j_connection):
    """Test basic Cypher query execution."""
    app = neo4j_connection

    # Make sure we're using Cypher language
    app.set_language("cypher")

    # Execute a simple query and capture the output
    _, output = capture_stdout(
        app.execute_query, "MATCH (p:Person) RETURN p.name AS name, p.age AS age"
    )

    # Check that the output contains expected data
    assert "Alice" in output
    assert "Bob" in output
    assert "Charlie" in output
    assert "David" in output


def test_neo4j_relationship_query(neo4j_connection):
    """Test relationship query execution."""
    app = neo4j_connection

    # Make sure we're using Cypher language
    app.set_language("cypher")

    # Execute a relationship query and capture the output
    _, output = capture_stdout(
        app.execute_query,
        """
        MATCH (a:Person)-[r:KNOWS]->(b:Person)
        RETURN a.name AS from, b.name AS to, r.since AS since
        """,
    )

    # Check that the output contains expected data
    assert "from" in output
    assert "to" in output
    assert "since" in output
    assert "Alice" in output
    assert "Bob" in output


def test_neo4j_language_switching(neo4j_connection):
    """Test switching between query languages."""
    app = neo4j_connection

    # Make sure we're using Cypher language
    app.set_language("cypher")

    # Execute a Cypher query
    _, output = capture_stdout(
        app.execute_query, "MATCH (p:Person) RETURN count(p) AS count"
    )
    assert "4" in output  # Just check for the count value instead of column name

    # Neo4j only supports Cypher, so trying to switch to Gremlin should fail
    try:
        app.set_language("gremlin")
        # If it doesn't fail, switch back to Cypher
        app.set_language("cypher")
    except Exception:
        # This is expected behavior
        pass

    # Make sure we're using Cypher
    assert app.current_language == "cypher"


# Tests from test_neo4j_output.py


def test_neo4j_person_query_table_format(neo4j_connection):
    """Test person query with table output format."""
    app = neo4j_connection

    # Set output format to table
    app.set_output_format("table")

    # Execute query and capture output
    _, output = capture_stdout(
        app.execute_query,
        "MATCH (p:Person) RETURN p.name AS name, p.age AS age ORDER BY p.name",
    )

    # Verify output contains expected person data
    assert "Alice" in output
    assert "Bob" in output
    assert "Charlie" in output
    assert "David" in output

    # Verify age data
    assert "30" in output  # Alice's age
    assert "40" in output  # Bob's age
    assert "25" in output  # Charlie's age
    assert "35" in output  # David's age

    # Verify table formatting elements are present
    # Note: Rich's box drawing characters might be different (rounded box)
    assert any(corner in output for corner in ["┌", "╭"])  # Table corner
    assert any(line in output for line in ["│", "│"])  # Table vertical line
    assert any(corner in output for corner in ["┐", "╮"])  # Table corner
    assert any(corner in output for corner in ["└", "╰"])  # Table corner
    assert any(corner in output for corner in ["┘", "╯"])  # Table corner

    # Verify column headers
    assert "name" in output
    assert "age" in output


def test_neo4j_relationship_details_query(neo4j_connection):
    """Test relationship details query results."""
    app = neo4j_connection

    # Set output format to table for readability
    app.set_output_format("table")

    # Execute query to get relationship details
    _, output = capture_stdout(
        app.execute_query,
        """
        MATCH (a:Person)-[r:KNOWS]->(b:Person)
        RETURN a.name AS from, b.name AS to, r.since AS since
        ORDER BY a.name, b.name
        """,
    )

    # Verify output contains expected relationship data
    assert "from" in output
    assert "to" in output
    assert "since" in output

    # Check specific relationships
    assert re.search(r"Alice.*Bob.*2010", output, re.DOTALL) or re.search(
        r"2010.*Alice.*Bob", output, re.DOTALL
    )

    assert re.search(r"Alice.*David.*2018", output, re.DOTALL) or re.search(
        r"2018.*Alice.*David", output, re.DOTALL
    )

    assert re.search(r"Bob.*Charlie.*2015", output, re.DOTALL) or re.search(
        r"2015.*Bob.*Charlie", output, re.DOTALL
    )

    assert re.search(r"Charlie.*David.*2020", output, re.DOTALL) or re.search(
        r"2020.*Charlie.*David", output, re.DOTALL
    )


def test_neo4j_path_query(neo4j_connection):
    """Test path query results."""
    app = neo4j_connection

    # Set output format to table
    app.set_output_format("table")

    # Execute path query
    _, output = capture_stdout(
        app.execute_query,
        """
        MATCH path = (a:Person {name: 'Alice'})-[:KNOWS*1..3]->(c:Person)
        RETURN a.name AS start, c.name AS end, length(path) AS path_length
        ORDER BY path_length
        """,
    )

    # Verify output contains expected path data
    assert "start" in output
    assert "end" in output
    assert "path_length" in output

    # Direct connections from Alice
    assert re.search(r"Alice.*Bob.*1", output, re.DOTALL) or re.search(
        r"1.*Alice.*Bob", output, re.DOTALL
    )

    assert re.search(r"Alice.*David.*1", output, re.DOTALL) or re.search(
        r"1.*Alice.*David", output, re.DOTALL
    )

    # Two-step path: Alice -> Bob -> Charlie
    assert re.search(r"Alice.*Charlie.*2", output, re.DOTALL) or re.search(
        r"2.*Alice.*Charlie", output, re.DOTALL
    )


def test_neo4j_aggregation_query(neo4j_connection):
    """Test aggregation query results."""
    app = neo4j_connection

    # Set output format to table
    app.set_output_format("table")

    # Execute aggregation query
    _, output = capture_stdout(
        app.execute_query,
        """
        MATCH (p:Person)
        RETURN avg(p.age) AS avg_age, min(p.age) AS min_age, max(p.age) AS max_age
        """,
    )

    # Verify output contains expected aggregation data
    assert "avg_age" in output
    assert "min_age" in output
    assert "max_age" in output

    # Check aggregation values
    # Average age: (30 + 40 + 25 + 35) / 4 = 32.5
    assert "32.5" in output

    # Min age: 25 (Charlie)
    assert "25" in output

    # Max age: 40 (Bob)
    assert "40" in output


def test_neo4j_error_handling(neo4j_connection):
    """Test error handling for invalid queries."""
    app = neo4j_connection

    # Execute an invalid query and capture output
    _, output = capture_stdout(
        app.execute_query,
        "MATCH (p:Person) RETURN p.invalid_property",  # Property doesn't exist
    )

    # Verify results are handled gracefully
    # This should return null values, not error
    assert "null" in output.lower() or "none" in output.lower()

    # Try a syntax error query
    _, output = capture_stdout(
        app.execute_query,
        "MATCH p:Person) RETURN p",  # Missing opening parenthesis
    )

    # Verify error message is displayed
    assert "error" in output.lower() or "exception" in output.lower()


def test_neo4j_complex_query(neo4j_connection):
    """Test complex query with multiple operations."""
    app = neo4j_connection

    # Set output format to table
    app.set_output_format("table")

    # Execute complex query
    _, output = capture_stdout(
        app.execute_query,
        """
        MATCH (p1:Person)-[r:KNOWS]->(p2:Person)
        WITH p1, count(r) AS num_friends, collect(p2.name) AS friend_names
        RETURN p1.name AS person, num_friends, friend_names
        ORDER BY num_friends DESC
        """,
    )

    # Verify output contains expected data
    assert "person" in output
    assert "num_friends" in output
    assert "friend_names" in output

    # Alice knows 2 people (Bob and David)
    assert re.search(r"Alice.*2", output, re.DOTALL) or re.search(
        r"2.*Alice", output, re.DOTALL
    )

    # Check that friend names are collected
    assert "Bob" in output
    assert "David" in output
    assert "Charlie" in output
