"""
Utils package for URDB Tariff Viewer.

Contains utility functions, styling, and helper classes.

Modules:
- helpers: Generic utilities (formatting, type conversion, etc.)
- excel_utils: Excel export functions
- rate_utils: Vectorized rate lookups
- schedule_utils: TOU schedule calculations
- styling: CSS and theme management
- validators: Data validation functions
"""

from .excel_utils import export_rate_table_to_excel, generate_energy_rates_excel
from .helpers import (
    extract_tariff_data,
    format_currency,
    format_percentage,
    get_month_name,
    wrap_tariff_data,
)
from .rate_utils import generate_energy_rate_timeseries, vectorized_rate_lookup
from .schedule_utils import (
    calculate_annual_period_hour_percentages,
    calculate_period_hour_percentages,
    get_active_demand_periods_for_month,
    get_active_demand_periods_for_year,
    get_active_energy_periods_for_month,
    get_active_energy_periods_for_year,
)
from .styling import apply_custom_css, get_theme_colors
from .validators import validate_load_profile, validate_tariff_data

__all__ = [
    # Styling
    "apply_custom_css",
    "get_theme_colors",
    # Validators
    "validate_tariff_data",
    "validate_load_profile",
    # Helpers
    "format_currency",
    "format_percentage",
    "get_month_name",
    "extract_tariff_data",
    "wrap_tariff_data",
    # Excel
    "export_rate_table_to_excel",
    "generate_energy_rates_excel",
    # Rate utils
    "vectorized_rate_lookup",
    "generate_energy_rate_timeseries",
    # Schedule utils
    "get_active_energy_periods_for_month",
    "get_active_demand_periods_for_month",
    "get_active_energy_periods_for_year",
    "get_active_demand_periods_for_year",
    "calculate_period_hour_percentages",
    "calculate_annual_period_hour_percentages",
]
