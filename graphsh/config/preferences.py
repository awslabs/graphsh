"""User preferences management for GraphSh.

This module handles loading, saving, and accessing user preferences
that persist across sessions.
"""

import json
import os
from typing import Any, Dict

# Default preferences
DEFAULT_PREFERENCES = {
    "language": "gremlin",  # Default query language
    "format": "table",  # Default output format
    "timing": False,  # Query timing disabled by default
}


class UserPreferences:
    """Manages user preferences that persist across sessions."""

    def __init__(self, config_dir: str = "~/.graphsh"):
        """Initialize user preferences.

        Args:
            config_dir: Directory to store preferences file
        """
        self.config_dir = os.path.expanduser(config_dir)
        self.config_file = os.path.join(self.config_dir, "preferences.json")
        self.preferences = DEFAULT_PREFERENCES.copy()
        self._load_preferences()

    def _load_preferences(self) -> None:
        """Load preferences from file if it exists."""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                return  # No preferences file yet

            # Load preferences if file exists
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    loaded_prefs = json.load(f)
                    # Update preferences with loaded values
                    self.preferences.update(loaded_prefs)
        except (IOError, json.JSONDecodeError) as e:
            # If there's an error loading preferences, use defaults
            print(f"Warning: Could not load preferences: {e}")

    def save_preferences(self) -> None:
        """Save current preferences to file."""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)

            # Write preferences to file
            with open(self.config_file, "w") as f:
                json.dump(self.preferences, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save preferences: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value.

        Args:
            key: Preference key
            default: Default value if key doesn't exist

        Returns:
            The preference value or default
        """
        return self.preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a preference value and save to file.

        Args:
            key: Preference key
            value: Preference value
        """
        self.preferences[key] = value
        self.save_preferences()

    def get_all(self) -> Dict[str, Any]:
        """Get all preferences.

        Returns:
            Dictionary of all preferences
        """
        return self.preferences.copy()
