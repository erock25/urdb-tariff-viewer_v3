"""
Rate lookup utilities for URDB Tariff Viewer.

This module contains vectorized rate lookup functions for high-performance
calculations on load profiles.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any


def vectorized_rate_lookup(
    df: pd.DataFrame,
    weekday_rates: pd.DataFrame,
    weekend_rates: pd.DataFrame,
    month_col: str = 'month',
    hour_col: str = 'hour',
    is_weekend_col: str = 'is_weekend'
) -> np.ndarray:
    """
    Perform vectorized rate lookup for a full year of timestamps.
    
    This is ~50-100x faster than using iterrows().
    
    Args:
        df: DataFrame with month, hour, and is_weekend columns
        weekday_rates: 12x24 DataFrame of weekday rates
        weekend_rates: 12x24 DataFrame of weekend rates
        month_col: Name of month column (0-indexed)
        hour_col: Name of hour column
        is_weekend_col: Name of is_weekend boolean column
        
    Returns:
        Array of rate values for each row
    """
    # Convert DataFrames to numpy arrays for faster indexing
    weekday_lookup = weekday_rates.values
    weekend_lookup = weekend_rates.values
    
    # Get indices as numpy arrays
    months = df[month_col].values.astype(int)
    hours = df[hour_col].values.astype(int)
    is_weekend = df[is_weekend_col].values
    
    # Vectorized conditional lookup
    rates = np.where(
        is_weekend,
        weekend_lookup[months, hours],
        weekday_lookup[months, hours]
    )
    
    return rates


def generate_energy_rate_timeseries(tariff_viewer, year: int = 2025) -> pd.DataFrame:
    """
    Generate a full year of timeseries data with timestamps and corresponding energy rates.
    
    Uses vectorized operations for ~50-100x faster performance compared to iterrows().
    
    Args:
        tariff_viewer: TariffViewer instance with energy rate data
        year: Year for timeseries generation
        
    Returns:
        DataFrame with 'timestamp' and 'energy_rate_$/kWh' columns
    """
    # Generate timestamps for full year at 15-minute intervals
    start_date = datetime(year, 1, 1, 0, 0, 0)
    end_date = datetime(year, 12, 31, 23, 45, 0)
    
    timestamps = pd.date_range(start=start_date, end=end_date, freq='15min')
    
    # Create DataFrame with derived columns
    df = pd.DataFrame({'timestamp': timestamps})
    df['month'] = df['timestamp'].dt.month - 1  # 0-indexed for array lookup
    df['hour'] = df['timestamp'].dt.hour
    df['is_weekend'] = df['timestamp'].dt.weekday >= 5  # Saturday=5, Sunday=6
    
    # Use vectorized rate lookup
    energy_rates = vectorized_rate_lookup(
        df=df,
        weekday_rates=tariff_viewer.weekday_df,
        weekend_rates=tariff_viewer.weekend_df,
        month_col='month',
        hour_col='hour',
        is_weekend_col='is_weekend'
    )
    
    # Create final DataFrame
    result_df = pd.DataFrame({
        'timestamp': df['timestamp'],
        'energy_rate_$/kWh': energy_rates
    })
    
    return result_df

