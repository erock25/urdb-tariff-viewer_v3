"""
Tariff data model for URDB Tariff Viewer.

This module contains the TariffViewer class responsible for loading and processing
utility rate structures from URDB JSON files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from urdb_viewer.config.constants import HOURS, MONTHS


class TariffViewer:
    """
    A class for processing and visualizing URDB tariff data.

    This class handles loading, parsing, and analyzing utility rate structures
    from the U.S. Utility Rate Database (URDB) JSON format.

    Attributes:
        utility_name (str): Name of the utility company
        rate_name (str): Name of the rate schedule
        sector (str): Customer sector (Residential/Commercial/Industrial)
        description (str): Rate description
        data (Dict): Complete tariff data from JSON
        tariff (Dict): Main tariff structure
        months (List[str]): Month abbreviations
        hours (List[int]): Hours 0-23
        weekday_df (pd.DataFrame): Weekday energy rates by month/hour
        weekend_df (pd.DataFrame): Weekend energy rates by month/hour
        demand_weekday_df (pd.DataFrame): Weekday demand rates by month/hour
        demand_weekend_df (pd.DataFrame): Weekend demand rates by month/hour
        flat_demand_df (pd.DataFrame): Flat demand rates by month

    Example:
        >>> viewer = TariffViewer('path/to/tariff.json')
        >>> heatmap = viewer.plot_heatmap(is_weekday=True)
    """

    def __init__(self, json_file: Union[str, Path]):
        """
        Initialize TariffViewer with a JSON tariff file.

        Args:
            json_file (Union[str, Path]): Path to the URDB JSON tariff file

        Raises:
            Exception: If the file cannot be loaded or parsed
        """
        try:
            with open(json_file, "r") as file:
                self.data = json.load(file)

            # Handle both direct tariff data and wrapped in 'items'
            if "items" in self.data:
                self.tariff = self.data["items"][0]
            else:
                self.tariff = self.data
                self.data = {"items": [self.data]}  # Wrap for consistency

            # Extract basic information with fallbacks
            self.utility_name = self.tariff.get("utility", "Unknown Utility")
            self.rate_name = self.tariff.get("name", "Unknown Rate")
            self.sector = self.tariff.get("sector", "Unknown Sector")
            self.description = self.tariff.get(
                "description", "No description available"
            )

        except Exception as e:
            raise RuntimeError(
                f"Error loading tariff file {json_file}: {str(e)}"
            ) from e

        # Setup data structures
        self.months = MONTHS
        self.hours = HOURS
        self.update_rate_dataframes()

    def get_rate(self, period_index: int, rate_structure: List[List[Dict]]) -> float:
        """
        Get the rate for a specific period from the rate structure.

        Works for both energy rates and demand rates.

        Args:
            period_index (int): Index of the time period
            rate_structure (List[List[Dict]]): Rate structure from tariff

        Returns:
            float: Rate value including any adjustments
        """
        if period_index < len(rate_structure) and rate_structure[period_index]:
            rate = rate_structure[period_index][0].get("rate", 0)
            adj = rate_structure[period_index][0].get("adj", 0)
            return rate + adj
        return 0

    # Alias for backward compatibility
    def get_demand_rate(
        self, period_index: int, rate_structure: List[List[Dict]]
    ) -> float:
        """Alias for get_rate() - provided for backward compatibility."""
        return self.get_rate(period_index, rate_structure)

    def update_rate_dataframes(self) -> None:
        """
        Update all rate DataFrames from the tariff data.

        This method processes the tariff structure and creates DataFrames for:
        - Weekday and weekend energy rates
        - Weekday and weekend demand rates
        - Flat demand rates
        """
        # Energy rates
        energy_rates = self.tariff.get("energyratestructure", [])
        weekday_schedule = self.tariff.get("energyweekdayschedule", [])
        weekend_schedule = self.tariff.get("energyweekendschedule", [])

        # Create weekday energy rates DataFrame
        if energy_rates and weekday_schedule:
            weekday_rates = []
            for month_schedule in weekday_schedule:
                rates = [
                    self.get_rate(period, energy_rates) for period in month_schedule
                ]
                weekday_rates.append(rates)
            self.weekday_df = pd.DataFrame(
                weekday_rates, index=self.months, columns=self.hours
            )
        else:
            self.weekday_df = pd.DataFrame(0, index=self.months, columns=self.hours)

        # Create weekend energy rates DataFrame
        if energy_rates and weekend_schedule:
            weekend_rates = []
            for month_schedule in weekend_schedule:
                rates = [
                    self.get_rate(period, energy_rates) for period in month_schedule
                ]
                weekend_rates.append(rates)
            self.weekend_df = pd.DataFrame(
                weekend_rates, index=self.months, columns=self.hours
            )
        else:
            self.weekend_df = pd.DataFrame(0, index=self.months, columns=self.hours)

        # Demand rates
        demand_rates = self.tariff.get("demandratestructure", [])
        demand_weekday_schedule = self.tariff.get("demandweekdayschedule", [])
        demand_weekend_schedule = self.tariff.get("demandweekendschedule", [])

        # Create weekday demand rates DataFrame
        if demand_rates and demand_weekday_schedule:
            demand_weekday_rates = []
            for month_schedule in demand_weekday_schedule:
                rates = [
                    self.get_demand_rate(period, demand_rates)
                    for period in month_schedule
                ]
                demand_weekday_rates.append(rates)
            self.demand_weekday_df = pd.DataFrame(
                demand_weekday_rates, index=self.months, columns=self.hours
            )
        else:
            self.demand_weekday_df = pd.DataFrame(
                0, index=self.months, columns=self.hours
            )

        # Create weekend demand rates DataFrame
        if demand_rates and demand_weekend_schedule:
            demand_weekend_rates = []
            for month_schedule in demand_weekend_schedule:
                rates = [
                    self.get_demand_rate(period, demand_rates)
                    for period in month_schedule
                ]
                demand_weekend_rates.append(rates)
            self.demand_weekend_df = pd.DataFrame(
                demand_weekend_rates, index=self.months, columns=self.hours
            )
        else:
            self.demand_weekend_df = pd.DataFrame(
                0, index=self.months, columns=self.hours
            )

        # Flat demand rates (seasonal/monthly)
        flat_demand_rates = self.tariff.get("flatdemandstructure", [])
        flat_demand_months = self.tariff.get("flatdemandmonths", [])

        if flat_demand_rates and flat_demand_months:
            flat_demand_rates_list = []
            for month_idx in range(12):
                period_idx = (
                    flat_demand_months[month_idx]
                    if month_idx < len(flat_demand_months)
                    else 0
                )
                if (
                    period_idx < len(flat_demand_rates)
                    and flat_demand_rates[period_idx]
                ):
                    rate = flat_demand_rates[period_idx][0].get("rate", 0)
                    adj = flat_demand_rates[period_idx][0].get("adj", 0)
                    flat_demand_rates_list.append(rate + adj)
                else:
                    flat_demand_rates_list.append(0)
            self.flat_demand_df = pd.DataFrame(
                flat_demand_rates_list, index=self.months, columns=["Rate ($/kW)"]
            )
        else:
            self.flat_demand_df = pd.DataFrame(
                0, index=self.months, columns=["Rate ($/kW)"]
            )

    def _calculate_period_statistics(
        self, weekday_schedule: List, weekend_schedule: List, year: int = 2025
    ) -> tuple:
        """
        Calculate period hours and days from schedules.

        This is a shared helper method used by both TOU and demand table creation.

        Args:
            weekday_schedule: List of weekday period schedules by month
            weekend_schedule: List of weekend period schedules by month
            year: Reference year for calendar calculations

        Returns:
            tuple: (period_hours dict, period_days dict, total_hours)
        """
        import calendar

        period_hours = {}
        period_days = {}
        total_hours = 0

        if len(weekday_schedule) >= 12 and len(weekend_schedule) >= 12:
            for month in range(12):
                cal = calendar.monthcalendar(year, month + 1)

                weekday_count = 0
                weekend_count = 0

                for week in cal:
                    for day_idx, day in enumerate(week):
                        if day == 0:
                            continue
                        if day_idx < 5:
                            weekday_count += 1
                        else:
                            weekend_count += 1

                for hour in range(24):
                    period = weekday_schedule[month][hour]
                    period_hours[period] = period_hours.get(period, 0) + weekday_count

                for hour in range(24):
                    period = weekend_schedule[month][hour]
                    period_hours[period] = period_hours.get(period, 0) + weekend_count

                periods_in_weekday = set(weekday_schedule[month])
                periods_in_weekend = set(weekend_schedule[month])

                for period in periods_in_weekday:
                    period_days[period] = period_days.get(period, 0) + weekday_count

                for period in periods_in_weekend:
                    period_days[period] = period_days.get(period, 0) + weekend_count

                total_hours += (weekday_count + weekend_count) * 24

        return period_hours, period_days, total_hours

    def _get_months_for_period(
        self,
        period_index: int,
        weekday_schedule: List,
        weekend_schedule: List,
        rate_structure: List,
    ) -> str:
        """
        Determine which months a period appears in for weekday and weekend schedules.

        This is a shared helper for both energy and demand period lookups.

        Args:
            period_index: Index of the period
            weekday_schedule: Weekday schedule from tariff
            weekend_schedule: Weekend schedule from tariff
            rate_structure: Rate structure to validate period indices

        Returns:
            str: Formatted string describing when the period is used
        """
        weekday_months = []
        weekend_months = []

        for month_idx, month_schedule in enumerate(weekday_schedule):
            if (
                month_idx < len(self.months)
                and period_index < len(rate_structure)
                and period_index in month_schedule
            ):
                weekday_months.append(self.months[month_idx])

        for month_idx, month_schedule in enumerate(weekend_schedule):
            if (
                month_idx < len(self.months)
                and period_index < len(rate_structure)
                and period_index in month_schedule
            ):
                weekend_months.append(self.months[month_idx])

        parts = []
        if weekday_months:
            parts.append(f"{self._format_month_range(weekday_months)} (Weekday)")
        if weekend_months:
            parts.append(f"{self._format_month_range(weekend_months)} (Weekend)")

        return ", ".join(parts) if parts else "Not used"

    def _create_rate_labels_table(
        self,
        rate_type: str,
        labels_key: str,
        rates_key: str,
        weekday_schedule_key: str,
        weekend_schedule_key: str,
    ) -> pd.DataFrame:
        """
        Create a table showing rate labels with their corresponding rates.

        This is a generic method used for both energy TOU and demand rate tables.

        Args:
            rate_type: "energy" or "demand" - used for column naming
            labels_key: Key in tariff for labels (e.g., 'energytoulabels')
            rates_key: Key in tariff for rate structure (e.g., 'energyratestructure')
            weekday_schedule_key: Key for weekday schedule
            weekend_schedule_key: Key for weekend schedule

        Returns:
            pd.DataFrame: Table with rate period information
        """
        labels = self.tariff.get(labels_key, None)
        rate_structure = self.tariff.get(rates_key, [])

        if not rate_structure:
            return pd.DataFrame()

        weekday_schedule = self.tariff.get(weekday_schedule_key, [])
        weekend_schedule = self.tariff.get(weekend_schedule_key, [])

        period_hours, period_days, total_hours = self._calculate_period_statistics(
            weekday_schedule, weekend_schedule
        )

        # Determine column names and default label based on rate type
        if rate_type == "energy":
            period_col = "TOU Period"
            rate_unit = "$/kWh"
            default_label = "TOU Label Not In Tariff JSON"
        else:
            period_col = "Demand Period"
            rate_unit = "$/kW"
            default_label = "Demand Label Not In Tariff JSON"

        labels_to_use = labels if labels else [default_label] * len(rate_structure)
        table_data = []

        for i, label in enumerate(labels_to_use):
            if i < len(rate_structure) and rate_structure[i]:
                rate_info = rate_structure[i][0]
                rate = rate_info.get("rate", 0)
                adj = rate_info.get("adj", 0)
                total_rate = rate + adj

                period_label = f"Period {i} - {default_label}" if not labels else label
                months_present = self._get_months_for_period(
                    i, weekday_schedule, weekend_schedule, rate_structure
                )

                hours = period_hours.get(i, 0)
                days = period_days.get(i, 0)
                percentage = (hours / total_hours * 100) if total_hours > 0 else 0

                table_data.append(
                    {
                        period_col: period_label,
                        f"Base Rate ({rate_unit})": f"${rate:.4f}",
                        f"Adjustment ({rate_unit})": f"${adj:.4f}",
                        f"Total Rate ({rate_unit})": f"${total_rate:.4f}",
                        "Hours/Year": hours,
                        "% of Year": f"{percentage:.1f}%",
                        "Days/Year": days,
                        "Months Present": months_present,
                    }
                )

        return pd.DataFrame(table_data)

    def create_tou_labels_table(self) -> pd.DataFrame:
        """
        Create a table showing TOU labels with their corresponding energy rates.

        Returns:
            pd.DataFrame: Table with TOU period information
        """
        return self._create_rate_labels_table(
            rate_type="energy",
            labels_key="energytoulabels",
            rates_key="energyratestructure",
            weekday_schedule_key="energyweekdayschedule",
            weekend_schedule_key="energyweekendschedule",
        )

    def create_demand_labels_table(self) -> pd.DataFrame:
        """
        Create a table showing demand charge labels with their corresponding rates.

        Returns:
            pd.DataFrame: Table with demand period information
        """
        return self._create_rate_labels_table(
            rate_type="demand",
            labels_key="demandlabels",
            rates_key="demandratestructure",
            weekday_schedule_key="demandweekdayschedule",
            weekend_schedule_key="demandweekendschedule",
        )

    def _get_months_for_demand_period(
        self, period_index: int, weekday_schedule: List, weekend_schedule: List
    ) -> str:
        """Legacy method - calls the consolidated _get_months_for_period."""
        return self._get_months_for_period(
            period_index,
            weekday_schedule,
            weekend_schedule,
            self.tariff.get("demandratestructure", []),
        )

    def _get_months_for_tou_period(
        self, period_index: int, weekday_schedule: List, weekend_schedule: List
    ) -> str:
        """Legacy method - calls the consolidated _get_months_for_period."""
        return self._get_months_for_period(
            period_index,
            weekday_schedule,
            weekend_schedule,
            self.tariff.get("energyratestructure", []),
        )

    def _format_month_range(self, months: List[str]) -> str:
        """
        Format a list of months into a compact range (e.g., 'Jan-Jun' or 'Jan, Mar, Jun').

        Args:
            months (List[str]): List of month abbreviations

        Returns:
            str: Formatted month range string
        """
        if not months:
            return ""

        if len(months) == 1:
            return months[0]

        # Check if months form a consecutive range
        month_indices = [self.months.index(m) for m in months]
        month_indices.sort()

        if month_indices == list(range(month_indices[0], month_indices[-1] + 1)):
            # Consecutive range
            if month_indices[0] == month_indices[-1]:
                return months[0]
            else:
                return f"{months[0]}-{months[-1]}"
        else:
            # Non-consecutive, list them
            return ", ".join(months)


class TempTariffViewer(TariffViewer):
    """
    Temporary TariffViewer that works with in-memory data instead of files.

    Use this class when you have modified tariff data in memory and need
    to create a viewer without saving to disk first.
    """

    def __init__(self, tariff_data: Dict[str, Any]):
        """
        Initialize TempTariffViewer with in-memory tariff data.

        Args:
            tariff_data: Tariff data dictionary (may be wrapped in 'items' or not)
        """
        # Skip file loading and work directly with data
        self.data = tariff_data

        # Handle both direct tariff data and wrapped in 'items'
        if "items" in self.data:
            self.tariff = self.data["items"][0]
        else:
            self.tariff = self.data
            self.data = {"items": [self.data]}  # Wrap for consistency

        # Extract basic information with fallbacks
        self.utility_name = self.tariff.get("utility", "Unknown Utility")
        self.rate_name = self.tariff.get("name", "Unknown Rate")
        self.sector = self.tariff.get("sector", "Unknown Sector")
        self.description = self.tariff.get("description", "No description available")

        # Setup data structures
        self.months = MONTHS
        self.hours = HOURS
        self.update_rate_dataframes()


def create_temp_viewer_with_modified_tariff(
    modified_tariff_data: Dict[str, Any],
) -> TempTariffViewer:
    """
    Create a temporary TariffViewer instance with modified tariff data.

    This is a convenience function that creates a TempTariffViewer.

    Args:
        modified_tariff_data: Modified tariff data dictionary

    Returns:
        TempTariffViewer instance
    """
    return TempTariffViewer(modified_tariff_data)
