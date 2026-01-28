"""
End-to-end integration tests for GraphSh.
"""

from unittest.mock import MagicMock, patch

import pytest

from graphsh.cli.app import GraphShApp
from graphsh.db.adapters.base import DatabaseAdapter


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock(spec=DatabaseAdapter)
    adapter.connect.return_value = True
    adapter.execute_query.return_value = [{"id": 1, "name": "test"}]
    return adapter


@pytest.mark.skip(reason="End-to-end test requiring actual database")
def test_end_to_end_workflow(mock_adapter):
    """Test end-to-end workflow."""
    with patch("graphsh.db.connection.get_adapter", return_value=mock_adapter):
        with patch("graphsh.cli.app.Connection"):
            with patch("graphsh.cli.app.ConfigManager"):
                with patch("graphsh.cli.repl.GraphShRepl") as mock_repl:
                    # Create app
                    app = GraphShApp()

                    # Connect to database
                    app.connect(
                        endpoint="localhost",
                        port=8182,
                        auth_type="none",
                        language="gremlin",
                        type="neptune",
                    )

                    # Set language
                    app.set_language("gremlin")

                    # Execute query
                    with patch("graphsh.cli.app.console.print"):
                        with patch("graphsh.cli.app.get_logger") as mock_get_logger:
                            mock_logger = MagicMock()
                            mock_get_logger.return_value = mock_logger

                            app.execute_query("g.V().limit(5)")
