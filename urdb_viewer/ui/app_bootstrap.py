"""
Streamlit app bootstrap and session-state helpers.

Keep Streamlit-coupled logic here so `urdb_viewer/main.py` can stay composition-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st

from urdb_viewer.components.rate_editor import get_tariff_identifier
from urdb_viewer.config.settings import Settings
from urdb_viewer.models.tariff import (
    TariffViewer,
    create_temp_viewer_with_modified_tariff,
)
from urdb_viewer.utils.helpers import extract_tariff_data
from urdb_viewer.utils.styling import apply_custom_css


def initialize_app() -> None:
    """Initialize Streamlit page config, styling, directories, and session state."""
    st.set_page_config(**Settings.get_streamlit_config())
    apply_custom_css()
    Settings.ensure_directories_exist()

    if "modified_tariff" not in st.session_state:
        st.session_state.modified_tariff = None
    if "has_modifications" not in st.session_state:
        st.session_state.has_modifications = False
    # Track modifications per-tariff-file so switching tariffs can't leak edits across files.
    # Key is `str(Path)` of the selected tariff file; value is the modified tariff JSON dict.
    if "modified_tariffs_by_file" not in st.session_state:
        st.session_state.modified_tariffs_by_file = {}
    # Convenience: current selected tariff file as string path (set in handle_tariff_switching).
    if "active_tariff_file" not in st.session_state:
        st.session_state.active_tariff_file = None


def load_tariff_viewer(selected_file: Path) -> Optional[TariffViewer]:
    """Load a TariffViewer, using in-memory modified tariff data when present."""
    try:
        # IMPORTANT:
        # Use modified tariff data whenever it exists, even if `has_modifications`
        # somehow got out of sync. This prevents UI sections from disagreeing about
        # which tariff data is the source of truth (e.g., editor shows modified,
        # table shows original).
        modified = st.session_state.get("modified_tariff")
        if modified is not None:
            # Safety: only use modified tariff data if it belongs to the currently
            # selected tariff file and appears to be the same tariff. If not, clear
            # it to avoid cross-tariff leakage.
            active_file = st.session_state.get("active_tariff_file")
            same_file = (not active_file) or (active_file == str(selected_file))
            try:
                modified_tariff = extract_tariff_data(modified)
                file_tariff = TariffViewer(selected_file).tariff
                same_tariff = get_tariff_identifier(
                    modified_tariff
                ) == get_tariff_identifier(file_tariff)
            except Exception:
                same_tariff = False

            if not same_file or not same_tariff:
                st.session_state.modified_tariff = None
                st.session_state.has_modifications = False
            else:
                st.session_state.has_modifications = True
                return create_temp_viewer_with_modified_tariff(modified)

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
    current_file_str = str(current_tariff_file)
    previous_file = st.session_state.get("last_tariff_file")
    previous_file_str = str(previous_file) if previous_file is not None else None

    # If the tariff didn't change, nothing to do.
    if previous_file is not None and previous_file == current_tariff_file:
        st.session_state.active_tariff_file = current_file_str
        return

    # Persist the outgoing tariff's modification state into the per-file map.
    modified_map = st.session_state.get("modified_tariffs_by_file", {})
    if previous_file_str:
        if (
            st.session_state.get("has_modifications", False)
            and st.session_state.get("modified_tariff") is not None
        ):
            modified_map[previous_file_str] = st.session_state.modified_tariff
        else:
            modified_map.pop(previous_file_str, None)

    st.session_state.modified_tariffs_by_file = modified_map

    # Load the incoming tariff's modification state from the per-file map.
    incoming_modified = modified_map.get(current_file_str)
    st.session_state.modified_tariff = incoming_modified
    st.session_state.has_modifications = incoming_modified is not None

    st.session_state.last_tariff_file = current_tariff_file
    st.session_state.active_tariff_file = current_file_str

    # Clear form states when switching tariffs
    form_state_keys = [
        "form_labels",
        "form_rates",
        "form_adjustments",
        "form_tariff_id",
        "demand_form_labels",
        "demand_form_rates",
        "demand_form_adjustments",
        "demand_form_tariff_id",
        "flat_demand_form_rates",
        "flat_demand_form_adjustments",
        "flat_demand_form_tariff_id",
    ]

    for key in form_state_keys:
        if key in st.session_state:
            del st.session_state[key]

    # Clear form widget keys (Streamlit widgets with keys persist values in session state)
    # These keys are dynamically created based on period index
    form_widget_prefixes = [
        "energy_rates_form_label_",
        "energy_rates_form_base_rate_",
        "energy_rates_form_adjustment_",
        "demand_rates_form_label_",
        "demand_rates_form_base_rate_",
        "demand_rates_form_adjustment_",
        "flat_demand_base_rate_",
        "flat_demand_adjustment_",
    ]

    keys_to_delete = [
        key
        for key in st.session_state.keys()
        if any(key.startswith(prefix) for prefix in form_widget_prefixes)
    ]

    for key in keys_to_delete:
        del st.session_state[key]

    # Note: we intentionally do NOT globally clear modification state here.
    # Instead, modifications are stored per-file in `modified_tariffs_by_file` and
    # restored for the active file above.
