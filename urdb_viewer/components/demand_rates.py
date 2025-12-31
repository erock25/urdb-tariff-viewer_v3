"""
Demand rates tab component for URDB Tariff Viewer.

This module contains the UI components for the demand rates analysis tab.
"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict

import pandas as pd
import streamlit as st

from urdb_viewer.components.rate_editor import (
    DEMAND_RATE_CONFIG,
    get_current_tariff_data,
    render_rate_editing_form,
)
from urdb_viewer.components.visualizations import create_heatmap
from urdb_viewer.models.tariff import (
    TariffViewer,
    create_temp_viewer_with_modified_tariff,
)
from urdb_viewer.utils.helpers import clean_filename, export_rate_table_to_excel
from urdb_viewer.utils.styling import create_custom_divider_html


def render_demand_rates_tab(
    tariff_viewer: TariffViewer, options: Dict[str, Any]
) -> None:
    """
    Render the demand rates analysis tab.

    Args:
        tariff_viewer: TariffViewer instance containing the tariff data
        options: Display and analysis options from sidebar
    """
    # Use shared helper to get current tariff data
    current_demand_tariff = get_current_tariff_data(tariff_viewer)

    # Show current demand rate table first
    st.markdown("#### Time of Use Demand Rates Table")

    try:
        demand_table = tariff_viewer.create_demand_labels_table()

        if not demand_table.empty:
            st.dataframe(
                demand_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "Demand Period": st.column_config.TextColumn(
                        "Demand Period",
                        width="medium",
                    ),
                    "Base Rate ($/kW)": st.column_config.TextColumn(
                        "Base Rate ($/kW)",
                        width="small",
                    ),
                    "Adjustment ($/kW)": st.column_config.TextColumn(
                        "Adjustment ($/kW)",
                        width="small",
                    ),
                    "Total Rate ($/kW)": st.column_config.TextColumn(
                        "Total Rate ($/kW)",
                        width="small",
                    ),
                    "Hours/Year": st.column_config.NumberColumn(
                        "Hours/Year", width="small", format="%d"
                    ),
                    "% of Year": st.column_config.TextColumn(
                        "% of Year",
                        width="small",
                    ),
                    "Days/Year": st.column_config.NumberColumn(
                        "Days/Year", width="small", format="%d"
                    ),
                    "Months Present": st.column_config.TextColumn(
                        "Months Present",
                        width="large",
                    ),
                },
            )

            # Download button for the demand rate table
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                # Use shared Excel export helper
                rate_columns = [
                    "Base Rate ($/kW)",
                    "Adjustment ($/kW)",
                    "Total Rate ($/kW)",
                ]
                excel_data = export_rate_table_to_excel(
                    df=demand_table,
                    sheet_name="Demand Rate Table",
                    rate_columns=rate_columns,
                    percentage_columns=["% of Year"],
                    rate_precision=2,  # Demand rates typically use 2 decimal places
                )

                # Create filename
                utility_clean = clean_filename(tariff_viewer.utility_name)
                rate_clean = clean_filename(tariff_viewer.rate_name)
                timestamp = datetime.now().strftime("%Y%m%d")
                filename = (
                    f"Demand_Rate_Table_{utility_clean}_{rate_clean}_{timestamp}.xlsx"
                )

                st.download_button(
                    label="📥 Download Table",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download the current demand rate table as an Excel file",
                )
        else:
            st.info("📝 **Note:** No demand rate structure found in this tariff JSON.")

    except Exception as e:
        st.error(f"❌ Error creating demand rate table: {str(e)}")

    st.markdown("---")

    # Demand Labels Table - Editable (above heatmaps for better UX)
    st.markdown("#### 🏷️ Demand Period Labels & Rates (Editable)")

    with st.expander("🔧 Edit Demand Rates", expanded=False):
        render_rate_editing_form(tariff_viewer, DEMAND_RATE_CONFIG, options)

    st.markdown("---")

    # Weekday Demand Rates - Full Width
    st.markdown("#### 📈 Weekday Demand Rates")

    # Create heatmap using the visualization function
    try:
        if st.session_state.get("has_modifications") and st.session_state.get(
            "modified_tariff"
        ):
            # Use modified tariff data for visualization
            temp_viewer = create_temp_viewer_with_modified_tariff(
                st.session_state.modified_tariff
            )
            fig = create_heatmap(
                tariff_viewer=temp_viewer,
                is_weekday=True,
                dark_mode=options.get("dark_mode", False),
                rate_type="demand",
                chart_height=options.get("chart_height", 700),
                text_size=options.get("text_size", 12),
            )
        else:
            fig = create_heatmap(
                tariff_viewer=tariff_viewer,
                is_weekday=True,
                dark_mode=options.get("dark_mode", False),
                rate_type="demand",
                chart_height=options.get("chart_height", 700),
                text_size=options.get("text_size", 12),
            )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error creating weekday demand rates heatmap: {str(e)}")
        st.info(
            "This may indicate missing or invalid demand rate data in the tariff file."
        )

    st.markdown("---")

    # Weekend Demand Rates - Full Width
    st.markdown("#### 📉 Weekend Demand Rates")

    try:
        if st.session_state.get("has_modifications") and st.session_state.get(
            "modified_tariff"
        ):
            # Use modified tariff data for visualization
            temp_viewer = create_temp_viewer_with_modified_tariff(
                st.session_state.modified_tariff
            )
            fig = create_heatmap(
                tariff_viewer=temp_viewer,
                is_weekday=False,
                dark_mode=options.get("dark_mode", False),
                rate_type="demand",
                chart_height=options.get("chart_height", 700),
                text_size=options.get("text_size", 12),
            )
        else:
            fig = create_heatmap(
                tariff_viewer=tariff_viewer,
                is_weekday=False,
                dark_mode=options.get("dark_mode", False),
                rate_type="demand",
                chart_height=options.get("chart_height", 700),
                text_size=options.get("text_size", 12),
            )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error creating weekend demand rates heatmap: {str(e)}")
        st.info(
            "This may indicate missing or invalid demand rate data in the tariff file."
        )


# End of file
