"""
Main entry point for URDB Tariff Viewer.

This is the new modular main application file that replaces the monolithic app.py.
Updated: 2025-11-23
"""

import streamlit as st

from urdb_viewer.components.cost_calculator import render_utility_cost_calculation_tab
from urdb_viewer.components.demand_rates import render_demand_rates_tab
from urdb_viewer.components.energy_rates import render_energy_rates_tab
from urdb_viewer.components.flat_demand_rates import render_flat_demand_rates_tab
from urdb_viewer.components.load_factor import render_load_factor_analysis_tab
from urdb_viewer.components.load_generator import render_load_generator_tab
from urdb_viewer.components.load_profile_analysis import (
    render_load_profile_analysis_tab,
)
from urdb_viewer.components.sidebar import create_sidebar
from urdb_viewer.components.tariff_builder_pkg import render_tariff_builder_tab
from urdb_viewer.components.tariff_information import render_tariff_information_section
from urdb_viewer.ui.app_bootstrap import (
    handle_tariff_switching,
    initialize_app,
    load_tariff_viewer,
)


def main() -> None:
    """Main Streamlit entrypoint (composition only)."""
    initialize_app(dark_mode=False)

    selected_tariff_file, selected_load_profile, sidebar_options = create_sidebar()

    if not selected_tariff_file:
        st.error("❌ No tariff file selected. Please select a tariff from the sidebar.")
        st.stop()

    handle_tariff_switching(selected_tariff_file)

    tariff_viewer = load_tariff_viewer(selected_tariff_file)
    if not tariff_viewer:
        st.error("❌ Failed to load tariff data.")
        st.stop()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📋 Tariff Information",
            "💰 Utility Cost Analysis",
            "🔧 Load Profile Generator",
            "📊 LP Analysis",
            "🏗️ Tariff Builder",
        ]
    )

    # Tariff Information tab with sub-tabs
    with tab1:
        subtab1, subtab2, subtab3, subtab4 = st.tabs(
            ["⚡ Energy Rates", "🔌 Demand Rates", "📊 Flat Demand", "📄 Basic Info"]
        )

        with subtab1:
            render_energy_rates_tab(tariff_viewer, sidebar_options)

        with subtab2:
            render_demand_rates_tab(tariff_viewer, sidebar_options)

        with subtab3:
            render_flat_demand_rates_tab(tariff_viewer, sidebar_options)

        with subtab4:
            render_tariff_information_section(tariff_viewer)

    # Utility Cost Analysis tab with sub-tabs
    with tab2:
        cost_subtab1, cost_subtab2 = st.tabs(
            ["Utilization Analysis", "Utility Bill Calculator"]
        )

        with cost_subtab1:
            render_load_factor_analysis_tab(tariff_viewer, sidebar_options)

        with cost_subtab2:
            render_utility_cost_calculation_tab(
                tariff_viewer, selected_load_profile, sidebar_options
            )

    # Other main tabs
    with tab3:
        render_load_generator_tab(tariff_viewer, sidebar_options)

    with tab4:
        render_load_profile_analysis_tab(selected_load_profile, sidebar_options)

    with tab5:
        render_tariff_builder_tab()


if __name__ == "__main__":
    main()
