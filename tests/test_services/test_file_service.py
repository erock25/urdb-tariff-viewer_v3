"""
Tests for the FileService.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from urdb_viewer.config.settings import Settings
from urdb_viewer.services.file_service import FileService


class TestFileService:
    """Test cases for FileService class."""

    def test_load_json_file(self, temp_tariff_file):
        """Test loading a JSON file."""
        data = FileService.load_json_file(temp_tariff_file)

        assert isinstance(data, dict)
        assert "items" in data
        assert data["items"][0]["utility"] == "Test Utility"

    def test_save_json_file(self, tmp_path):
        """Test saving a JSON file."""
        test_data = {"test": "data", "number": 123}
        test_file = tmp_path / "test.json"

        FileService.save_json_file(test_data, test_file)

        assert test_file.exists()

        # Load and verify
        with open(test_file, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data

    def test_load_csv_file(self, temp_load_profile_file):
        """Test loading a CSV file."""
        df = FileService.load_csv_file(temp_load_profile_file)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "load_kW" in df.columns
        assert len(df) > 0

    def test_save_csv_file(self, tmp_path):
        """Test saving a CSV file."""
        test_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        test_file = tmp_path / "test.csv"

        FileService.save_csv_file(test_df, test_file)

        assert test_file.exists()

        # Load and verify
        loaded_df = pd.read_csv(test_file)
        pd.testing.assert_frame_equal(test_df, loaded_df)

    def test_create_modified_filename(self):
        """Test creating modified filenames."""
        original_path = Path("test_tariff.json")

        # Test default prefix
        modified_path = FileService.create_modified_filename(original_path)
        expected_path = Settings.USER_DATA_DIR / "modified_test_tariff.json"

        assert modified_path == expected_path

        # Test custom prefix
        modified_path = FileService.create_modified_filename(original_path, "custom_")
        expected_path = Settings.USER_DATA_DIR / "custom_test_tariff.json"

        assert modified_path == expected_path

    def test_get_file_info(self, temp_tariff_file):
        """Test getting file information."""
        file_info = FileService.get_file_info(temp_tariff_file)

        assert file_info["exists"] is True
        assert file_info["is_file"] is True
        assert file_info["is_directory"] is False
        assert file_info["size_bytes"] > 0
        assert file_info["size_mb"] > 0
        assert file_info["extension"] == ".json"
        assert "name" in file_info
        assert "stem" in file_info

    def test_get_file_info_nonexistent(self):
        """Test getting info for non-existent file."""
        file_info = FileService.get_file_info("nonexistent.json")

        assert file_info["exists"] is False

    def test_validate_file_size(self, temp_tariff_file):
        """Test file size validation."""
        # Should pass with default limit
        assert FileService.validate_file_size(temp_tariff_file) is True

        # Should fail with very small limit
        assert (
            FileService.validate_file_size(temp_tariff_file, max_size_mb=0.001) is False
        )

        # Should fail for non-existent file
        assert FileService.validate_file_size("nonexistent.json") is False

    def test_get_display_name(self):
        """Test getting display names for files."""
        # Test regular filename
        display_name = FileService.get_display_name("test_tariff.json")
        assert display_name == "Test Tariff"

        # Test filename with modified prefix
        display_name = FileService.get_display_name("modified_test_tariff.json")
        assert display_name == "Test Tariff"

        # Test filename with underscores
        display_name = FileService.get_display_name("utility_rate_schedule.json")
        assert display_name == "Utility Rate Schedule"
