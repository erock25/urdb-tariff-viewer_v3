"""
Data validation utilities for URDB Tariff Viewer.

This module contains functions for validating tariff data and load profiles.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def validate_tariff_data(tariff_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate tariff data structure and content.

    Args:
        tariff_data (Dict[str, Any]): Tariff data to validate

    Returns:
        Dict[str, Any]: Validation results with errors, warnings, and info
    """
    validation_results = {"is_valid": True, "errors": [], "warnings": [], "info": {}}

    try:
        # Handle both direct tariff data and wrapped in 'items'
        if "items" in tariff_data:
            if not tariff_data["items"] or len(tariff_data["items"]) == 0:
                validation_results["errors"].append("No tariff items found in data")
                validation_results["is_valid"] = False
                return validation_results
            tariff = tariff_data["items"][0]
        else:
            tariff = tariff_data

        # Check required basic fields
        required_fields = ["utility", "name"]
        for field in required_fields:
            if field not in tariff or not tariff[field]:
                validation_results["errors"].append(
                    f"Missing or empty required field: {field}"
                )
                validation_results["is_valid"] = False

        # Validate energy rate structure
        energy_validation = _validate_energy_rates(tariff)
        validation_results["errors"].extend(energy_validation["errors"])
        validation_results["warnings"].extend(energy_validation["warnings"])
        if not energy_validation["is_valid"]:
            validation_results["is_valid"] = False

        # Validate demand rate structure
        demand_validation = _validate_demand_rates(tariff)
        validation_results["warnings"].extend(demand_validation["warnings"])
        # Demand rates are optional, so don't fail validation if missing

        # Validate schedules
        schedule_validation = _validate_schedules(tariff)
        validation_results["errors"].extend(schedule_validation["errors"])
        validation_results["warnings"].extend(schedule_validation["warnings"])
        if not schedule_validation["is_valid"]:
            validation_results["is_valid"] = False

        # Add info about the tariff
        validation_results["info"] = {
            "utility_name": tariff.get("utility", "Unknown"),
            "rate_name": tariff.get("name", "Unknown"),
            "sector": tariff.get("sector", "Unknown"),
            "has_energy_rates": bool(tariff.get("energyratestructure")),
            "has_demand_rates": bool(tariff.get("demandratestructure")),
            "has_flat_demand": bool(tariff.get("flatdemandstructure")),
        }

    except Exception as e:
        validation_results["errors"].append(f"Validation error: {str(e)}")
        validation_results["is_valid"] = False

    return validation_results


def _validate_energy_rates(tariff: Dict[str, Any]) -> Dict[str, Any]:
    """Validate energy rate structure."""
    result = {"is_valid": True, "errors": [], "warnings": []}

    energy_rates = tariff.get("energyratestructure", [])

    if not energy_rates:
        result["warnings"].append("No energy rate structure found")
        return result

    if not isinstance(energy_rates, list):
        result["errors"].append("Energy rate structure must be a list")
        result["is_valid"] = False
        return result

    # Validate each energy rate period
    for i, rate_period in enumerate(energy_rates):
        if not isinstance(rate_period, list) or not rate_period:
            result["errors"].append(f"Energy rate period {i} is invalid")
            result["is_valid"] = False
            continue

        # Check first tier
        first_tier = rate_period[0]
        if not isinstance(first_tier, dict):
            result["errors"].append(f"Energy rate period {i} first tier is invalid")
            result["is_valid"] = False
            continue

        if "rate" not in first_tier:
            result["errors"].append(f"Energy rate period {i} missing 'rate' field")
            result["is_valid"] = False

        try:
            rate_value = float(first_tier["rate"])
            if rate_value < 0:
                result["warnings"].append(f"Energy rate period {i} has negative rate")
            if rate_value > 1:  # Assuming rates over $1/kWh are unusual
                result["warnings"].append(
                    f"Energy rate period {i} has unusually high rate: ${rate_value:.4f}/kWh"
                )
        except (ValueError, TypeError):
            result["errors"].append(f"Energy rate period {i} has invalid rate value")
            result["is_valid"] = False

    return result


def _validate_demand_rates(tariff: Dict[str, Any]) -> Dict[str, Any]:
    """Validate demand rate structure."""
    result = {"is_valid": True, "errors": [], "warnings": []}

    demand_rates = tariff.get("demandratestructure", [])

    if not demand_rates:
        result["warnings"].append("No demand rate structure found")
        return result

    if not isinstance(demand_rates, list):
        result["warnings"].append("Demand rate structure should be a list")
        return result

    # Validate each demand rate period
    for i, rate_period in enumerate(demand_rates):
        if not isinstance(rate_period, list) or not rate_period:
            result["warnings"].append(f"Demand rate period {i} is invalid")
            continue

        # Check first tier
        first_tier = rate_period[0]
        if not isinstance(first_tier, dict):
            result["warnings"].append(f"Demand rate period {i} first tier is invalid")
            continue

        if "rate" not in first_tier:
            result["warnings"].append(f"Demand rate period {i} missing 'rate' field")
            continue

        try:
            rate_value = float(first_tier["rate"])
            if rate_value < 0:
                result["warnings"].append(f"Demand rate period {i} has negative rate")
            if rate_value > 100:  # Assuming rates over $100/kW are unusual
                result["warnings"].append(
                    f"Demand rate period {i} has unusually high rate: ${rate_value:.2f}/kW"
                )
        except (ValueError, TypeError):
            result["warnings"].append(f"Demand rate period {i} has invalid rate value")

    return result


