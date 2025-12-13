"""
Tariff information UI.

This module contains UI rendering functions for the "📄 Basic Info" section.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from urdb_viewer.models.tariff import TariffViewer
from urdb_viewer.utils.styling import (
    create_custom_divider_html,
    create_section_header_html,
)


def render_tariff_info_chips(tariff_viewer: TariffViewer) -> None:
    """Render compact "chips" showing utility, rate name, and sector."""
    st.markdown(
        f"""
        <div class="chips">
            <div class="chip">🏢 {tariff_viewer.utility_name}</div>
            <div class="chip">⚡ {tariff_viewer.rate_name}</div>
            <div class="chip">🏭 {tariff_viewer.sector}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tariff_information_section(tariff_viewer: TariffViewer) -> None:
    """Render the tariff information section (basic info + raw JSON)."""
    st.markdown(
        create_section_header_html("📋 Basic Tariff Information"),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Utility Company</h3>
            <p>{tariff_viewer.utility_name}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Rate Schedule</h3>
            <p>{tariff_viewer.rate_name}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Customer Sector</h3>
            <p>{tariff_viewer.sector}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown(create_section_header_html("📝 Description"), unsafe_allow_html=True)
    st.markdown(tariff_viewer.description)

    st.markdown(
        create_section_header_html("💰 Cost Information"), unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        fixed_charge = tariff_viewer.tariff.get("fixedchargefirstmeter", None)
        fixed_charge_units = tariff_viewer.tariff.get("fixedchargeunits", "$/month")
        if fixed_charge is not None:
            st.metric(
                "Fixed Monthly Charge",
                f"${fixed_charge:,.2f}",
                delta=fixed_charge_units,
            )
        else:
            st.metric("Fixed Monthly Charge", "Not specified")

    with col2:
        min_charge = tariff_viewer.tariff.get("mincharge", None)
        min_charge_units = tariff_viewer.tariff.get("minchargeunits", "$/month")
        if min_charge is not None:
            st.metric(
                "Minimum Monthly Charge", f"${min_charge:,.2f}", delta=min_charge_units
            )
        else:
            st.metric("Minimum Monthly Charge", "Not specified")

    with col3:
        start_date = tariff_viewer.tariff.get("startdate", None)
        if start_date:
            date_obj = datetime.fromtimestamp(start_date)
            formatted_date = date_obj.strftime("%B %d, %Y")
            st.metric("Effective Date", formatted_date)
        else:
            st.metric("Effective Date", "Not specified")

    st.markdown(
        create_section_header_html("⚙️ Service Requirements"), unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        service_type = tariff_viewer.tariff.get("servicetype", "Not specified")
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Service Type</h3>
            <p>{service_type}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        voltage = tariff_viewer.tariff.get("voltagecategory", "Not specified")
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Voltage Category</h3>
            <p>{voltage}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        phase = tariff_viewer.tariff.get("phasewiring", "Not specified")
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Phase Wiring</h3>
            <p>{phase}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        country = tariff_viewer.tariff.get("country", "Not specified")
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Country</h3>
            <p>{country}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    min_capacity = tariff_viewer.tariff.get("peakkwcapacitymin", None)
    max_capacity = tariff_viewer.tariff.get("peakkwcapacitymax", None)

    if min_capacity is not None or max_capacity is not None:
        col1, col2 = st.columns(2)

        with col1:
            if min_capacity is not None:
                st.metric("Minimum Peak Capacity", f"{min_capacity:,.0f} kW")
            else:
                st.metric("Minimum Peak Capacity", "Not specified")

        with col2:
            if max_capacity is not None:
                st.metric("Maximum Peak Capacity", f"{max_capacity:,.0f} kW")
            else:
                st.metric("Maximum Peak Capacity", "Not specified")

    st.markdown(
        create_section_header_html("📚 Documentation & Sources"), unsafe_allow_html=True
    )

    eiaid = tariff_viewer.tariff.get("eiaid", None)
    if eiaid:
        st.info(f"**EIA Utility ID:** {eiaid}")

    source = tariff_viewer.tariff.get("source", None)
    if source:
        st.markdown(f"**📄 Source Document:** [View Tariff PDF]({source})")

    source_parent = tariff_viewer.tariff.get("sourceparent", None)
    if source_parent:
        st.markdown(f"**🌐 Utility Tariff Page:** [View All Tariffs]({source_parent})")

    uri = tariff_viewer.tariff.get("uri", None)
    if uri:
        st.markdown(f"**🔗 OpenEI Database Entry:** [View on OpenEI]({uri})")

    supersedes = tariff_viewer.tariff.get("supersedes", None)
    if supersedes:
        st.info(f"**Supersedes:** Previous tariff version ID: `{supersedes}`")

    st.markdown(
        create_section_header_html("📌 Important Notes"), unsafe_allow_html=True
    )

    energy_comments = tariff_viewer.tariff.get("energycomments", None)
    if energy_comments:
        with st.expander("⚡ Energy Rate Comments", expanded=True):
            st.markdown(energy_comments)

    demand_comments = tariff_viewer.tariff.get("demandcomments", None)
    if demand_comments:
        with st.expander("🔌 Demand Rate Comments", expanded=True):
            st.markdown(demand_comments)

    dg_rules = tariff_viewer.tariff.get("dgrules", None)
    if dg_rules:
        st.success(f"**🔋 Distributed Generation Rules:** {dg_rules}")

    demand_units = tariff_viewer.tariff.get("demandunits", None)
    flat_demand_unit = tariff_viewer.tariff.get("flatdemandunit", None)
    demand_rate_unit = tariff_viewer.tariff.get("demandrateunit", None)
    reactive_power_charge = tariff_viewer.tariff.get("demandreactivepowercharge", None)

    if any([demand_units, flat_demand_unit, demand_rate_unit, reactive_power_charge]):
        with st.expander("⚙️ Additional Technical Details"):
            if demand_units:
                st.write(f"**Demand Units:** {demand_units}")
            if flat_demand_unit:
                st.write(f"**Flat Demand Unit:** {flat_demand_unit}")
            if demand_rate_unit:
                st.write(f"**Demand Rate Unit:** {demand_rate_unit}")
            if reactive_power_charge:
                st.write(
                    f"**Reactive Power Charge:** ${reactive_power_charge:.2f}/kVAR"
                )

    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    with st.expander("🔍 View Raw JSON Data"):
        st.json(tariff_viewer.data)
