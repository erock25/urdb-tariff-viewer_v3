"""
Load factor analysis UI components.

This module contains Streamlit UI rendering for the load factor analysis tool,
including input forms, results display, and visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from typing import Dict, Any, Optional, List, Set, Tuple

from src.models.tariff import TariffViewer
from src.utils.helpers import (
    get_active_energy_periods_for_month,
    get_active_demand_periods_for_month,
    get_active_energy_periods_for_year,
    get_active_demand_periods_for_year,
    calculate_period_hour_percentages,
    calculate_annual_period_hour_percentages,
)
from .calculations import (
    calculate_load_factor_rates,
    calculate_annual_load_factor_rates,
    calculate_comprehensive_breakdown,
    calculate_max_valid_load_factor,
)


# =============================================================================
# Constants
# =============================================================================

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

HOURS_IN_MONTH = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]


# =============================================================================
# Input UI Components
# =============================================================================

def render_rate_structure_info(tariff_data: Dict[str, Any]) -> None:
    """Display information about the tariff's rate structures."""
    has_tou_demand = bool(tariff_data.get('demandratestructure'))
    has_flat_demand = bool(tariff_data.get('flatdemandstructure'))
    has_energy_structure = bool(tariff_data.get('energyratestructure'))
    
    rate_structure_info = []
    if has_tou_demand:
        rate_structure_info.append("Time-of-Use Demand Charges")
    if has_flat_demand:
        rate_structure_info.append("Flat Monthly Demand Charges")
    if has_energy_structure:
        num_energy_periods = len(tariff_data.get('energyratestructure', []))
        if num_energy_periods == 1:
            rate_structure_info.append("Flat Energy Rate (no time-of-use periods)")
        else:
            rate_structure_info.append(f"{num_energy_periods} Time-of-Use Energy Periods")
    
    if rate_structure_info:
        st.info(f"📊 **This tariff includes:** {', '.join(rate_structure_info)}")
    else:
        st.warning("⚠️ No rate structure information found in this tariff.")


def render_analysis_period_selector() -> Tuple[str, int]:
    """
    Render the analysis period selection UI.
    
    Returns:
        Tuple of (analysis_period, selected_month)
    """
    analysis_period = st.radio(
        "📅 Analysis Period",
        options=["Single Month", "Full Year"],
        horizontal=True,
        help="Choose whether to analyze a single month or calculate annual effective rates"
    )
    
    if analysis_period == "Single Month":
        selected_month = st.selectbox(
            "Select Month",
            options=list(range(12)),
            format_func=lambda x: MONTH_NAMES[x],
            help="Select the month for which to calculate effective rates"
        )
    else:
        selected_month = 0  # Reference month for UI purposes
    
    return analysis_period, selected_month


