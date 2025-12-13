"""
Load profile analysis UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from urdb_viewer.services.file_service import FileService
from urdb_viewer.ui.cached import validate_load_profile
from urdb_viewer.utils.styling import create_section_header_html


def render_load_profile_analysis_tab(
    selected_load_profile: Optional[Path], options: Dict[str, Any]
) -> None:
    """Render the load profile analysis tab."""
    st.markdown(
        create_section_header_html("📊 Load Profile Analysis"), unsafe_allow_html=True
    )

    if not selected_load_profile:
        st.info("ℹ️ Select a load profile from the sidebar to analyze.")
        return

    try:
        validation_results = validate_load_profile(selected_load_profile)

        if validation_results["is_valid"]:
            profile_df = FileService.load_csv_file(selected_load_profile)

            # Reuse existing analysis renderer
            from urdb_viewer.components.load_generator import show_load_profile_analysis

            show_load_profile_analysis(profile_df, options)
            return

        st.error("❌ Invalid load profile file")
        for error in validation_results.get("errors", []):
            st.error(f"• {error}")

    except Exception as e:
        st.error(f"❌ Error analyzing load profile: {str(e)}")
