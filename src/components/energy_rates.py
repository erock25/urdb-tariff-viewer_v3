"""
Energy rates tab component for URDB Tariff Viewer.

This module contains the UI components for the energy rates analysis tab.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from io import BytesIO

from src.models.tariff import TariffViewer
from src.components.visualizations import create_heatmap
from src.components.rate_editor import (
    render_rate_editing_form,
    ENERGY_RATE_CONFIG
)
from src.utils.styling import create_custom_divider_html
from src.utils.helpers import (
    generate_energy_rates_excel,
    clean_filename,
    export_rate_table_to_excel
)


def render_energy_rates_tab(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the energy rates analysis tab.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display and analysis options
    """
    # Show current table (read-only) first - matching original
    st.markdown("#### Current Rate Table")
    
    try:
        tou_table = tariff_viewer.create_tou_labels_table()
        
        if not tou_table.empty:
            st.dataframe(
                tou_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "TOU Period": st.column_config.TextColumn(
                        "TOU Period",
                        width="medium",
                    ),
                    "Base Rate ($/kWh)": st.column_config.TextColumn(
                        "Base Rate ($/kWh)",
                        width="small",
                    ),
                    "Adjustment ($/kWh)": st.column_config.TextColumn(
                        "Adjustment ($/kWh)", 
                        width="small",
                    ),
                    "Total Rate ($/kWh)": st.column_config.TextColumn(
                        "Total Rate ($/kWh)",
                        width="small",
                    ),
                    "Hours/Year": st.column_config.NumberColumn(
                        "Hours/Year",
                        width="small",
                        format="%d"
                    ),
                    "% of Year": st.column_config.TextColumn(
                        "% of Year",
                        width="small",
                    ),
                    "Days/Year": st.column_config.NumberColumn(
                        "Days/Year",
                        width="small",
                        format="%d"
                    ),
                    "Months Present": st.column_config.TextColumn(
                        "Months Present",
                        width="large",
                    )
                }
            )
            
            # Download button for the rate table
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                # Use shared Excel export helper
                rate_columns = ['Base Rate ($/kWh)', 'Adjustment ($/kWh)', 'Total Rate ($/kWh)']
                excel_data = export_rate_table_to_excel(
                    df=tou_table,
                    sheet_name='Energy Rate Table',
                    rate_columns=rate_columns,
                    percentage_columns=['% of Year'],
                    rate_precision=4
                )
                
                # Create filename
                utility_clean = clean_filename(tariff_viewer.utility_name)
                rate_clean = clean_filename(tariff_viewer.rate_name)
                timestamp = datetime.now().strftime("%Y%m%d")
                filename = f"Energy_Rate_Table_{utility_clean}_{rate_clean}_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Download Table",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download the current rate table as an Excel file"
                )
        else:
            st.info("📝 **Note:** No energy rate structure found in this tariff JSON.")
            
    except Exception as e:
        st.error(f"❌ Error creating rate table: {str(e)}")
    
    st.markdown("---")
    
    # Rate editing section
    st.markdown("#### ✏️ Rate Editing")
    
    with st.expander("🔧 Edit Energy Rates", expanded=False):
        render_rate_editing_form(tariff_viewer, ENERGY_RATE_CONFIG, options)
    
    st.markdown("---")
    
    # Heatmap visualization section
    st.markdown("#### 🗓️ Time-of-Use Energy Rates Heatmap")
    
    # Controls for heatmap
    col1, col2 = st.columns(2)
    
    with col1:
        is_weekday = st.radio(
            "Day Type",
            options=[True, False],
            format_func=lambda x: "Weekday" if x else "Weekend",
            horizontal=True,
            help="Choose between weekday and weekend energy rates"
        )
    
    with col2:
        show_heatmap_text = st.checkbox(
            "Show Values on Heatmap",
            value=options.get('text_size', 12) > 0,
            help="Display rate values on heatmap tiles"
        )
    
    # Adjust text size based on checkbox
    text_size = options.get('text_size', 12) if show_heatmap_text else 0
    
    try:
        heatmap_fig = create_heatmap(
            tariff_viewer=tariff_viewer,
            is_weekday=is_weekday,
            dark_mode=options.get('dark_mode', False),
            rate_type="energy",
            chart_height=options.get('chart_height', 700),
            text_size=text_size
        )
        
        st.plotly_chart(heatmap_fig, width="stretch")
        
    except Exception as e:
        st.error(f"❌ Error creating energy rates heatmap: {str(e)}")
        st.info("This may indicate missing or invalid energy rate data in the tariff file.")
    
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    
    # Add Excel download section at the bottom
    _render_excel_download_section(tariff_viewer)


