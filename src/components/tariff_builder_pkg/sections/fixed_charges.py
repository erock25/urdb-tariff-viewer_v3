"""
Fixed and flat demand charges section for tariff builder.

Handles flat (non-TOU) demand charges and fixed monthly charges.
"""

import streamlit as st
from typing import Dict, Any

from src.config.constants import MONTHS
from ..utils import get_tariff_data


def render_flat_demand_section() -> None:
    """Render the flat demand charges section."""
    st.markdown("### 📊 Flat Demand Charges")
    st.markdown("""
    Define monthly flat demand charges. These are demand charges that don't vary by time of day.
    """)
    
    data = get_tariff_data()
    
    demand_type = st.radio(
        "Flat Demand Structure",
        options=["Same for all months", "Seasonal (different rates for different months)"],
        help="How do flat demand charges vary?"
    )
    
    if demand_type == "Same for all months":
        _render_uniform_flat_demand(data)
    else:
        _render_seasonal_flat_demand(data)


def _render_uniform_flat_demand(data: Dict) -> None:
    """Render flat demand input for uniform (same for all months) rate."""
    col1, col2 = st.columns(2)
    
    with col1:
        rate = st.number_input(
            "Flat Demand Rate ($/kW)",
            min_value=0.0,
            max_value=100.0,
            value=data['flatdemandstructure'][0][0].get('rate', 0.0),
            format="%.4f",
            step=0.1,
            help="Monthly demand charge per kW"
        )
        data['flatdemandstructure'][0][0]['rate'] = rate
    
    with col2:
        adj = st.number_input(
            "Adjustment ($/kW)",
            min_value=-10.0,
            max_value=10.0,
            value=data['flatdemandstructure'][0][0].get('adj', 0.0),
            format="%.4f",
            step=0.1,
            help="Rate adjustment"
        )
        data['flatdemandstructure'][0][0]['adj'] = adj
    
    # Apply to all months
    data['flatdemandmonths'] = [0] * 12
    
    total_rate = rate + adj
    st.info(f"**Total Flat Demand Rate:** ${total_rate:.4f}/kW for all months")


def _render_seasonal_flat_demand(data: Dict) -> None:
    """Render flat demand inputs for seasonal rates."""
    st.markdown("#### Define Seasonal Demand Rates")
    
    num_seasons = st.number_input(
        "Number of Seasons",
        min_value=1,
        max_value=12,
        value=max(1, len(data.get('flatdemandstructure', [[]]))),
        help="e.g., 2 for summer/winter, 4 for quarterly"
    )
    
    # Adjust structure
    if len(data['flatdemandstructure']) != num_seasons:
        data['flatdemandstructure'] = [
            [{"rate": 0.0, "adj": 0.0}] 
            for _ in range(num_seasons)
        ]
    
    # Rate inputs for each season
    for i in range(num_seasons):
        with st.expander(f"Season {i}", expanded=(i == 0)):
            col1, col2 = st.columns(2)
            
            with col1:
                rate = st.number_input(
                    "Rate ($/kW)",
                    min_value=0.0,
                    value=data['flatdemandstructure'][i][0].get('rate', 0.0),
                    format="%.4f",
                    key=f"flat_demand_rate_{i}"
                )
                data['flatdemandstructure'][i][0]['rate'] = rate
            
            with col2:
                adj = st.number_input(
                    "Adjustment ($/kW)",
                    min_value=-10.0,
                    max_value=10.0,
                    value=data['flatdemandstructure'][i][0].get('adj', 0.0),
                    format="%.4f",
                    key=f"flat_demand_adj_{i}"
                )
                data['flatdemandstructure'][i][0]['adj'] = adj
    
    # Month assignments
    st.markdown("#### Assign Months to Seasons")
    st.markdown("Select which season applies to each month:")
    
    cols = st.columns(4)
    for month_idx, month in enumerate(MONTHS):
        with cols[month_idx % 4]:
            current_idx = data['flatdemandmonths'][month_idx] if month_idx < len(data['flatdemandmonths']) else 0
            season = st.selectbox(
                month,
                options=list(range(num_seasons)),
                format_func=lambda x: f"Season {x}",
                key=f"flat_demand_month_{month_idx}",
                index=min(current_idx, num_seasons - 1)
            )
            data['flatdemandmonths'][month_idx] = season


def render_fixed_charges_section() -> None:
    """Render the fixed charges section."""
    st.markdown("### 💰 Fixed Monthly Charges")
    st.markdown("Define fixed charges that are applied regardless of usage.")
    
    data = get_tariff_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fixed_charge = st.number_input(
            "Fixed Monthly Charge ($)",
            min_value=0.0,
            max_value=10000.0,
            value=data.get('fixedchargefirstmeter', 0.0),
            format="%.2f",
            step=1.0,
            help="Monthly customer charge or service charge"
        )
        data['fixedchargefirstmeter'] = fixed_charge
    
    with col2:
        charge_units = st.selectbox(
            "Charge Units",
            options=["$/month", "$/day", "$/year"],
            index=["$/month", "$/day", "$/year"].index(data.get('fixedchargeunits', '$/month')),
            help="How is the fixed charge billed?"
        )
        data['fixedchargeunits'] = charge_units
    
    st.info(f"**Total Fixed Charge:** ${fixed_charge:.2f} {charge_units}")

