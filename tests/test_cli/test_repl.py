"""
Tests for GraphSh REPL.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.document import Document

from graphsh.cli.repl import GraphShRepl


@pytest.fixture
def mock_app():
    """Create a mock GraphSh application."""
    app = MagicMock()
    app.current_language = "gremlin"
    app.output_format = "table"
    app.current_query = "g.V().limit(10)"
    app.last_results = [{"id": 1, "name": "Alice"}]
    app.timing_enabled = False
    app.language_processor = MagicMock()
    app.config_manager = MagicMock()
    return app


@pytest.fixture
def repl(mock_app):
    """Create a GraphSh REPL with mock app."""
    with patch("graphsh.cli.repl.PromptSession"):
        with patch("graphsh.cli.repl.get_logger"):
            return GraphShRepl(mock_app)


def test_repl_init(repl, mock_app):
    """Test REPL initialization."""
    assert repl.app == mock_app
    assert repl.current_query == ""


def test_process_input_empty(repl):
    """Test processing empty input."""
    # Should return True to continue
    result = repl._process_input("")
    assert result is True


def test_process_input_command(repl):
    """Test processing command input."""
    with patch.object(repl, "_process_command") as mock_process_command:
        mock_process_command.return_value = True

        # Process command
        result = repl._process_input("/help")

        # Check that command was processed
        mock_process_command.assert_called_once_with("/help")

        # Check that result is True (continue)
        assert result is True


def test_process_command_quit(repl):
    """Test processing quit command."""
    with patch("graphsh.cli.repl.console") as mock_console:
        with patch.object(
            repl.command_registry, "execute", return_value=False
        ) as mock_execute:
            # Process quit command
            result = repl._process_command("/quit")

            # Check that command registry was called with correct arguments
            mock_execute.assert_called_once_with("quit", [])

            # Check that result is False (exit)
            assert result is False


def test_process_command_help(repl):
    """Test processing help command."""
    with patch.object(
        repl.command_registry, "execute", return_value=True
    ) as mock_execute:
        # Process help command
        result = repl._process_command("/help")

        # Check that command registry was called with correct arguments
        mock_execute.assert_called_once_with("help", [])

        # Check that result is True (continue)
        assert result is True


def test_process_command_unknown(repl):
    """Test processing unknown command."""
    with patch.object(
        repl.command_registry, "execute", return_value=True
    ) as mock_execute:
        # Process unknown command
        result = repl._process_command("/unknown")

        # Check that command registry was called with correct arguments
        mock_execute.assert_called_once_with("unknown", [])

        # Check that result is True (continue)
        assert result is True

        # Check that result is True (continue)
        assert result is True


def test_process_input_query_single_line(repl, mock_app):
    """Test processing single-line query."""
    with patch.object(repl, "_execute_query") as mock_execute:
        # Process query
        repl._process_input("g.V().limit(10);")

        # Check that query was executed
        mock_execute.assert_called_once_with("g.V().limit(10);")

        # Check that query buffer is empty
        assert repl.current_query == ""


def test_execute_query(repl, mock_app):
    """Test execute_query method."""
    # Execute query
    repl._execute_query("g.V().limit(10);")

    # Check that query was executed with semicolon removed
    mock_app.execute_query.assert_called_once_with("g.V().limit(10);")