def show_energy_rate_comparison(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Show energy rate comparison between weekday and weekend.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display options
    """
    st.markdown("#### 📊 Weekday vs Weekend Rate Comparison")
    
    # Calculate differences
    rate_diff = tariff_viewer.weekday_df - tariff_viewer.weekend_df
    
    # Show summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_weekday = tariff_viewer.weekday_df.values.mean()
        st.metric("Avg Weekday Rate", f"${avg_weekday:.4f}/kWh")
    
    with col2:
        avg_weekend = tariff_viewer.weekend_df.values.mean()
        st.metric("Avg Weekend Rate", f"${avg_weekend:.4f}/kWh")
    
    with col3:
        avg_difference = rate_diff.values.mean()
        st.metric(
            "Average Difference", 
            f"${avg_difference:.4f}/kWh",
            delta=f"Weekday {'higher' if avg_difference > 0 else 'lower'}"
        )
    
    # Show difference heatmap
    if st.checkbox("Show Rate Difference Heatmap"):
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=rate_diff.values,
            x=[f'{h:02d}:00' for h in range(24)],
            y=rate_diff.index,
            colorscale='RdBu_r',
            colorbar=dict(title="Rate Difference<br>($/kWh)"),
            hovertemplate="<b>%{y}</b> - %{x}<br>Difference: $%{z:.4f}/kWh<extra></extra>"
        ))
        
        fig.update_layout(
            title="Weekday vs Weekend Rate Differences",
            xaxis_title="Hour of Day",
            yaxis_title="Month",
            height=options.get('chart_height', 700)
        )
        
        st.plotly_chart(fig, width="stretch")


def _render_excel_download_section(tariff_viewer: TariffViewer) -> None:
    """
    Render the Excel download section with button.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    st.markdown("#### 📥 Download Rate Data (Energy & Demand)")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        # Year selection for timeseries
        current_year = datetime.now().year
        year = st.number_input(
            "Year for Timeseries",
            min_value=2020,
            max_value=2050,
            value=current_year,
            step=1,
            help="Select the year for generating the full energy timeseries data"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        
        # Generate Excel file
        try:
            excel_data = generate_energy_rates_excel(tariff_viewer, year=year)
            
            # Create filename
            utility_clean = clean_filename(tariff_viewer.utility_name)
            rate_clean = clean_filename(tariff_viewer.rate_name)
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"Tariff_Rates_{utility_clean}_{rate_clean}_{timestamp}.xlsx"
            
            # Download button
            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download Excel file with 8 sheets containing energy and demand rate data"
            )
            
        except Exception as e:
            st.error(f"❌ Error generating Excel file: {str(e)}")
    
    with col3:
        st.info(
            """
            **Excel file contains 8 sheets:**
            
            **Energy Rates:**
            - **Energy Rate Table**: TOU periods with base rates and adjustments
            - **Weekday Energy Rates**: 12x24 heatmap (Month x Hour)
            - **Weekend Energy Rates**: 12x24 heatmap (Month x Hour)
            - **Energy Timeseries**: Full year 15-min interval data
            
            **Demand Rates:**
            - **Demand Rate Table**: Demand periods with rates
            - **Weekday Demand Rates**: 12x24 heatmap (Month x Hour)
            - **Weekend Demand Rates**: 12x24 heatmap (Month x Hour)
            - **Flat Demand Rates**: Seasonal/Monthly flat demand charges
            """
        )
