"""
Basic information section for tariff builder.

Handles utility name, rate schedule name, sector, and other basic tariff metadata.
"""

from typing import Any, Dict

import streamlit as st

from ..utils import get_tariff_data, show_section_validation


def render_basic_info_section() -> None:
    """Render the basic information section of the tariff builder."""
    st.markdown("### 📋 Basic Tariff Information")
    st.markdown("Enter the essential details about this utility rate.")

    data = get_tariff_data()

    form_key = f"basic_info_form_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            utility = st.text_input(
                "Utility Company Name *",
                value=data.get("utility", ""),
                help="e.g., 'Pacific Gas & Electric Co'",
            )

            name = st.text_input(
                "Rate Schedule Name *",
                value=data.get("name", ""),
                help="e.g., 'TOU-EV-9 (below 2kV)'",
            )

            sector = st.selectbox(
                "Customer Sector *",
                options=[
                    "Commercial",
                    "Residential",
                    "Industrial",
                    "Agricultural",
                    "Lighting",
                ],
                index=[
                    "Commercial",
                    "Residential",
                    "Industrial",
                    "Agricultural",
                    "Lighting",
                ].index(data.get("sector", "Commercial")),
                help="Type of customer this rate applies to",
            )

            servicetype = st.selectbox(
                "Service Type",
                options=["Bundled", "Energy Only", "Delivery Only"],
                index=["Bundled", "Energy Only", "Delivery Only"].index(
                    data.get("servicetype", "Bundled")
                ),
                help="Type of service provided",
            )

        with col2:
            voltagecategory = st.selectbox(
                "Voltage Category",
                options=["Secondary", "Primary", "Transmission"],
                index=["Secondary", "Primary", "Transmission"].index(
                    data.get("voltagecategory", "Secondary")
                ),
                help="Voltage level of service",
            )

            phasewiring = st.selectbox(
                "Phase Wiring",
                options=["Single Phase", "Three Phase"],
                index=["Single Phase", "Three Phase"].index(
                    data.get("phasewiring", "Single Phase")
                ),
                help="Electrical phase configuration",
            )

            country = st.text_input(
                "Country",
                value=data.get("country", "USA"),
                help="Country where this tariff applies",
            )

        st.markdown("---")

        description = st.text_area(
            "Description *",
            value=data.get("description", ""),
            height=100,
            help="Detailed description of the rate, applicability, and any special conditions",
        )

        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input(
                "Tariff Source URL (optional)",
                value=data.get("source", ""),
                help="URL to the official tariff document",
            )

        with col2:
            sourceparent = st.text_input(
                "Utility Tariff Page URL (optional)",
                value=data.get("sourceparent", ""),
                help="URL to the utility's main tariff page",
            )

        submitted = st.form_submit_button(
            "✅ Apply Changes", type="primary", use_container_width=True
        )

        if submitted:
            data["utility"] = utility
            data["name"] = name
            data["sector"] = sector
            data["servicetype"] = servicetype
            data["voltagecategory"] = voltagecategory
            data["phasewiring"] = phasewiring
            data["country"] = country
            data["description"] = description
            data["source"] = source
            data["sourceparent"] = sourceparent
            st.success("✓ Basic information updated!")

    show_section_validation("basic_info", data)
