"""
Preview and save section for tariff builder.

Handles tariff validation, JSON preview, and saving to file.
"""

import streamlit as st
from typing import Dict, Any

from ..utils import (
    get_tariff_data,
    validate_tariff,
    generate_filename,
    save_tariff,
    create_empty_tariff_structure,
)


def render_preview_and_save_section() -> None:
    """Render the preview and save section."""
    st.markdown("### 🔍 Preview & Save Tariff")
    st.markdown("Review your tariff configuration and save it as a JSON file.")
    
    data = st.session_state.tariff_builder_data
    tariff_data = data['items'][0]
    
    # Validation
    is_valid, validation_messages = validate_tariff(tariff_data)
    
    if not is_valid:
        st.error("❌ **Validation Issues:**")
        for msg in validation_messages:
            st.error(f"• {msg}")
        st.warning("⚠️ Please fix the issues above before saving.")
    else:
        st.success("✅ Tariff configuration is valid!")
    
    # Preview JSON
    with st.expander("📄 Preview JSON", expanded=False):
        st.json(data)
    
    # Summary
    _render_tariff_summary(tariff_data)
    
    # Save section
    _render_save_section(data, tariff_data, is_valid)
    
    # Reset button
    if st.button("🔄 Reset Form", help="Clear all data and start over"):
        st.session_state.tariff_builder_data = create_empty_tariff_structure()
        st.rerun()


def _render_tariff_summary(tariff_data: Dict) -> None:
    """Render a summary of the tariff configuration."""
    st.markdown("---")
    st.markdown("#### 📊 Tariff Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Utility", tariff_data.get('utility', 'N/A'))
        st.metric("Rate Name", tariff_data.get('name', 'N/A'))
    
    with col2:
        st.metric("Sector", tariff_data.get('sector', 'N/A'))
        st.metric("Energy Periods", len(tariff_data.get('energyratestructure', [])))
    
    with col3:
        st.metric("Fixed Charge", f"${tariff_data.get('fixedchargefirstmeter', 0):.2f}")
        has_tou_demand = len(tariff_data.get('demandratestructure', [])) > 0
        st.metric("TOU Demand", "Yes" if has_tou_demand else "No")


def _render_save_section(data: Dict, tariff_data: Dict, is_valid: bool) -> None:
    """Render the save section with filename input and save button."""
    st.markdown("---")
    st.markdown("#### 💾 Save Tariff")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filename = st.text_input(
            "Filename",
            value=generate_filename(tariff_data),
            help="Name for the JSON file (without .json extension)"
        )
    
    with col2:
        st.markdown("")  # Spacing
        st.markdown("")  # Spacing
        
        if st.button("💾 Save Tariff", type="primary", disabled=not is_valid, use_container_width=True):
            save_tariff(data, filename)

