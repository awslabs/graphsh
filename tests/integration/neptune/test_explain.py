"""Integration tests for Neptune explain functionality."""

import pytest


def test_gremlin_explain(neptune_connection):
    """Test Gremlin explain mode."""
    app = neptune_connection
    app.set_language("gremlin")

    result = app.connection.adapter.execute_explain(
        "g.V().hasLabel('product').count()", "gremlin", "explain"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    # Gremlin explain returns traversal explanation
    assert "Traversal" in result[0]["explain"] or "Original" in result[0]["explain"]


def test_gremlin_profile(neptune_connection):
    """Test Gremlin profile mode."""
    app = neptune_connection
    app.set_language("gremlin")

    result = app.connection.adapter.execute_explain(
        "g.V().hasLabel('product').count()", "gremlin", "profile"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    # Profile includes timing information
    explain_text = result[0]["explain"]
    assert "Traversal" in explain_text or "dur" in explain_text.lower()


def test_sparql_explain(neptune_connection):
    """Test SPARQL explain mode."""
    app = neptune_connection

    result = app.connection.adapter.execute_explain(
        "SELECT ?s WHERE { ?s ?p ?o } LIMIT 10", "sparql", "explain"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    # SPARQL explain returns query plan
    explain_text = result[0]["explain"]
    assert "ID" in explain_text or "Name" in explain_text or "╔" in explain_text


def test_sparql_profile(neptune_connection):
    """Test SPARQL profile (dynamic) mode."""
    app = neptune_connection

    result = app.connection.adapter.execute_explain(
        "SELECT ?s WHERE { ?s ?p ?o } LIMIT 10", "sparql", "profile"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    # Dynamic mode includes execution stats
    explain_text = result[0]["explain"]
    assert "Units" in explain_text or "Time" in explain_text or "╔" in explain_text


def test_sparql_details(neptune_connection):
    """Test SPARQL details mode."""
    app = neptune_connection

    result = app.connection.adapter.execute_explain(
        "SELECT ?s WHERE { ?s ?p ?o } LIMIT 10", "sparql", "details"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    # Details mode includes query string and estimates
    explain_text = result[0]["explain"]
    assert "╔" in explain_text or "ID" in explain_text


def test_cypher_explain(neptune_connection):
    """Test Cypher explain mode."""
    app = neptune_connection

    result = app.connection.adapter.execute_explain(
        "MATCH (n) RETURN count(n)", "cypher", "explain"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    explain_text = result[0]["explain"]
    assert len(explain_text) > 0


def test_cypher_profile(neptune_connection):
    """Test Cypher profile (dynamic) mode."""
    app = neptune_connection

    result = app.connection.adapter.execute_explain(
        "MATCH (n) RETURN count(n)", "cypher", "profile"
    )

    assert len(result) == 1
    assert "explain" in result[0]
    explain_text = result[0]["explain"]
    assert len(explain_text) > 0


def test_explain_modes_list(neptune_connection):
    """Test that adapter reports correct explain modes."""
    app = neptune_connection
    modes = app.connection.adapter.get_explain_modes()

    assert "off" in modes
    assert "explain" in modes
    assert "profile" in modes
    assert "details" in modes
