"""
Tariff Database Service for URDB Tariff Viewer.

This module provides functions for loading and searching the USURDB parquet database,
allowing users to search for tariffs by utility name and apply various filters.

IMPORTANT: Tariff Data Format Conversion
========================================
This service handles tariffs from the usurdb.parquet file which stores data in
"Local DB Format" (MongoDB export with camelCase field names). However, the
URDB_JSON_Viewer app expects tariffs in "OpenEI API Format" (lowercase field names).

When importing tariffs, use `convert_local_to_api_format()` to convert field names.

Key Format Differences:
    Local DB Format          API Format (App expects)
    ---------------          -----------------------
    utilityName         ->   utility
    rateName            ->   name
    energyRateStrux     ->   energyratestructure
    energyWeekdaySched  ->   energyweekdayschedule
    flatDemandStrux     ->   flatdemandstructure
    effectiveDate       ->   startdate

See docs/development/tariff-data-formats.md for complete documentation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from urdb_viewer.config.settings import Settings


class TariffDatabaseService:
    """Service for searching and loading tariffs from the parquet database."""

    @staticmethod
    def check_database_available() -> bool:
        """
        Check if the parquet database files exist.

        Returns:
            bool: True if database is available
        """
        return Settings.TARIFF_DB_PATH.exists()

    @staticmethod
    def check_utility_index_available() -> bool:
        """
        Check if the utility index file exists.

        Returns:
            bool: True if utility index is available
        """
        return Settings.UTILITY_INDEX_PATH.exists()

    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_utility_index() -> pd.DataFrame:
        """
        Load the utility index for fast utility name lookups.

        Returns:
            DataFrame with utility_name_lower, utility_name, tariff_count
        """
        if Settings.UTILITY_INDEX_PATH.exists():
            return pd.read_parquet(Settings.UTILITY_INDEX_PATH)
        return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_all_utility_names() -> List[str]:
        """
        Get list of all unique utility names for autocomplete/suggestions.

        Returns:
            Sorted list of utility names
        """
        if TariffDatabaseService.check_utility_index_available():
            index_df = TariffDatabaseService.load_utility_index()
            if not index_df.empty and "utility_name" in index_df.columns:
                return sorted(index_df["utility_name"].tolist())

        # Fallback to loading from main database
        if TariffDatabaseService.check_database_available():
            try:
                df = pd.read_parquet(Settings.TARIFF_DB_PATH, columns=["utility_name"])
                return sorted(df["utility_name"].unique().tolist())
            except Exception:
                pass

        return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_database_stats() -> Dict[str, Any]:
        """
        Get statistics about the tariff database.

        Returns:
            Dictionary with database statistics
        """
        if not TariffDatabaseService.check_database_available():
            return {"available": False}

        try:
            df = pd.read_parquet(
                Settings.TARIFF_DB_PATH,
                columns=["utility_name", "sector", "effective_date"],
            )
            return {
                "available": True,
                "total_tariffs": len(df),
                "unique_utilities": df["utility_name"].nunique(),
                "sectors": sorted(df["sector"].dropna().unique().tolist()),
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def search_tariffs(
        utility_name: str,
        sectors: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        name_contains: Optional[str] = None,
        exclude_terms: Optional[List[str]] = None,
        min_kw_filter: float = 0.0,
        max_kw_filter: float = 0.0,
        include_superseded: bool = True,
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Search tariffs from the parquet database.

        Args:
            utility_name: Utility name to search for (partial match)
            sectors: List of sectors to filter by
            years: List of effective years to filter by
            name_contains: Filter tariff names containing this string
            exclude_terms: List of terms to exclude from tariff names
            min_kw_filter: Filter tariffs where Min kW <= this value
            max_kw_filter: Filter tariffs where Max kW >= this value
            include_superseded: Whether to include superseded tariffs

        Returns:
            Tuple of (DataFrame for display, List of full tariff dicts)
        """
        if not TariffDatabaseService.check_database_available():
            return pd.DataFrame(), []

        try:
            # Load relevant columns for filtering
            df = pd.read_parquet(
                Settings.TARIFF_DB_PATH,
                columns=[
                    "label",
                    "utility_name",
                    "utility_name_lower",
                    "rate_name",
                    "sector",
                    "service_type",
                    "demand_min",
                    "demand_max",
                    "energy_min",
                    "energy_max",
                    "effective_date",
                    "end_date",
                    "description",
                    "eia_id",
                    "full_tariff_json",
                ],
            )

            # Filter by utility name (case-insensitive substring match)
            if utility_name:
                utility_lower = utility_name.lower()
                df = df[df["utility_name_lower"].str.contains(utility_lower, na=False)]

            if df.empty:
                return pd.DataFrame(), []

            # Parse effective year
            df["effective_year"] = pd.to_datetime(
                df["effective_date"], errors="coerce"
            ).dt.year

            # Filter by sectors
            if sectors:
                df = df[df["sector"].isin(sectors)]

            # Filter by years
            if years:
                df = df[df["effective_year"].isin(years)]

            # Filter by tariff name contains
            if name_contains:
                df = df[
                    df["rate_name"].str.contains(name_contains, case=False, na=False)
                ]

            # Filter by exclude terms
            if exclude_terms:
                for term in exclude_terms:
                    if term.strip():
                        df = df[
                            ~df["rate_name"].str.contains(
                                term.strip(), case=False, na=False
                            )
                        ]

            # Filter by Min kW
            if min_kw_filter > 0:
                df = df[(df["demand_min"].isna()) | (df["demand_min"] <= min_kw_filter)]

            # Filter by Max kW
            if max_kw_filter > 0:
                df = df[(df["demand_max"].isna()) | (df["demand_max"] >= max_kw_filter)]

            # Filter superseded tariffs
            if not include_superseded:
                df = df[df["end_date"].isna() | (df["end_date"] == "")]

            if df.empty:
                return pd.DataFrame(), []

            # Extract full tariff data
            tariffs = [json.loads(row) for row in df["full_tariff_json"]]

            # Create display DataFrame
            display_df = TariffDatabaseService._create_display_dataframe(df)

            return display_df, tariffs

        except Exception as e:
            st.error(f"Error searching tariffs: {e}")
            return pd.DataFrame(), []

    @staticmethod
    def _create_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a display-friendly DataFrame from search results.

        Args:
            df: Raw DataFrame from parquet search

        Returns:
            Formatted DataFrame for display
        """
        from datetime import datetime

        display_data = []

        for _, row in df.iterrows():
            # Generate flags
            flags = []

            # Superseded flag
            if pd.notna(row.get("end_date")) and str(row.get("end_date")).strip():
                flags.append("📛")

            # Service type flags
            service_type = row.get("service_type", "")
            if service_type:
                service_lower = str(service_type).lower()
                if service_lower == "delivery":
                    flags.append("🚚")
                elif service_lower == "energy":
                    flags.append("⚡")

            # Old tariff flag (>2 years)
            try:
                effective_dt = pd.to_datetime(row.get("effective_date"))
                if pd.notna(effective_dt):
                    years_old = (
                        datetime.now() - effective_dt.to_pydatetime()
                    ).days / 365
                    if years_old > 2:
                        flags.append("📅")
            except Exception:
                pass

            flag_str = " ".join(flags) if flags else "✅"

            # Format dates
            effective_date = row.get("effective_date", "")
            if pd.notna(effective_date):
                try:
                    effective_date = pd.to_datetime(effective_date).strftime("%Y-%m-%d")
                except Exception:
                    effective_date = str(effective_date)

            end_date = row.get("end_date", "")
            if pd.notna(end_date) and str(end_date).strip():
                try:
                    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
                except Exception:
                    end_date = str(end_date)
            else:
                end_date = ""

            # Handle numeric fields
            min_kw = row.get("demand_min")
            max_kw = row.get("demand_max")
            min_kwh = row.get("energy_min")
            max_kwh = row.get("energy_max")

            display_data.append(
                {
                    "Label": row.get("label", ""),
                    "Tariff Name": row.get("rate_name", "N/A"),
                    "Utility": row.get("utility_name", "N/A"),
                    "EIA ID": row.get("eia_id"),
                    "Sector": row.get("sector", "N/A"),
                    "Service Type": str(service_type) if service_type else "",
                    "Flags": flag_str,
                    "Min kW": float(min_kw) if pd.notna(min_kw) else 0,
                    "Max kW": float(max_kw) if pd.notna(max_kw) else float("inf"),
                    "Min kWh": float(min_kwh) if pd.notna(min_kwh) else 0,
                    "Max kWh": float(max_kwh) if pd.notna(max_kwh) else float("inf"),
                    "Effective Date": effective_date,
                    "End Date": end_date,
                    "Description": row.get("description", ""),
                }
            )

        return pd.DataFrame(display_data)

    @staticmethod
    def get_unique_sectors() -> List[str]:
        """
        Get list of unique sectors from the database.

        Returns:
            Sorted list of sector names
        """
        if not TariffDatabaseService.check_database_available():
            return []

        try:
            df = pd.read_parquet(Settings.TARIFF_DB_PATH, columns=["sector"])
            return sorted(df["sector"].dropna().unique().tolist())
        except Exception:
            return []

    @staticmethod
    def get_unique_years() -> List[int]:
        """
        Get list of unique effective years from the database.

        Returns:
            Sorted list of years (descending)
        """
        if not TariffDatabaseService.check_database_available():
            return []

        try:
            df = pd.read_parquet(Settings.TARIFF_DB_PATH, columns=["effective_date"])
            years = pd.to_datetime(df["effective_date"], errors="coerce").dt.year
            return sorted([int(y) for y in years.dropna().unique()], reverse=True)
        except Exception:
            return []

    @staticmethod
    def convert_local_to_api_format(tariff: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a tariff from local database format (MongoDB export/camelCase)
        to OpenEI API format (lowercase) which the URDB_JSON_Viewer app expects.

        Args:
            tariff: Tariff dictionary in local database format

        Returns:
            Tariff dictionary in API format
        """
        # Field mapping from local DB format to API format
        field_map = {
            # Basic info
            "utilityName": "utility",
            "rateName": "name",
            "eiaId": "eiaid",
            "serviceType": "servicetype",
            "effectiveDate": "startdate",
            "endDate": "enddate",
            "demandMin": "mindemand",
            "demandMax": "maxdemand",
            "energyMin": "minenergy",
            "energyMax": "maxenergy",
            "voltageCategory": "voltagecategory",
            "phaseWiring": "phasewiring",
            # Energy rates
            "energyRateStrux": "energyratestructure",
            "energyWeekdaySched": "energyweekdayschedule",
            "energyWeekendSched": "energyweekendschedule",
            "energyTOULabels": "energytoulabels",
            "energyComments": "energycomments",
            # Demand rates
            "demandRateStrux": "demandratestructure",
            "demandWeekdaySched": "demandweekdayschedule",
            "demandWeekendSched": "demandweekendschedule",
            "demandLabels": "demandtoulabels",
            "demandUnits": "demandunits",
            "demandRateUnit": "demandrateunit",
            "demandReactivePowerCharge": "demandreactivepowercharge",
            # Flat demand
            "flatDemandStrux": "flatdemandstructure",
            "flatDemandMonths": "flatdemandmonths",
            "flatDemandUnit": "flatdemandunit",
            # Fixed charges
            "fixedChargeFirstMeter": "fixedchargefirstmeter",
            "fixedChargeUnits": "fixedchargeunits",
            "minMonthlyCharge": "minmonthlycharge",
            # Other
            "sourceParent": "sourceparent",
            "peakKWCapacityMin": "peakkwcapacitymin",
            "peakKWCapacityMax": "peakkwcapacitymax",
            "peakKWhUsageMin": "peakkwhusagemin",
            "peakKWhUsageMax": "peakkwhusagemax",
        }

        converted = {}

        for key, value in tariff.items():
            # Check if this is a known field to convert
            if key in field_map:
                new_key = field_map[key]
            elif key == "_id":
                # Convert MongoDB _id to label
                if isinstance(value, dict) and "$oid" in value:
                    converted["label"] = value["$oid"]
                else:
                    converted["label"] = str(value) if value else ""
                continue
            else:
                # Keep lowercase keys as-is, convert others to lowercase
                new_key = key.lower() if key[0].isupper() else key

            # Handle special conversions
            if key == "effectiveDate" and isinstance(value, dict):
                # Convert MongoDB date format to Unix timestamp or ISO string
                date_str = value.get("$date", "")
                if date_str:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        converted[new_key] = int(dt.timestamp())
                    except Exception:
                        converted[new_key] = date_str
                continue
            elif key == "endDate" and isinstance(value, dict):
                date_str = value.get("$date", "")
                if date_str:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        converted[new_key] = int(dt.timestamp())
                    except Exception:
                        converted[new_key] = date_str
                continue
            elif key in ("energyRateStrux", "demandRateStrux", "flatDemandStrux"):
                # Convert rate structure format if needed
                # Local format: [{"energyRateTiers": [{...}]}]
                # API format: [[{...}]]
                if isinstance(value, list) and value:
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        # Check if it's in the nested tier format
                        tier_key = (
                            "energyRateTiers"
                            if "energy" in key.lower()
                            else (
                                "demandRateTiers"
                                if "demand" in key.lower()
                                else "flatDemandTiers"
                            )
                        )
                        if tier_key in first_item:
                            # Convert from nested format to flat format
                            converted[new_key] = [
                                item.get(tier_key, [item]) for item in value
                            ]
                            continue
                converted[new_key] = value
            else:
                converted[new_key] = value

        return converted

    @staticmethod
    def normalize_rate_structures(tariff: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize rate structures to the flat API format expected by TariffViewer.

        Handles the case where tariffs have lowercase field names but nested tier structures.

        The TariffViewer expects rate structures like:
            [[{rate: 0.10, adj: 0}], [{rate: 0.15, adj: 0}]]

        But some tariffs have nested tier format:
            [{flatDemandTiers: [{rate: 0.10}]}, {flatDemandTiers: [{rate: 0.15}]}]

        This function converts nested formats to flat formats.

        Args:
            tariff: Tariff dictionary (may have nested or flat rate structures)

        Returns:
            Tariff with normalized rate structures
        """
        normalized = tariff.copy()

        # Rate structure fields and their nested tier keys
        rate_structure_mapping = {
            "energyratestructure": "energyRateTiers",
            "demandratestructure": "demandRateTiers",
            "flatdemandstructure": "flatDemandTiers",
        }

        for field_name, tier_key in rate_structure_mapping.items():
            if field_name in normalized:
                value = normalized[field_name]
                if isinstance(value, list) and value:
                    first_item = value[0]
                    # Check if it's in nested tier format
                    if isinstance(first_item, dict) and tier_key in first_item:
                        # Convert from nested format to flat format
                        normalized[field_name] = [
                            (
                                item.get(tier_key, [item])
                                if isinstance(item, dict)
                                else item
                            )
                            for item in value
                        ]

        return normalized

    @staticmethod
    def convert_tariff_to_json_format(tariff: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a tariff from the database format to the JSON format
        expected by the URDB_JSON_Viewer app (wrapped in 'items' array).

        Handles conversion from local DB format to API format if needed,
        and normalizes rate structures to the expected flat format.

        Args:
            tariff: Tariff dictionary from database

        Returns:
            Tariff data in the expected JSON format
        """
        # Check if tariff is in local DB format (has camelCase keys like utilityName)
        # or already in API format (has lowercase keys like utility)
        if (
            "utilityName" in tariff
            or "rateName" in tariff
            or "energyRateStrux" in tariff
        ):
            # Convert from local DB format to API format
            converted_tariff = TariffDatabaseService.convert_local_to_api_format(tariff)
        else:
            # Already in API format - just copy
            converted_tariff = tariff.copy()

        # Always normalize rate structures (handles hybrid formats)
        converted_tariff = TariffDatabaseService.normalize_rate_structures(
            converted_tariff
        )

        return {"items": [converted_tariff]}

    @staticmethod
    def generate_filename(tariff: Dict[str, Any]) -> str:
        """
        Generate a clean filename for a tariff.

        Handles both API format (utility, name) and local DB format (utilityName, rateName).

        Args:
            tariff: Tariff dictionary

        Returns:
            Clean filename string (without .json extension)
        """
        import re

        # Handle both formats
        utility = tariff.get("utility") or tariff.get("utilityName") or "Unknown"
        name = tariff.get("name") or tariff.get("rateName") or "Unknown"

        # Clean the strings
        def clean_string(s: str) -> str:
            # Replace common problematic characters
            s = s.replace("/", "_").replace("\\", "_").replace(":", "_")
            s = s.replace(" ", "_").replace("-", "_")
            # Remove any remaining invalid characters
            s = re.sub(r"[^\w_]", "", s)
            # Collapse multiple underscores
            s = re.sub(r"_+", "_", s)
            return s.strip("_")

        utility_clean = clean_string(utility)
        name_clean = clean_string(name)

        return f"{utility_clean}_{name_clean}"

    @staticmethod
    def save_tariffs_to_files(
        tariffs: List[Dict[str, Any]], target_dir: Optional[Path] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Save selected tariffs as JSON files.

        Args:
            tariffs: List of tariff dictionaries to save
            target_dir: Target directory (defaults to Settings.TARIFFS_DIR)

        Returns:
            Tuple of (list of successful filenames, list of error messages)
        """
        if target_dir is None:
            target_dir = Settings.TARIFFS_DIR

        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        successful = []
        errors = []

        for tariff in tariffs:
            try:
                filename = TariffDatabaseService.generate_filename(tariff)
                filepath = target_dir / f"{filename}.json"

                # Handle duplicate filenames
                counter = 1
                original_filepath = filepath
                while filepath.exists():
                    filepath = target_dir / f"{filename}_{counter}.json"
                    counter += 1

                # Convert to expected format and save
                json_data = TariffDatabaseService.convert_tariff_to_json_format(tariff)

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

                successful.append(filepath.name)

            except Exception as e:
                tariff_name = tariff.get("name", tariff.get("rateName", "Unknown"))
                errors.append(f"{tariff_name}: {str(e)}")

        return successful, errors

    @staticmethod
    def find_similar_utilities(search_term: str, limit: int = 10) -> List[str]:
        """
        Find utilities with names similar to the search term.

        Args:
            search_term: The search term to find similar utilities for
            limit: Maximum number of suggestions to return

        Returns:
            List of similar utility names
        """
        all_utilities = TariffDatabaseService.get_all_utility_names()
        if not all_utilities or not search_term:
            return []

        search_lower = search_term.lower()
        search_words = search_lower.split()

        # Find utilities containing any of the search words
        similar = []
        for utility in all_utilities:
            utility_lower = utility.lower()
            if any(word in utility_lower for word in search_words):
                similar.append(utility)
                if len(similar) >= limit:
                    break

        return similar
