"""
Special commands for GraphSh interactive shell.
"""

import logging
import os
import sys
from typing import Callable, Dict, List, Tuple

from rich.console import Console
from rich.table import Table

from graphsh.renderers import get_renderer
from graphsh.config.preferences import UserPreferences, DEFAULT_PREFERENCES
from graphsh.config.profiles import ConnectionProfiles
from graphsh.lang import get_language_processor

logger = logging.getLogger(__name__)
console = Console()


class CommandRegistry:
    """Registry of special commands for the interactive shell."""

    def __init__(self, app):
        """Initialize command registry.

        Args:
            app: GraphSh application instance.
        """
        self.app = app
        # Command dictionary with (function, description, usage, examples)
        self.commands: Dict[str, Tuple[Callable, str, str, List[str]]] = {
            "help": (
                self.cmd_help,
                "Show help for commands",
                "/help [command]",
                ["/help"],
            ),
            "quit": (self.cmd_quit, "Exit the shell", "/quit", ["/quit"]),
            "language": (
                self.cmd_language,
                "Switch query language (gremlin, sparql, cypher)",
                "/language [language_name]",
                [
                    "/language",
                    "/language gremlin",
                    "/language sparql",
                    "/language cypher",
                ],
            ),
            "connect": (
                self.cmd_connect,
                "Connect to a database using a profile or connection parameters",
                "/connect <profile_name> or /connect --type <db_type> [options]",
                [
                    "/connect",
                    "/connect my-neptune-profile",
                    "/connect --endpoint https://neptune-instance.region.amazonaws.com:8182 --type neptune --auth iam",
                    "/connect --endpoint bolt://localhost:7687 --type neo4j --username neo4j --password password",
                ],
            ),
            "clear": (self.cmd_clear, "Clear the screen", "/clear", ["/clear"]),
            "timing": (
                self.cmd_timing,
                "Toggle query execution timing",
                "/timing [on|off]",
                ["/timing", "/timing on", "/timing off"],
            ),
            "format": (
                self.cmd_format,
                "Set output format (table, raw)",
                "/format [format_name]",
                [
                    "/format",
                    "/format table",
                    "/format raw",
                ],
            ),
            "preferences": (
                self.cmd_preferences,
                "Show or reset user preferences",
                "/preferences [reset]",
                ["/preferences", "/preferences reset"],
            ),
            "profile": (
                self.cmd_profile,
                "Manage connection profiles",
                "/profile list|save|delete <name>",
                [
                    "/profile list",
                    "/profile save my-neptune",
                    "/profile delete my-neptune",
                    "/profile show my-neptune",
                ],
            ),
        }

    def execute(self, cmd_name: str, args: List[str]) -> bool:
        """Execute a command.

        Args:
            cmd_name: Command name.
            args: Command arguments.

        Returns:
            bool: True if command was executed, False otherwise.
        """
        if cmd_name not in self.commands:
            console.print(f"[bold red]Unknown command:[/bold red] {cmd_name}")
            console.print("Type [bold]/help[/bold] for available commands.")
            return False

        try:
            cmd_func, _, _, _ = self.commands[cmd_name]
            cmd_func(args)
            return True
        except Exception as e:
            logger.error(f"Error executing command {cmd_name}: {e}")
            console.print(f"[bold red]Error:[/bold red] {e}")
            return False

    def cmd_help(self, args: List[str]) -> None:
        """Show help for commands.

        Args:
            args: Command arguments. If provided, shows help for specific command.
        """
        table = Table(title="GraphSh Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        table.add_column("Default", style="green")

        for cmd_name, (_, description, _, _) in sorted(self.commands.items()):
            default_value = ""
            if cmd_name == "language":
                default_value = self.app.preferences.get("language", "gremlin")
            elif cmd_name == "format":
                default_value = self.app.preferences.get("format", "table")
            elif cmd_name == "timing":
                default_value = (
                    "off" if not self.app.preferences.get("timing", False) else "on"
                )

            table.add_row(f"/{cmd_name}", description, default_value)

        console.print(table)

    def cmd_quit(self, args: List[str]) -> None:
        """Exit the shell.

        Args:
            args: Command arguments.
        """
        console.print("Goodbye!")
        sys.exit(0)

    def cmd_language(self, args: List[str]) -> None:
        """Switch query language.

        Args:
            args: Command arguments.
        """
        if not args:
            console.print(f"Current language: [bold]{self.app.current_language}[/bold]")
            console.print(
                f"Default language: [bold]{DEFAULT_PREFERENCES['language']}[/bold]"
            )
            console.print("Available languages: gremlin, sparql, cypher")
            return

        language = args[0].lower()
        try:
            self.app.set_language(language)
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    def cmd_connect(self, args: List[str]) -> None:
        """Connect to database using a profile or connection parameters.

        Args:
            args: Command arguments.
        """
        if not args:
            console.print(
                "[bold red]Error:[/bold red] Profile name or connection parameters not specified."
            )
            console.print("Usage: /connect <profile_name>")
            console.print("   or: /connect --endpoint <url> --type <db_type> [options]")
            console.print("\nAvailable database types and their options:")

            console.print("\n[bold cyan]Neptune[/bold cyan] (--type neptune)")
            console.print("  --endpoint <url>           : Neptune endpoint URL")
            console.print(
                "  --auth iam|none           : Authentication type (required)"
            )
            console.print("  --aws-profile <profile>   : AWS profile name for IAM auth")
            console.print("  --region <region>         : AWS region for IAM auth")
            console.print(
                "  --cluster-id <id>         : Neptune cluster ID (alternative to endpoint)"
            )
            console.print(
                "  --no-verify-ssl           : Disable SSL certificate verification"
            )

            console.print(
                "\n[bold cyan]Neptune Analytics[/bold cyan] (--type neptune-analytics)"
            )
            console.print(
                "  --endpoint <id>           : Neptune Analytics graph ID or endpoint URL"
            )
            console.print(
                "  --graph-id <id>           : Graph ID (if not specified in endpoint)"
            )
            console.print("  --aws-profile <profile>   : AWS profile name")
            console.print("  --region <region>         : AWS region")

            console.print("\n[bold cyan]Neo4j[/bold cyan] (--type neo4j)")
            console.print(
                "  --endpoint <url>          : Neo4j endpoint URL (bolt://host:port)"
            )
            console.print("  --username <user>         : Neo4j username (required)")
            console.print("  --password <pass>         : Neo4j password (required)")

            console.print("\n[bold cyan]TinkerPop[/bold cyan] (--type tinkerpop)")
            console.print("  --endpoint <url>          : Gremlin server endpoint URL")
            console.print(
                "  --no-verify-ssl           : Disable SSL certificate verification"
            )

            console.print("\nExamples:")
            console.print("  /connect my-neptune-profile")
            console.print(
                "  /connect --endpoint https://neptune-instance.region.amazonaws.com:8182 --type neptune --auth iam"
            )
            console.print(
                "  /connect --endpoint my-graph-id --type neptune-analytics --region us-east-1"
            )
            console.print(
                "  /connect --endpoint bolt://localhost:7687 --type neo4j --username neo4j --password password"
            )
            console.print("  /connect --endpoint ws://localhost:8182 --type tinkerpop")
            return

        # Check if we're using a profile or direct connection parameters
        if args[0].startswith("--"):
            # Parse connection parameters
            connection_params = {}
            i = 0
            verify_ssl = True  # Default to True

            while i < len(args):
                if args[i].startswith("--"):
                    param_name = args[i][2:]  # Remove '--' prefix

                    # Handle --verify-ssl and --no-verify-ssl flags
                    if param_name == "verify-ssl":
                        verify_ssl = True
                        i += 1
                    elif param_name == "no-verify-ssl":
                        verify_ssl = False
                        i += 1
                    elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                        param_value = args[i + 1]
                        i += 2

                        # Convert parameter names to the format expected by app.connect
                        if param_name == "auth":
                            connection_params["auth_type"] = param_value
                        elif param_name == "type":
                            connection_params["type"] = param_value
                        elif param_name == "aws-profile":
                            connection_params["aws_profile"] = param_value
                        elif param_name == "graph-id":
                            connection_params["graph_id"] = param_value
                        elif param_name == "cluster-id":
                            connection_params["cluster_id"] = param_value
                        else:
                            connection_params[param_name] = param_value
                    else:
                        # Flag parameter without value
                        param_value = True
                        i += 1
                        connection_params[param_name] = param_value
                else:
                    i += 1

            # Add verify_ssl to connection parameters
            connection_params["verify_ssl"] = verify_ssl

            if "type" not in connection_params:
                console.print(
                    "[bold red]Error:[/bold red] --type is required for direct connection"
                )
                return

            # Connect using parameters
            if self.app.connect(**connection_params):
                console.print("[bold green]Connected to database.[/bold green]")
            else:
                console.print("[bold red]Failed to connect to database.[/bold red]")
        else:
            # Connect using a profile
            profile_name = args[0]
            profiles = ConnectionProfiles()
            profile_data = profiles.get_profile(profile_name)

            if not profile_data:
                console.print(
                    f"[bold red]Error:[/bold red] Profile '{profile_name}' not found."
                )
                console.print(
                    "Use [bold]/profile list[/bold] to see available profiles."
                )
                return

            # Connect using profile data
            if self.app.connect(**profile_data):
                console.print(
                    f"[bold green]Connected to database using profile '{profile_name}'.[/bold green]"
                )

                # If profile has a language preference, set it
                if "language" in profile_data:
                    try:
                        self.app.set_language(profile_data["language"])
                    except ValueError as e:
                        console.print(f"[bold yellow]Warning:[/bold yellow] {e}")
            else:
                console.print(
                    f"[bold red]Failed to connect using profile '{profile_name}'.[/bold red]"
                )

    def cmd_clear(self, args: List[str]) -> None:
        """Clear the screen.

        Args:
            args: Command arguments.
        """
        os.system("cls" if os.name == "nt" else "clear")

    def cmd_timing(self, args: List[str]) -> None:
        """Toggle query execution timing.

        Args:
            args: Command arguments.
        """
        if not args:
            current = getattr(self.app, "timing_enabled", False)
            console.print(f"Query timing is [bold]{'on' if current else 'off'}[/bold]")
            console.print(
                f"Default timing is [bold]{'on' if DEFAULT_PREFERENCES['timing'] else 'off'}[/bold]"
            )
            return

        value = args[0].lower()
        if value in ("on", "true", "yes", "1"):
            self.app.timing_enabled = True
            self.app.preferences.set("timing", True)
            console.print("Query timing is [bold]on[/bold]")
        elif value in ("off", "false", "no", "0"):
            self.app.timing_enabled = False
            self.app.preferences.set("timing", False)
            console.print("Query timing is [bold]off[/bold]")
        else:
            console.print("[bold red]Invalid value.[/bold red] Use 'on' or 'off'.")

    def cmd_format(self, args: List[str]) -> None:
        """Set output format.

        Args:
            args: Command arguments.
        """
        if not args:
            console.print(f"Current format: [bold]{self.app.output_format}[/bold]")
            console.print(
                f"Default format: [bold]{DEFAULT_PREFERENCES['format']}[/bold]"
            )
            console.print("Available formats: table, raw")
            return

        format_type = args[0].lower()
        try:
            # Test if renderer exists
            from graphsh.renderers import get_renderer

            get_renderer(format_type)
            self.app.set_output_format(format_type)
            console.print(f"Output format set to [bold]{format_type}[/bold]")
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    def cmd_preferences(self, args: List[str]) -> None:
        """Show or reset user preferences.

        Args:
            args: Command arguments.
        """
        if args and args[0].lower() == "reset":
            # Reset preferences to defaults
            self.app.preferences = UserPreferences()
            self.app.preferences.preferences = DEFAULT_PREFERENCES.copy()
            self.app.preferences.save_preferences()

            # Update app state with default preferences
            self.app.current_language = self.app.preferences.get("language")
            self.app.language_processor = get_language_processor(
                self.app.current_language
            )
            self.app.output_format = self.app.preferences.get("format")
            self.app.renderer = get_renderer(self.app.output_format)
            self.app.timing_enabled = self.app.preferences.get("timing")

            console.print("[bold green]Preferences reset to defaults.[/bold green]")
            return

        # Show current preferences
        table = Table(title="User Preferences")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        table.add_column("Default", style="green")

        # Get all preferences and display with defaults
        for key, value in self.app.preferences.get_all().items():
            default_value = DEFAULT_PREFERENCES.get(key, "N/A")
            table.add_row(key, str(value), str(default_value))

        console.print(table)
        console.print(
            "\nPreferences are stored in [bold]~/.graphsh/preferences.json[/bold]"
        )
        console.print("Use [bold]/preferences reset[/bold] to restore defaults")

    def cmd_profile(self, args: List[str]) -> None:
        """Manage connection profiles.

        Args:
            args: Command arguments.
        """
        if not args:
            console.print("[bold red]Error:[/bold red] Profile command not specified.")
            console.print("Usage: /profile list|save|delete|show <name>")
            return

        profiles = ConnectionProfiles()
        command = args[0].lower()

        if command == "list":
            # List all profiles
            profile_names = profiles.list_profiles()

            if not profile_names:
                console.print("No connection profiles found.")
                console.print(
                    "Use [bold]/profile save <name>[/bold] to create a profile."
                )
                return

            table = Table(title="Connection Profiles")
            table.add_column("Name", style="cyan")
            table.add_column("Type")
            table.add_column("Endpoint")
            table.add_column("Language")

            for name in profile_names:
                profile = profiles.get_profile(name)
                table.add_row(
                    name,
                    profile.get("type", "unknown"),
                    profile.get("endpoint", "unknown"),
                    profile.get("language", "default"),
                )

            console.print(table)
            console.print(
                "\nUse [bold]/connect <profile_name>[/bold] to connect using a profile"
            )
            console.print(
                "Use [bold]/profile show <profile_name>[/bold] to see profile details"
            )

        elif command == "save":
            # Save current connection as a profile
            if len(args) < 2:
                console.print("[bold red]Error:[/bold red] Profile name not specified.")
                console.print("Usage: /profile save <name>")
                return

            profile_name = args[1]

            # Check if we have an active connection
            if not self.app.connection.current_connection:
                console.print(
                    "[bold red]Error:[/bold red] Not connected to a database."
                )
                console.print("Connect to a database first before saving a profile.")
                return

            # Create profile data from current connection
            profile_data = self.app.connection.connection_params.copy()

            # Add current language to profile
            profile_data["language"] = self.app.current_language

            # Save the profile
            profiles.save_profile(profile_name, profile_data)
            console.print(
                f"[bold green]Profile '{profile_name}' saved successfully.[/bold green]"
            )

        elif command == "delete":
            # Delete a profile
            if len(args) < 2:
                console.print("[bold red]Error:[/bold red] Profile name not specified.")
                console.print("Usage: /profile delete <name>")
                return

            profile_name = args[1]

            if profiles.delete_profile(profile_name):
                console.print(
                    f"[bold green]Profile '{profile_name}' deleted successfully.[/bold green]"
                )
            else:
                console.print(
                    f"[bold red]Error:[/bold red] Profile '{profile_name}' not found."
                )

        elif command == "show":
            # Show profile details
            if len(args) < 2:
                console.print("[bold red]Error:[/bold red] Profile name not specified.")
                console.print("Usage: /profile show <name>")
                return

            profile_name = args[1]
            profile_data = profiles.get_profile(profile_name)

            if not profile_data:
                console.print(
                    f"[bold red]Error:[/bold red] Profile '{profile_name}' not found."
                )
                return

            # Display profile details
            table = Table(title=f"Profile: {profile_name}")
            table.add_column("Setting", style="cyan")
            table.add_column("Value")

            # Sort keys for consistent display
            for key in sorted(profile_data.keys()):
                value = profile_data[key]
                # Don't show password in plain text
                if key == "password":
                    value = "********"
                table.add_row(key, str(value))

            console.print(table)
            console.print(
                f"\nUse [bold]/connect {profile_name}[/bold] to connect using this profile"
            )

        else:
            console.print(
                f"[bold red]Error:[/bold red] Unknown profile command: {command}"
            )
            console.print("Available commands: list, save, delete, show")
