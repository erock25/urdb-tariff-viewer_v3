"""
Streamlit app bootstrap and session-state helpers.

Keep Streamlit-coupled logic here so `urdb_viewer/main.py` can stay composition-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st

from urdb_viewer.config.settings import Settings
from urdb_viewer.models.tariff import (
    TariffViewer,
    create_temp_viewer_with_modified_tariff,
)
from urdb_viewer.utils.styling import apply_custom_css


def initialize_app(*, dark_mode: bool = False) -> None:
    """Initialize Streamlit page config, styling, directories, and session state."""
    st.set_page_config(**Settings.get_streamlit_config())
    apply_custom_css(dark_mode=dark_mode)
    Settings.ensure_directories_exist()

    if "modified_tariff" not in st.session_state:
        st.session_state.modified_tariff = None
    if "has_modifications" not in st.session_state:
        st.session_state.has_modifications = False


def load_tariff_viewer(selected_file: Path) -> Optional[TariffViewer]:
    """Load a TariffViewer, using in-memory modified tariff data when present."""
    try:
        if (
            st.session_state.get("has_modifications", False)
            and st.session_state.get("modified_tariff") is not None
        ):
            return create_temp_viewer_with_modified_tariff(
                st.session_state.modified_tariff
            )

        return TariffViewer(selected_file)
    except Exception as e:
        st.error(f"❌ Error loading tariff: {str(e)}")
        st.info("💡 **Troubleshooting Tips:**")
        st.info("• Check that the JSON file is properly formatted")
        st.info("• Ensure the file contains valid URDB tariff data")
        st.info("• Try selecting a different tariff file")
        return None


def handle_tariff_switching(current_tariff_file: Path) -> None:
    """Clear relevant session state when the user switches tariffs."""
    if (
        "last_tariff_file" in st.session_state
        and st.session_state.last_tariff_file == current_tariff_file
    ):
        return

    st.session_state.last_tariff_file = current_tariff_file

    # Clear form states when switching tariffs
    form_state_keys = [
        "form_labels",
        "form_rates",
        "form_adjustments",
        "demand_form_labels",
        "demand_form_rates",
        "demand_form_adjustments",
        "flat_demand_form_rates",
        "flat_demand_form_adjustments",
    ]

    for key in form_state_keys:
        if key in st.session_state:
            del st.session_state[key]

    # Clear modification state when switching tariffs (unless it's a user-generated tariff)
    if not str(current_tariff_file).startswith(str(Settings.USER_DATA_DIR)):
        st.session_state.modified_tariff = None
        st.session_state.has_modifications = False
