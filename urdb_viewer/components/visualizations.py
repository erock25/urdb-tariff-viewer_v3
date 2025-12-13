"""
Visualization components for URDB Tariff Viewer.

This module contains functions for creating charts, heatmaps, and other visualizations.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from urdb_viewer.config.constants import (
    DEFAULT_CHART_HEIGHT,
    DEFAULT_COLORS,
    DEFAULT_FLAT_DEMAND_HEIGHT,
)
from urdb_viewer.models.tariff import TariffViewer


def create_heatmap(
    tariff_viewer: TariffViewer,
    is_weekday: bool = True,
    dark_mode: bool = False,
    rate_type: str = "energy",
    chart_height: int = DEFAULT_CHART_HEIGHT,
    text_size: int = 12,
) -> go.Figure:
    """
    Create an interactive heatmap for energy or demand rates.

    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        is_weekday (bool): Whether to show weekday or weekend rates
        dark_mode (bool): Whether to use dark mode styling
        rate_type (str): Type of rates ("energy" or "demand")
        chart_height (int): Height of the chart in pixels
        text_size (int): Size of text on heatmap tiles

    Returns:
        go.Figure: Plotly figure object
    """
    if rate_type == "energy":
        df = tariff_viewer.weekday_df if is_weekday else tariff_viewer.weekend_df
        day_type = "Weekday" if is_weekday else "Weekend"
        title_suffix = "Energy Rates"
        colorbar_title = "Rate ($/kWh)"
        unit = "kWh"
        schedule_key = (
            "energyweekdayschedule" if is_weekday else "energyweekendschedule"
        )
        rate_structure = tariff_viewer.tariff.get("energyratestructure", [])
    else:  # demand
        df = (
            tariff_viewer.demand_weekday_df
            if is_weekday
            else tariff_viewer.demand_weekend_df
        )
        day_type = "Weekday" if is_weekday else "Weekend"
        title_suffix = "Demand Rates"
        colorbar_title = "Rate ($/kW)"
        unit = "kW"
        schedule_key = (
            "demandweekdayschedule" if is_weekday else "demandweekendschedule"
        )
        rate_structure = tariff_viewer.tariff.get("demandratestructure", [])

    # Get TOU labels for enhanced hover information
    energy_labels = tariff_viewer.tariff.get("energytoulabels", [])
    schedule = tariff_viewer.tariff.get(schedule_key, [])

    # Create enhanced heatmap with translucent tiles
    fig = go.Figure()

    # Select colors based on theme
    colors = DEFAULT_COLORS["heatmap_dark" if dark_mode else "heatmap_light"]

    # Create custom colorscale
    colorscale = [
        [0.0, colors[0]],  # Lowest rates - green
        [0.25, colors[1]],  # Low rates - light green
        [0.5, colors[2]],  # Medium rates - yellow/amber
        [0.75, colors[3]],  # High rates - orange
        [1.0, colors[4]],  # Highest rates - red
    ]

    # Create custom hover text with TOU period information
    hover_text = []
    custom_data = []

    for month_idx, month in enumerate(df.index):
        month_hover = []
        month_custom = []
        for hour_idx, hour in enumerate(df.columns):
            rate_value = df.iloc[month_idx, hour_idx]

            # Get TOU period information
            period_info = "N/A"
            if (
                schedule
                and month_idx < len(schedule)
                and hour_idx < len(schedule[month_idx])
            ):
                period_idx = schedule[month_idx][hour_idx]
                if energy_labels and period_idx < len(energy_labels):
                    period_info = energy_labels[period_idx]
                else:
                    period_info = f"Period {period_idx}"

            # Create rich hover text
            hover_info = (
                f"<b>{month}</b> - {hour:02d}:00<br>"
                f"<b>TOU Period:</b> {period_info}<br>"
                f"<b>Rate:</b> ${rate_value:.4f}/{unit}<br>"
                f"<span style='font-size: 0.9em; color: #6b7280;'>Click tile for details</span>"
            )
            month_hover.append(hover_info)
            month_custom.append([month, hour, rate_value, period_info])

        hover_text.append(month_hover)
        custom_data.append(month_custom)

    # Create the enhanced heatmap
    heatmap = go.Heatmap(
        z=df.values,
        x=[f"{h:02d}:00" for h in tariff_viewer.hours],
        y=df.index,
        colorscale=colorscale,
        showscale=True,
        hoverongaps=False,
        text=df.values.round(4) if text_size > 0 else None,
        texttemplate="<b>%{text}</b>" if text_size > 0 else None,
        textfont=(
            {
                "size": text_size,
                "color": "#1f2937" if not dark_mode else "#f1f5f9",
                "family": "Inter, sans-serif",
            }
            if text_size > 0
            else {}
        ),
        hovertemplate="%{customdata[0]}<extra></extra>",
        customdata=hover_text,
        colorbar=dict(
            title=dict(
                text=f"<b>{colorbar_title}</b>",
                font=dict(size=14, family="Inter, sans-serif"),
            ),
            thickness=25,
            len=0.7,
            outlinewidth=0,
            tickfont=dict(
                size=12,
                color="#0f172a" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
            tickformat=".4f",
            bgcolor=(
                "rgba(255, 255, 255, 0.9)" if not dark_mode else "rgba(15, 23, 42, 0.9)"
            ),
            bordercolor="#e5e7eb" if not dark_mode else "#374151",
            borderwidth=1,
        ),
        opacity=0.9,
    )

    fig.add_trace(heatmap)

    # Enhanced layout with modern styling
    fig.update_layout(
        title=dict(
            text=f'<b>{day_type} {title_suffix}</b><br><span style="font-size: 0.75em; color: #6b7280;">{tariff_viewer.utility_name} - {tariff_viewer.rate_name}</span>',
            font=dict(
                size=24,
                color="#0f172a" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        xaxis=dict(
            title=dict(
                text="<b>Hour of Day</b>",
                font=dict(
                    size=16,
                    color="#0f172a" if not dark_mode else "#f1f5f9",
                    family="Inter, sans-serif",
                ),
            ),
            tickfont=dict(
                size=12,
                color="#1f2937" if not dark_mode else "#cbd5e1",
                family="Inter, sans-serif",
            ),
            showgrid=True,
            gridwidth=1,
            gridcolor=(
                "rgba(229, 231, 235, 0.5)" if not dark_mode else "rgba(75, 85, 99, 0.5)"
            ),
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#e5e7eb" if not dark_mode else "#4b5563",
            tickangle=0,
            dtick=2,  # Show every 2 hours
        ),
        yaxis=dict(
            title=dict(
                text="<b>Month</b>",
                font=dict(
                    size=16,
                    color="#0f172a" if not dark_mode else "#f1f5f9",
                    family="Inter, sans-serif",
                ),
            ),
            tickfont=dict(
                size=12,
                color="#1f2937" if not dark_mode else "#cbd5e1",
                family="Inter, sans-serif",
            ),
            showgrid=True,
            gridwidth=1,
            gridcolor=(
                "rgba(229, 231, 235, 0.5)" if not dark_mode else "rgba(75, 85, 99, 0.5)"
            ),
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#e5e7eb" if not dark_mode else "#4b5563",
        ),
        plot_bgcolor=(
            "rgba(248, 250, 252, 0.8)" if not dark_mode else "rgba(15, 23, 42, 0.5)"
        ),
        paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
        margin=dict(l=80, r=100, t=120, b=80),
        height=chart_height,
        hoverlabel=dict(
            bgcolor=(
                "rgba(255, 255, 255, 0.95)"
                if not dark_mode
                else "rgba(30, 41, 59, 0.95)"
            ),
            font_size=13,
            font_family="Inter, sans-serif",
            bordercolor="#e5e7eb" if not dark_mode else "#475569",
            align="left",
        ),
        font=dict(family="Inter, sans-serif"),
        transition=dict(duration=300, easing="cubic-in-out"),
    )

    # Add subtle border around the heatmap
    fig.add_shape(
        type="rect",
        x0=-0.5,
        y0=-0.5,
        x1=23.5,
        y1=11.5,
        line=dict(color="#d1d5db" if not dark_mode else "#4b5563", width=2),
        fillcolor="rgba(0,0,0,0)",
    )

    return fig


def create_flat_demand_chart(
    tariff_viewer: TariffViewer, dark_mode: bool = False
) -> go.Figure:
    """
    Create a bar chart for flat demand rates.

    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        dark_mode (bool): Whether to use dark mode styling

    Returns:
        go.Figure: Plotly figure object
    """
    # Create gradient colors for bars based on rate values
    rates = tariff_viewer.flat_demand_df["Rate ($/kW)"].values
    max_rate = rates.max()
    min_rate = rates.min()

    # Create color gradient from green to red based on rate values
    colors = []
    for rate in rates:
        if max_rate > min_rate:
            intensity = (rate - min_rate) / (max_rate - min_rate)
        else:
            intensity = 0.5

        # Interpolate between bright green and bright red for light theme
        r = int(34 + (239 - 34) * intensity)  # Green to red
        g = int(197 + (68 - 197) * intensity)  # Green to red
        b = int(94 + (68 - 94) * intensity)  # Green to red
        colors.append(f"rgba({r}, {g}, {b}, 0.9)")

    fig = go.Figure(
        data=go.Bar(
            x=tariff_viewer.flat_demand_df.index,
            y=tariff_viewer.flat_demand_df["Rate ($/kW)"],
            text=[f"${rate:.4f}" for rate in rates],
            texttemplate="<b>%{text}</b>",
            textposition="outside",
            textfont=dict(
                size=12,
                color="#0f172a" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
            marker=dict(
                color=colors,
                line=dict(
                    color=(
                        "rgba(255, 255, 255, 0.8)"
                        if not dark_mode
                        else "rgba(15, 23, 42, 0.8)"
                    ),
                    width=2,
                ),
                opacity=0.9,
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<b>Flat Demand Rate:</b> $%{y:.4f}/kW<br>"
                "<span style='font-size: 0.9em; color: #6b7280;'>Monthly fixed rate</span>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text=f'<b>Seasonal/Monthly Demand Rates</b><br><span style="font-size: 0.75em; color: #6b7280;">{tariff_viewer.utility_name} - {tariff_viewer.rate_name}</span>',
            font=dict(
                size=24,
                color="#0f172a" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        xaxis=dict(
            title=dict(
                text="<b>Month</b>",
                font=dict(
                    size=16,
                    color="#0f172a" if not dark_mode else "#f1f5f9",
                    family="Inter, sans-serif",
                ),
            ),
            tickfont=dict(
                size=12,
                color="#1f2937" if not dark_mode else "#cbd5e1",
                family="Inter, sans-serif",
            ),
            showgrid=True,
            gridwidth=1,
            gridcolor=(
                "rgba(229, 231, 235, 0.5)" if not dark_mode else "rgba(75, 85, 99, 0.5)"
            ),
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#e5e7eb" if not dark_mode else "#4b5563",
        ),
        yaxis=dict(
            title=dict(
                text="<b>Demand Rate ($/kW)</b>",
                font=dict(
                    size=16,
                    color="#0f172a" if not dark_mode else "#f1f5f9",
                    family="Inter, sans-serif",
                ),
            ),
            tickfont=dict(
                size=12,
                color="#1f2937" if not dark_mode else "#cbd5e1",
                family="Inter, sans-serif",
            ),
            showgrid=True,
            gridwidth=1,
            gridcolor=(
                "rgba(229, 231, 235, 0.5)" if not dark_mode else "rgba(75, 85, 99, 0.5)"
            ),
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#e5e7eb" if not dark_mode else "#4b5563",
        ),
        plot_bgcolor=(
            "rgba(248, 250, 252, 0.8)" if not dark_mode else "rgba(15, 23, 42, 0.5)"
        ),
        paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
        margin=dict(l=80, r=70, t=120, b=70),
        height=DEFAULT_FLAT_DEMAND_HEIGHT,
        hoverlabel=dict(
            bgcolor=(
                "rgba(255, 255, 255, 0.95)"
                if not dark_mode
                else "rgba(30, 41, 59, 0.95)"
            ),
            font_size=13,
            font_family="Inter, sans-serif",
            bordercolor="#e5e7eb" if not dark_mode else "#475569",
            align="left",
        ),
        font=dict(family="Inter, sans-serif"),
        transition=dict(duration=300, easing="cubic-in-out"),
    )

    return fig


def create_load_duration_curve(
    load_profile_df: pd.DataFrame, dark_mode: bool = False
) -> go.Figure:
    """
    Create a load duration curve from load profile data.

    Args:
        load_profile_df (pd.DataFrame): Load profile DataFrame
        dark_mode (bool): Whether to use dark mode styling

    Returns:
        go.Figure: Plotly figure object
    """
    # Sort loads in descending order
    sorted_loads = (
        load_profile_df["load_kW"].sort_values(ascending=False).reset_index(drop=True)
    )

    # Calculate percentiles
    percentiles = np.arange(0, 100.1, 0.1)  # 0 to 100% in 0.1% increments
    duration_loads = np.percentile(sorted_loads, 100 - percentiles)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=percentiles,
            y=duration_loads,
            mode="lines",
            name="Load Duration Curve",
            line=dict(color="#1e40af" if not dark_mode else "#60a5fa", width=3),
            hovertemplate=(
                "<b>Duration:</b> %{x:.1f}%<br>"
                "<b>Load:</b> %{y:.2f} kW<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>Load Duration Curve</b>",
            font=dict(
                size=24,
                color="#0f172a" if not dark_mode else "#f1f5f9",
                family="Inter, sans-serif",
            ),
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(
            title=dict(
                text="<b>Percentage of Time (%)</b>",
                font=dict(
                    size=16,
                    color="#0f172a" if not dark_mode else "#f1f5f9",
                    family="Inter, sans-serif",
                ),
            ),
            tickfont=dict(
                size=12,
                color="#1f2937" if not dark_mode else "#cbd5e1",
                family="Inter, sans-serif",
            ),
            showgrid=True,
            gridwidth=1,
            gridcolor=(
                "rgba(229, 231, 235, 0.5)" if not dark_mode else "rgba(75, 85, 99, 0.5)"
            ),
        ),
        yaxis=dict(
            title=dict(
                text="<b>Load (kW)</b>",
                font=dict(
                    size=16,
                    color="#0f172a" if not dark_mode else "#f1f5f9",
                    family="Inter, sans-serif",
                ),
            ),
            tickfont=dict(
                size=12,
                color="#1f2937" if not dark_mode else "#cbd5e1",
                family="Inter, sans-serif",
            ),
            showgrid=True,
            gridwidth=1,
            gridcolor=(
                "rgba(229, 231, 235, 0.5)" if not dark_mode else "rgba(75, 85, 99, 0.5)"
            ),
        ),
        plot_bgcolor=(
            "rgba(248, 250, 252, 0.8)" if not dark_mode else "rgba(15, 23, 42, 0.5)"
        ),
        paper_bgcolor="#ffffff" if not dark_mode else "#0f172a",
        height=450,
        font=dict(family="Inter, sans-serif"),
    )

    return fig


def display_rate_statistics(tariff_viewer: TariffViewer) -> None:
    """
    Display rate statistics in a formatted layout.

    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    # Calculate statistics
    weekday_rates = tariff_viewer.weekday_df.values.flatten()
    weekend_rates = tariff_viewer.weekend_df.values.flatten()
    all_energy_rates = list(weekday_rates) + list(weekend_rates)
    all_energy_rates = [r for r in all_energy_rates if r > 0]  # Remove zero rates

    demand_weekday_rates = tariff_viewer.demand_weekday_df.values.flatten()
    demand_weekend_rates = tariff_viewer.demand_weekend_df.values.flatten()
    all_demand_rates = list(demand_weekday_rates) + list(demand_weekend_rates)
    all_demand_rates = [r for r in all_demand_rates if r > 0]  # Remove zero rates

    # Display energy rate statistics
    if all_energy_rates:
        st.markdown("#### ⚡ Energy Rate Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Lowest Rate", f"${min(all_energy_rates):.4f}/kWh")
        with col2:
            st.metric("Highest Rate", f"${max(all_energy_rates):.4f}/kWh")
        with col3:
            st.metric(
                "Average Rate",
                f"${sum(all_energy_rates)/len(all_energy_rates):.4f}/kWh",
            )
        with col4:
            st.metric(
                "Rate Spread",
                f"${max(all_energy_rates) - min(all_energy_rates):.4f}/kWh",
            )

    # Display demand rate statistics
    if all_demand_rates:
        st.markdown("#### 🔌 Demand Rate Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Lowest Rate", f"${min(all_demand_rates):.4f}/kW")
        with col2:
            st.metric("Highest Rate", f"${max(all_demand_rates):.4f}/kW")
        with col3:
            st.metric(
                "Average Rate", f"${sum(all_demand_rates)/len(all_demand_rates):.4f}/kW"
            )
        with col4:
            st.metric(
                "Rate Spread",
                f"${max(all_demand_rates) - min(all_demand_rates):.4f}/kW",
            )
