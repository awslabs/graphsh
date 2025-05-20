"""
Tests for connection manager.
"""

import pytest
from unittest.mock import MagicMock, patch

from graphsh.db.connection import Connection as ConnectionManager


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.connect = MagicMock(return_value=True)
    adapter.close = MagicMock()
    return adapter


def test_connect_with_none_auth(mock_adapter):
    """Test connecting with none auth."""
    with patch(
        "graphsh.db.connection.get_adapter",
        return_value=mock_adapter,
    ):
        manager = ConnectionManager()
        result = manager.connect(
            type="neptune",
            endpoint="localhost",
            port=8182,
            auth_type="none",
        )

        assert result is True
        mock_adapter.connect.assert_called_once()

        # Verify the adapter was created with the correct parameters
        assert manager.current_connection is True


def test_execute_query(mock_adapter):
    """Test executing query."""
    with patch(
        "graphsh.db.connection.get_adapter",
        return_value=mock_adapter,
    ):
        manager = ConnectionManager()

        # Set up connection
        manager.connect(
            type="neptune",
            endpoint="localhost",
            port=8182,
            auth_type="none",
            language="gremlin",
        )

        # Set up mock adapter
        mock_adapter.execute_query.return_value = {
            "results": [{"id": 1, "name": "Alice"}]
        }

        # Execute query
        results = manager.execute("g.V().limit(5)")

        # Check that query was executed
        mock_adapter.execute_query.assert_called_with("g.V().limit(5)", "gremlin")

        # Check results
        assert results == [{"id": 1, "name": "Alice"}]


def test_execute_query_no_connection():
    """Test executing query with no connection."""
    manager = ConnectionManager()

    # Execute query
    with pytest.raises(RuntimeError) as excinfo:
        manager.execute("g.V().limit(5)")

    # Check error message
    assert "Not connected to a database" in str(excinfo.value)


def test_disconnect(mock_adapter):
    """Test disconnecting."""
    with patch(
        "graphsh.db.connection.get_adapter",
        return_value=mock_adapter,
    ):
        manager = ConnectionManager()

        # Set up connection
        manager.connect(
            type="neptune",
            endpoint="localhost",
            port=8182,
            auth_type="none",
        )

        # Disconnect
        manager.disconnect()

        # Check that adapter was closed
        mock_adapter.close.assert_called_once()

        # Check that connection was reset
        assert manager.current_connection is None
        assert manager.connection_params == {}
