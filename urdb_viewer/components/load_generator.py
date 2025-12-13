"""
Load profile generator tab component for URDB Tariff Viewer.

This module contains the UI components for generating synthetic load profiles.
"""

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from urdb_viewer.config.constants import DEFAULT_TOU_PERCENTAGES
from urdb_viewer.config.settings import Settings
from urdb_viewer.models.load_profile import LoadProfileGenerator
from urdb_viewer.models.tariff import TariffViewer
from urdb_viewer.services.file_service import FileService
from urdb_viewer.utils.styling import (
    create_custom_divider_html,
    create_section_header_html,
)


def render_load_generator_tab(
    tariff_viewer: TariffViewer, options: Dict[str, Any]
) -> None:
    """
    Render the load profile generator tab.

    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display and analysis options
    """
    st.markdown(
        create_section_header_html("🔧 Load Profile Generator"), unsafe_allow_html=True
    )

    st.markdown(
        """
    Generate synthetic load profiles that align with your tariff's Time-of-Use periods.
    This tool creates realistic load patterns based on your specifications.
    """
    )

    # Load generation parameters
    st.markdown("#### ⚙️ Load Profile Parameters")

    col1, col2 = st.columns(2)

    with col1:
        avg_load = st.number_input(
            "Average Load (kW)",
            min_value=1.0,
            max_value=10000.0,
            value=options["load_generation"]["avg_load"],
            step=10.0,
            help="Average load across the entire year",
        )

        load_factor = st.slider(
            "Load Factor",
            min_value=0.1,
            max_value=1.0,
            value=options["load_generation"]["load_factor"],
            step=0.05,
            help="Ratio of average load to peak load (higher = more consistent)",
        )

        year = st.selectbox(
            "Year",
            options=[2023, 2024, 2025, 2026],
            index=2,
            help="Year for the load profile timestamps",
        )

    with col2:
        seasonal_variation = st.slider(
            "Seasonal Variation",
            min_value=0.0,
            max_value=0.5,
            value=options["load_generation"]["seasonal_variation"],
            step=0.05,
            help="How much load varies by season (0 = no variation)",
        )

        weekend_factor = st.slider(
            "Weekend Factor",
            min_value=0.1,
            max_value=1.5,
            value=options["load_generation"]["weekend_factor"],
            step=0.05,
            help="Weekend load as fraction of weekday load",
        )

        daily_variation = st.slider(
            "Daily Variation",
            min_value=0.0,
            max_value=0.3,
            value=0.15,
            step=0.05,
            help="How much load varies throughout the day",
        )

    # TOU energy distribution
    st.markdown("#### ⚡ Time-of-Use Energy Distribution")
    st.info(
        "Specify what percentage of your annual energy consumption occurs in each TOU period."
    )

    # Get TOU periods from tariff
    energy_rates = tariff_viewer.tariff.get("energyratestructure", [])
    energy_labels = tariff_viewer.tariff.get("energytoulabels", [])

    tou_percentages = {}

    if energy_rates:
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]

        total_percentage = 0

        for i, rate_info in enumerate(energy_rates):
            if energy_labels and i < len(energy_labels):
                label = energy_labels[i]
            else:
                label = f"Period {i}"

            col_idx = i % 3
            with cols[col_idx]:
                percentage = st.slider(
                    f"{label} (%)",
                    min_value=0,
                    max_value=100,
                    value=int(
                        DEFAULT_TOU_PERCENTAGES.get(
                            ["peak", "mid_peak", "off_peak"][min(i, 2)], 0.3
                        )
                        * 100
                    ),
                    step=1,
                    key=f"tou_period_{i}",
                    help=f"Percentage of annual energy in {label}",
                )
                tou_percentages[i] = percentage
                total_percentage += percentage

        # Show total percentage
        if total_percentage != 100:
            st.warning(f"⚠️ Total percentage is {total_percentage}% (should be 100%)")
        else:
            st.success("✅ Total percentage equals 100%")

    else:
        st.warning(
            "⚠️ No energy rate structure found in tariff. Using default TOU periods."
        )
        tou_percentages = {0: 30, 1: 40, 2: 30}  # Default periods (percentages)

    # Advanced options
    with st.expander("🔬 Advanced Options"):
        noise_level = st.slider(
            "Noise Level",
            min_value=0.0,
            max_value=0.2,
            value=0.05,
            step=0.01,
            help="Random variation in load values (adds realism)",
        )

        custom_filename = st.text_input(
            "Custom Filename (optional)",
            placeholder="my_load_profile",
            help="Custom name for the generated file (without .csv extension)",
        )

    # Generate profile button
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)

    if st.button("🚀 Generate Load Profile", type="primary", width="stretch"):
        _generate_load_profile(
            tariff_viewer=tariff_viewer,
            avg_load=avg_load,
            load_factor=load_factor,
            year=year,
            tou_percentages=tou_percentages,
            seasonal_variation=seasonal_variation,
            weekend_factor=weekend_factor,
            daily_variation=daily_variation,
            noise_level=noise_level,
            custom_filename=custom_filename,
            options=options,
        )

    # Show existing generated profiles
    _show_existing_profiles()


