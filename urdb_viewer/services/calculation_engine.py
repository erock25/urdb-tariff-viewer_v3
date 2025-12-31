"""
Backward compatibility shim for calculation_engine.

This module has been moved to `urdb_viewer.core.bill_calculator`.
All imports are re-exported here for backward compatibility.

New code should import directly from `urdb_viewer.core`:
    from urdb_viewer.core import calculate_monthly_bill, calculate_utility_costs_for_app
"""

# Re-export everything from the new location for backward compatibility
from urdb_viewer.core.bill_calculator import (
    calculate_monthly_bill,
    calculate_utility_costs_for_app,
    ensure_integer_columns,
    extract_adjustments,
    get_rate_for_consumption,
    get_rate_for_demand,
    load_profile_csv,
    load_urdb_json,
    main,
    validate_tariff,
    vectorized_energy_charges,
    vectorized_schedule_lookup,
)

__all__ = [
    "calculate_monthly_bill",
    "calculate_utility_costs_for_app",
    "ensure_integer_columns",
    "extract_adjustments",
    "get_rate_for_consumption",
    "get_rate_for_demand",
    "load_profile_csv",
    "load_urdb_json",
    "main",
    "validate_tariff",
    "vectorized_energy_charges",
    "vectorized_schedule_lookup",
]
