"""
Command-line application for GraphSh.
"""

import os
import sys
import logging
import time
import urllib3
from typing import Dict, Any, List

import click
from rich.console import Console

from graphsh.db.connection import Connection
from graphsh.lang import get_language_processor
from graphsh.renderers import get_renderer
from graphsh.cli.logger import get_logger
from graphsh.config import UserPreferences, ConnectionProfiles
from graphsh.config.preferences import DEFAULT_PREFERENCES


def initialize_environment():
    """Initialize environment for GraphSh application."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # disable warning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Set up logging - default to ERROR level only
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


class GraphShApp:
    """Main application class for GraphSh."""

    def __init__(self, verbose: bool = False):
        """Initialize application.

        Args:
            config_path: Path to configuration file. If None, uses default path.
            verbose: Whether to enable verbose logging.
        """
        # Set up logging based on verbose flag
        if verbose:
            logging.getLogger().setLevel(logging.INFO)

        # Initialize logger
        self.logger = get_logger()
        self.logger.set_verbose(verbose)

        # Load user preferences
        self.preferences = UserPreferences()

        # Initialize profiles
        self.profiles = ConnectionProfiles()

        self.connection = Connection()
        self.current_language = self.preferences.get("language", "gremlin")
        self.connection.current_language = self.current_language
        self.language_processor = get_language_processor(self.current_language)
        self.output_format = self.preferences.get("format", "table")
        self.renderer = get_renderer(self.output_format)
        self.repl = None  # Will be set when running in interactive mode
        self.timing_enabled = self.preferences.get("timing", False)

    def connect(self, **kwargs) -> bool:
        """Connect to database.

        Args:
            **kwargs: Connection parameters.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        return self.connect_endpoint(**kwargs)

    def connect_endpoint(self, **kwargs) -> bool:
        """Connect to database using endpoint.

        Args:
            **kwargs: Connection parameters.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            # Log connection attempt
            logger.info(f"Connecting to endpoint with parameters: {kwargs}")

            # Ensure type is set correctly
            if "type" not in kwargs and "db_type" in kwargs:
                kwargs["type"] = kwargs.pop("db_type")

            # Store the current language before connecting
            previous_language = self.current_language

            # Connect to the database
            connection_success = self.connection.connect(**kwargs)

            if connection_success:
                # Check if the connection manager has automatically selected a language
                if (
                    hasattr(self.connection, "current_language")
                    and self.connection.current_language
                    and self.connection.current_language != previous_language
                ):
                    # Update the app's language to match the connection's language
                    new_language = self.connection.current_language
                    logger.info(
                        f"Automatically switching language to {new_language} based on database type"
                    )
                    console.print(
                        f"Automatically switching language to [green]{new_language}[/green] based on database type"
                    )

                    # Update the language processor
                    self.set_language(new_language)

                # If a language was specified in the connection parameters, use it
                if "language" in kwargs and kwargs["language"] != previous_language:
                    try:
                        self.set_language(kwargs["language"])
                    except ValueError as e:
                        logger.warning(f"Could not set language from profile: {e}")
                        console.print(f"[yellow]Warning:[/yellow] {e}")

            return connection_success
        except Exception as e:
            logger.error(f"Connection error: {e}")
            console.print(f"[bold red]Connection error:[/bold red] {e}")
            return False

    def connect_profile(self, profile_name: str) -> bool:
        """Connect to database using a named profile.

        Args:
            profile_name: Name of the profile to use

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Get profile data
            profile_data = self.profiles.get_profile(profile_name)

            if not profile_data:
                logger.error(f"Profile not found: {profile_name}")
                console.print(
                    f"[bold red]Error:[/bold red] Profile '{profile_name}' not found"
                )
                return False

            # Connect using profile data
            return self.connect(**profile_data)
        except Exception as e:
            logger.error(f"Error connecting with profile {profile_name}: {e}")
            console.print(
                f"[bold red]Error connecting with profile '{profile_name}':[/bold red] {e}"
            )
            return False

    def set_language(self, language: str) -> None:
        """Set query language.

        Args:
            language: Query language.

        Raises:
            ValueError: If language is not supported.
        """
        try:
            # Check if we have an active connection and if the language is compatible
            if (
                hasattr(self.connection, "adapter")
                and self.connection.adapter
                and hasattr(self.connection, "db_type")
            ):
                # Check if the language is compatible with the current database
                if not self.connection._is_language_compatible(
                    self.connection.db_type, language
                ):
                    logger.warning(
                        f"Language '{language}' may not be compatible with {self.connection.db_type}. "
                        f"Recommended language: {self.connection._get_recommended_language(self.connection.db_type)}"
                    )
                    console.print(
                        f"[yellow]Warning:[/yellow] Language '{language}' may not be compatible with "
                        f"{self.connection.db_type}. Continuing anyway."
                    )

            self.language_processor = get_language_processor(language)
            self.current_language = language

            # Also update the connection's current language
            if hasattr(self.connection, "current_language"):
                self.connection.current_language = language

            # Save preference
            self.preferences.set("language", language)

            console.print(f"Language switched to [green]{language}[/green]")
        except ValueError as e:
            logger.error(f"Error setting language: {e}")
            raise

    def set_output_format(self, format_type: str) -> None:
        """Set output format.

        Args:
            format_type: Output format.

        Raises:
            ValueError: If format is not supported.
        """
        try:
            from graphsh.renderers import get_renderer

            self.renderer = get_renderer(format_type)
            self.output_format = format_type

            # Save preference
            self.preferences.set("format", format_type)
        except ValueError as e:
            logger.error(f"Error setting output format: {e}")
            raise

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query using current language processor.

        Args:
            query: Query string.

        Returns:
            List[Dict[str, Any]]: Query results.

        Raises:
            ValueError: If query validation fails.
            RuntimeError: If not connected to a database.
        """
        if not self.connection.current_connection:
            error_msg = "Not connected to a database"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Start timing if enabled
            start_time = time.time() if self.timing_enabled else None

            # Validate query
            self.language_processor.validate(query)

            # Execute query
            results = self.connection.execute(query)

            # Calculate execution time if timing is enabled
            if self.timing_enabled:
                execution_time = time.time() - start_time
                console.print(
                    f"[bold blue]Execution time:[/bold blue] {execution_time:.6f} seconds"
                )

            # Render results
            self.renderer.display_results(results)

            # Log results
            log_manager = get_logger()
            log_manager.log_output(str(results))

            return results  # Return raw results, not formatted

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            # Print error directly to console without table formatting
            console.print(f"[bold red]Query execution error:[/bold red] {e}")

            # Log error
            log_manager = get_logger()
            log_manager.log_error(f"Query execution error: {e}")

            raise

    def run_interactive(self) -> None:
        """Run in interactive REPL mode."""
        # Start REPL session
        from graphsh.cli.repl import GraphShRepl

        self.repl = GraphShRepl(self)
        self.repl.run()

    def run_commands_file(self, file_path: str) -> None:
        """Execute commands from a file in sequence.

        Args:
            file_path: Path to file containing commands.
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                console.print(
                    f"[bold red]Error:[/bold red] File not found: {file_path}"
                )
                return

            # Read commands from file
            with open(file_path, "r") as f:
                commands = f.readlines()

            console.print(
                f"[bold green]Executing commands from file:[/bold green] {file_path}"
            )

            # Create a temporary REPL for command processing
            from graphsh.cli.repl import GraphShRepl

            repl = GraphShRepl(self)

            # Process each command
            for i, cmd in enumerate(commands):
                cmd = cmd.strip()

                # Skip empty lines and comments
                if not cmd or cmd.startswith("#"):
                    continue

                console.print(f"[bold blue]Command {i + 1}:[/bold blue] {cmd}")
                self.logger.log_input(cmd)

                try:
                    # Process command using REPL's command processor
                    repl._process_input(cmd)
                except Exception as e:
                    error_msg = f"Error executing command: {e}"
                    console.print(f"[bold red]{error_msg}[/bold red]")
                    self.logger.log_error(error_msg)

                console.print("")  # Add spacing between commands

            console.print("[bold green]Commands execution completed[/bold green]")

        except Exception as e:
            error_msg = f"Error processing commands file: {e}"
            console.print(f"[bold red]{error_msg}[/bold red]")

            # Log error
            self.logger.log_error(error_msg)