def render_tou_demand_inputs(
    tariff_data: Dict[str, Any],
    analysis_period: str,
    selected_month: int,
    demand_period_month_counts: Dict[int, int]
) -> Tuple[Dict[str, float], Dict[int, int]]:
    """
    Render TOU demand input fields.
    
    Returns:
        Tuple of (demand_inputs dict, updated demand_period_month_counts)
    """
    st.markdown("##### ⚡ TOU Demand Charges")
    st.markdown("Specify the maximum demand (kW) for each TOU demand period:")
    
    demand_inputs = {}
    demand_labels = tariff_data.get('demandtoulabels', [])
    num_demand_periods = len(tariff_data['demandratestructure'])
    
    # Get active demand periods
    if analysis_period == "Single Month":
        active_demand_periods = get_active_demand_periods_for_month(tariff_data, selected_month)
        demand_period_month_counts = {p: 1 for p in active_demand_periods}
        
        if len(active_demand_periods) < num_demand_periods:
            inactive_periods = set(range(num_demand_periods)) - active_demand_periods
            inactive_labels = [demand_labels[i] if i < len(demand_labels) else f"Period {i}" 
                             for i in sorted(inactive_periods)]
            st.info(f"ℹ️ Only showing demand periods present in {MONTH_NAMES[selected_month]}. "
                   f"The following demand periods are not scheduled this month: {', '.join(inactive_labels)}")
    else:
        demand_period_month_counts = get_active_demand_periods_for_year(tariff_data)
        active_demand_periods = set(demand_period_month_counts.keys())
        
        if len(active_demand_periods) < num_demand_periods:
            st.info("ℹ️ Showing all demand periods active during the year.")
    
    active_demand_periods_list = sorted(list(active_demand_periods))
    
    if not active_demand_periods_list:
        st.warning("⚠️ No demand periods found in the schedule. Please check the tariff data.")
        return demand_inputs, demand_period_month_counts
    
    cols = st.columns(min(len(active_demand_periods_list), 3))
    for idx, i in enumerate(active_demand_periods_list):
        label = demand_labels[i] if i < len(demand_labels) else f"Demand Period {i}"
        rate = tariff_data['demandratestructure'][i][0].get('rate', 0)
        adj = tariff_data['demandratestructure'][i][0].get('adj', 0)
        total_rate = rate + adj
        
        month_info = ""
        if analysis_period == "Full Year":
            month_count = demand_period_month_counts.get(i, 0)
            month_info = f"\n({month_count} months)"
        
        with cols[idx % min(len(active_demand_periods_list), 3)]:
            demand_inputs[f'tou_demand_{i}'] = st.number_input(
                f"{label}{month_info}\n(${total_rate:.2f}/kW)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"lf_tou_demand_{i}_{analysis_period}",
                help=f"Base rate: ${rate:.2f}/kW" + (f" + Adjustment: ${adj:.2f}/kW" if adj != 0 else "") +
                     (f"\n\nActive in {demand_period_month_counts.get(i, 0)} months" if analysis_period == "Full Year" else "")
            )
    
    return demand_inputs, demand_period_month_counts


def render_flat_demand_inputs(
    tariff_data: Dict[str, Any],
    analysis_period: str,
    selected_month: int,
    demand_inputs: Dict[str, float],
    has_tou_demand: bool
) -> Dict[str, float]:
    """
    Render flat demand input fields.
    
    Returns:
        Updated demand_inputs dict
    """
    st.markdown("##### 📊 Flat Monthly Demand Charge")
    
    flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
    flat_structure = tariff_data['flatdemandstructure']
    
    if analysis_period == "Single Month":
        demand_inputs = _render_single_month_flat_demand(
            tariff_data, selected_month, demand_inputs, has_tou_demand,
            flatdemandmonths, flat_structure
        )
    else:
        demand_inputs = _render_annual_flat_demand(
            tariff_data, demand_inputs, has_tou_demand, flatdemandmonths, flat_structure
        )
    
    return demand_inputs


def _render_single_month_flat_demand(
    tariff_data: Dict[str, Any],
    selected_month: int,
    demand_inputs: Dict[str, float],
    has_tou_demand: bool,
    flatdemandmonths: List[int],
    flat_structure: list
) -> Dict[str, float]:
    """Render flat demand input for single month analysis."""
    flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
    
    if flat_tier < len(flat_structure):
        flat_rate = flat_structure[flat_tier][0].get('rate', 0)
        flat_adj = flat_structure[flat_tier][0].get('adj', 0)
    else:
        flat_rate = flat_structure[0][0].get('rate', 0)
        flat_adj = flat_structure[0][0].get('adj', 0)
    
    total_flat_rate = flat_rate + flat_adj
    
    help_text = f"Base rate: ${flat_rate:.2f}/kW" + (f" + Adjustment: ${flat_adj:.2f}/kW" if flat_adj != 0 else "")
    if len(flat_structure) > 1:
        help_text += f"\n\n(Rate for {MONTH_NAMES[selected_month]} - tier {flat_tier})"
    if has_tou_demand:
        help_text += "\n\nNote: If entered value is less than highest TOU demand, it will be auto-adjusted upward"
    
    flat_demand_value = st.number_input(
        f"Maximum Monthly Demand (${total_flat_rate:.2f}/kW)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="lf_flat_demand",
        help=help_text
    )
    
    demand_inputs = _apply_flat_demand_auto_adjust(
        demand_inputs, flat_demand_value, has_tou_demand
    )
    
    return demand_inputs


