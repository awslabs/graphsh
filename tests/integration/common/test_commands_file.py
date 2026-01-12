"""
Integration tests for commands file functionality.
"""

import os
import tempfile
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


@pytest.fixture
def commands_file():
    """Create a temporary commands file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("/language gremlin\n")
        f.write("g.V().limit(5);\n")
        f.write("/format json\n")
        f.write("g.E().limit(3);\n")
        f.write("/quit\n")
        file_path = f.name

    yield file_path

    # Clean up
    os.unlink(file_path)


@pytest.mark.skip(reason="Integration test requiring actual database")
def test_commands_file(commands_file, mock_adapter):
    """Test executing commands from file."""
    with patch("graphsh.db.connection.get_adapter", return_value=mock_adapter):
        with patch("graphsh.cli.app.Connection"):
            with patch("graphsh.cli.app.ConfigManager"):
                with patch("graphsh.cli.repl.GraphShRepl") as mock_repl:
                    # Create app
                    app = GraphShApp()

                    # Execute commands from file
                    app.run_commands_file(commands_file)

                    # Check that REPL was not started
                    mock_repl.assert_not_called()
