"""
Custom exceptions for URDB Tariff Viewer.

This module contains custom exception classes used throughout the application.
"""


class InvalidTariffError(Exception):
    """Raised when tariff data is invalid or missing required fields"""

    pass


class InvalidLoadProfileError(Exception):
    """Raised when load profile data is invalid or missing required fields"""

    pass