def _render_annual_flat_demand(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    has_tou_demand: bool,
    flatdemandmonths: List[int],
    flat_structure: list
) -> Dict[str, float]:
    """Render flat demand input for annual analysis."""
    tier_month_counts = {}
    for month_tier in flatdemandmonths:
        tier_month_counts[month_tier] = tier_month_counts.get(month_tier, 0) + 1
    
    if len(tier_month_counts) > 1:
        st.info(f"ℹ️ This tariff has {len(tier_month_counts)} different flat demand rate tiers across the year. "
                "Enter the same demand value for all tiers (will be applied to appropriate months).")
    
    flat_demand_value = st.number_input(
        "Maximum Monthly Demand (kW)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="lf_flat_demand_annual",
        help="This demand value will be applied to all months, but charged at the appropriate rate for each month"
    )
    
    demand_inputs = _apply_flat_demand_auto_adjust(
        demand_inputs, flat_demand_value, has_tou_demand
    )
    demand_inputs['_flat_tier_month_counts'] = tier_month_counts
    
    return demand_inputs


def _apply_flat_demand_auto_adjust(
    demand_inputs: Dict[str, float],
    flat_demand_value: float,
    has_tou_demand: bool
) -> Dict[str, float]:
    """Auto-adjust flat demand to be at least max TOU demand."""
    if has_tou_demand:
        tou_demands = [v for k, v in demand_inputs.items() 
                       if k.startswith('tou_demand_') and isinstance(v, (int, float)) and v > 0]
        if tou_demands:
            max_tou_demand = max(tou_demands)
            if flat_demand_value == 0:
                st.info(f"ℹ️ Note: Flat demand automatically set to {max_tou_demand:.1f} kW to match the highest TOU demand.")
                demand_inputs['flat_demand'] = max_tou_demand
            elif flat_demand_value < max_tou_demand:
                st.info(f"ℹ️ Note: Flat demand ({flat_demand_value:.1f} kW) is less than highest TOU demand "
                        f"({max_tou_demand:.1f} kW). Using {max_tou_demand:.1f} kW for calculations.")
                demand_inputs['flat_demand'] = max_tou_demand
            else:
                demand_inputs['flat_demand'] = flat_demand_value
        else:
            demand_inputs['flat_demand'] = flat_demand_value
    else:
        demand_inputs['flat_demand'] = flat_demand_value
    
    return demand_inputs