def _generate_load_profile(
    tariff_viewer: TariffViewer,
    avg_load: float,
    load_factor: float,
    year: int,
    tou_percentages: Dict[int, float],
    seasonal_variation: float,
    weekend_factor: float,
    daily_variation: float,
    noise_level: float,
    custom_filename: str,
    options: Dict[str, Any],
) -> None:
    """Generate the load profile and save it."""

    with st.spinner("🔧 Generating load profile..."):
        try:
            # Create load profile generator
            generator = LoadProfileGenerator(
                tariff=tariff_viewer.tariff,
                avg_load=avg_load,
                load_factor=load_factor,
                year=year,
            )

            # Generate profile
            profile_df = generator.generate_profile(
                tou_percentages=tou_percentages,
                seasonal_variation=seasonal_variation,
                weekend_factor=weekend_factor,
                daily_variation=daily_variation,
                noise_level=noise_level,
            )

            # Validate profile
            validation_results = generator.validate_profile(profile_df)

            # Save profile
            if custom_filename:
                filename = f"{custom_filename}.csv"
            else:
                filename = f"generated_profile_{tariff_viewer.utility_name}_{avg_load}kW_{year}.csv"

            # Clean filename
            filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
            save_path = Settings.LOAD_PROFILES_DIR / filename

            FileService.save_csv_file(profile_df, save_path)

            # Store in session state for display
            st.session_state.generated_profile = profile_df
            st.session_state.generation_stats = generator.get_load_statistics(
                profile_df
            )
            st.session_state.validation_results = validation_results

            st.success(f"✅ Load profile generated successfully!")
            st.info(f"📁 Saved to: `{save_path}`")

            # Display results
            _display_generation_results(
                profile_df,
                generator.get_load_statistics(profile_df),
                validation_results,
                options,
            )

        except Exception as e:
            st.error(f"❌ Error generating load profile: {str(e)}")


