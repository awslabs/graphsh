"""Profile management for GraphSh.

This module handles loading, saving, and accessing connection profiles
that persist across sessions.
"""

import json
import os
from typing import Any, Dict, List, Optional


class ConnectionProfiles:
    """Manages connection profiles that persist across sessions."""

    def __init__(self, config_dir: str = "~/.graphsh"):
        """Initialize connection profiles.

        Args:
            config_dir: Directory to store profiles file
        """
        self.config_dir = os.path.expanduser(config_dir)
        self.profiles_file = os.path.join(self.config_dir, "profiles.json")
        self.profiles = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load profiles from file if it exists."""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                return  # No profiles file yet

            # Load profiles if file exists
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, "r") as f:
                    self.profiles = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            # If there's an error loading profiles, use empty dict
            print(f"Warning: Could not load profiles: {e}")
            self.profiles = {}

    def save_profiles(self) -> None:
        """Save current profiles to file."""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)

            # Write profiles to file
            with open(self.profiles_file, "w") as f:
                json.dump(self.profiles, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save profiles: {e}")

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a profile by name.

        Args:
            name: Profile name

        Returns:
            The profile or None if it doesn't exist
        """
        return self.profiles.get(name)

    def save_profile(self, name: str, profile_data: Dict[str, Any]) -> None:
        """Save a profile.

        Args:
            name: Profile name
            profile_data: Profile data
        """
        self.profiles[name] = profile_data
        self.save_profiles()

    def delete_profile(self, name: str) -> bool:
        """Delete a profile.

        Args:
            name: Profile name

        Returns:
            bool: True if profile was deleted, False if it didn't exist
        """
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()
            return True
        return False

    def list_profiles(self) -> List[str]:
        """Get list of profile names.

        Returns:
            List of profile names
        """
        return list(self.profiles.keys())

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all profiles.

        Returns:
            Dictionary of all profiles
        """
        return self.profiles.copy()