def render_energy_distribution_inputs(
    tariff_data: Dict[str, Any],
    analysis_period: str,
    selected_month: int
) -> Tuple[Dict[int, float], float, List[int], Dict[int, float], Dict[int, int]]:
    """
    Render energy distribution input fields.
    
    Returns:
        Tuple of (energy_percentages, total_percentage, active_periods_list, 
                  period_hour_percentages, energy_period_month_counts)
    """
    st.markdown("##### 💡 Energy Distribution")
    
    energy_structure = tariff_data.get('energyratestructure', [])
    energy_labels = tariff_data.get('energytoulabels', [])
    num_energy_periods = len(energy_structure)
    
    # Get active periods based on analysis period
    if analysis_period == "Single Month":
        active_periods = get_active_energy_periods_for_month(tariff_data, selected_month)
        period_hour_percentages = calculate_period_hour_percentages(tariff_data, selected_month)
        energy_period_month_counts = {p: 1 for p in active_periods}
        time_label = f"{MONTH_NAMES[selected_month]}'s hours"
        
        if len(active_periods) < num_energy_periods:
            inactive_periods = set(range(num_energy_periods)) - active_periods
            inactive_labels = [energy_labels[i] if i < len(energy_labels) else f"Period {i}" 
                             for i in sorted(inactive_periods)]
            st.info(f"ℹ️ Only showing periods present in {MONTH_NAMES[selected_month]}. "
                   f"The following periods are not scheduled this month: {', '.join(inactive_labels)}")
    else:
        energy_period_month_counts = get_active_energy_periods_for_year(tariff_data)
        active_periods = set(energy_period_month_counts.keys())
        period_hour_percentages = calculate_annual_period_hour_percentages(tariff_data)
        time_label = "year's hours"
        
        if len(active_periods) < num_energy_periods:
            st.info("ℹ️ Showing all energy periods active during the year.")
    
    st.markdown("Specify the percentage of energy consumption in each rate period (must sum to 100%):")
    st.caption("💡 **Note:** Your energy distribution determines the maximum **physically possible** load factor. "
               "For each period, the constraint is: LF ≤ (hour %) / (energy %). Example: if a period represents 20% "
               "of hours but you allocate 40% of energy there, max LF = 50%.")
    
    energy_percentages = {}
    total_percentage = 0.0
    active_periods_list = sorted(list(active_periods))
    
    # Fallback if no periods found
    if not active_periods_list and num_energy_periods > 0:
        st.warning(f"⚠️ No energy periods found in the schedule. Using all {num_energy_periods} period(s) from energy rate structure.")
        active_periods_list = list(range(num_energy_periods))
        if not period_hour_percentages:
            period_hour_percentages = {i: 100.0 / num_energy_periods for i in range(num_energy_periods)}
    
    if not active_periods_list:
        st.error("⚠️ No energy rate structure found in this tariff.")
        return energy_percentages, total_percentage, active_periods_list, period_hour_percentages, energy_period_month_counts
    
    cols = st.columns(min(len(active_periods_list), 3))
    for idx, i in enumerate(active_periods_list):
        label = energy_labels[i] if i < len(energy_labels) else f"Energy Period {i}"
        rate = energy_structure[i][0].get('rate', 0)
        adj = energy_structure[i][0].get('adj', 0)
        total_rate = rate + adj
        hour_pct = period_hour_percentages.get(i, 0)
        
        with cols[idx % min(len(active_periods_list), 3)]:
            st.caption(f"📊 {hour_pct:.1f}% of {time_label}")
            
            default_value = 100.0 if idx == 0 else 0.0
            
            help_text = f"Base rate: ${rate:.4f}/kWh" + (f" + Adjustment: ${adj:.4f}/kWh" if adj != 0 else "")
            help_text += f"\n\nThis period is present for {hour_pct:.1f}% of {time_label}"
            if analysis_period == "Full Year":
                month_count = energy_period_month_counts.get(i, 0)
                help_text += f"\nActive in {month_count} months"
            
            energy_percentages[i] = st.number_input(
                f"{label}\n(${total_rate:.4f}/kWh)",
                min_value=0.0,
                max_value=100.0,
                value=default_value,
                step=1.0,
                key=f"lf_energy_pct_{i}_{analysis_period}",
                help=help_text
            )
            total_percentage += energy_percentages[i]
    
    # Show percentage total
    percentage_color = "green" if abs(total_percentage - 100.0) < 0.01 else "red"
    st.markdown(f"**Total: <span style='color:{percentage_color}'>{total_percentage:.1f}%</span>**", 
                unsafe_allow_html=True)
    
    if abs(total_percentage - 100.0) >= 0.01:
        st.warning("⚠️ Energy percentages must sum to 100%")
    
    return energy_percentages, total_percentage, active_periods_list, period_hour_percentages, energy_period_month_counts


# =============================================================================
# Results Display Components
# =============================================================================