def _display_generation_results(
    profile_df: pd.DataFrame,
    stats: Dict[str, float],
    validation_results: Dict[str, bool],
    options: Dict[str, Any],
) -> None:
    """Display the generated load profile results."""

    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    st.markdown("#### 📊 Generated Load Profile Results")

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Peak Load", f"{stats['peak_kw']:.1f} kW")

    with col2:
        st.metric("Average Load", f"{stats['avg_kw']:.1f} kW")

    with col3:
        st.metric("Total Energy", f"{stats['total_kwh']:,.0f} kWh")

    with col4:
        st.metric("Load Factor", f"{stats['load_factor']:.1%}")

    # Validation results
    st.markdown("##### ✅ Validation Results")

    validation_cols = st.columns(4)
    validation_items = [
        ("Average Load", validation_results["avg_load_valid"]),
        ("Load Factor", validation_results["load_factor_valid"]),
        ("No Negative Values", validation_results["no_negative_values"]),
        ("Reasonable Peak", validation_results["reasonable_peak"]),
    ]

    for i, (label, is_valid) in enumerate(validation_items):
        with validation_cols[i]:
            status = "✅ Pass" if is_valid else "❌ Fail"
            st.metric(label, status)

    # Load profile visualization
    st.markdown("##### 📈 Load Profile Visualization")

    # Sample the data for visualization (show every 96th point = daily peaks for 15-min data)
    sample_df = profile_df[::96].copy()  # Daily samples

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sample_df["timestamp"],
            y=sample_df["load_kW"],
            mode="lines",
            name="Load Profile",
            line=dict(color="#1e40af", width=2),
            hovertemplate="<b>%{x}</b><br>Load: %{y:.1f} kW<extra></extra>",
        )
    )

    fig.update_layout(
        title="Generated Load Profile (Daily Averages)",
        xaxis_title="Date",
        yaxis_title="Load (kW)",
        height=400,
        font=dict(family="Inter, sans-serif"),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch")

    # Download section
    st.markdown("##### 📥 Download Generated Profile")

    csv_data = profile_df.to_csv(index=False)

    st.download_button(
        label="📁 Download CSV File",
        data=csv_data,
        file_name=f"generated_load_profile_{stats['avg_kw']:.0f}kW.csv",
        mime="text/csv",
        width="stretch",
    )


def _show_existing_profiles() -> None:
    """Show existing generated load profiles."""

    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    st.markdown("#### 📁 Existing Load Profiles")

    csv_files = FileService.find_csv_files()

    if csv_files:
        st.markdown(f"Found {len(csv_files)} load profile files:")

        for file_path in csv_files:
            file_info = FileService.get_file_info(file_path)

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{file_info['name']}**")

            with col2:
                st.markdown(f"{file_info['size_mb']:.1f} MB")

            with col3:
                if st.button("🗑️", key=f"delete_{file_path}", help="Delete file"):
                    try:
                        file_path.unlink()
                        st.success(f"Deleted {file_info['name']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {str(e)}")

    else:
        st.info("No load profile files found. Generate your first profile above!")


def show_load_profile_analysis(
    profile_df: pd.DataFrame, options: Dict[str, Any]
) -> None:
    """
    Show detailed analysis of a load profile.

    Args:
        profile_df (pd.DataFrame): Load profile DataFrame
        options (Dict[str, Any]): Display options
    """
    from ..services.calculation_service import CalculationService

    st.markdown("#### 🔍 Load Profile Analysis")

    try:
        analysis_results = CalculationService.analyze_load_profile(profile_df)

        # Basic statistics
        basic_stats = analysis_results["basic_stats"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Data Points", f"{basic_stats['data_points']:,}")

        with col2:
            st.metric("Peak Demand", f"{basic_stats['peak_kw']:.1f} kW")

        with col3:
            st.metric("Average Load", f"{basic_stats['avg_kw']:.1f} kW")

        with col4:
            st.metric("Load Factor", f"{basic_stats['load_factor']:.1%}")

        # Load profile time series chart
        if "load_profile" in analysis_results:
            st.markdown("##### 📈 Load Profile Time Series")

            load_profile_data = analysis_results["load_profile"]

            # Date range selection
            col1, col2 = st.columns(2)

            with col1:
                # Get available date range
                available_start = pd.to_datetime(
                    load_profile_data["date_range"]["start"]
                )
                available_end = pd.to_datetime(load_profile_data["date_range"]["end"])

                # Default to first 7 days or available range, whichever is smaller
                default_end = min(available_start + pd.Timedelta(days=7), available_end)

                start_date = st.date_input(
                    "Start Date",
                    value=available_start.date(),
                    min_value=available_start.date(),
                    max_value=available_end.date(),
                    help="Select the start date for the load profile visualization",
                )

            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=default_end.date(),
                    min_value=available_start.date(),
                    max_value=available_end.date(),
                    help="Select the end date for the load profile visualization",
                )

            # Validate date range
            if start_date > end_date:
                st.error("❌ Start date must be before or equal to end date")
                st.stop()

            try:
                # Convert timestamps to datetime for filtering
                timestamps = pd.to_datetime(load_profile_data["timestamps"])
                loads = load_profile_data["loads"]

                # Filter data based on selected date range
                start_datetime = pd.to_datetime(start_date)
                end_datetime = pd.to_datetime(end_date) + pd.Timedelta(
                    days=1
                )  # Include the entire end date

                # Create a DataFrame for easier filtering
                df_filter = pd.DataFrame({"timestamp": timestamps, "load": loads})

                # Filter the DataFrame
                mask = (df_filter["timestamp"] >= start_datetime) & (
                    df_filter["timestamp"] < end_datetime
                )
                filtered_df = df_filter[mask]

                filtered_timestamps = filtered_df["timestamp"]
                filtered_loads = filtered_df["load"].tolist()

            except Exception as e:
                st.error(f"❌ Error processing load profile data: {str(e)}")
                st.stop()

            if len(filtered_timestamps) == 0:
                st.warning("⚠️ No data available for the selected date range")
                st.stop()

            # Show data info
            st.info(
                f"📊 Showing {len(filtered_timestamps):,} data points from {start_date} to {end_date}"
            )

            # Create time series chart
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=filtered_timestamps,
                    y=filtered_loads,
                    mode="lines",
                    name="Load (kW)",
                    line=dict(color="#1e40af", width=2),
                    hovertemplate="<b>%{x}</b><br>Load: %{y:.2f} kW<extra></extra>",
                )
            )

            # Get dark mode setting
            dark_mode = options.get("dark_mode", False)

            fig.update_layout(
                title=dict(
                    text=f"Load Profile - {start_date} to {end_date}",
                    font=dict(
                        size=16,
                        color="#1f2937" if not dark_mode else "#f1f5f9",
                        family="Inter, sans-serif",
                    ),
                ),
                xaxis_title="Timestamp",
                yaxis_title="Load (kW)",
                height=400,
                showlegend=False,
                plot_bgcolor=(
                    "rgba(248, 250, 252, 0.8)"
                    if not dark_mode
                    else "rgba(15, 23, 42, 0.5)"
                ),
                paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
                font=dict(
                    family="Inter, sans-serif",
                    color="#1f2937" if not dark_mode else "#f1f5f9",
                ),
                xaxis=dict(tickformat="%m/%d %H:%M", tickangle=45),
                yaxis=dict(rangemode="tozero"),
            )

            st.plotly_chart(fig, use_container_width=True)

        # Monthly statistics
        if "monthly_stats" in analysis_results:
            st.markdown("##### 📅 Monthly Statistics")
            monthly_df = pd.DataFrame(analysis_results["monthly_stats"])
            st.dataframe(monthly_df, width="stretch")

        # Daily energy consumption by day of week
        if "daily_energy" in analysis_results:
            st.markdown("##### 📊 Energy Consumption by Day of Week")

            daily_energy_data = analysis_results["daily_energy"]

            # Create bar chart
            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=list(daily_energy_data.keys()),
                    y=list(daily_energy_data.values()),
                    marker_color="#1e40af",  # Single blue color for all bars
                    hovertemplate="<b>%{x}</b><br>Energy: %{y:,.0f} kWh<extra></extra>",
                )
            )

            # Get dark mode setting
            dark_mode = options.get("dark_mode", False)

            fig.update_layout(
                title=dict(
                    text="Total Energy Consumption by Day of Week",
                    font=dict(
                        size=16,
                        color="#1f2937" if not dark_mode else "#f1f5f9",
                        family="Inter, sans-serif",
                    ),
                ),
                xaxis_title="Day of Week",
                yaxis_title="Energy Consumption (kWh)",
                height=400,
                showlegend=False,
                plot_bgcolor=(
                    "rgba(248, 250, 252, 0.8)"
                    if not dark_mode
                    else "rgba(15, 23, 42, 0.5)"
                ),
                paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
                font=dict(
                    family="Inter, sans-serif",
                    color="#1f2937" if not dark_mode else "#f1f5f9",
                ),
                xaxis=dict(
                    tickangle=0,
                    categoryorder="array",
                    categoryarray=[
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ],
                ),
            )

            st.plotly_chart(fig, use_container_width=True)

        # Hourly energy consumption
        if "hourly_energy" in analysis_results:
            st.markdown("##### ⏰ Energy Consumption by Hour of Day")

            hourly_energy_data = analysis_results["hourly_energy"]

            # Create line chart for hourly energy consumption
            fig = go.Figure()

            # Ensure we have data and handle the conversion safely
            if hourly_energy_data:
                # Debug: show the data structure
                with st.expander("Debug: Hourly Energy Data", expanded=False):
                    st.write("Keys:", list(hourly_energy_data.keys()))
                    st.write("Data:", hourly_energy_data)

                # Convert hour keys to integers and sort
                try:
                    hours = sorted([int(h) for h in hourly_energy_data.keys()])
                    energy_values = [hourly_energy_data[h] for h in hours]
                except (ValueError, KeyError) as e:
                    # Fallback: create a simple list if there are issues
                    st.warning(f"Warning: Issue processing hourly data: {e}")
                    hours = list(range(24))
                    energy_values = [0] * 24
            else:
                # No data available
                hours = list(range(24))
                energy_values = [0] * 24

            fig.add_trace(
                go.Scatter(
                    x=hours,
                    y=energy_values,
                    mode="lines+markers",
                    name="Hourly Energy Consumption",
                    line=dict(color="#1e40af", width=3),
                    marker=dict(color="#1e40af", size=6),
                    hovertemplate="<b>Hour %{x}:00</b><br>Energy: %{y:,.0f} kWh<extra></extra>",
                )
            )

            # Get dark mode setting
            dark_mode = options.get("dark_mode", False)

            fig.update_layout(
                title=dict(
                    text="Total Energy Consumption by Hour of Day",
                    font=dict(
                        size=16,
                        color="#1f2937" if not dark_mode else "#f1f5f9",
                        family="Inter, sans-serif",
                    ),
                ),
                xaxis_title="Hour of Day",
                yaxis_title="Energy Consumption (kWh)",
                height=400,
                showlegend=False,
                plot_bgcolor=(
                    "rgba(248, 250, 252, 0.8)"
                    if not dark_mode
                    else "rgba(15, 23, 42, 0.5)"
                ),
                paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
                font=dict(
                    family="Inter, sans-serif",
                    color="#1f2937" if not dark_mode else "#f1f5f9",
                ),
                xaxis=dict(tickmode="linear", tick0=0, dtick=2, range=[-0.5, 23.5]),
                yaxis=dict(rangemode="tozero"),
            )

            st.plotly_chart(fig, use_container_width=True)

        # Load duration curve
        if "duration_curve" in analysis_results:
            st.markdown("##### 📈 Load Duration Curve")

            duration_data = analysis_results["duration_curve"]

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=duration_data["percentiles"],
                    y=duration_data["loads"],
                    mode="lines",
                    name="Load Duration Curve",
                    line=dict(color="#1e40af", width=3),
                )
            )

            fig.update_layout(
                title="Load Duration Curve",
                xaxis_title="Percentage of Time (%)",
                yaxis_title="Load (kW)",
                height=400,
                font=dict(family="Inter, sans-serif"),
            )

            st.plotly_chart(fig, width="stretch")

    except Exception as e:
        st.error(f"❌ Error analyzing load profile: {str(e)}")