def _validate_schedules(tariff: Dict[str, Any]) -> Dict[str, Any]:
    """Validate TOU schedules."""
    result = {"is_valid": True, "errors": [], "warnings": []}

    # Check energy schedules
    weekday_schedule = tariff.get("energyweekdayschedule", [])
    weekend_schedule = tariff.get("energyweekendschedule", [])

    if not weekday_schedule and not weekend_schedule:
        result["warnings"].append("No energy schedules found")
        return result

    # Validate weekday schedule
    if weekday_schedule:
        if len(weekday_schedule) != 12:
            result["errors"].append(
                f"Energy weekday schedule should have 12 months, found {len(weekday_schedule)}"
            )
            result["is_valid"] = False
        else:
            for month_idx, month_schedule in enumerate(weekday_schedule):
                if not isinstance(month_schedule, list):
                    result["errors"].append(
                        f"Energy weekday schedule month {month_idx + 1} should be a list"
                    )
                    result["is_valid"] = False
                elif len(month_schedule) != 24:
                    result["errors"].append(
                        f"Energy weekday schedule month {month_idx + 1} should have 24 hours, found {len(month_schedule)}"
                    )
                    result["is_valid"] = False

    # Validate weekend schedule
    if weekend_schedule:
        if len(weekend_schedule) != 12:
            result["errors"].append(
                f"Energy weekend schedule should have 12 months, found {len(weekend_schedule)}"
            )
            result["is_valid"] = False
        else:
            for month_idx, month_schedule in enumerate(weekend_schedule):
                if not isinstance(month_schedule, list):
                    result["errors"].append(
                        f"Energy weekend schedule month {month_idx + 1} should be a list"
                    )
                    result["is_valid"] = False
                elif len(month_schedule) != 24:
                    result["errors"].append(
                        f"Energy weekend schedule month {month_idx + 1} should have 24 hours, found {len(month_schedule)}"
                    )
                    result["is_valid"] = False

    return result


def validate_load_profile(load_profile_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate a load profile CSV file.

    Args:
        load_profile_path (Union[str, Path]): Path to load profile CSV

    Returns:
        Dict[str, Any]: Validation results
    """
    validation_results = {"is_valid": True, "errors": [], "warnings": [], "info": {}}

    try:
        # Check if file exists
        file_path = Path(load_profile_path)
        if not file_path.exists():
            validation_results["errors"].append(f"File does not exist: {file_path}")
            validation_results["is_valid"] = False
            return validation_results

        # Try to load the CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            validation_results["errors"].append(f"Could not read CSV file: {str(e)}")
            validation_results["is_valid"] = False
            return validation_results

        # Check for required columns
        required_columns = ["timestamp", "load_kW"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            validation_results["errors"].append(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
            validation_results["is_valid"] = False
            return validation_results

        # Validate timestamp column
        try:
            timestamps = pd.to_datetime(df["timestamp"])

            # Check for duplicates
            if timestamps.duplicated().any():
                validation_results["warnings"].append("Duplicate timestamps found")

            # Check for proper ordering
            if not timestamps.is_monotonic_increasing:
                validation_results["warnings"].append(
                    "Timestamps are not in chronological order"
                )

        except Exception as e:
            validation_results["errors"].append(f"Invalid timestamp format: {str(e)}")
            validation_results["is_valid"] = False

        # Validate load_kW column
        if not pd.api.types.is_numeric_dtype(df["load_kW"]):
            validation_results["errors"].append("load_kW column must be numeric")
            validation_results["is_valid"] = False
        else:
            # Check for negative values
            if (df["load_kW"] < 0).any():
                negative_count = (df["load_kW"] < 0).sum()
                validation_results["warnings"].append(
                    f"Found {negative_count} negative load values"
                )

            # Check for missing values
            if df["load_kW"].isna().any():
                missing_count = df["load_kW"].isna().sum()
                validation_results["warnings"].append(
                    f"Found {missing_count} missing load values"
                )

            # Check for unrealistic values
            max_load = df["load_kW"].max()
            if max_load > 100000:  # 100 MW seems like a reasonable upper bound
                validation_results["warnings"].append(
                    f"Very high peak load detected: {max_load:.1f} kW"
                )

        # Add file information
        validation_results["info"] = {
            "row_count": len(df),
            "columns": list(df.columns),
            "file_size_mb": file_path.stat().st_size / (1024 * 1024),
        }

        if validation_results["is_valid"]:
            validation_results["info"].update(
                {
                    "date_range": {
                        "start": timestamps.min().strftime("%Y-%m-%d %H:%M:%S"),
                        "end": timestamps.max().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    "load_range": {
                        "min": df["load_kW"].min(),
                        "max": df["load_kW"].max(),
                        "avg": df["load_kW"].mean(),
                    },
                }
            )

    except Exception as e:
        validation_results["errors"].append(f"Validation error: {str(e)}")
        validation_results["is_valid"] = False

    return validation_results


def validate_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate that a file contains valid JSON.

    Args:
        file_path (Union[str, Path]): Path to JSON file

    Returns:
        Dict[str, Any]: Validation results
    """
    validation_results = {"is_valid": True, "errors": [], "warnings": [], "data": None}

    try:
        file_path = Path(file_path)

        if not file_path.exists():
            validation_results["errors"].append(f"File does not exist: {file_path}")
            validation_results["is_valid"] = False
            return validation_results

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        validation_results["data"] = data

        # Basic JSON structure checks
        if not isinstance(data, dict):
            validation_results["warnings"].append("JSON root is not a dictionary")

    except json.JSONDecodeError as e:
        validation_results["errors"].append(f"Invalid JSON format: {str(e)}")
        validation_results["is_valid"] = False
    except Exception as e:
        validation_results["errors"].append(f"Error reading file: {str(e)}")
        validation_results["is_valid"] = False

    return validation_results