def display_load_factor_results(
    results: pd.DataFrame,
    options: Dict[str, Any],
    tariff_data: Optional[Dict[str, Any]] = None,
    demand_inputs: Optional[Dict[str, float]] = None,
    energy_percentages: Optional[Dict[int, float]] = None,
    selected_month: Optional[int] = 0,
    has_tou_demand: bool = False,
    has_flat_demand: bool = False,
    analysis_period: str = "Single Month",
    demand_period_month_counts: Optional[Dict[int, int]] = None,
    energy_period_month_counts: Optional[Dict[int, int]] = None
) -> None:
    """
    Display load factor analysis results.
    
    Args:
        results: DataFrame with analysis results
        options: Display options
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values
        energy_percentages: Dictionary of energy percentages
        selected_month: Month index (0-11, or None for annual)
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        analysis_period: "Single Month" or "Full Year"
        demand_period_month_counts: Dict mapping demand period to # months active
        energy_period_month_counts: Dict mapping energy period to # months active
    """
    st.markdown("### 📊 Load Factor Analysis Results")
    
    if results['Peak Demand (kW)'].iloc[0] == 0:
        st.warning("⚠️ No demand values specified. Please enter at least one demand value to calculate effective rates.")
        return
    
    # Display summary metrics
    _display_summary_metrics(results)
    
    st.markdown("---")
    
    # Display results table
    _display_results_table(results)
    
    # Visualization
    comprehensive_df = None
    if tariff_data is not None and demand_inputs is not None and energy_percentages is not None:
        comprehensive_df = calculate_comprehensive_breakdown(
            results=results,
            tariff_data=tariff_data,
            demand_inputs=demand_inputs,
            energy_percentages=energy_percentages,
            selected_month=selected_month,
            has_tou_demand=has_tou_demand,
            has_flat_demand=has_flat_demand,
            analysis_period=analysis_period,
            demand_period_month_counts=demand_period_month_counts,
            energy_period_month_counts=energy_period_month_counts
        )
    
    _display_chart(results, options, tariff_data, comprehensive_df)
    
    # Comprehensive breakdown table
    if comprehensive_df is not None:
        _display_comprehensive_table(
            comprehensive_df, tariff_data, has_tou_demand, has_flat_demand, analysis_period
        )