@click.command()
@click.option(
    "--type", help="Database type (neptune, neptune-analytics, neo4j, tinkerpop)"
)
@click.option(
    "--endpoint", help="Database endpoint URL (e.g., https://example.com:8182)"
)
@click.option(
    "--cluster-id",
    help="Cluster identifier of Neptune database (only applicable for neptune type)",
)
@click.option(
    "--graph-id",
    help="Graph identifier of Neptune Analytics graphs (only applicable for neptune-analytics type)",
)
@click.option("--auth", help="Authentication type (iam, none)")
@click.option("--username", help="Username for basic auth")
@click.option("--password", help="Password for basic auth")
@click.option("--aws-profile", help="AWS profile for IAM auth")
@click.option("--region", help="AWS region to use")
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=True,
    help="Enable/disable SSL certificate verification (default: enabled)",
)
@click.option(
    "--language",
    help=f"Query language (gremlin, sparql, cypher) (default: {DEFAULT_PREFERENCES['language']})",
)
@click.option(
    "--output",
    help=f"Output format (table, raw) (default: {DEFAULT_PREFERENCES['format']})",
)
@click.option("--profile", help="Connection profile to use")
@click.option("--commands-file", help="File containing commands to execute in sequence")
@click.option(
    "--verbose", is_flag=True, help="Enable verbose logging (default: disabled)"
)
def main(
    endpoint,
    graph_id,
    cluster_id,
    type,
    auth,
    username,
    password,
    aws_profile,
    region,
    verify_ssl,
    language,
    output,
    profile,
    commands_file,
    verbose,
):
    """GraphSh - Interactive Terminal Client for Graph Databases."""
    # Initialize environment
    initialize_environment()

    try:
        # Initialize application with verbose flag
        app = GraphShApp(verbose=verbose)

        # Set output format if specified
        if output:
            app.set_output_format(output)

        # Set language if specified
        if language:
            app.set_language(language)

        # Connect to database if endpoint or profile is provided
        if profile:
            # Connect using profile
            if not app.connect_profile(profile):
                sys.exit(1)
        elif endpoint or cluster_id or graph_id:
            # Connect using parameters if they are specified
            # Only add below connection_params if they are not None
            all_args = {
                "endpoint": endpoint,
                "graph_id": graph_id,
                "cluster_id": cluster_id,
                "type": type,
                "auth_type": auth,
                "username": username,
                "password": password,
                "aws_profile": aws_profile,
                "region": region,
                "verify_ssl": verify_ssl,
            }
            connection_params = {k: v for k, v in all_args.items() if v is not None}
            if not app.connect(**connection_params):
                sys.exit(1)

        # Run in appropriate mode
        if commands_file:
            # Commands file mode
            app.run_commands_file(commands_file)
        else:
            # Interactive mode
            app.run_interactive()

    except Exception as e:
        logger.error(f"Error: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
