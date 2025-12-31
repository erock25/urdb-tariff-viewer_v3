"""
Main entry point for URDB Tariff Viewer.

This module contains the main Streamlit application entry point that composes
all UI components into a cohesive interface. It handles tab layout and routing
to appropriate component renderers.
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
from urdb_viewer.components.tariff_database_search import (
    render_tariff_database_search_tab,
)
from urdb_viewer.components.tariff_information import render_tariff_information_section
from urdb_viewer.ui.app_bootstrap import (
    handle_tariff_switching,
    initialize_app,
    load_tariff_viewer,
)


def main() -> None:
    """Main Streamlit entrypoint (composition only)."""
    initialize_app()

    selected_tariff_file, selected_load_profile, sidebar_options = create_sidebar()

    # Create tabs first - Database Search should always be accessible
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📋 Tariff Information",
            "💰 Utility Cost Analysis",
            "🔧 Load Profile Generator",
            "📊 LP Analysis",
            "🏗️ Tariff Builder",
            "🔍 Database Search",
        ]
    )

    # Check if tariff is selected and load it
    tariff_available = False
    tariff_viewer = None

    if selected_tariff_file:
        handle_tariff_switching(selected_tariff_file)
        tariff_viewer = load_tariff_viewer(selected_tariff_file)
        tariff_available = tariff_viewer is not None

    # Tariff Information tab with sub-tabs
    with tab1:
        if not tariff_available:
            st.warning(
                "⚠️ No tariff selected. Please select a tariff from the sidebar "
                "or use the **🔍 Database Search** tab to import tariffs."
            )
        else:
            subtab1, subtab2, subtab3, subtab4 = st.tabs(
                [
                    "⚡ Energy Rates",
                    "🔌 Demand Rates",
                    "📊 Flat Demand",
                    "📄 Basic Info",
                ]
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
        if not tariff_available:
            st.warning(
                "⚠️ No tariff selected. Please select a tariff from the sidebar "
                "or use the **🔍 Database Search** tab to import tariffs."
            )
        else:
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
        if not tariff_available:
            st.warning(
                "⚠️ No tariff selected. Please select a tariff from the sidebar "
                "or use the **🔍 Database Search** tab to import tariffs."
            )
        else:
            render_load_generator_tab(tariff_viewer, sidebar_options)

    with tab4:
        render_load_profile_analysis_tab(selected_load_profile, sidebar_options)

    with tab5:
        render_tariff_builder_tab()

    # Database Search tab - always accessible
    with tab6:
        render_tariff_database_search_tab()


if __name__ == "__main__":
    main()
