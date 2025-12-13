"""
Load profile generation model for URDB Tariff Viewer.

This module contains the LoadProfileGenerator class for creating synthetic load profiles
based on tariff structures and customer parameters.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import numpy as np
import pandas as pd

from urdb_viewer.config.constants import (
    DEFAULT_DAILY_VARIATION,
    DEFAULT_LOAD_FACTOR,
    DEFAULT_NOISE_LEVEL,
    DEFAULT_SEASONAL_VARIATION,
    DEFAULT_TOU_PERCENTAGES,
    DEFAULT_WEEKEND_FACTOR,
)


class LoadProfileGenerator:
    """
    A class for generating synthetic load profiles based on tariff structures.

    This class creates realistic load profiles that align with Time-of-Use (TOU)
    periods defined in utility rate structures.

    Attributes:
        tariff (Dict): Tariff data containing TOU schedules
        avg_load (float): Average load in kW
        load_factor (float): Load factor (average/peak ratio)
        year (int): Year for timestamps
    """

    def __init__(
        self,
        tariff: Dict,
        avg_load: float,
        load_factor: float = DEFAULT_LOAD_FACTOR,
        year: int = 2025,
    ):
        """
        Initialize LoadProfileGenerator.

        Args:
            tariff (Dict): Tariff data containing TOU schedules
            avg_load (float): Average load in kW across the year
            load_factor (float): Load factor (average/peak ratio)
            year (int): Year for the timestamps
        """
        self.tariff = tariff
        self.avg_load = avg_load
        self.load_factor = load_factor
        self.year = year

    def generate_profile(
        self,
        tou_percentages: Dict[str, float],
        seasonal_variation: float = DEFAULT_SEASONAL_VARIATION,
        weekend_factor: float = DEFAULT_WEEKEND_FACTOR,
        daily_variation: float = DEFAULT_DAILY_VARIATION,
        noise_level: float = DEFAULT_NOISE_LEVEL,
    ) -> pd.DataFrame:
        """
        Generate a synthetic load profile with specified characteristics.

        Args:
            tou_percentages (Dict[str, float]): Percentage of energy in each TOU period
            seasonal_variation (float): Seasonal variation factor (0-0.5)
            weekend_factor (float): Weekend load as fraction of weekday (0.1-1.5)
            daily_variation (float): Daily variation factor (0-0.3)
            noise_level (float): Random noise level (0-0.2)

        Returns:
            pd.DataFrame: Load profile with timestamp, load_kW, kWh, month, energy_period columns
        """

        # Create 15-minute intervals for the entire year
        start_date = datetime(self.year, 1, 1)
        end_date = datetime(self.year + 1, 1, 1)
        timestamps = []
        current = start_date
        while current < end_date:
            timestamps.append(current)
            current += timedelta(minutes=15)

        df = pd.DataFrame({"timestamp": timestamps})
        df["month"] = df["timestamp"].dt.month
        df["hour"] = df["timestamp"].dt.hour
        df["weekday"] = df["timestamp"].dt.weekday
        df["is_weekend"] = df["weekday"] >= 5

        # Calculate peak load from average and load factor
        peak_load = self.avg_load / self.load_factor

        # Get TOU schedules from tariff
        weekday_schedule = self.tariff.get("energyweekdayschedule", [])
        weekend_schedule = self.tariff.get("energyweekendschedule", [])

        # Assign TOU periods
        energy_periods = []
        for _, row in df.iterrows():
            month_idx = row["month"] - 1
            hour = row["hour"]

            if (
                row["is_weekend"]
                and weekend_schedule
                and month_idx < len(weekend_schedule)
            ):
                if hour < len(weekend_schedule[month_idx]):
                    period = weekend_schedule[month_idx][hour]
                else:
                    period = 0
            elif weekday_schedule and month_idx < len(weekday_schedule):
                if hour < len(weekday_schedule[month_idx]):
                    period = weekday_schedule[month_idx][hour]
                else:
                    period = 0
            else:
                period = 0

            energy_periods.append(int(period))

        df["energy_period"] = energy_periods

        # Create base load profile with seasonal variation
        seasonal_multiplier = 1 + seasonal_variation * np.sin(
            2 * np.pi * (df["month"] - 1) / 12
        )

        # Weekend factor
        weekend_multiplier = np.where(df["is_weekend"], weekend_factor, 1.0)

        # Daily variation (higher during certain hours)
        daily_multiplier = 1 + daily_variation * np.sin(2 * np.pi * df["hour"] / 24)

        # Random noise
        np.random.seed(42)  # For reproducibility
        noise = 1 + noise_level * np.random.normal(0, 1, len(df))

        # Calculate target energy for each TOU period
        total_annual_kwh = self.avg_load * 8760  # kW * hours in year
        target_energy_by_period = {}

        for period, percentage in tou_percentages.items():
            target_energy_by_period[period] = total_annual_kwh * (percentage / 100.0)

        # Initialize load array
        load_kw = np.full(len(df), self.avg_load)

        # Apply multipliers
        load_kw *= seasonal_multiplier * weekend_multiplier * daily_multiplier * noise

        # Adjust to meet TOU energy targets
        for period in tou_percentages.keys():
            period_mask = df["energy_period"] == period
            if period_mask.sum() > 0:
                current_energy = (
                    load_kw[period_mask] * 0.25
                ).sum()  # 15-min intervals = 0.25 hours
                target_energy = target_energy_by_period[period]

                if current_energy > 0:
                    adjustment_factor = target_energy / current_energy
                    load_kw[period_mask] *= adjustment_factor

        # Scale to meet overall average load target
        actual_avg = load_kw.mean()
        if actual_avg > 0:
            load_kw *= self.avg_load / actual_avg

        # Apply load factor constraint by scaling peaks
        actual_peak = load_kw.max()
        target_peak = self.avg_load / self.load_factor

        if actual_peak > target_peak:
            # Compress peaks to meet load factor
            excess_mask = load_kw > target_peak
            load_kw[excess_mask] = (
                target_peak + (load_kw[excess_mask] - target_peak) * 0.1
            )

        # Ensure non-negative loads
        load_kw = np.maximum(load_kw, 0)

        # Calculate kWh for 15-minute intervals
        df["load_kW"] = load_kw
        df["kWh"] = df["load_kW"] * 0.25  # 15 minutes = 0.25 hours

        return df[["timestamp", "load_kW", "kWh", "month", "energy_period"]]

    def get_load_statistics(self, profile_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate statistics for a load profile.

        Args:
            profile_df (pd.DataFrame): Load profile DataFrame

        Returns:
            Dict[str, float]: Dictionary of load statistics
        """
        return {
            "peak_kw": profile_df["load_kW"].max(),
            "avg_kw": profile_df["load_kW"].mean(),
            "min_kw": profile_df["load_kW"].min(),
            "total_kwh": profile_df["kWh"].sum(),
            "load_factor": profile_df["load_kW"].mean() / profile_df["load_kW"].max(),
            "std_dev": profile_df["load_kW"].std(),
        }

    def validate_profile(
        self, profile_df: pd.DataFrame, tolerance: float = 0.05
    ) -> Dict[str, bool]:
        """
        Validate that the generated profile meets the target parameters.

        Args:
            profile_df (pd.DataFrame): Generated load profile
            tolerance (float): Acceptable tolerance for validation

        Returns:
            Dict[str, bool]: Validation results
        """
        stats = self.get_load_statistics(profile_df)

        avg_error = abs(stats["avg_kw"] - self.avg_load) / self.avg_load
        load_factor_error = (
            abs(stats["load_factor"] - self.load_factor) / self.load_factor
        )

        return {
            "avg_load_valid": avg_error <= tolerance,
            "load_factor_valid": load_factor_error <= tolerance,
            "no_negative_values": stats["min_kw"] >= 0,
            "reasonable_peak": stats["peak_kw"]
            <= self.avg_load * 5,  # Peak shouldn't be more than 5x average
        }


