"""
Tests for GraphShApp.
"""

import pytest
from unittest.mock import MagicMock, patch

from graphsh.cli import GraphShApp


@pytest.fixture
def mock_connection():
    """Create a mock connection."""
    connection = MagicMock()
    connection.connect.return_value = True
    return connection


@pytest.fixture
def app():
    """Create a GraphShApp with mocked dependencies."""
    with patch("graphsh.cli.app.Connection") as mock_connection_cls:
        mock_connection = MagicMock()
        mock_connection.connect.return_value = True
        mock_connection_cls.return_value = mock_connection
        app = GraphShApp()
        app.connection = mock_connection
        yield app


def test_connect_with_params(app):
    """Test connecting with parameters."""
    app.connect(
        endpoint="test-neptune.example.com",
        port=8182,
        auth_type="iam",
        region="us-west-2",
        language="gremlin",
    )

    # Check that connection was established
    app.connection.connect.assert_called_once()


def test_set_language(app):
    """Test setting language."""
    with patch("graphsh.cli.app.get_language_processor") as mock_get_processor:
        mock_processor = MagicMock()
        mock_get_processor.return_value = mock_processor

        app.set_language("gremlin")

        # Check that processor was created
        mock_get_processor.assert_called_with("gremlin")

        # Check that language was set
        assert app.current_language == "gremlin"
        assert app.language_processor == mock_processor


def test_set_output_format(app):
    """Test setting output format."""
    # Valid format
    app.set_output_format("raw")
    assert app.output_format == "raw"

    # Invalid format
    with pytest.raises(ValueError):
        app.set_output_format("invalid")


def test_execute_query(app):
    """Test executing query."""
    # Mock connection and language processor
    app.connection.current_connection = True
    app.language_processor = MagicMock()
    app.current_language = "gremlin"
    app.renderer = MagicMock()
    app.timing_enabled = False

    # Set up mocks
    app.language_processor.validate.return_value = True
    app.connection.execute.return_value = [{"id": 1, "name": "Alice"}]

    # Execute query
    with patch("graphsh.cli.app.console.print") as mock_print:
        with patch("graphsh.cli.app.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            results = app.execute_query("g.V().limit(5)")

            # Check that query was validated
            app.language_processor.validate.assert_called_with("g.V().limit(5)")

            # Check that query was executed
            app.connection.execute.assert_called_with("g.V().limit(5)")

            # Check that results were displayed
            app.renderer.display_results.assert_called_once()

            # Check that results were logged
            mock_logger.log_output.assert_called_once()


def test_execute_query_with_timing(app):
    """Test executing query with timing enabled."""
    # Mock connection and language processor
    app.connection.current_connection = True
    app.language_processor = MagicMock()
    app.current_language = "gremlin"
    app.renderer = MagicMock()
    app.timing_enabled = True

    # Set up mocks
    app.language_processor.validate.return_value = True
    app.connection.execute.return_value = [{"id": 1, "name": "Alice"}]

    # Execute query
    with patch("graphsh.cli.app.console.print") as mock_print:
        with patch("graphsh.cli.app.get_logger") as mock_get_logger:
            with patch("graphsh.cli.app.time.time") as mock_time:
                # Mock time.time() to return sequential values
                mock_time.side_effect = [1000.0, 1002.5]  # Start time, end time
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                results = app.execute_query("g.V().limit(5)")

                # Check that timing was displayed
                mock_print.assert_any_call(
                    "[bold blue]Execution time:[/bold blue] 2.500000 seconds"
                )

                # Check that query was validated
                app.language_processor.validate.assert_called_with("g.V().limit(5)")

                # Check that query was executed
                app.connection.execute.assert_called_with("g.V().limit(5)")

                # Check that results were displayed
                app.renderer.display_results.assert_called_once()


def test_execute_query_no_connection(app):
    """Test executing query with no connection."""
    # Mock connection
    app.connection.current_connection = None

    # Execute query
    with pytest.raises(RuntimeError) as excinfo:
        app.execute_query("g.V().limit(5)")

    # Check error message
    assert "Not connected to a database" in str(excinfo.value)


def test_execute_query_validation_error(app):
    """Test executing query with validation error."""
    # Mock connection and language processor
    app.connection.current_connection = True
    app.language_processor = MagicMock()
    app.current_language = "gremlin"

    # Set up mocks to raise exception
    app.language_processor.validate.side_effect = ValueError("Invalid query")

    # Execute query
    with pytest.raises(ValueError) as excinfo:
        app.execute_query("invalid query")

    # Check error message
    assert "Invalid query" in str(excinfo.value)

    # Check that query was validated but not executed
    app.language_processor.validate.assert_called_with("invalid query")
    app.connection.execute.assert_not_called()
