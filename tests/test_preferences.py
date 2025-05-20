"""
Tests for user preferences functionality.
"""

import os
import json
import tempfile
import shutil


from graphsh.config.preferences import UserPreferences, DEFAULT_PREFERENCES


class TestUserPreferences:
    """Test user preferences functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Create a temporary directory for test preferences
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def test_default_preferences(self):
        """Test default preferences are loaded correctly."""
        prefs = UserPreferences(config_dir=self.temp_dir)

        # Check that default preferences are set
        assert prefs.get("language") == DEFAULT_PREFERENCES["language"]
        assert prefs.get("format") == DEFAULT_PREFERENCES["format"]
        assert prefs.get("timing") == DEFAULT_PREFERENCES["timing"]

    def test_save_and_load_preferences(self):
        """Test saving and loading preferences."""
        # Create preferences and modify them
        prefs = UserPreferences(config_dir=self.temp_dir)
        prefs.set("language", "sparql")
        prefs.set("format", "raw")
        prefs.set("timing", True)

        # Create a new preferences object that should load the saved preferences
        prefs2 = UserPreferences(config_dir=self.temp_dir)

        # Check that preferences were loaded correctly
        assert prefs2.get("language") == "sparql"
        assert prefs2.get("format") == "raw"
        assert prefs2.get("timing") is True

    def test_get_nonexistent_preference(self):
        """Test getting a preference that doesn't exist."""
        prefs = UserPreferences(config_dir=self.temp_dir)

        # Should return the default value
        assert prefs.get("nonexistent", "default") == "default"

    def test_get_all_preferences(self):
        """Test getting all preferences."""
        prefs = UserPreferences(config_dir=self.temp_dir)

        # Should return a copy of all preferences
        all_prefs = prefs.get_all()
        assert isinstance(all_prefs, dict)
        assert all_prefs == DEFAULT_PREFERENCES

        # Modifying the returned dict should not affect the original
        all_prefs["language"] = "modified"
        assert prefs.get("language") == DEFAULT_PREFERENCES["language"]

    def test_preferences_file_created(self):
        """Test that preferences file is created."""
        prefs = UserPreferences(config_dir=self.temp_dir)
        prefs.set("language", "cypher")

        # Check that file exists
        prefs_file = os.path.join(self.temp_dir, "preferences.json")
        assert os.path.exists(prefs_file)

        # Check file contents
        with open(prefs_file, "r") as f:
            data = json.load(f)
            assert data["language"] == "cypher"

    def test_invalid_json_fallback(self, monkeypatch):
        """Test fallback to defaults when preferences file is invalid."""
        # Create an invalid preferences file
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(os.path.join(self.temp_dir, "preferences.json"), "w") as f:
            f.write("invalid json")

        # Should fall back to defaults
        prefs = UserPreferences(config_dir=self.temp_dir)
        assert prefs.get("language") == DEFAULT_PREFERENCES["language"]
