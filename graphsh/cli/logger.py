"""
Logging functionality for GraphSh.
"""

import os
import logging
from datetime import datetime
from typing import Any

# Singleton instance
_logger_instance = None


class Logger:
    """Logger for GraphSh."""

    def __init__(self):
        """Initialize logger."""
        self.enabled = True  # Always enabled for file logging
        self.log_file = None
        self.log_path = None
        self.verbose = False  # Default to non-verbose mode

        # Set up the log file automatically
        self._setup_log_file()

    def _setup_log_file(self) -> None:
        """Set up the log file in the default location."""
        try:
            # Create default log file in ~/.graphsh/logs
            log_dir = os.path.expanduser("~/.graphsh/logs")
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_path = os.path.join(log_dir, f"graphsh_{timestamp}.log")

            # Open log file
            self.log_file = open(self.log_path, "a")

            # Log session start
            self.log_file.write(
                f"=== GraphSh Session Started at {datetime.now()} ===\n\n"
            )
            self.log_file.flush()
        except Exception as e:
            logging.error(f"Error setting up log file: {e}")
            # Continue without file logging if there's an error

    def set_verbose(self, verbose: bool) -> None:
        """Set verbose mode.

        Args:
            verbose: Whether to enable verbose logging to console.
        """
        self.verbose = verbose

    def stop(self) -> None:
        """Stop logging and close the log file."""
        if self.log_file:
            # Log session end
            self.log_file.write(
                f"\n=== GraphSh Session Ended at {datetime.now()} ===\n"
            )
            self.log_file.close()
            self.log_file = None

    def log_input(self, input_text: str) -> None:
        """Log user input.

        Args:
            input_text: User input text.
        """
        if self.log_file:
            self.log_file.write(f">>> {input_text}\n")
            self.log_file.flush()

        if self.verbose:
            logging.info(f"Input: {input_text}")

    def log_output(self, output: Any) -> None:
        """Log command output.

        Args:
            output: Command output.
        """
        if self.log_file:
            self.log_file.write(f"{output}\n\n")
            self.log_file.flush()

        if self.verbose:
            logging.info(f"Output: {str(output)[:100]}...")  # Truncate long outputs

    def log_error(self, error: str) -> None:
        """Log error.

        Args:
            error: Error message.
        """
        if self.log_file:
            self.log_file.write(f"ERROR: {error}\n\n")
            self.log_file.flush()

        # Always log errors regardless of verbose mode
        logging.error(error)


def get_logger() -> Logger:
    """Get logger instance.

    Returns:
        Logger: Logger instance.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance
