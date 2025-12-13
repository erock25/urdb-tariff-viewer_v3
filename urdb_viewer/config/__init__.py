"""
Configuration package for URDB Tariff Viewer.

Contains application settings and constants.
"""

from .constants import DEFAULT_COLORS, HOURS, MONTHS
from .settings import Settings

__all__ = ["Settings", "MONTHS", "HOURS", "DEFAULT_COLORS"]
