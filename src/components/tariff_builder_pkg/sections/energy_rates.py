"""
Energy rates section for tariff builder.

Handles TOU energy rate period configuration.
"""

import streamlit as st
from typing import Dict, Any

from ..utils import get_tariff_data, show_section_validation


def render_energy_rates_section() -> None:
    """Render the energy rates section of the tariff builder."""
    st.markdown("### ⚡ Energy Rate Structure")
    st.markdown("""
    Define your Time-of-Use (TOU) energy rate periods. Each period represents a different 
    energy rate (e.g., Summer/Winter On-Peak, Off-Peak, Super Off-Peak).
    """)
    
    data = get_tariff_data()
    
    # Number of TOU periods (outside form, as it restructures data)
    num_periods = st.number_input(
        "Number of TOU Periods",
        min_value=1,
        max_value=12,
        value=len(data.get('energyratestructure', [{}])),
        help="How many different rate periods do you have? (e.g., 3 for Peak/Mid-Peak/Off-Peak)"
    )
    
    # Adjust arrays based on number of periods
    if len(data['energyratestructure']) != num_periods:
        data['energyratestructure'] = [
            [{"unit": "kWh", "rate": 0.0, "adj": 0.0}] 
            for _ in range(num_periods)
        ]
        data['energytoulabels'] = [f"Period {i}" for i in range(num_periods)]
    
    st.markdown("---")
    
    form_key = f"energy_rates_form_{num_periods}_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        period_data = []
        for i in range(num_periods):
            st.markdown(f"#### ⚡ TOU Period {i}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                label = st.text_input(
                    "Period Label",
                    value=data['energytoulabels'][i],
                    help="e.g., 'Peak', 'Off-Peak', 'Super Off-Peak'",
                    key=f"energy_label_{i}"
                )
            
            with col2:
                rate = st.number_input(
                    "Base Rate ($/kWh)",
                    min_value=0.0,
                    max_value=10.0,
                    value=data['energyratestructure'][i][0].get('rate', 0.0),
                    format="%.5f",
                    step=0.001,
                    help="Base energy rate in dollars per kWh",
                    key=f"energy_rate_{i}"
                )
            
            with col3:
                adj = st.number_input(
                    "Adjustment ($/kWh)",
                    min_value=-1.0,
                    max_value=1.0,
                    value=data['energyratestructure'][i][0].get('adj', 0.0),
                    format="%.5f",
                    step=0.001,
                    help="Rate adjustment (can be negative)",
                    key=f"energy_adj_{i}"
                )
            
            total_rate = rate + adj
            st.caption(f"**Total Rate:** ${total_rate:.5f}/kWh")
            
            period_data.append({'label': label, 'rate': rate, 'adj': adj})
            
            if i < num_periods - 1:
                st.markdown("---")
        
        st.markdown("---")
        comments = st.text_area(
            "Energy Rate Comments (optional)",
            value=data.get('energycomments', ''),
            help="Additional notes about energy rates, adjustments, or special conditions"
        )
        
        submitted = st.form_submit_button("✅ Apply Changes", type="primary", use_container_width=True)
        
        if submitted:
            for i, pd in enumerate(period_data):
                data['energytoulabels'][i] = pd['label']
                data['energyratestructure'][i][0]['rate'] = pd['rate']
                data['energyratestructure'][i][0]['adj'] = pd['adj']
            data['energycomments'] = comments
            st.success("✓ Energy rates updated!")
    
    show_section_validation("energy_rates", data)

