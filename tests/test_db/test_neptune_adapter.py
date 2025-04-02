"""
Unit tests for Neptune adapter.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from graphsh.db.adapters.neptune import NeptuneAdapter


def test_init():
    """Test adapter initialization."""
    adapter = NeptuneAdapter(endpoint="neptune-instance.region.amazonaws.com")
    assert adapter.endpoint == "neptune-instance.region.amazonaws.com"
    assert adapter.port == 443
    assert adapter.http_session is None


def test_connect():
    """Test connecting to Neptune."""
    mock_session = MagicMock()
    status_response = MagicMock()
    status_response.raise_for_status.return_value = None
    mock_session.get.return_value = status_response

    with patch("requests.Session", return_value=mock_session):
        adapter = NeptuneAdapter(endpoint="localhost:8182")
        result = adapter.connect()

        assert result is True
        assert adapter.http_session == mock_session


def test_execute_gremlin_query():
    """Test executing Gremlin query."""
    # Setup
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "requestId": "test-id",
        "status": {"message": "", "code": 200, "attributes": {}},
        "result": {"data": [{"id": 1, "label": "person"}], "meta": {}},
    }
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        adapter = NeptuneAdapter(endpoint="localhost:8182")
        adapter.http_session = mock_session

        # Execute
        query = "g.V().limit(1)"
        result = adapter.execute_query(query, language="gremlin")

        # Verify
        assert isinstance(result, list)
        assert len(result) == 1
        assert "id" in result[0]
        assert result[0]["id"] == 1


def test_execute_gremlin_query_with_params():
    """Test executing Gremlin query with parameters."""
    # Setup
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {"data": [{"id": 1, "name": "Alice"}], "meta": {}}
    }
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        adapter = NeptuneAdapter(endpoint="localhost:8182")
        adapter.http_session = mock_session

        # Execute
        query = "g.V().has('name', name)"
        params = {"name": "Alice"}
        result = adapter.execute_query(query, language="gremlin", **params)

        # Verify
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"


def test_execute_sparql_query():
    """Test executing SPARQL query."""
    # Setup
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": {
            "bindings": [
                {
                    "s": {"type": "uri", "value": "http://example.org/person/1"},
                    "p": {"type": "uri", "value": "http://example.org/name"},
                    "o": {"type": "literal", "value": "Alice"},
                }
            ]
        }
    }
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        adapter = NeptuneAdapter(endpoint="localhost:8182")
        adapter.http_session = mock_session

        # Execute
        query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
        result = adapter.execute_query(query, language="sparql")

        # Verify
        assert isinstance(result, list)
        assert len(result) == 1
        assert "s" in result[0]
        assert result[0]["s"] == "http://example.org/person/1"


def test_execute_cypher_query():
    """Test executing OpenCypher query."""
    # Setup
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"n.name": "Alice", "labels": ["Person"]}]
    }
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        adapter = NeptuneAdapter(endpoint="localhost:8182")
        adapter.http_session = mock_session

        # Execute
        query = "MATCH (n:Person) RETURN n.name, labels(n) as labels LIMIT 1"
        result = adapter.execute_query(query, language="cypher")

        # Verify
        assert isinstance(result, list)
        assert len(result) == 1
        assert "n.name" in result[0]
        assert result[0]["n.name"] == "Alice"
        assert result[0]["labels"] == ["Person"]


def test_execute_cypher_query_with_params():
    """Test executing OpenCypher query with parameters."""
    # Setup
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"n": {"name": "Alice"}}]}
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        adapter = NeptuneAdapter(endpoint="localhost:8182")
        adapter.http_session = mock_session

        # Execute
        query = "MATCH (n:Person) WHERE n.name = $name RETURN n"
        params = {"name": "Alice"}
        result = adapter.execute_query(query, language="cypher", **params)

        # Verify
        assert isinstance(result, list)


def test_execute_unsupported_language():
    """Test executing query with unsupported language."""
    adapter = NeptuneAdapter(endpoint="localhost:8182")
    with pytest.raises(ValueError, match="Unsupported language"):
        adapter.execute_query("query", language="unsupported")


def test_close():
    """Test closing connection."""
    mock_session = MagicMock()

    adapter = NeptuneAdapter(endpoint="localhost:8182")
    adapter.http_session = mock_session
    adapter.close()

    mock_session.close.assert_called_once()
    assert adapter.http_session is None


def test_normalize_sparql_binding():
    """Test normalizing SPARQL binding."""
    adapter = NeptuneAdapter(endpoint="localhost:8182")

    # URI
    binding = {"s": {"type": "uri", "value": "http://example.org/person/1"}}
    result = adapter._normalize_sparql_binding(binding)
    assert result["s"] == "http://example.org/person/1"

    # Integer literal
    binding = {
        "age": {
            "type": "literal",
            "value": "30",
            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
        }
    }
    result = adapter._normalize_sparql_binding(binding)
    assert result["age"] == 30

    # Float literal
    binding = {
        "score": {
            "type": "literal",
            "value": "4.5",
            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
        }
    }
    result = adapter._normalize_sparql_binding(binding)
    assert result["score"] == 4.5

    # Boolean literal
    binding = {
        "active": {
            "type": "literal",
            "value": "true",
            "datatype": "http://www.w3.org/2001/XMLSchema#boolean",
        }
    }
    result = adapter._normalize_sparql_binding(binding)
    assert result["active"] is True

    # Plain literal
    binding = {"name": {"type": "literal", "value": "Alice"}}
    result = adapter._normalize_sparql_binding(binding)
    assert result["name"] == "Alice"
