"""
Tariff modification management for the sidebar.

This module handles saving, resetting, and managing modified tariff data.
"""

import json

import streamlit as st

from urdb_viewer.config.settings import Settings


def render_tariff_modification_section() -> None:
    """Render the tariff modification management section in sidebar."""
    # Tariff save functionality
    if st.session_state.get("has_modifications", False):
        st.sidebar.markdown("### 💾 Save Modified Tariff")
        st.sidebar.success(
            "✏️ **Modified tariff** - Changes are not saved to original file"
        )

        if st.sidebar.button(
            "🔄 Reset to Original",
            help="Discard all changes and restore original tariff",
            use_container_width=True,
        ):
            _reset_tariff_modifications()
            st.rerun()

        if st.sidebar.button(
            "💾 Save As New File",
            type="primary",
            help="Save modified tariff as a new JSON file",
            use_container_width=True,
        ):
            st.session_state.show_save_dialog = True

        # Save dialog in sidebar
        if st.session_state.get("show_save_dialog", False):
            _render_save_dialog()

        st.sidebar.markdown("---")


def _reset_tariff_modifications() -> None:
    """Reset all tariff modifications to original values."""
    # Clear per-file modified state for the active tariff (if known)
    active_file = st.session_state.get("active_tariff_file")
    if active_file:
        modified_map = st.session_state.get("modified_tariffs_by_file", {})
        modified_map.pop(active_file, None)
        st.session_state.modified_tariffs_by_file = modified_map

    st.session_state.modified_tariff = None
    st.session_state.has_modifications = False

    # Clear energy form state to reload original values
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

    # Also clear form widget keys (Streamlit widgets persist values by key)
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


def _render_save_dialog() -> None:
    """Render the save dialog for modified tariffs."""
    st.sidebar.markdown("#### 💾 Save File")

    with st.sidebar.form("sidebar_save_tariff_form"):
        # Generate default filename - need to get current tariff info
        try:
            if st.session_state.get("modified_tariff"):
                if "items" in st.session_state.modified_tariff:
                    tariff_data = st.session_state.modified_tariff["items"][0]
                else:
                    tariff_data = st.session_state.modified_tariff

                utility_name = tariff_data.get("utility", "Unknown")
                rate_name = tariff_data.get("name", "Modified")
                default_name = f"{utility_name}_{rate_name}_Modified".replace(
                    " ", "_"
                ).replace("-", "_")
            else:
                default_name = "Modified_Tariff"

            # Clean filename by replacing invalid characters
            clean_default = "".join(
                c if c.isalnum() or c in "._-" else "_" for c in default_name
            )
        except Exception:
            clean_default = "Modified_Tariff"

        new_filename = st.text_input(
            "Filename:",
            value=clean_default,
            help="Enter a name for the new tariff file (without .json extension)",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", type="primary"):
                if new_filename.strip():
                    try:
                        # Clean filename
                        clean_filename = "".join(
                            c if c.isalnum() or c in "._-" else "_"
                            for c in new_filename.strip()
                        )
                        if not clean_filename.endswith(".json"):
                            clean_filename += ".json"

                        # Create user_data directory if it doesn't exist
                        Settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
                        filepath = Settings.USER_DATA_DIR / clean_filename

                        # Save the modified tariff
                        with open(filepath, "w") as f:
                            json.dump(
                                st.session_state.modified_tariff,
                                f,
                                indent=2,
                                ensure_ascii=False,
                            )

                        st.sidebar.success(f"✅ Saved as '{clean_filename}'!")
                        st.sidebar.info("🔄 Refresh to see in dropdown")
                        st.session_state.show_save_dialog = False

                    except Exception as e:
                        st.sidebar.error(f"❌ Error: {str(e)}")
                else:
                    st.sidebar.error("❌ Please enter a filename.")

        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_save_dialog = False
                st.rerun()
