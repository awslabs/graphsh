"""
REPL (Read-Eval-Print Loop) for GraphSh.
"""

import os
import logging

from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter, Completer, Completion
import os.path

from graphsh.cli.logger import get_logger
from graphsh.cli.commands import CommandRegistry

console = Console()
logger = logging.getLogger(__name__)


class GraphShRepl:
    """REPL for GraphSh."""

    def __init__(self, app):
        """Initialize REPL.

        Args:
            app: GraphShApp instance.
        """
        self.app = app
        self.current_query = ""

        # Initialize command registry
        self.command_registry = CommandRegistry(app)

        # Create history directory if it doesn't exist
        history_dir = os.path.expanduser("~/.graphsh")
        os.makedirs(history_dir, exist_ok=True)

        # Initialize prompt session with history
        self.history_file = os.path.join(history_dir, "history")
        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
        )

        # Initialize command completer with commands from registry
        self.commands = [f"/{cmd}" for cmd in self.command_registry.commands.keys()]
        self.command_completer = WordCompleter(self.commands, pattern=r"^/")

    def run(self) -> None:
        """Run REPL loop."""
        console.print(
            "[bold green]GraphSh - Interactive Terminal Client for Graph Databases[/bold green]"
        )
        console.print("Type '/help' for help, '/quit' to exit.")

        while True:
            try:
                # Get input with proper history and completion
                prompt = f"{self.app.current_language}> "

                # Use the unified completer for all languages
                completer = GraphShCompleter(self.app, self.commands)
                line = self.session.prompt(
                    prompt, completer=completer, complete_while_typing=True
                )

                # Process input
                if not self._process_input(line):
                    break
            except KeyboardInterrupt:
                console.print("\nUse '/quit' to exit.")
            except EOFError:
                console.print("\nExiting...")
                break

    def _process_input(self, line: str) -> bool:
        """Process input line.

        Args:
            line: Input line.

        Returns:
            bool: True to continue, False to exit.
        """
        # Log input
        log_manager = get_logger()
        log_manager.log_input(line)

        # Handle empty line
        if not line.strip():
            return True

        # Handle special commands
        if line.strip().startswith("/"):
            return self._process_command(line.strip())

        # Execute query directly (no need for semicolon)
        self._execute_query(line)

        return True

    def _process_command(self, command: str) -> bool:
        """Process special command.

        Args:
            command: Command string.

        Returns:
            bool: True to continue, False to exit.
        """
        # Split command and arguments
        parts = command.split(maxsplit=1)
        cmd = parts[0][1:].lower()  # Remove the leading '/'
        args = parts[1].split() if len(parts) > 1 else []

        # Handle quit command specially to return False and exit the loop
        if cmd in ["quit"]:
            self.command_registry.execute(cmd, args)
            return False

        # Process all other commands through the registry
        self.command_registry.execute(cmd, args)
        return True

    def _execute_query(self, query: str) -> None:
        """Execute query.

        Args:
            query: Query string.
        """
        try:
            self.app.execute_query(query)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


class GraphShCompleter(Completer):
    """Unified completer for all graph query languages."""

    def __init__(self, app, commands):
        """Initialize completer.

        Args:
            app: GraphShApp instance.
            commands: List of special commands.
        """
        self.app = app
        self.commands = commands

    def get_completions(self, document, complete_event):
        """Get completions for current text.

        Args:
            document: Document object containing current text.
            complete_event: Complete event.

        Yields:
            Completion: Completion objects.
        """
        text = document.text
        cursor_position = document.cursor_position

        # If text starts with '/', provide command completions
        if text.lstrip().startswith("/"):
            word_before_cursor = document.get_word_before_cursor(WORD=True)
            for command in self.commands:
                if command.startswith(word_before_cursor):
                    yield Completion(command, start_position=-len(word_before_cursor))
            return
