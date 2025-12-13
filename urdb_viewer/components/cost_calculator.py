"""
Cost calculator tab component for URDB Tariff Viewer.

This module contains the UI components for the utility cost analysis tab.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from urdb_viewer.components.load_factor import render_load_factor_analysis_tool
from urdb_viewer.models.tariff import TariffViewer
from urdb_viewer.services.calculation_service import CalculationService
from urdb_viewer.services.file_service import FileService
from urdb_viewer.ui.cached import validate_load_profile
from urdb_viewer.utils.styling import (
    create_custom_divider_html,
    create_section_header_html,
)


def render_cost_calculator_tab(
    tariff_viewer: TariffViewer,
    load_profile_path: Optional[Path],
    options: Dict[str, Any],
) -> None:
    """
    Render the utility cost analysis tab.

    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        load_profile_path (Optional[Path]): Path to selected load profile
        options (Dict[str, Any]): Display and analysis options
    """
    st.markdown(
        create_section_header_html("💰 Utility Cost Analysis"), unsafe_allow_html=True
    )

    # Load Factor Analysis Tool - Always available
    st.markdown("#### 📊 Load Factor Rate Analysis")
    render_load_factor_analysis_tool(tariff_viewer, options)

    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)

    # Rest of the calculator (requires load profile)
    if not load_profile_path:
        _show_no_load_profile_message()
        return

    # Load profile validation
    st.markdown("#### 📋 Load Profile Validation")

    try:
        validation_results = validate_load_profile(load_profile_path)
        _display_validation_results(validation_results)

        if not validation_results["is_valid"]:
            st.error(
                "❌ Cannot proceed with cost calculation due to validation errors."
            )
            return

    except Exception as e:
        st.error(f"❌ Error validating load profile: {str(e)}")
        return

    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)

    # Calculate button
    if st.button("🧮 Calculate Utility Costs", type="primary", width="stretch"):
        # Use default customer voltage from options
        customer_voltage = options.get("customer_voltage", 480.0)
        _perform_cost_calculation(
            tariff_viewer, load_profile_path, customer_voltage, options
        )

    # Show existing results if available
    if "calculation_results" in st.session_state:
        st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
        _display_calculation_results(st.session_state.calculation_results, options)


def render_utility_cost_calculation_tab(
    tariff_viewer: TariffViewer,
    load_profile_path: Optional[Path],
    options: Dict[str, Any],
) -> None:
    """
    Render the utility cost calculation tool tab.

    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        load_profile_path (Optional[Path]): Path to selected load profile
        options (Dict[str, Any]): Display and analysis options
    """
    # Rest of the calculator (requires load profile)
    if not load_profile_path:
        _show_no_load_profile_message()
        return

    # Load profile validation
    st.markdown("#### 📋 Load Profile Validation")

    try:
        validation_results = validate_load_profile(load_profile_path)
        _display_validation_results(validation_results)

        if not validation_results["is_valid"]:
            st.error(
                "❌ Cannot proceed with cost calculation due to validation errors."
            )
            return

    except Exception as e:
        st.error(f"❌ Error validating load profile: {str(e)}")
        return

    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)

    # Calculate button
    if st.button("🧮 Calculate Utility Costs", type="primary", width="stretch"):
        # Use default customer voltage from options
        customer_voltage = options.get("customer_voltage", 480.0)
        _perform_cost_calculation(
            tariff_viewer, load_profile_path, customer_voltage, options
        )

    # Show existing results if available
    if "calculation_results" in st.session_state:
        st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
        _display_calculation_results(st.session_state.calculation_results, options)


def _show_no_load_profile_message() -> None:
    """Show message when no load profile is selected."""
    st.info("ℹ️ **No Load Profile Selected**")
    st.markdown(
        """
    To calculate utility costs, you need to:

    1. **Select a load profile** from the sidebar dropdown, or
    2. **Upload a CSV file** with your load data, or
    3. **Generate a synthetic profile** using the Load Profile Generator tab

    **Required CSV Format:**
    - `timestamp`: Date and time in YYYY-MM-DD HH:MM:SS format
    - `load_kW`: Load values in kilowatts
    - Optional: `kWh` column (will be calculated if missing)
    """
    )

    # Show available load profiles
    csv_files = FileService.find_csv_files()
    if csv_files:
        st.markdown("**Available Load Profiles:**")
        for file_path in csv_files[:5]:  # Show first 5
            file_info = FileService.get_file_info(file_path)
            st.markdown(f"- `{file_info['name']}` ({file_info['size_mb']:.1f} MB)")

        if len(csv_files) > 5:
            st.markdown(f"... and {len(csv_files) - 5} more files")


def _display_validation_results(validation_results: Dict[str, Any]) -> None:
    """Display load profile validation results."""
    if validation_results["is_valid"]:
        st.success("✅ Load profile validation passed")

        # Show file info
        info = validation_results.get("info", {})
        if info:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Data Points", f"{info.get('row_count', 0):,}")

            with col2:
                load_range = info.get("load_range", {})
                if load_range.get("avg"):
                    st.metric("Avg Load", f"{load_range['avg']:.1f} kW")

            with col3:
                if load_range.get("max"):
                    st.metric("Peak Load", f"{load_range['max']:.1f} kW")

            with col4:
                date_range = info.get("date_range", {})
                if date_range.get("start") and date_range.get("end"):
                    st.metric(
                        "Date Range", f"{date_range['start']} to {date_range['end']}"
                    )

    else:
        st.error("❌ Load profile validation failed")

        # Show errors
        for error in validation_results.get("errors", []):
            st.error(f"• {error}")

    # Show warnings
    for warning in validation_results.get("warnings", []):
        st.warning(f"⚠️ {warning}")


def _perform_cost_calculation(
    tariff_viewer: TariffViewer,
    load_profile_path: Path,
    customer_voltage: float,
    options: Dict[str, Any],
) -> None:
    """Perform the utility cost calculation."""

    with st.spinner("🧮 Calculating utility costs..."):
        try:
            # Check if we have modified tariff data and use it directly
            if (
                st.session_state.get("has_modifications", False)
                and st.session_state.get("modified_tariff") is not None
            ):
                # Use modified tariff data directly
                from urdb_viewer.services.calculation_engine import (
                    calculate_utility_costs_for_app,
                )

                # Extract the actual tariff data from the wrapper structure
                modified_tariff = st.session_state.modified_tariff
                if "items" in modified_tariff:
                    tariff_data = modified_tariff["items"][0]
                else:
                    tariff_data = modified_tariff

                results = calculate_utility_costs_for_app(
                    tariff_data=tariff_data,
                    load_profile_path=str(load_profile_path),
                    default_voltage=customer_voltage,
                )
            else:
                # Use the calculation service with original tariff
                results = CalculationService.calculate_utility_bill(
                    tariff_viewer=tariff_viewer,
                    load_profile_path=load_profile_path,
                    customer_voltage=customer_voltage,
                )

            # Store results in session state
            st.session_state.calculation_results = results
            st.session_state.calculation_tariff = {
                "utility": tariff_viewer.utility_name,
                "rate": tariff_viewer.rate_name,
                "sector": tariff_viewer.sector,
            }

            st.success("✅ Cost calculation completed successfully!")
            st.rerun()  # Refresh to show results

        except Exception as e:
            st.error(f"❌ Calculation failed: {str(e)}")
            st.info("💡 **Troubleshooting Tips:**")
            st.info("• Ensure your load profile has the correct format")
            st.info("• Check that the tariff file contains valid rate structures")
            st.info(
                "• Verify that timestamps in your load profile are properly formatted"
            )


def _display_calculation_results(
    results: pd.DataFrame, options: Dict[str, Any]
) -> None:
    """Display the calculation results."""
    st.markdown("#### 💰 Cost Calculation Results")

    tariff_info = st.session_state.get("calculation_tariff", {})
    if tariff_info:
        st.info(
            f"**Tariff:** {tariff_info.get('utility', 'Unknown')} - {tariff_info.get('rate', 'Unknown')}"
        )

    # Calculate summary metrics from DataFrame (matching original app.py)
    total_annual_cost = results["total_charge"].sum()
    total_annual_kwh = results["total_kwh"].sum()
    avg_monthly_cost = results["total_charge"].mean()
    effective_rate_per_kwh = (
        total_annual_cost / total_annual_kwh if total_annual_kwh > 0 else 0
    )

    # Main cost metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Annual Total Cost", f"${total_annual_cost:,.0f}")

    with col2:
        st.metric("Annual Total kWh", f"{total_annual_kwh:,.0f}")

    with col3:
        st.metric("Average Monthly Cost", f"${avg_monthly_cost:,.0f}")

    with col4:
        st.metric("Effective Rate $/kWh", f"${effective_rate_per_kwh:.4f}")

    st.markdown("---")

    # Display detailed monthly breakdown (matching original app.py)
    st.markdown("#### 📅 Detailed Monthly Breakdown")

    # Prepare display dataframe
    display_df = results[
        [
            "month_name",
            "total_kwh",
            "peak_kw",
            "avg_load",
            "load_factor",
            "total_energy_cost",
            "total_demand_cost",
            "fixed_charge",
            "total_charge",
        ]
    ].copy()

    # Format the dataframe for better display
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "month_name": st.column_config.TextColumn(
                "Month", help="Month of the year", width="small"
            ),
            "total_kwh": st.column_config.NumberColumn(
                "Total kWh",
                help="Total energy consumption for the month",
                format="%.0f",
            ),
            "peak_kw": st.column_config.NumberColumn(
                "Peak Load (kW)", help="Maximum demand during the month", format="%.2f"
            ),
            "avg_load": st.column_config.NumberColumn(
                "Avg Load (kW)", help="Average load during the month", format="%.2f"
            ),
            "load_factor": st.column_config.NumberColumn(
                "Load Factor", help="Load factor (average/peak)", format="%.3f"
            ),
            "total_energy_cost": st.column_config.NumberColumn(
                "Energy Cost ($)",
                help="Total energy charges including adjustments",
                format="$%.2f",
            ),
            "total_demand_cost": st.column_config.NumberColumn(
                "Demand Cost ($)",
                help="Total demand charges including adjustments",
                format="$%.2f",
            ),
            "fixed_charge": st.column_config.NumberColumn(
                "Fixed Charge ($)", help="Monthly fixed charges", format="$%.2f"
            ),
            "total_charge": st.column_config.NumberColumn(
                "Total Cost ($)", help="Total monthly utility bill", format="$%.2f"
            ),
        },
    )

    # Cost breakdown chart
    st.markdown("#### 📈 Monthly Cost Visualization")
    _create_cost_breakdown_chart(results, options)

    # Load profile chart
    st.markdown("#### ⚡ Load Profile Overview")
    _create_load_profile_chart(results, options)


def _create_cost_breakdown_chart(
    results: pd.DataFrame, options: Dict[str, Any]
) -> None:
    """Create a monthly cost breakdown chart."""
    dark_mode = options.get("dark_mode", False)

    # Create monthly bar chart instead of annual donut chart
    fig = go.Figure()

    # Add grouped bar chart for monthly cost breakdown
    fig.add_trace(
        go.Bar(
            x=results["month_name"],
            y=results["total_energy_cost"],
            name="Energy Costs",
            marker_color="rgba(59, 130, 246, 0.8)",
            hovertemplate="<b>%{x}</b><br>Energy Cost: $%{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=results["month_name"],
            y=results["total_demand_cost"],
            name="Demand Costs",
            marker_color="rgba(249, 115, 22, 0.8)",
            hovertemplate="<b>%{x}</b><br>Demand Cost: $%{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=results["month_name"],
            y=results["fixed_charge"],
            name="Fixed Charges",
            marker_color="rgba(34, 197, 94, 0.8)",
            hovertemplate="<b>%{x}</b><br>Fixed Charge: $%{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Monthly Cost Breakdown by Month",
            font=dict(
                size=18,
                color="#1f2937" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
        ),
        barmode="stack",
        xaxis_title="Month",
        yaxis_title="Cost ($)",
        height=500,
        showlegend=True,
        plot_bgcolor=(
            "rgba(248, 250, 252, 0.8)" if not dark_mode else "rgba(15, 23, 42, 0.5)"
        ),
        paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
        font=dict(
            family="Inter, sans-serif", color="#1f2937" if not dark_mode else "#f1f5f9"
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def _create_load_profile_chart(results: pd.DataFrame, options: Dict[str, Any]) -> None:
    """Create a load profile overview chart."""
    dark_mode = options.get("dark_mode", False)

    # Show monthly peak and average loads
    fig_load = go.Figure()

    fig_load.add_trace(
        go.Scatter(
            x=results["month_name"],
            y=results["peak_kw"],
            mode="lines+markers",
            name="Peak Load (kW)",
            line=dict(color="rgba(239, 68, 68, 0.8)", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Peak Load: %{y:.2f} kW<extra></extra>",
        )
    )

    fig_load.add_trace(
        go.Scatter(
            x=results["month_name"],
            y=results["avg_load"],
            mode="lines+markers",
            name="Average Load (kW)",
            line=dict(color="rgba(59, 130, 246, 0.8)", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Average Load: %{y:.2f} kW<extra></extra>",
        )
    )

    fig_load.update_layout(
        title=dict(
            text="<b>Monthly Load Profile Summary</b>",
            font=dict(size=20, color="#0f172a" if not dark_mode else "#f1f5f9"),
            x=0.5,
            xanchor="center",
        ),
        xaxis_title="Month",
        yaxis_title="Load (kW)",
        height=400,
        showlegend=True,
        plot_bgcolor=(
            "rgba(248, 250, 252, 0.8)" if not dark_mode else "rgba(15, 23, 42, 0.5)"
        ),
        paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
        font=dict(color="#0f172a" if not dark_mode else "#f1f5f9"),
    )

    st.plotly_chart(fig_load, use_container_width=True)


def _display_monthly_breakdown(
    monthly_costs: Dict[str, Any], options: Dict[str, Any]
) -> None:
    """Display monthly cost breakdown."""
    dark_mode = options.get("dark_mode", False)

    # Convert to DataFrame for easier handling
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # Extract monthly data (assuming it exists in results)
    monthly_data = []
    for i, month in enumerate(months):
        # This is a placeholder - actual structure depends on calculation service
        total = monthly_costs.get(f"month_{i+1}", {}).get("total", 0)
        energy = monthly_costs.get(f"month_{i+1}", {}).get("energy", 0)
        demand = monthly_costs.get(f"month_{i+1}", {}).get("demand", 0)

        monthly_data.append(
            {"Month": month, "Total": total, "Energy": energy, "Demand": demand}
        )

    df = pd.DataFrame(monthly_data)

    # Create stacked bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Energy Charges",
            x=df["Month"],
            y=df["Energy"],
            marker_color="#1e40af" if not dark_mode else "#3b82f6",
            hovertemplate="<b>Energy Charges</b><br>Month: %{x}<br>Cost: $%{y:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Demand Charges",
            x=df["Month"],
            y=df["Demand"],
            marker_color="#7c3aed" if not dark_mode else "#8b5cf6",
            hovertemplate="<b>Demand Charges</b><br>Month: %{x}<br>Cost: $%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Monthly Cost Breakdown",
            font=dict(
                size=18,
                color="#1f2937" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
        ),
        xaxis=dict(
            title="Month",
            titlefont=dict(color="#1f2937" if not dark_mode else "#f1f5f9"),
            tickfont=dict(color="#1f2937" if not dark_mode else "#f1f5f9"),
        ),
        yaxis=dict(
            title="Cost ($)",
            titlefont=dict(color="#1f2937" if not dark_mode else "#f1f5f9"),
            tickfont=dict(color="#1f2937" if not dark_mode else "#f1f5f9"),
        ),
        barmode="stack",
        height=400,
        font=dict(
            family="Inter, sans-serif", color="#1f2937" if not dark_mode else "#f1f5f9"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#1f2937" if not dark_mode else "#f1f5f9")),
    )

    st.plotly_chart(fig, width="stretch")

    # Show data table
    st.dataframe(df.round(2), width="stretch", hide_index=True)


def _display_load_statistics(load_stats: Dict[str, Any]) -> None:
    """Display load profile statistics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        peak_kw = load_stats.get("peak_kw", 0)
        st.metric("Peak Demand", f"{peak_kw:.1f} kW")

    with col2:
        avg_kw = load_stats.get("avg_kw", 0)
        st.metric("Average Load", f"{avg_kw:.1f} kW")

    with col3:
        total_kwh = load_stats.get("total_kwh", 0)
        st.metric("Total Energy", f"{total_kwh:,.0f} kWh")

    with col4:
        load_factor = load_stats.get("load_factor", 0)
        st.metric("Load Factor", f"{load_factor:.1%}")


