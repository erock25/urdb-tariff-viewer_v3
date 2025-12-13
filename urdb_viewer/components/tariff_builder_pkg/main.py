"""
Tariff Builder main entry point.

This module provides the main rendering function for the tariff builder tab,
orchestrating the various section components.
"""

import streamlit as st

from .sections import (
    render_basic_info_section,
    render_demand_charges_section,
    render_energy_rates_section,
    render_energy_schedule_section,
    render_fixed_charges_section,
    render_flat_demand_section,
    render_preview_and_save_section,
)
from .utils import create_empty_tariff_structure


def render_tariff_builder_tab() -> None:
    """
    Render the tariff builder tab for creating new tariffs from scratch.

    This is the main entry point called from the application.
    """
    st.markdown(
        """
    Create a new utility tariff from scratch. Fill in the required fields below and
    optionally configure advanced rate structures. When finished, save your tariff
    as a JSON file.
    """
    )

    # Performance tip
    st.info(
        """
    💡 **Performance Tip**: Each section uses forms to batch updates. Fill in all fields
    in a section, then click the **"✅ Apply Changes"** button to save your entries without
    constant screen refreshes.
    """
    )

    # Initialize session state for tariff builder if not exists
    if "tariff_builder_data" not in st.session_state:
        st.session_state.tariff_builder_data = create_empty_tariff_structure()

    # Create tabs for different sections
    builder_tabs = st.tabs(
        [
            "📋 Basic Info",
            "⚡ Energy Rates",
            "📅 Energy Schedule",
            "🔌 Demand Charges",
            "📊 Flat Demand",
            "💰 Fixed Charges",
            "🔍 Preview & Save",
        ]
    )

    with builder_tabs[0]:
        render_basic_info_section()

    with builder_tabs[1]:
        render_energy_rates_section()

    with builder_tabs[2]:
        render_energy_schedule_section()

    with builder_tabs[3]:
        render_demand_charges_section()

    with builder_tabs[4]:
        render_flat_demand_section()

    with builder_tabs[5]:
        render_fixed_charges_section()

    with builder_tabs[6]:
        render_preview_and_save_section()
