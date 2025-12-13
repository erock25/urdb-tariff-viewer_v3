"""
Load factor analysis main entry point.

This module provides the main rendering functions for the load factor analysis tool,
orchestrating the UI components and calculation logic.
"""

from typing import Any, Dict

import streamlit as st

from urdb_viewer.models.tariff import TariffViewer
from urdb_viewer.utils.helpers import (
    calculate_annual_period_hour_percentages,
    calculate_period_hour_percentages,
    get_active_demand_periods_for_year,
    get_active_energy_periods_for_year,
)

from .calculations import (
    calculate_annual_load_factor_rates,
    calculate_load_factor_rates,
    calculate_max_valid_load_factor,
)
from .ui import (
    display_load_factor_results,
    render_analysis_period_selector,
    render_energy_distribution_inputs,
    render_flat_demand_inputs,
    render_rate_structure_info,
    render_tou_demand_inputs,
)


def render_load_factor_analysis_tab(
    tariff_viewer: TariffViewer, options: Dict[str, Any]
) -> None:
    """
    Render the load factor analysis tool tab.

    This is the main entry point called from the main application.

    Args:
        tariff_viewer: TariffViewer instance
        options: Display and analysis options
    """
    render_load_factor_analysis_tool(tariff_viewer, options)


def render_load_factor_analysis_tool(
    tariff_viewer: TariffViewer, options: Dict[str, Any]
) -> None:
    """
    Render the load factor analysis tool.

    This tool allows users to calculate effective utility rates ($/kWh) at different load factors
    by specifying demand assumptions and energy distribution percentages.

    Args:
        tariff_viewer: TariffViewer instance
        options: Display options
    """
    _render_tool_description()

    tariff_data = tariff_viewer.tariff

    # Show rate structure info
    render_rate_structure_info(tariff_data)

    # Analysis period selection
    analysis_period, selected_month = render_analysis_period_selector()

    st.markdown("---")

    # Check for rate structures
    has_tou_demand = bool(tariff_data.get("demandratestructure"))
    has_flat_demand = bool(tariff_data.get("flatdemandstructure"))

    demand_inputs = {}
    demand_period_month_counts = {}
    energy_period_month_counts = {}

    # TOU Demand inputs
    if has_tou_demand:
        demand_inputs, demand_period_month_counts = render_tou_demand_inputs(
            tariff_data, analysis_period, selected_month, demand_period_month_counts
        )

    # Flat demand inputs
    if has_flat_demand:
        demand_inputs = render_flat_demand_inputs(
            tariff_data, analysis_period, selected_month, demand_inputs, has_tou_demand
        )
        st.markdown("---")

    # Energy distribution inputs
    (
        energy_percentages,
        total_percentage,
        active_periods_list,
        period_hour_percentages,
        energy_period_month_counts,
    ) = render_energy_distribution_inputs(tariff_data, analysis_period, selected_month)

    st.markdown("---")

    # Calculate and display results
    if active_periods_list and (has_tou_demand or has_flat_demand):
        _render_calculate_button(
            tariff_data=tariff_data,
            demand_inputs=demand_inputs,
            energy_percentages=energy_percentages,
            total_percentage=total_percentage,
            selected_month=selected_month,
            has_tou_demand=has_tou_demand,
            has_flat_demand=has_flat_demand,
            analysis_period=analysis_period,
            demand_period_month_counts=demand_period_month_counts,
            energy_period_month_counts=energy_period_month_counts,
            period_hour_percentages=period_hour_percentages,
            options=options,
        )
    else:
        st.info(
            "ℹ️ This tariff does not have the required rate structure data for utilization analysis. "
            "Please select a different tariff or check the tariff configuration."
        )


def _render_tool_description() -> None:
    """Render the tool description markdown."""
    st.markdown(
        """
    This tool calculates the **effective utility rate in $/kWh** for different load factors.

    **How it works:**
    - Select single month or full year analysis
    - Specify the maximum demand for each applicable demand period
    - Specify the energy distribution across all energy rate periods
    - View effective rates from 1% up to the maximum physically possible load factor (in 1% increments), plus 100%

    **Note:** The maximum physically possible load factor is determined by your energy distribution.
    For each period: LF ≤ (hour %) / (energy %). The tool uses the most restrictive constraint.
    Example: if a period is 20% of hours but you allocate 40% of energy there, max LF = 50%.
    """
    )


def _render_calculate_button(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    total_percentage: float,
    selected_month: int,
    has_tou_demand: bool,
    has_flat_demand: bool,
    analysis_period: str,
    demand_period_month_counts: Dict[int, int],
    energy_period_month_counts: Dict[int, int],
    period_hour_percentages: Dict[int, float],
    options: Dict[str, Any],
) -> None:
    """Render the calculate button and handle calculation."""
    if st.button(
        "🧮 Calculate Effective Rates", type="primary", key="calc_load_factor"
    ):
        # Validation
        if abs(total_percentage - 100.0) >= 0.01:
            st.error("❌ Energy percentages must sum to 100% before calculating")
            return

        # Calculate max valid LF for info message
        max_valid_lf = calculate_max_valid_load_factor(
            energy_percentages, period_hour_percentages
        )
        _display_load_factor_info(max_valid_lf, analysis_period)

        # Run calculations
        if analysis_period == "Single Month":
            results = calculate_load_factor_rates(
                tariff_data=tariff_data,
                demand_inputs=demand_inputs,
                energy_percentages=energy_percentages,
                selected_month=selected_month,
                has_tou_demand=has_tou_demand,
                has_flat_demand=has_flat_demand,
            )
        else:
            results = calculate_annual_load_factor_rates(
                tariff_data=tariff_data,
                demand_inputs=demand_inputs,
                energy_percentages=energy_percentages,
                has_tou_demand=has_tou_demand,
                has_flat_demand=has_flat_demand,
                demand_period_month_counts=demand_period_month_counts,
                energy_period_month_counts=energy_period_month_counts,
            )

        # Display results
        display_load_factor_results(
            results=results,
            options=options,
            tariff_data=tariff_data,
            demand_inputs=demand_inputs,
            energy_percentages=energy_percentages,
            selected_month=(
                selected_month if analysis_period == "Single Month" else None
            ),
            has_tou_demand=has_tou_demand,
            has_flat_demand=has_flat_demand,
            analysis_period=analysis_period,
            demand_period_month_counts=demand_period_month_counts,
            energy_period_month_counts=energy_period_month_counts,
        )


def _display_load_factor_info(max_valid_lf: float, analysis_period: str) -> None:
    """Display information about the load factor calculation range."""
    num_points = int(max_valid_lf * 100)

    if max_valid_lf < 1.0:
        st.info(
            f"ℹ️ Maximum physically possible load factor: **{max_valid_lf*100:.1f}%** "
            f"(based on your energy distribution). "
            f"Calculations from 1% to {max_valid_lf*100:.1f}% LF use your specified energy distribution "
            f"({num_points} data points). "
            f"Additionally, 100% LF is calculated using hour percentages (constant 24/7 operation at full power)."
        )
    else:
        st.info(
            f"ℹ️ Your energy distribution allows calculations up to 100% load factor ({num_points} data points). "
            f"At 100% LF, energy distribution matches hour percentages (constant 24/7 operation)."
        )
