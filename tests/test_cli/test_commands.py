"""
Tests for command registry and commands.
"""

from unittest.mock import MagicMock, patch, call

import pytest

from graphsh.cli.commands import CommandRegistry


@pytest.fixture
def mock_app():
    """Mock GraphShApp instance."""
    app = MagicMock()
    app.current_language = "gremlin"
    app.current_query = "g.V().count()"
    app.last_results = {"data": [42]}
    return app


@pytest.fixture
def command_registry(mock_app):
    """Command registry instance."""
    registry = CommandRegistry(mock_app)
    return registry


def test_cmd_help_no_args(command_registry):
    """Test help command with no arguments."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        with patch("graphsh.cli.commands.Table") as mock_table:
            command_registry.cmd_help([])
            mock_table.assert_called_once()
            mock_print.assert_called()


def test_cmd_quit(command_registry):
    """Test quit command."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        with patch("graphsh.cli.commands.sys.exit") as mock_exit:
            command_registry.cmd_quit([])
            mock_print.assert_called_once_with("Goodbye!")
            mock_exit.assert_called_once_with(0)


def test_cmd_language_no_args(command_registry, mock_app):
    """Test language command with no arguments."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_language([])
        mock_print.assert_any_call("Current language: [bold]gremlin[/bold]")


def test_cmd_language_with_args(command_registry, mock_app):
    """Test language command with arguments."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_language(["sparql"])
        mock_app.set_language.assert_called_once_with("sparql")


def test_cmd_language_error(command_registry, mock_app):
    """Test language command with error."""
    mock_app.set_language.side_effect = ValueError("Invalid language")

    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_language(["invalid"])
        mock_print.assert_called_once_with(
            "[bold red]Error:[/bold red] Invalid language"
        )


def test_cmd_connect_no_args(command_registry):
    """Test connect command with no arguments."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_connect([])
        mock_print.assert_any_call(
            "[bold red]Error:[/bold red] Profile name or connection parameters not specified."
        )


def test_cmd_connect_with_direct_params(command_registry, mock_app):
    """Test connect command with direct connection parameters."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_connect(
            [
                "--endpoint",
                "https://neptune-instance.region.amazonaws.com:8182",
                "--auth",
                "iam",
                "--aws-profile",
                "default",
                "--type",
                "neptune",
            ]
        )

        # Check that app.connect was called with the correct parameters
        mock_app.connect.assert_called_once_with(
            endpoint="https://neptune-instance.region.amazonaws.com:8182",
            auth_type="iam",
            aws_profile="default",
            type="neptune",
            verify_ssl=True,
        )

        # Check that print was called with the connection message
        # Note: We're checking any_call instead of assert_called_once because there's a debug print
        mock_print.assert_any_call("[bold green]Connected to database.[/bold green]")


def test_cmd_connect_with_no_verify_ssl(command_registry, mock_app):
    """Test connect command with --no-verify-ssl flag."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_connect(
            [
                "--endpoint",
                "https://neptune-instance.region.amazonaws.com:8182",
                "--auth",
                "iam",
                "--type",
                "neptune",
                "--no-verify-ssl",
            ]
        )

        # Check that app.connect was called with the correct parameters
        mock_app.connect.assert_called_once_with(
            endpoint="https://neptune-instance.region.amazonaws.com:8182",
            auth_type="iam",
            type="neptune",
            verify_ssl=False,
        )

        # Check that print was called with the connection message
        mock_print.assert_any_call("[bold green]Connected to database.[/bold green]")


def test_cmd_connect_direct_missing_endpoint(command_registry):
    """Test connect command with direct parameters but missing endpoint."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        command_registry.cmd_connect(["--auth", "iam"])
        mock_print.assert_any_call(
            "[bold red]Error:[/bold red] --type is required for direct connection"
        )


def test_cmd_clear(command_registry):
    """Test clear command."""
    with patch("graphsh.cli.commands.os.system") as mock_system:
        command_registry.cmd_clear([])
        mock_system.assert_called_once_with("clear")


# Removed tests for /info and /schema commands


def test_cmd_timing(command_registry, mock_app):
    """Test timing command."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        # Test turning timing on
        command_registry.cmd_timing(["on"])
        assert mock_app.timing_enabled is True
        mock_print.assert_called_with("Query timing is [bold]on[/bold]")

        # Test turning timing off
        mock_print.reset_mock()
        command_registry.cmd_timing(["off"])
        assert mock_app.timing_enabled is False
        mock_print.assert_called_with("Query timing is [bold]off[/bold]")

        # Test with no arguments
        mock_print.reset_mock()
        mock_app.timing_enabled = True
        command_registry.cmd_timing([])
        # First call is for current status
        assert mock_print.call_args_list[0] == call("Query timing is [bold]on[/bold]")
        # Second call is for default status
        assert mock_print.call_args_list[1] == call(
            "Default timing is [bold]off[/bold]"
        )


def test_cmd_format(command_registry, mock_app):
    """Test format command."""
    with patch("graphsh.cli.commands.console.print") as mock_print:
        # Test with no arguments
        command_registry.cmd_format([])
        mock_print.assert_any_call(
            f"Current format: [bold]{mock_app.output_format}[/bold]"
        )
        mock_print.assert_any_call("Available formats: table, raw")

        # Test with valid format
        mock_print.reset_mock()
        with patch("graphsh.renderers.get_renderer"):
            command_registry.cmd_format(["raw"])
            mock_app.set_output_format.assert_called_with("raw")
            mock_print.assert_called_with("Output format set to [bold]raw[/bold]")

        # Test with invalid format
        mock_print.reset_mock()
        with patch(
            "graphsh.renderers.get_renderer",
            side_effect=ValueError(
                "Unsupported renderer type: invalid. Available renderers: table, raw, json, csv"
            ),
        ):
            command_registry.cmd_format(["invalid"])
            mock_print.assert_called_with(
                "[bold red]Error:[/bold red] Unsupported renderer type: invalid. Available renderers: table, raw, json, csv"
            )
