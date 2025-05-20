"""Tests for connection profiles."""

import os
import json
import tempfile
from unittest.mock import patch, mock_open


from graphsh.config.profiles import ConnectionProfiles


class TestConnectionProfiles:
    """Test connection profiles functionality."""

    def test_default_profiles(self):
        """Test default profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles = ConnectionProfiles(config_dir=temp_dir)
            assert profiles.profiles == {}

    def test_save_and_load_profiles(self):
        """Test saving and loading profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create profiles
            profiles = ConnectionProfiles(config_dir=temp_dir)

            # Save a profile
            test_profile = {
                "endpoint": "https://test-endpoint:8182",
                "type": "neptune",
                "auth_type": "iam",
                "language": "gremlin",
            }
            profiles.save_profile("test-profile", test_profile)

            # Check if profile was saved
            assert "test-profile" in profiles.profiles
            assert profiles.profiles["test-profile"] == test_profile

            # Create a new instance to test loading
            profiles2 = ConnectionProfiles(config_dir=temp_dir)
            assert "test-profile" in profiles2.profiles
            assert profiles2.profiles["test-profile"] == test_profile

    def test_get_profile(self):
        """Test getting a profile."""
        profiles = ConnectionProfiles()

        # Add a test profile
        test_profile = {
            "endpoint": "https://test-endpoint:8182",
            "type": "neptune",
            "auth_type": "iam",
        }
        profiles.profiles["test-profile"] = test_profile

        # Get the profile
        profile = profiles.get_profile("test-profile")
        assert profile == test_profile

        # Get a non-existent profile
        profile = profiles.get_profile("non-existent")
        assert profile is None

    def test_delete_profile(self):
        """Test deleting a profile."""
        profiles = ConnectionProfiles()

        # Add a test profile
        test_profile = {
            "endpoint": "https://test-endpoint:8182",
            "type": "neptune",
            "auth_type": "iam",
        }
        profiles.profiles["test-profile"] = test_profile

        # Delete the profile
        result = profiles.delete_profile("test-profile")
        assert result is True
        assert "test-profile" not in profiles.profiles

        # Delete a non-existent profile
        result = profiles.delete_profile("non-existent")
        assert result is False

    def test_list_profiles(self):
        """Test listing profiles."""
        profiles = ConnectionProfiles()

        # Clear existing profiles and add test profiles
        profiles.profiles = {}
        profiles.profiles["profile1"] = {"endpoint": "endpoint1"}
        profiles.profiles["profile2"] = {"endpoint": "endpoint2"}

        # List profiles
        profile_list = profiles.list_profiles()
        assert len(profile_list) == 2
        assert "profile1" in profile_list
        assert "profile2" in profile_list

    def test_get_all_profiles(self):
        """Test getting all profiles."""
        profiles = ConnectionProfiles()

        # Add test profiles
        test_profiles = {
            "profile1": {"endpoint": "endpoint1"},
            "profile2": {"endpoint": "endpoint2"},
        }
        profiles.profiles = test_profiles

        # Get all profiles
        all_profiles = profiles.get_all_profiles()
        assert all_profiles == test_profiles

        # Ensure it's a copy
        all_profiles["profile3"] = {"endpoint": "endpoint3"}
        assert "profile3" not in profiles.profiles

    def test_profiles_file_created(self):
        """Test that profiles file is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_file = os.path.join(temp_dir, "profiles.json")

            # Create profiles and save a profile
            profiles = ConnectionProfiles(config_dir=temp_dir)
            profiles.save_profile("test", {"endpoint": "test"})

            # Check if file was created
            assert os.path.exists(profiles_file)

            # Check file content
            with open(profiles_file, "r") as f:
                data = json.load(f)
                assert "test" in data
                assert data["test"]["endpoint"] == "test"

    def test_invalid_json_fallback(self):
        """Test fallback to empty dict when JSON is invalid."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists", return_value=True):
                profiles = ConnectionProfiles()
                assert profiles.profiles == {}
