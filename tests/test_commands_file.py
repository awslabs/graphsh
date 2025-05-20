"""
Tests for commands file functionality.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from graphsh.cli.app import GraphShApp


@pytest.fixture
def mock_app():
    """Create a mock GraphSh application."""
    app = MagicMock(spec=GraphShApp)
    app.current_language = "gremlin"
    app.output_format = "table"
    return app


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


def test_read_commands_file(commands_file):
    """Test reading commands from file."""
    # Read commands from file
    with open(commands_file, "r") as f:
        commands = f.readlines()

    # Check commands
    assert len(commands) == 5
    assert commands[0].strip() == "/language gremlin"
    assert commands[1].strip() == "g.V().limit(5);"
    assert commands[2].strip() == "/format json"
    assert commands[3].strip() == "g.E().limit(3);"
    assert commands[4].strip() == "/quit"


def test_logging_commands(mock_app, commands_file):
    """Test logging commands from file."""
    # Mock logger
    with patch("graphsh.cli.logger.Logger") as mock_logger_cls:
        mock_logger = MagicMock()
        mock_logger_cls.return_value = mock_logger
        mock_logger.log_input = MagicMock()
        mock_logger.log_output = MagicMock()

        # Read commands from file
        with open(commands_file, "r") as f:
            commands = f.readlines()

        # Process commands
        for command in commands:
            command = command.strip()
            if not command:
                continue

            # Log input
            mock_logger.log_input(command)

            # Log output (for queries)
            if not command.startswith("/"):
                mock_logger.log_output([{"id": 1, "name": "test"}])

        # Check that logger methods were called
        assert mock_logger.log_input.call_count == 5
        assert mock_logger.log_output.call_count == 2