def generate_load_profile(
    tariff: Dict,
    avg_load: float,
    load_factor: float,
    tou_percentages: Dict[str, float],
    year: int,
    seasonal_variation: float = DEFAULT_SEASONAL_VARIATION,
    weekend_factor: float = DEFAULT_WEEKEND_FACTOR,
    daily_variation: float = DEFAULT_DAILY_VARIATION,
    noise_level: float = DEFAULT_NOISE_LEVEL,
) -> pd.DataFrame:
    """
    Generate a synthetic load profile with specified characteristics.

    This is a convenience function that creates a LoadProfileGenerator and generates a profile.

    Args:
        tariff (Dict): The tariff data containing TOU schedules
        avg_load (float): Average load in kW across the year
        load_factor (float): Load factor (average/peak ratio)
        tou_percentages (Dict[str, float]): Percentage of energy in each TOU period
        year (int): Year for the timestamps
        seasonal_variation (float): Seasonal variation factor (0-0.5)
        weekend_factor (float): Weekend load as fraction of weekday (0.1-1.5)
        daily_variation (float): Daily variation factor (0-0.3)
        noise_level (float): Random noise level (0-0.2)

    Returns:
        pd.DataFrame: Load profile with timestamp, load_kW, kWh, month, energy_period columns
    """
    generator = LoadProfileGenerator(tariff, avg_load, load_factor, year)
    return generator.generate_profile(
        tou_percentages=tou_percentages,
        seasonal_variation=seasonal_variation,
        weekend_factor=weekend_factor,
        daily_variation=daily_variation,
        noise_level=noise_level,
    )
