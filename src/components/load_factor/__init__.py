"""
Load factor analysis package.

This package provides tools for calculating effective utility rates ($/kWh) 
at different load factors based on tariff structures and user-defined 
demand and energy distribution assumptions.

Modules:
    - analysis: Main entry point and orchestration
    - calculations: Pure calculation logic
    - ui: Streamlit UI components
"""

from .analysis import (
    render_load_factor_analysis_tab,
    render_load_factor_analysis_tool,
)

from .calculations import (
    calculate_load_factor_rates,
    calculate_annual_load_factor_rates,
    calculate_comprehensive_breakdown,
    calculate_max_valid_load_factor,
    generate_load_factors,
)

__all__ = [
    # Main entry points
    'render_load_factor_analysis_tab',
    'render_load_factor_analysis_tool',
    # Calculation functions
    'calculate_load_factor_rates',
    'calculate_annual_load_factor_rates',
    'calculate_comprehensive_breakdown',
    'calculate_max_valid_load_factor',
    'generate_load_factors',
]