def _display_detailed_breakdown(results: Dict[str, Any]) -> None:
    """Display detailed cost breakdown."""
    st.json(results)


def _create_export_section(results: Dict[str, Any]) -> None:
    """Create export options for results."""
    col1, col2, col3 = st.columns(3)

    with col1:
        # Export as JSON
        if st.button("📄 Export as JSON"):
            import json

            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="utility_cost_calculation.json",
                mime="application/json",
            )

    with col2:
        # Export summary as CSV
        if st.button("📊 Export Summary as CSV"):
            # Convert values to float in case they're pandas Series
            def safe_float_convert(value):
                if hasattr(value, "iloc"):
                    return float(value.iloc[0]) if len(value) > 0 else 0.0
                else:
                    return float(value) if value is not None else 0.0

            summary_data = {
                "Metric": [
                    "Total Annual Cost",
                    "Energy Charges",
                    "Demand Charges",
                    "Fixed Charges",
                ],
                "Amount ($)": [
                    safe_float_convert(results.get("total_annual_cost", 0)),
                    safe_float_convert(results.get("total_energy_cost", 0)),
                    safe_float_convert(results.get("total_demand_cost", 0)),
                    safe_float_convert(results.get("total_fixed_cost", 0)),
                ],
            }

            df = pd.DataFrame(summary_data)
            csv_str = df.to_csv(index=False)

            st.download_button(
                label="Download CSV",
                data=csv_str,
                file_name="utility_cost_summary.csv",
                mime="text/csv",
            )

    with col3:
        # Generate report
        if st.button("📋 Generate Report"):
            st.info("📋 Report generation feature coming soon!")


