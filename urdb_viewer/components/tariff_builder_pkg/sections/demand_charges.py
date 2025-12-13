"""
Demand charges section for tariff builder.

Handles TOU demand charge configuration and demand schedule setup.
"""

from typing import Any, Dict

import streamlit as st

from urdb_viewer.config.constants import HOURS, MONTHS

from ..utils import get_tariff_data
from .schedules import (
    _render_advanced_schedule_editor,
    _render_simple_schedule_editor,
    _show_schedule_heatmap,
)


def render_demand_charges_section() -> None:
    """Render the demand charges section of the tariff builder."""
    st.markdown("### 🔌 Demand Charge Structure (Optional)")
    st.markdown(
        """
    Define Time-of-Use demand charges if your tariff has them. Leave this section
    empty if your tariff only has flat demand charges or no demand charges.
    """
    )

    data = get_tariff_data()

    has_demand = st.checkbox(
        "This tariff has TOU demand charges",
        value=len(data.get("demandratestructure", [])) > 0,
        help="Check if this tariff has time-varying demand charges",
    )

    if not has_demand:
        data["demandratestructure"] = []
        data["demandweekdayschedule"] = []
        data["demandweekendschedule"] = []
        st.info(
            "ℹ️ No TOU demand charges configured. You can still set flat demand charges in the next tab."
        )
        return

    # Number of demand periods
    num_periods = st.number_input(
        "Number of Demand Periods",
        min_value=1,
        max_value=12,
        value=max(1, len(data.get("demandratestructure", []))),
        help="How many different demand rate periods?",
    )

    st.info(
        "💡 **Tip**: If your tariff has hours when no TOU-based demand charge applies, "
        "include a period with a $0.00 rate."
    )

    # Adjust arrays
    if len(data["demandratestructure"]) != num_periods:
        data["demandratestructure"] = [
            [{"rate": 0.0, "adj": 0.0}] for _ in range(num_periods)
        ]
        data["demandweekdayschedule"] = [[0] * 24 for _ in range(12)]
        data["demandweekendschedule"] = [[0] * 24 for _ in range(12)]
        data["demandlabels"] = [f"Period {i}" for i in range(num_periods)]

    # Ensure demandlabels exists
    if "demandlabels" not in data or len(data["demandlabels"]) != num_periods:
        data["demandlabels"] = [f"Period {i}" for i in range(num_periods)]

    st.markdown("---")

    # Render demand rate inputs
    _render_demand_rate_inputs(data, num_periods)

    # Comments
    st.markdown("---")
    data["demandcomments"] = st.text_area(
        "Demand Charge Comments (optional)",
        value=data.get("demandcomments", ""),
        help="Additional notes about demand charges",
    )

    # Demand Schedule Configuration
    st.markdown("---")
    st.markdown("### 📅 Demand Charge Schedule")
    st.markdown("Configure when each demand charge period applies throughout the year.")

    demand_schedule_mode = st.radio(
        "Schedule Configuration",
        options=["Simple (same for all months)", "Advanced (different by month)"],
        help="Simple mode applies the same daily pattern to all months",
        key="demand_schedule_mode",
    )

    if demand_schedule_mode == "Simple (same for all months)":
        _render_simple_schedule_editor(data, num_periods, "demand")
    else:
        _render_advanced_schedule_editor(data, num_periods, "demand")

    # Show schedule preview
    st.markdown("---")
    st.markdown("#### 📊 Demand Schedule Preview")

    tab1, tab2 = st.tabs(["Weekday Schedule", "Weekend Schedule"])

    with tab1:
        _show_schedule_heatmap(
            data["demandweekdayschedule"],
            "Demand Weekday",
            data.get("demandlabels", [f"Period {i}" for i in range(num_periods)]),
            rate_structure=data.get("demandratestructure"),
            rate_type="demand",
        )

    with tab2:
        _show_schedule_heatmap(
            data["demandweekendschedule"],
            "Demand Weekend",
            data.get("demandlabels", [f"Period {i}" for i in range(num_periods)]),
            rate_structure=data.get("demandratestructure"),
            rate_type="demand",
        )


def _render_demand_rate_inputs(data: Dict, num_periods: int) -> None:
    """Render the demand rate input fields for each period."""
    for i in range(num_periods):
        with st.expander(f"🔌 Demand Period {i}", expanded=(i == 0)):
            label = st.text_input(
                "Period Label",
                value=(
                    data["demandlabels"][i]
                    if i < len(data["demandlabels"])
                    else f"Period {i}"
                ),
                help="e.g., 'Peak', 'Mid-Peak', 'Off-Peak', 'No Charge'",
                key=f"demand_label_{num_periods}_{i}",
            )
            data["demandlabels"][i] = label

            col1, col2 = st.columns(2)

            with col1:
                rate = st.number_input(
                    "Base Rate ($/kW)",
                    min_value=0.0,
                    max_value=100.0,
                    value=data["demandratestructure"][i][0].get("rate", 0.0),
                    format="%.4f",
                    step=0.1,
                    help="Base demand rate in dollars per kW",
                    key=f"demand_rate_{i}",
                )
                data["demandratestructure"][i][0]["rate"] = rate

            with col2:
                adj = st.number_input(
                    "Adjustment ($/kW)",
                    min_value=-10.0,
                    max_value=10.0,
                    value=data["demandratestructure"][i][0].get("adj", 0.0),
                    format="%.4f",
                    step=0.1,
                    help="Rate adjustment (can be negative)",
                    key=f"demand_adj_{i}",
                )
                data["demandratestructure"][i][0]["adj"] = adj

            total_rate = rate + adj
            st.info(f"**Total Rate:** ${total_rate:.4f}/kW")
