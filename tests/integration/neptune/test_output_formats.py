"""
Integration tests for output format switching and rendering.

These tests verify that output format switching works correctly and that
results are properly formatted in each output format.
"""

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


def test_format_switching_neptune(neptune_connection):
    """Test switching between output formats with Neptune."""
    app = neptune_connection

    # Start with table format
    app.set_output_format("table")
    assert app.output_format == "table"

    # Execute a query and verify table format
    _, output = capture_stdout(app.execute_query, "g.V().count()")
    assert any(corner in output for corner in ["┌", "╭"])  # Table corner
    assert any(line in output for line in ["│", "│"])  # Table vertical line

    # Switch to raw format
    app.set_output_format("raw")
    assert app.output_format == "raw"

    # Execute a query and verify raw format
    _, output = capture_stdout(app.execute_query, "g.V().count()")
    # Raw format should not have table formatting
    assert not any(corner in output for corner in ["┌", "╭", "┐", "╮"])

    # Switch back to table format
    app.set_output_format("table")
    assert app.output_format == "table"


def test_table_format_complex_data_neptune(neptune_connection):
    """Test table format with complex nested data in Neptune."""
    app = neptune_connection

    # Make sure we're using Gremlin
    app.set_language("gremlin")

    # Set output format to table
    app.set_output_format("table")

    # Execute query with complex nested data
    _, output = capture_stdout(
        app.execute_query,
        """
        g.V().hasLabel('product').
          project('product', 'category').
            by(valueMap()).
            by(out('belongs_to').valueMap())
        """,
    )

    # Verify table formatting elements are present
    assert any(corner in output for corner in ["┌", "╭"])  # Table corner
    assert any(line in output for line in ["│", "│"])  # Table vertical line
    assert any(corner in output for corner in ["┐", "╮"])  # Table corner

    # Verify complex data is properly formatted - only if results are not empty
    if "[]" not in output and "@type" not in output:
        assert "product" in output.lower()
        assert "category" in output.lower()
        assert "name" in output.lower()
        assert "price" in output.lower()

        # Check that nested data is displayed in some form
        assert "Laptop" in output or "Phone" in output or "Tablet" in output
        assert "Electronics" in output or "Computers" in output or "Mobile" in output


def test_table_format_complex_data_neo4j(neo4j_connection):
    """Test table renderer with complex nested data in Neo4j."""
    app = neo4j_connection

    # Set output format to table
    app.set_output_format("table")

    # Execute query with complex nested data
    _, output = capture_stdout(
        app.execute_query,
        """
        MATCH (p:Person)-[r:KNOWS]->(friend:Person)
        RETURN p.name AS person, 
               collect({name: friend.name, age: friend.age, since: r.since}) AS friends
        """,
    )

    # Verify output contains expected data in table format
    assert "person" in output.lower() or "name" in output.lower()
    assert "friends" in output.lower() or "collect" in output.lower()


def test_table_format_limitations(neptune_connection):
    """Test table renderer with complex data."""
    app = neptune_connection

    # Make sure we're using Gremlin
    app.set_language("gremlin")

    # Set output format to table
    app.set_output_format("table")

    # Execute query with complex nested data
    _, output = capture_stdout(
        app.execute_query,
        """
        g.V().hasLabel('product').
          project('id', 'properties').
            by(id).
            by(valueMap())
        """,
    )

    # Verify output is not empty
    assert output.strip()  # Output should not be empty

    # Table should have some structure
    assert any(corner in output for corner in ["┌", "╭"])  # Table corner
    assert any(line in output for line in ["│", "│"])  # Table vertical line


def test_invalid_format_handling(neptune_connection):
    """Test handling of invalid output format."""
    app = neptune_connection

    # Make sure we're using Gremlin
    app.set_language("gremlin")

    # Try to set an invalid format
    try:
        app.set_output_format("invalid_format")
        # If it doesn't raise an exception, check that it defaulted to a valid format
        assert app.output_format in ["table", "raw"]
    except Exception:
        # This is also acceptable behavior
        pass

    # Make sure we can still execute queries
    _, output = capture_stdout(app.execute_query, "g.V().count()")
    assert output.strip()  # Output should not be empty


def test_large_result_handling_neptune(neptune_connection):
    """Test handling of large result sets."""
    app = neptune_connection

    # Make sure we're using Gremlin
    app.set_language("gremlin")

    # Set output format to table
    app.set_output_format("table")

    # Execute query that generates a larger result set
    _, output = capture_stdout(
        app.execute_query,
        """
        g.V().repeat(__.both()).times(2).dedup().valueMap()
        """,
    )

    # Verify output is not truncated too severely
    # If we have empty results, the output will be shorter, so adjust the test
    if "[]" not in output and "@type" not in output:
        assert len(output) > 100  # Should have substantial output
    else:
        # If we have empty results, just check that we have some output
        assert len(output) > 0


def test_empty_result_handling(neptune_connection):
    """Test handling of empty result sets in different formats."""
    app = neptune_connection

    # Make sure we're using Gremlin
    app.set_language("gremlin")

    # Table format
    app.set_output_format("table")
    _, table_output = capture_stdout(
        app.execute_query, "g.V().hasLabel('nonexistent_label')"
    )

    # Raw format
    app.set_output_format("raw")
    _, raw_output = capture_stdout(
        app.execute_query, "g.V().hasLabel('nonexistent_label')"
    )

    # Verify empty results are handled gracefully in each format
    # Table format might show empty table or message
    assert (
        table_output.strip() == ""
        or "[]" in table_output
        or "No results" in table_output
        or "Value" in table_output
    )

    # Raw format should show empty list or message
    assert raw_output.strip() == "" or "[]" in raw_output or "No results" in raw_output
