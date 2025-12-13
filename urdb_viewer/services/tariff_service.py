"""
Tariff service for URDB Tariff Viewer.

This module provides business logic for tariff data processing and manipulation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from urdb_viewer.config.constants import MONTHS
from urdb_viewer.config.settings import Settings
from urdb_viewer.models.tariff import (
    TariffViewer,
    create_temp_viewer_with_modified_tariff,
)
from urdb_viewer.services.file_service import FileService
from urdb_viewer.utils.helpers import extract_tariff_data


class TariffService:
    """Service for tariff data processing and business logic."""

    @staticmethod
    def load_tariff_viewer(file_path: Union[str, Path]) -> TariffViewer:
        """
        Load a TariffViewer instance from a file with caching.

        Args:
            file_path (Union[str, Path]): Path to the tariff JSON file

        Returns:
            TariffViewer: Loaded tariff viewer instance
        """
        return TariffViewer(file_path)

    @staticmethod
    def get_available_tariffs() -> List[Dict[str, Any]]:
        """
        Get a list of available tariff files with metadata.

        Results are cached for faster subsequent loads.

        Returns:
            List[Dict[str, Any]]: List of tariff file information
        """
        json_files = FileService.find_json_files()
        tariff_info = []

        for file_path in json_files:
            try:
                # Load basic info without creating full TariffViewer
                data = FileService.load_json_file(file_path)

                # Use shared helper for tariff extraction
                tariff = extract_tariff_data(data)

                info = {
                    "file_path": file_path,
                    "display_name": FileService.get_display_name(file_path),
                    "utility_name": tariff.get("utility", "Unknown Utility"),
                    "rate_name": tariff.get("name", "Unknown Rate"),
                    "sector": tariff.get("sector", "Unknown Sector"),
                    "file_size_mb": FileService.get_file_info(file_path)["size_mb"],
                }
                tariff_info.append(info)

            except Exception:
                # Skip files that can't be loaded (don't show warning in cached function)
                continue

        return tariff_info

    @staticmethod
    def update_tariff_rate(
        tariff_data: Dict[str, Any],
        rate_type: str,
        period_index: int,
        new_rate: float,
        new_adjustment: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Update a rate in the tariff data structure.

        Args:
            tariff_data (Dict[str, Any]): Original tariff data
            rate_type (str): Type of rate ('energy' or 'demand')
            period_index (int): Index of the period to update
            new_rate (float): New rate value
            new_adjustment (float): New adjustment value

        Returns:
            Dict[str, Any]: Updated tariff data
        """
        # Deep copy the tariff data
        updated_data = json.loads(json.dumps(tariff_data))

        # Get the appropriate rate structure
        if rate_type == "energy":
            rate_structure_key = "energyratestructure"
        elif rate_type == "demand":
            rate_structure_key = "demandratestructure"
        else:
            raise ValueError(f"Invalid rate type: {rate_type}")

        # Use shared helper for tariff extraction
        tariff = extract_tariff_data(updated_data)

        # Update the rate structure
        if rate_structure_key in tariff and period_index < len(
            tariff[rate_structure_key]
        ):
            if tariff[rate_structure_key][period_index]:
                tariff[rate_structure_key][period_index][0]["rate"] = new_rate
                tariff[rate_structure_key][period_index][0]["adj"] = new_adjustment

        return updated_data

    @staticmethod
    def update_flat_demand_rate(
        tariff_data: Dict[str, Any],
        month_index: int,
        new_rate: float,
        new_adjustment: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Update a flat demand rate for a specific month.

        Args:
            tariff_data (Dict[str, Any]): Original tariff data
            month_index (int): Index of the month to update (0-11)
            new_rate (float): New rate value
            new_adjustment (float): New adjustment value

        Returns:
            Dict[str, Any]: Updated tariff data
        """
        # Deep copy the tariff data
        updated_data = json.loads(json.dumps(tariff_data))

        # Use shared helper for tariff extraction
        tariff = extract_tariff_data(updated_data)

        # Update flat demand structure
        flat_demand_rates = tariff.get("flatdemandstructure", [])
        flat_demand_months = tariff.get("flatdemandmonths", [])

        if (
            flat_demand_rates
            and flat_demand_months
            and month_index < len(flat_demand_months)
        ):
            period_idx = flat_demand_months[month_index]
            if period_idx < len(flat_demand_rates) and flat_demand_rates[period_idx]:
                flat_demand_rates[period_idx][0]["rate"] = new_rate
                flat_demand_rates[period_idx][0]["adj"] = new_adjustment

        return updated_data

    @staticmethod
    def validate_tariff_data(tariff_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tariff data structure and return validation results.

        Args:
            tariff_data (Dict[str, Any]): Tariff data to validate

        Returns:
            Dict[str, Any]: Validation results
        """
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        try:
            # Use shared helper for tariff extraction
            tariff = extract_tariff_data(tariff_data)

            # Check required fields
            required_fields = ["utility", "name"]
            for field in required_fields:
                if field not in tariff:
                    validation_results["errors"].append(
                        f"Missing required field: {field}"
                    )
                    validation_results["is_valid"] = False

            # Check energy rate structure
            if "energyratestructure" in tariff:
                energy_rates = tariff["energyratestructure"]
                if not isinstance(energy_rates, list):
                    validation_results["errors"].append(
                        "Energy rate structure must be a list"
                    )
                    validation_results["is_valid"] = False
                elif len(energy_rates) == 0:
                    validation_results["warnings"].append("No energy rates defined")
            else:
                validation_results["warnings"].append("No energy rate structure found")

            # Check schedules
            weekday_schedule = tariff.get("energyweekdayschedule", [])
            weekend_schedule = tariff.get("energyweekendschedule", [])

            if len(weekday_schedule) != 12:
                validation_results["warnings"].append(
                    "Weekday schedule should have 12 months"
                )

            if len(weekend_schedule) != 12:
                validation_results["warnings"].append(
                    "Weekend schedule should have 12 months"
                )

            # Check for demand rates
            if "demandratestructure" in tariff and tariff["demandratestructure"]:
                demand_weekday_schedule = tariff.get("demandweekdayschedule", [])
                demand_weekend_schedule = tariff.get("demandweekendschedule", [])

                if len(demand_weekday_schedule) != 12:
                    validation_results["warnings"].append(
                        "Demand weekday schedule should have 12 months"
                    )

                if len(demand_weekend_schedule) != 12:
                    validation_results["warnings"].append(
                        "Demand weekend schedule should have 12 months"
                    )

        except Exception as e:
            validation_results["errors"].append(f"Validation error: {str(e)}")
            validation_results["is_valid"] = False

        return validation_results

    @staticmethod
    def get_tariff_summary(tariff_viewer: TariffViewer) -> Dict[str, Any]:
        """
        Get a summary of tariff information.

        Args:
            tariff_viewer (TariffViewer): Tariff viewer instance

        Returns:
            Dict[str, Any]: Tariff summary information
        """
        # Calculate rate statistics
        weekday_rates = tariff_viewer.weekday_df.values.flatten()
        weekend_rates = tariff_viewer.weekend_df.values.flatten()
        all_energy_rates = list(weekday_rates) + list(weekend_rates)
        all_energy_rates = [r for r in all_energy_rates if r > 0]  # Remove zero rates

        demand_weekday_rates = tariff_viewer.demand_weekday_df.values.flatten()
        demand_weekend_rates = tariff_viewer.demand_weekend_df.values.flatten()
        all_demand_rates = list(demand_weekday_rates) + list(demand_weekend_rates)
        all_demand_rates = [r for r in all_demand_rates if r > 0]  # Remove zero rates

        flat_demand_rates = tariff_viewer.flat_demand_df["Rate ($/kW)"].values
        flat_demand_rates = [r for r in flat_demand_rates if r > 0]  # Remove zero rates

        summary = {
            "utility_name": tariff_viewer.utility_name,
            "rate_name": tariff_viewer.rate_name,
            "sector": tariff_viewer.sector,
            "description": tariff_viewer.description,
            "energy_rates": {
                "count": len(all_energy_rates),
                "min": min(all_energy_rates) if all_energy_rates else 0,
                "max": max(all_energy_rates) if all_energy_rates else 0,
                "avg": (
                    sum(all_energy_rates) / len(all_energy_rates)
                    if all_energy_rates
                    else 0
                ),
            },
            "demand_rates": {
                "count": len(all_demand_rates),
                "min": min(all_demand_rates) if all_demand_rates else 0,
                "max": max(all_demand_rates) if all_demand_rates else 0,
                "avg": (
                    sum(all_demand_rates) / len(all_demand_rates)
                    if all_demand_rates
                    else 0
                ),
            },
            "flat_demand_rates": {
                "count": len(flat_demand_rates),
                "min": min(flat_demand_rates) if flat_demand_rates else 0,
                "max": max(flat_demand_rates) if flat_demand_rates else 0,
                "avg": (
                    sum(flat_demand_rates) / len(flat_demand_rates)
                    if flat_demand_rates
                    else 0
                ),
            },
        }

        return summary

    @staticmethod
    def save_modified_tariff(
        original_file_path: Union[str, Path],
        modified_data: Dict[str, Any],
        custom_name: Optional[str] = None,
    ) -> Path:
        """
        Save a modified tariff to a new file.

        Args:
            original_file_path (Union[str, Path]): Path to the original tariff file
            modified_data (Dict[str, Any]): Modified tariff data
            custom_name (Optional[str]): Custom filename (without extension)

        Returns:
            Path: Path to the saved file
        """
        if custom_name:
            new_filename = f"{custom_name}.json"
            save_path = Settings.USER_DATA_DIR / new_filename
        else:
            save_path = FileService.create_modified_filename(original_file_path)

        FileService.save_json_file(modified_data, save_path)
        return save_path
