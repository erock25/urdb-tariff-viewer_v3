"""
Constants for URDB Tariff Viewer.

This module contains all application constants and default values.
"""

from typing import Dict, List

# Time constants
MONTHS: List[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# Alias for clarity
MONTHS_ABBREVIATED: List[str] = MONTHS

MONTHS_FULL: List[str] = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

HOURS: List[int] = list(range(24))

# Default color schemes
DEFAULT_COLORS: Dict[str, List[str]] = {
    "heatmap_light": [
        "rgba(34, 197, 94, 0.95)",  # Bright green (lowest rates)
        "rgba(74, 222, 128, 0.95)",  # Light green (low rates)
        "rgba(251, 191, 36, 0.95)",  # Yellow/amber (medium rates)
        "rgba(249, 115, 22, 0.95)",  # Orange (high rates)
        "rgba(239, 68, 68, 0.95)",  # Bright red (highest rates)
    ],
    "heatmap_dark": [
        "rgba(34, 197, 94, 0.9)",  # Bright green (lowest rates)
        "rgba(74, 222, 128, 0.9)",  # Light green (low rates)
        "rgba(251, 191, 36, 0.9)",  # Yellow/amber (medium rates)
        "rgba(249, 115, 22, 0.9)",  # Orange (high rates)
        "rgba(239, 68, 68, 0.9)",  # Bright red (highest rates)
    ],
}

# Chart configuration defaults
DEFAULT_CHART_HEIGHT: int = 700
DEFAULT_TEXT_SIZE: int = 12
DEFAULT_FLAT_DEMAND_HEIGHT: int = 450

# File configuration
MAX_FILE_SIZE_MB: int = 50
SUPPORTED_FILE_TYPES: List[str] = [".json", ".csv"]

# Load profile defaults
DEFAULT_LOAD_FACTOR: float = 0.7
DEFAULT_SEASONAL_VARIATION: float = 0.1
DEFAULT_WEEKEND_FACTOR: float = 0.8
DEFAULT_DAILY_VARIATION: float = 0.15
DEFAULT_NOISE_LEVEL: float = 0.05

# TOU percentage defaults
DEFAULT_TOU_PERCENTAGES: Dict[str, float] = {
    "peak": 0.3,
    "mid_peak": 0.4,
    "off_peak": 0.3,
}