def _display_summary_metrics(results: pd.DataFrame) -> None:
    """Display summary metrics cards."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        peak_demand = results['Peak Demand (kW)'].iloc[0]
        st.metric("Peak Demand", f"{peak_demand:.1f} kW")
    
    with col2:
        min_rate = results['Effective Rate ($/kWh)'].min()
        min_lf = results.loc[results['Effective Rate ($/kWh)'].idxmin(), 'Load Factor']
        st.metric("Lowest Effective Rate", f"${min_rate:.4f}/kWh", delta=f"at {min_lf}")
    
    with col3:
        max_rate = results['Effective Rate ($/kWh)'].max()
        max_lf = results.loc[results['Effective Rate ($/kWh)'].idxmax(), 'Load Factor']
        st.metric("Highest Effective Rate", f"${max_rate:.4f}/kWh", delta=f"at {max_lf}")


def _display_results_table(results: pd.DataFrame) -> None:
    """Display the detailed results table with download button."""
    st.markdown("#### 📋 Detailed Results Table")
    
    display_df = results[[
        'Load Factor', 'Average Load (kW)', 'Total Energy (kWh)', 
        'Demand Charges ($)', 'Energy Charges ($)', 'Fixed Charges ($)', 
        'Total Cost ($)', 'Effective Rate ($/kWh)'
    ]].copy()
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Load Factor": st.column_config.TextColumn("Load Factor", width="small"),
            "Average Load (kW)": st.column_config.NumberColumn("Avg Load (kW)", format="%.2f"),
            "Total Energy (kWh)": st.column_config.NumberColumn("Total Energy (kWh)", format="%.0f"),
            "Demand Charges ($)": st.column_config.NumberColumn("Demand ($)", format="$%.2f"),
            "Energy Charges ($)": st.column_config.NumberColumn("Energy ($)", format="$%.2f"),
            "Fixed Charges ($)": st.column_config.NumberColumn("Fixed ($)", format="$%.2f"),
            "Total Cost ($)": st.column_config.NumberColumn("Total ($)", format="$%.2f"),
            "Effective Rate ($/kWh)": st.column_config.NumberColumn("Effective Rate", format="$%.4f")
        }
    )
    
    # Download button
    excel_data = _create_results_excel(display_df)
    st.download_button(
        label="📥 Download Detailed Results as Excel",
        data=excel_data,
        file_name="load_factor_detailed_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_detailed_results"
    )


def _create_results_excel(display_df: pd.DataFrame) -> bytes:
    """Create Excel file from results DataFrame."""
    from openpyxl.styles import numbers
    
    buffer = BytesIO()
    excel_df = display_df.copy()
    
    if 'Load Factor' in excel_df.columns:
        excel_df['Load Factor'] = excel_df['Load Factor'].str.replace('%', '').astype(float) / 100
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        excel_df.to_excel(writer, sheet_name='Load Factor Analysis', index=False)
        worksheet = writer.sheets['Load Factor Analysis']
        headers = list(excel_df.columns)
        
        for col_idx, col_name in enumerate(headers, start=1):
            for row_idx in range(2, len(excel_df) + 2):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                
                if col_name == 'Load Factor':
                    cell.number_format = '0%'
                elif col_name in ['Demand Charges ($)', 'Energy Charges ($)', 'Fixed Charges ($)', 'Total Cost ($)']:
                    cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
                elif col_name == 'Effective Rate ($/kWh)':
                    cell.number_format = '_($* #,##0.0000_);_($* (#,##0.0000);_($* "-"????_);_(@_)'
                elif col_name == 'Total Energy (kWh)':
                    cell.number_format = '#,##0'
                elif col_name == 'Average Load (kW)':
                    cell.number_format = '#,##0'
    
    buffer.seek(0)
    return buffer.getvalue()


def _display_chart(
    results: pd.DataFrame,
    options: Dict[str, Any],
    tariff_data: Optional[Dict[str, Any]],
    comprehensive_df: Optional[pd.DataFrame]
) -> None:
    """Display the effective rate vs load factor chart."""
    st.markdown("#### 📈 Effective Rate vs Load Factor")
    
    dark_mode = options.get('dark_mode', False)
    
    fig = go.Figure()
    
    # Effective rate line
    fig.add_trace(go.Scatter(
        x=results['Load Factor Value'] * 100,
        y=results['Effective Rate ($/kWh)'],
        mode='lines+markers',
        name='Effective Rate ($/kWh)',
        line=dict(color='rgba(59, 130, 246, 0.8)', width=3),
        marker=dict(size=10),
        yaxis='y1',
        hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Effective Rate: $%{y:.4f}/kWh<extra></extra>"
    ))
    
    # Add energy period breakdown bars if available
    if comprehensive_df is not None and tariff_data is not None:
        _add_energy_breakdown_bars(fig, results, tariff_data, comprehensive_df)
    else:
        fig.add_trace(go.Bar(
            x=results['Load Factor Value'] * 100,
            y=results['Energy Charges ($)'],
            name='Energy Charges',
            marker_color='rgba(34, 197, 94, 0.7)',
            yaxis='y2',
            hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Energy: $%{y:.2f}<extra></extra>"
        ))
    
    # Demand and fixed charges
    fig.add_trace(go.Bar(
        x=results['Load Factor Value'] * 100,
        y=results['Demand Charges ($)'],
        name='Demand Charges',
        marker_color='rgba(249, 115, 22, 0.7)',
        yaxis='y2',
        hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Demand: $%{y:.2f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        x=results['Load Factor Value'] * 100,
        y=results['Fixed Charges ($)'],
        name='Fixed Charges',
        marker_color='rgba(156, 163, 175, 0.7)',
        yaxis='y2',
        hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Fixed: $%{y:.2f}<extra></extra>"
    ))
    
    _apply_chart_layout(fig, dark_mode)
    st.plotly_chart(fig, use_container_width=True)


def _add_energy_breakdown_bars(
    fig: go.Figure,
    results: pd.DataFrame,
    tariff_data: Dict[str, Any],
    comprehensive_df: pd.DataFrame
) -> None:
    """Add energy period breakdown bars to the chart."""
    energy_structure = tariff_data.get('energyratestructure', [])
    energy_labels = tariff_data.get('energyweekdaylabels', [])
    
    energy_colors = [
        'rgba(34, 197, 94, 0.9)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(5, 150, 105, 0.7)',
        'rgba(132, 204, 22, 0.7)',
        'rgba(101, 163, 13, 0.7)',
        'rgba(74, 222, 128, 0.6)',
        'rgba(22, 163, 74, 0.6)',
        'rgba(187, 247, 208, 0.7)',
    ]
    
    for period_idx in range(len(energy_structure)):
        period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
        cost_col = f'{period_label} Cost ($)'
        
        if cost_col in comprehensive_df.columns:
            color_idx = period_idx % len(energy_colors)
            fig.add_trace(go.Bar(
                x=results['Load Factor Value'] * 100,
                y=comprehensive_df[cost_col],
                name=f'{period_label} Energy',
                marker_color=energy_colors[color_idx],
                yaxis='y2',
                hovertemplate=f"<b>Load Factor: %{{x:.0f}}%</b><br>{period_label}: $%{{y:.2f}}<extra></extra>"
            ))


def _apply_chart_layout(fig: go.Figure, dark_mode: bool) -> None:
    """Apply layout styling to the chart."""
    fig.update_layout(
        title=dict(
            text="Effective Rate and Cost Breakdown by Load Factor",
            font=dict(size=18, color='#1f2937' if not dark_mode else '#f1f5f9')
        ),
        xaxis=dict(
            title=dict(
                text="Load Factor (%)",
                font=dict(color='#1f2937' if not dark_mode else '#f1f5f9')
            ),
            tickfont=dict(color='#1f2937' if not dark_mode else '#f1f5f9'),
            tickmode='array',
            tickvals=[1, 5, 10, 20, 30, 50, 100]
        ),
        yaxis=dict(
            title=dict(
                text="Effective Rate ($/kWh)",
                font=dict(color='rgba(59, 130, 246, 0.8)')
            ),
            tickfont=dict(color='rgba(59, 130, 246, 0.8)'),
            side='left'
        ),
        yaxis2=dict(
            title=dict(
                text="Cost ($)",
                font=dict(color='#1f2937' if not dark_mode else '#f1f5f9')
            ),
            tickfont=dict(color='#1f2937' if not dark_mode else '#f1f5f9'),
            overlaying='y',
            side='right'
        ),
        barmode='stack',
        height=500,
        showlegend=True,
        legend=dict(
            font=dict(color='#1f2937' if not dark_mode else '#f1f5f9'),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
        paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
        font=dict(family="Inter, sans-serif", color='#1f2937' if not dark_mode else '#f1f5f9')
    )


def _display_comprehensive_table(
    comprehensive_df: pd.DataFrame,
    tariff_data: Dict[str, Any],
    has_tou_demand: bool,
    has_flat_demand: bool,
    analysis_period: str
) -> None:
    """Display the comprehensive breakdown table."""
    st.markdown("---")
    st.markdown("#### 📊 Comprehensive Breakdown Table")
    
    if analysis_period == "Single Month":
        st.caption("This table shows all load factors with detailed breakdowns by energy rate period and demand period.")
    else:
        st.caption("This table shows all load factors with detailed breakdowns for the full year. "
                   "The '# Months' columns indicate how many months each period/tier is active.")
    
    column_config = _build_comprehensive_column_config(tariff_data, has_tou_demand, has_flat_demand)
    
    st.dataframe(
        comprehensive_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        height=min(400, 35 * len(comprehensive_df) + 38)
    )
    
    # Download button
    excel_data = _create_comprehensive_excel(comprehensive_df)
    st.download_button(
        label="📥 Download Comprehensive Breakdown as Excel",
        data=excel_data,
        file_name="load_factor_comprehensive_breakdown.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_comprehensive_breakdown"
    )


def _build_comprehensive_column_config(
    tariff_data: Dict[str, Any],
    has_tou_demand: bool,
    has_flat_demand: bool
) -> Dict[str, Any]:
    """Build column configuration for comprehensive table."""
    column_config = {
        "Load Factor": st.column_config.TextColumn("Load Factor", width="small"),
        "Average Load (kW)": st.column_config.NumberColumn("Avg Load (kW)", format="%.2f"),
        "Total Energy (kWh)": st.column_config.NumberColumn("Total Energy (kWh)", format="%.0f")
    }
    
    # Energy period columns
    energy_structure = tariff_data.get('energyratestructure', [])
    energy_labels = tariff_data.get('energyweekdaylabels', [])
    
    for period_idx in range(len(energy_structure)):
        period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
        column_config[f'{period_label} (kWh)'] = st.column_config.NumberColumn(
            f'{period_label} (kWh)', format="%.0f", width="small")
        column_config[f'{period_label} Rate ($/kWh)'] = st.column_config.NumberColumn(
            f'{period_label} Rate ($/kWh)', format="$%.4f", width="small")
        column_config[f'{period_label} Cost ($)'] = st.column_config.NumberColumn(
            f'{period_label} Cost ($)', format="$%.2f", width="small")
    
    # TOU demand columns
    if has_tou_demand:
        demand_structure = tariff_data.get('demandratestructure', [])
        demand_labels = tariff_data.get('demandtoulabels', [])
        for i in range(len(demand_structure)):
            period_label = demand_labels[i] if i < len(demand_labels) else f"TOU Period {i}"
            column_config[f'{period_label} Demand (kW)'] = st.column_config.NumberColumn(
                f'{period_label} Demand (kW)', format="%.2f", width="small")
            column_config[f'{period_label} Rate ($/kW)'] = st.column_config.NumberColumn(
                f'{period_label} Rate ($/kW)', format="$%.2f", width="small")
            column_config[f'{period_label} Demand Cost ($)'] = st.column_config.NumberColumn(
                f'{period_label} Demand Cost ($)', format="$%.2f", width="small")
    
    # Flat demand columns
    if has_flat_demand:
        column_config['Flat Demand (kW)'] = st.column_config.NumberColumn(
            'Flat Demand (kW)', format="%.2f", width="small")
        column_config['Flat Demand Rate ($/kW)'] = st.column_config.NumberColumn(
            'Flat Demand Rate ($/kW)', format="$%.2f", width="small")
        column_config['Flat Demand Cost ($)'] = st.column_config.NumberColumn(
            'Flat Demand Cost ($)', format="$%.2f", width="small")
    
    # Summary columns
    column_config['Total Demand Charges ($)'] = st.column_config.NumberColumn('Total Demand ($)', format="$%.2f")
    column_config['Total Energy Charges ($)'] = st.column_config.NumberColumn('Total Energy ($)', format="$%.2f")
    column_config['Fixed Charges ($)'] = st.column_config.NumberColumn('Fixed ($)', format="$%.2f")
    column_config['Total Cost ($)'] = st.column_config.NumberColumn('Total Cost ($)', format="$%.2f")
    column_config['Effective Rate ($/kWh)'] = st.column_config.NumberColumn('Effective Rate ($/kWh)', format="$%.4f")
    
    return column_config


def _create_comprehensive_excel(comprehensive_df: pd.DataFrame) -> bytes:
    """Create Excel file from comprehensive breakdown DataFrame."""
    from openpyxl.styles import numbers
    
    buffer = BytesIO()
    excel_df = comprehensive_df.copy()
    
    if 'Load Factor' in excel_df.columns:
        excel_df['Load Factor'] = excel_df['Load Factor'].str.replace('%', '').astype(float) / 100
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        excel_df.to_excel(writer, sheet_name='Comprehensive Breakdown', index=False)
        worksheet = writer.sheets['Comprehensive Breakdown']
        headers = list(excel_df.columns)
        
        for col_idx, col_name in enumerate(headers, start=1):
            for row_idx in range(2, len(excel_df) + 2):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                
                if col_name == 'Load Factor':
                    cell.number_format = '0%'
                elif col_name.endswith('Rate ($/kW)') or '($/kW)' in col_name:
                    cell.number_format = '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'
                elif col_name.endswith('Rate ($/kWh)') or col_name == 'Effective Rate ($/kWh)':
                    cell.number_format = '_($* #,##0.0000_);_($* (#,##0.0000);_($* "-"????_);_(@_)'
                elif col_name.endswith('Cost ($)') or col_name.endswith('Charges ($)') or col_name == 'Total Cost ($)':
                    cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
                elif col_name.endswith('(kWh)') or col_name == 'Total Energy (kWh)':
                    cell.number_format = '#,##0'
                elif col_name.endswith('(kW)') or col_name == 'Average Load (kW)':
                    cell.number_format = '#,##0'
    
    buffer.seek(0)
    return buffer.getvalue()

