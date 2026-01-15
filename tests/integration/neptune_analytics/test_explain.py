"""Integration tests for Neptune Analytics explain functionality."""

import pytest


def test_cypher_explain(neptune_analytics_connection):
    """Test Cypher explain mode on Neptune Analytics."""
    app = neptune_analytics_connection

    result = app.connection.adapter.execute_explain(
        "MATCH (n) RETURN count(n)", "cypher", "explain"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    explain_text = result[0]["explain"]
    assert len(explain_text) > 0


def test_cypher_details(neptune_analytics_connection):
    """Test Cypher details mode on Neptune Analytics."""
    app = neptune_analytics_connection

    result = app.connection.adapter.execute_explain(
        "MATCH (n) RETURN count(n)", "cypher", "details"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    explain_text = result[0]["explain"]
    assert len(explain_text) > 0


def test_explain_modes_list(neptune_analytics_connection):
    """Test that adapter reports correct explain modes."""
    app = neptune_analytics_connection
    modes = app.connection.adapter.get_explain_modes()

    assert "off" in modes
    assert "explain" in modes
    assert "details" in modes
    # Neptune Analytics doesn't support profile mode
    assert "profile" not in modes


def test_unsupported_language_explain(neptune_analytics_connection):
    """Test explain with unsupported language returns error."""
    app = neptune_analytics_connection

    result = app.connection.adapter.execute_explain(
        "g.V().count()", "gremlin", "explain"
    )

    assert len(result) == 1
    assert "error" in result[0]
