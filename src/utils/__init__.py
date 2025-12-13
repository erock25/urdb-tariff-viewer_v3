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

from .styling import apply_custom_css, get_theme_colors
from .validators import validate_tariff_data, validate_load_profile
from .helpers import (
    format_currency, 
    format_percentage, 
    get_month_name,
    extract_tariff_data,
    wrap_tariff_data,
)
from .excel_utils import (
    export_rate_table_to_excel,
    generate_energy_rates_excel,
)
from .rate_utils import (
    vectorized_rate_lookup,
    generate_energy_rate_timeseries,
)
from .schedule_utils import (
    get_active_energy_periods_for_month,
    get_active_demand_periods_for_month,
    get_active_energy_periods_for_year,
    get_active_demand_periods_for_year,
    calculate_period_hour_percentages,
    calculate_annual_period_hour_percentages,
)

__all__ = [
    # Styling
    'apply_custom_css',
    'get_theme_colors',
    # Validators
    'validate_tariff_data',
    'validate_load_profile',
    # Helpers
    'format_currency',
    'format_percentage',
    'get_month_name',
    'extract_tariff_data',
    'wrap_tariff_data',
    # Excel
    'export_rate_table_to_excel',
    'generate_energy_rates_excel',
    # Rate utils
    'vectorized_rate_lookup',
    'generate_energy_rate_timeseries',
    # Schedule utils
    'get_active_energy_periods_for_month',
    'get_active_demand_periods_for_month',
    'get_active_energy_periods_for_year',
    'get_active_demand_periods_for_year',
    'calculate_period_hour_percentages',
    'calculate_annual_period_hour_percentages',
]
