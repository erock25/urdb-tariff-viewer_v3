"""
File service for URDB Tariff Viewer.

This module handles file operations including loading, saving, and discovering tariff files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from urdb_viewer.config.settings import Settings


class FileService:
    """Service for handling file operations."""

    @staticmethod
    def find_json_files() -> List[Path]:
        """
        Find all JSON files in the data directories.

        Returns:
            List[Path]: List of JSON file paths
        """
        json_files = []

        # Search in all data directories
        for directory in Settings.get_data_directories():
            if directory.exists():
                json_files.extend(directory.glob("*.json"))

        # Also check the base directory for backward compatibility
        base_json_files = list(Settings.BASE_DIR.glob("*.json"))
        json_files.extend(base_json_files)

        return sorted(json_files)

    @staticmethod
    def find_csv_files() -> List[Path]:
        """
        Find all CSV files in the load profiles directory.

        Returns:
            List[Path]: List of CSV file paths
        """
        csv_files = []

        if Settings.LOAD_PROFILES_DIR.exists():
            csv_files.extend(Settings.LOAD_PROFILES_DIR.glob("*.csv"))

        return sorted(csv_files)

    @staticmethod
    def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON file and return its contents.

        Args:
            file_path (Union[str, Path]): Path to the JSON file

        Returns:
            Dict[str, Any]: Loaded JSON data

        Raises:
            Exception: If the file cannot be loaded
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            raise RuntimeError(f"Error loading file {file_path}: {str(e)}") from e

    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save data to a JSON file.

        Args:
            data (Dict[str, Any]): Data to save
            file_path (Union[str, Path]): Path to save the file

        Raises:
            Exception: If the file cannot be saved
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Error saving file {file_path}: {str(e)}") from e

    @staticmethod
    def load_csv_file(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load a CSV file and return it as a DataFrame.

        Args:
            file_path (Union[str, Path]): Path to the CSV file

        Returns:
            pd.DataFrame: Loaded CSV data

        Raises:
            Exception: If the file cannot be loaded
        """
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise RuntimeError(f"Error loading CSV file {file_path}: {str(e)}") from e

    @staticmethod
    def save_csv_file(df: pd.DataFrame, file_path: Union[str, Path]) -> None:
        """
        Save a DataFrame to a CSV file.

        Args:
            df (pd.DataFrame): DataFrame to save
            file_path (Union[str, Path]): Path to save the file

        Raises:
            Exception: If the file cannot be saved
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            df.to_csv(file_path, index=False)
        except Exception as e:
            raise RuntimeError(f"Error saving CSV file {file_path}: {str(e)}") from e

    @staticmethod
    def create_modified_filename(
        original_path: Union[str, Path], prefix: str = "modified_"
    ) -> Path:
        """
        Create a filename for a modified version of a file.

        Args:
            original_path (Union[str, Path]): Original file path
            prefix (str): Prefix to add to the filename

        Returns:
            Path: New file path with prefix
        """
        original_path = Path(original_path)
        new_filename = f"{prefix}{original_path.name}"
        return Settings.USER_DATA_DIR / new_filename

    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get information about a file.

        Args:
            file_path (Union[str, Path]): Path to the file

        Returns:
            Dict[str, Any]: File information
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {"exists": False}

        stat = file_path.stat()
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified_time": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "extension": file_path.suffix,
            "name": file_path.name,
            "stem": file_path.stem,
        }

    @staticmethod
    def validate_file_size(
        file_path: Union[str, Path], max_size_mb: Optional[float] = None
    ) -> bool:
        """
        Validate that a file is within the size limit.

        Args:
            file_path (Union[str, Path]): Path to the file
            max_size_mb (Optional[float]): Maximum size in MB (defaults to Settings.MAX_FILE_SIZE_MB)

        Returns:
            bool: True if file size is valid
        """
        if max_size_mb is None:
            max_size_mb = Settings.MAX_FILE_SIZE_MB

        file_info = FileService.get_file_info(file_path)

        if not file_info["exists"]:
            return False

        return file_info["size_mb"] <= max_size_mb

    @staticmethod
    def get_display_name(file_path: Union[str, Path]) -> str:
        """
        Get a display-friendly name for a file.

        Args:
            file_path (Union[str, Path]): Path to the file

        Returns:
            str: Display name for the file
        """
        file_path = Path(file_path)

        # Remove common prefixes for cleaner display
        name = file_path.stem

        # Remove "modified_" prefix if present
        if name.startswith("modified_"):
            name = name[9:]  # Remove "modified_" prefix

        # Replace underscores with spaces and title case
        name = name.replace("_", " ").title()

        return name
