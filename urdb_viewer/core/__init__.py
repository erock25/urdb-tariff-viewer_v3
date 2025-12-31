"""
Core package for URDB Tariff Viewer.

Contains pure Python business logic that is framework-agnostic.
These modules have no Streamlit dependencies and can be used independently.

Modules:
    - bill_calculator: Utility bill calculation engine
"""

from .bill_calculator import (
    calculate_monthly_bill,
    calculate_utility_costs_for_app,
    ensure_integer_columns,
    extract_adjustments,
    get_rate_for_consumption,
    get_rate_for_demand,
    load_profile_csv,
    load_urdb_json,
    validate_tariff,
    vectorized_energy_charges,
    vectorized_schedule_lookup,
)

__all__ = [
    # Main calculation functions
    "calculate_monthly_bill",
    "calculate_utility_costs_for_app",
    # Validation
    "validate_tariff",
    # Rate calculation helpers
    "get_rate_for_consumption",
    "get_rate_for_demand",
    "extract_adjustments",
    # Vectorized operations
    "vectorized_schedule_lookup",
    "vectorized_energy_charges",
    # Data loading
    "load_profile_csv",
    "load_urdb_json",
    # Utilities
    "ensure_integer_columns",
]
