"""
Flat demand rates tab component for URDB Tariff Viewer.

This module contains the UI components for the flat demand rates analysis tab.
"""

from typing import Any, Dict

import pandas as pd
import streamlit as st

from urdb_viewer.components.rate_editor import (
    get_current_tariff_data,
    render_flat_demand_editing_form,
)
from urdb_viewer.components.visualizations import create_flat_demand_chart
from urdb_viewer.config.constants import MONTHS_ABBREVIATED
from urdb_viewer.models.tariff import (
    TariffViewer,
    create_temp_viewer_with_modified_tariff,
)


def render_flat_demand_rates_tab(
    tariff_viewer: TariffViewer, options: Dict[str, Any]
) -> None:
    """
    Render the flat demand rates analysis tab.

    Args:
        tariff_viewer: TariffViewer instance containing the tariff data
        options: Display and analysis options from sidebar
    """
    st.markdown("### 📊 Seasonal/Monthly Flat Demand Rates")

    # Use shared helper to get current tariff data
    current_flat_demand_tariff = get_current_tariff_data(tariff_viewer)

    # Show current flat demand table first
    st.markdown("#### 📊 Current Monthly Flat Demand Rates")

    flat_demand_rates = current_flat_demand_tariff.get("flatdemandstructure", [])
    flat_demand_months = current_flat_demand_tariff.get("flatdemandmonths", [])

    # Create table data for display
    flat_demand_table_data = []

    current_flat_demand_rates = current_flat_demand_tariff.get(
        "flatdemandstructure", []
    )
    current_flat_demand_months = current_flat_demand_tariff.get("flatdemandmonths", [])

    for month_idx in range(12):
        period_idx = (
            current_flat_demand_months[month_idx]
            if month_idx < len(current_flat_demand_months)
            else 0
        )
        if (
            period_idx < len(current_flat_demand_rates)
            and current_flat_demand_rates[period_idx]
        ):
            rate = current_flat_demand_rates[period_idx][0].get("rate", 0)
            adj = current_flat_demand_rates[period_idx][0].get("adj", 0)
        else:
            rate = 0
            adj = 0

        total_rate = rate + adj

        flat_demand_table_data.append(
            {
                "Month": MONTHS_ABBREVIATED[month_idx],
                "Base Rate ($/kW)": f"${rate:.4f}",
                "Adjustment ($/kW)": f"${adj:.4f}",
                "Total Rate ($/kW)": f"${total_rate:.4f}",
            }
        )

    if flat_demand_table_data:
        display_flat_demand_df = pd.DataFrame(flat_demand_table_data)
        st.dataframe(
            display_flat_demand_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Month": st.column_config.TextColumn(
                    "Month",
                    width="small",
                ),
                "Base Rate ($/kW)": st.column_config.TextColumn(
                    "Base Rate ($/kW)",
                    width="medium",
                ),
                "Adjustment ($/kW)": st.column_config.TextColumn(
                    "Adjustment ($/kW)",
                    width="medium",
                ),
                "Total Rate ($/kW)": st.column_config.TextColumn(
                    "Total Rate ($/kW)",
                    width="medium",
                ),
            },
        )
    else:
        st.info("📝 **Note:** No flat demand rate structure found in this tariff JSON.")

    st.markdown("---")

    # Flat Demand Rates - Editable
    st.markdown("#### 🏷️ Monthly Flat Demand Rates (Editable)")

    with st.expander("🔧 Edit Flat Demand Rates", expanded=False):
        render_flat_demand_editing_form(tariff_viewer, options)

    st.markdown("---")

    # Flat Demand Rates Chart
    st.markdown("#### 📈 Monthly Flat Demand Rates Visualization")

    try:
        # Use modified tariff for chart if available
        if st.session_state.get("has_modifications") and st.session_state.get(
            "modified_tariff"
        ):
            temp_viewer = create_temp_viewer_with_modified_tariff(
                st.session_state.modified_tariff
            )
            fig = create_flat_demand_chart(
                tariff_viewer=temp_viewer, dark_mode=options.get("dark_mode", False)
            )
        else:
            fig = create_flat_demand_chart(
                tariff_viewer=tariff_viewer, dark_mode=options.get("dark_mode", False)
            )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error creating flat demand rates chart: {str(e)}")
        st.info(
            "This may indicate missing or invalid flat demand rate data in the tariff file."
        )


# Editing form is now handled by the shared rate_editor module
