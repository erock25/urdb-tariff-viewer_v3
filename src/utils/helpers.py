"""
Generic helper utilities for URDB Tariff Viewer.

This module contains common utility functions used throughout the application.
For specialized utilities, see:
- excel_utils.py: Excel export functions
- rate_utils.py: Vectorized rate lookups
- schedule_utils.py: TOU schedule calculations
"""

import re
from datetime import datetime
from typing import Any, Optional, Union, Dict

from src.config.constants import MONTHS_ABBREVIATED, MONTHS_FULL


# =============================================================================
# Tariff Data Extraction
# =============================================================================

def extract_tariff_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract tariff dict from URDB data structure.
    
    Handles both direct tariff data and data wrapped in 'items' array.
    
    Args:
        data: Raw tariff data (may be wrapped in 'items')
        
    Returns:
        The actual tariff dictionary
    """
    if 'items' in data and isinstance(data['items'], list) and data['items']:
        return data['items'][0]
    return data


def wrap_tariff_data(tariff: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap tariff data in 'items' array for consistency with URDB format.
    
    Args:
        tariff: Raw tariff data
        
    Returns:
        Tariff wrapped in 'items' array
    """
    if 'items' not in tariff:
        return {'items': [tariff]}
    return tariff


# =============================================================================
# Formatting Utilities
# =============================================================================

def format_currency(amount: Union[int, float], precision: int = 2) -> str:
    """
    Format a number as currency.
    
    Args:
        amount: Amount to format
        precision: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if amount is None:
        return "$0.00"
    return f"${amount:,.{precision}f}"


def format_percentage(value: Union[int, float], precision: int = 1) -> str:
    """
    Format a decimal as a percentage.
    
    Args:
        value: Decimal value (0.5 = 50%)
        precision: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "0.0%"
    return f"{value * 100:.{precision}f}%"


def get_month_name(month_index: int, abbreviated: bool = True) -> str:
    """
    Get month name from index.
    
    Args:
        month_index: Month index (0-11 or 1-12)
        abbreviated: Whether to return abbreviated name
        
    Returns:
        Month name
    """
    if month_index > 12:
        month_index = month_index % 12
    elif month_index > 11:
        month_index -= 1
    
    month_index = max(0, min(11, month_index))
    
    if abbreviated:
        return MONTHS_ABBREVIATED[month_index]
    else:
        return MONTHS_FULL[month_index]


# =============================================================================
# String and File Utilities
# =============================================================================

def clean_filename(filename: str) -> str:
    """
    Clean a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = cleaned.strip('_.')
    
    if not cleaned:
        cleaned = "untitled"
    
    return cleaned


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


# =============================================================================
# Type Conversion Utilities
# =============================================================================

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Converted value or default
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Converted value or default
    """
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# =============================================================================
# Date/Time Utilities
# =============================================================================

def get_current_timestamp() -> str:
    """
    Get current timestamp as string.
    
    Returns:
        Current timestamp in YYYY-MM-DD HH:MM:SS format
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse a timestamp string into datetime object.
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return None


# =============================================================================
# Math Utilities
# =============================================================================

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change (as decimal, e.g., 0.1 = 10% increase)
    """
    if old_value == 0:
        return 1.0 if new_value > 0 else 0.0
    return (new_value - old_value) / old_value


def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


# =============================================================================
# Re-exports for backwards compatibility
# =============================================================================

# These imports allow existing code to continue using:
# from src.utils.helpers import generate_energy_rates_excel, etc.

from src.utils.excel_utils import (
    export_rate_table_to_excel,
    apply_excel_rate_formatting,
    generate_energy_rates_excel,
)

from src.utils.rate_utils import (
    vectorized_rate_lookup,
    generate_energy_rate_timeseries,
)

from src.utils.schedule_utils import (
    get_active_energy_periods_for_month,
    get_active_demand_periods_for_month,
    get_active_demand_periods_for_year,
    get_active_energy_periods_for_year,
    calculate_annual_period_hour_percentages,
    calculate_period_hour_percentages,
)