def show_cost_comparison(
    tariff_viewers: list, load_profile_path: Path, options: Dict[str, Any]
) -> None:
    """
    Show cost comparison between multiple tariffs.

    Args:
        tariff_viewers (list): List of TariffViewer instances
        load_profile_path (Path): Path to load profile
        options (Dict[str, Any]): Display options
    """
    st.markdown("#### 🔄 Tariff Comparison")

    if len(tariff_viewers) < 2:
        st.info("Select multiple tariffs to compare costs.")
        return

    with st.spinner("Comparing tariffs..."):
        try:
            comparison_results = CalculationService.compare_tariffs(
                tariff_viewers=tariff_viewers,
                load_profile_path=load_profile_path,
                customer_voltage=options.get("customer_voltage", 480.0),
            )

            # Display comparison results
            _display_comparison_results(comparison_results, options)

        except Exception as e:
            st.error(f"❌ Comparison failed: {str(e)}")


def _display_comparison_results(
    comparison_results: Dict[str, Any], options: Dict[str, Any]
) -> None:
    """Display tariff comparison results."""
    tariff_results = comparison_results.get("tariff_results", [])
    summary = comparison_results.get("summary", {})

    if not tariff_results:
        st.error("No comparison results available.")
        return

    # Summary metrics
    if summary:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Lowest Cost", f"${summary.get('lowest_cost', 0):,.2f}")

        with col2:
            st.metric("Highest Cost", f"${summary.get('highest_cost', 0):,.2f}")

        with col3:
            savings = summary.get("highest_cost", 0) - summary.get("lowest_cost", 0)
            st.metric("Potential Savings", f"${savings:,.2f}")

    # Comparison table
    comparison_df = pd.DataFrame(
        [
            {
                "Utility": result["utility_name"],
                "Rate": result["rate_name"],
                "Total Cost ($)": result["total_cost"],
                "Energy Cost ($)": result["energy_cost"],
                "Demand Cost ($)": result["demand_cost"],
                "Status": (
                    "✅ Success" if result["calculation_successful"] else "❌ Failed"
                ),
            }
            for result in tariff_results
        ]
    )

    st.dataframe(comparison_df, width="stretch", hide_index=True)

    # Comparison chart
    successful_results = [r for r in tariff_results if r["calculation_successful"]]

    if len(successful_results) > 1:
        fig = px.bar(
            x=[f"{r['utility_name']}\n{r['rate_name']}" for r in successful_results],
            y=[r["total_cost"] for r in successful_results],
            title="Annual Cost Comparison",
            labels={"x": "Tariff", "y": "Annual Cost ($)"},
        )

        fig.update_layout(height=400, font=dict(family="Inter, sans-serif"))

        st.plotly_chart(fig, width="stretch")
