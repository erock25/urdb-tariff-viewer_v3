"""
Shared rate editing component for URDB Tariff Viewer.

This module provides a reusable rate editing form component that can be used
for energy rates, demand rates, and flat demand rates.
"""

import copy
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from urdb_viewer.config.constants import MONTHS_FULL
from urdb_viewer.models.tariff import TariffViewer
from urdb_viewer.utils.helpers import extract_tariff_data


class RateEditorConfig:
    """Configuration for the rate editor component."""

    def __init__(
        self,
        rate_type: str,
        form_key: str,
        session_prefix: str,
        labels_key: str,
        rates_key: str,
        rate_unit: str = "$/kWh",
        default_label_prefix: str = "Period",
    ):
        """
        Initialize rate editor configuration.

        Args:
            rate_type: Type of rate ("energy", "demand", or "flat_demand")
            form_key: Unique key for the Streamlit form
            session_prefix: Prefix for session state keys
            labels_key: Key in tariff data for rate labels
            rates_key: Key in tariff data for rate structure
            rate_unit: Unit string for display (e.g., "$/kWh" or "$/kW")
            default_label_prefix: Prefix for auto-generated labels
        """
        self.rate_type = rate_type
        self.form_key = form_key
        self.session_prefix = session_prefix
        self.labels_key = labels_key
        self.rates_key = rates_key
        self.rate_unit = rate_unit
        self.default_label_prefix = default_label_prefix


# Pre-configured rate editor settings
ENERGY_RATE_CONFIG = RateEditorConfig(
    rate_type="energy",
    form_key="energy_rates_form",
    session_prefix="form",
    labels_key="energytoulabels",
    rates_key="energyratestructure",
    rate_unit="$/kWh",
    default_label_prefix="Period",
)

DEMAND_RATE_CONFIG = RateEditorConfig(
    rate_type="demand",
    form_key="demand_rates_form",
    session_prefix="demand_form",
    labels_key="demandlabels",
    rates_key="demandratestructure",
    rate_unit="$/kW",
    default_label_prefix="Demand Period",
)

FLAT_DEMAND_RATE_CONFIG = RateEditorConfig(
    rate_type="flat_demand",
    form_key="flat_demand_rates_form",
    session_prefix="flat_demand_form",
    labels_key=None,  # Flat demand uses months as labels
    rates_key="flatdemandstructure",
    rate_unit="$/kW",
    default_label_prefix="Month",
)


def get_current_tariff_data(tariff_viewer: TariffViewer) -> Dict[str, Any]:
    """
    Get the current tariff data, accounting for any modifications.

    Args:
        tariff_viewer: TariffViewer instance

    Returns:
        Current tariff data dictionary
    """
    modified = st.session_state.get("modified_tariff")
    if modified:
        modified_tariff = extract_tariff_data(modified)
        # Defensive: only use modified data if it corresponds to the currently selected tariff.
        # This prevents leaking edits from a different tariff into this editor.
        if get_tariff_identifier(modified_tariff) == get_tariff_identifier(
            tariff_viewer.tariff
        ):
            return modified_tariff
    return tariff_viewer.tariff


def initialize_form_state(
    config: RateEditorConfig,
    rate_labels: List[str],
    rate_structure: List[List[Dict]],
    num_periods: int,
    tariff_id: str,
) -> None:
    """
    Initialize session state for the rate editing form.

    Args:
        config: Rate editor configuration
        rate_labels: List of period labels
        rate_structure: Rate structure from tariff
        num_periods: Number of rate periods
        tariff_id: Unique identifier for the tariff
    """
    labels_key = f"{config.session_prefix}_labels"
    rates_key = f"{config.session_prefix}_rates"
    adjs_key = f"{config.session_prefix}_adjustments"
    tariff_id_key = f"{config.session_prefix}_tariff_id"

    # Store the tariff identifier to detect tariff changes
    st.session_state[tariff_id_key] = tariff_id

    # Initialize labels
    st.session_state[labels_key] = rate_labels.copy() if rate_labels else []
    st.session_state[rates_key] = []
    st.session_state[adjs_key] = []

    # Extract rates and adjustments from structure
    for i in range(num_periods):
        if i < len(rate_structure) and rate_structure[i]:
            rate_info = rate_structure[i][0]
            st.session_state[rates_key].append(float(rate_info.get("rate", 0)))
            st.session_state[adjs_key].append(float(rate_info.get("adj", 0)))
        else:
            st.session_state[rates_key].append(0.0)
            st.session_state[adjs_key].append(0.0)

    # Ensure we have labels for all periods
    while len(st.session_state[labels_key]) < num_periods:
        st.session_state[labels_key].append(
            f"{config.default_label_prefix} {len(st.session_state[labels_key])}"
        )

    # Clear any stale widget keys from previous tariff
    # This is crucial because Streamlit widgets with keys persist their values
    form_widget_prefixes = [
        f"{config.form_key}_label_",
        f"{config.form_key}_base_rate_",
        f"{config.form_key}_adjustment_",
    ]

    keys_to_delete = [
        key
        for key in list(st.session_state.keys())
        if any(key.startswith(prefix) for prefix in form_widget_prefixes)
    ]

    for key in keys_to_delete:
        del st.session_state[key]


def get_tariff_identifier(tariff_data: Dict[str, Any]) -> str:
    """
    Generate a unique identifier for a tariff based on its content.

    Args:
        tariff_data: The tariff dictionary

    Returns:
        A string identifier for the tariff
    """
    # Use utility name + rate name + label as a unique identifier
    utility = tariff_data.get("utility", "")
    name = tariff_data.get("name", "")
    label = tariff_data.get("label", "")
    return f"{utility}|{name}|{label}"


def get_tariff_key_suffix(tariff_data: Dict[str, Any]) -> str:
    """
    Generate a short, sanitized key suffix for widget keys based on tariff identity.

    This ensures widget keys are unique per tariff, preventing Streamlit's
    widget state from persisting across tariff switches.

    Args:
        tariff_data: The tariff dictionary

    Returns:
        A sanitized string suitable for use in widget keys
    """
    import hashlib

    # Create a hash of the tariff identifier for a short, consistent key
    identifier = get_tariff_identifier(tariff_data)
    # Use first 8 chars of MD5 hash for brevity
    return hashlib.md5(identifier.encode()).hexdigest()[:8]


def check_form_needs_initialization(
    config: RateEditorConfig, num_periods: int, tariff_id: str
) -> bool:
    """
    Check if the form state needs to be initialized.

    Args:
        config: Rate editor configuration
        num_periods: Expected number of rate periods
        tariff_id: Unique identifier for the current tariff

    Returns:
        True if initialization is needed
    """
    labels_key = f"{config.session_prefix}_labels"
    rates_key = f"{config.session_prefix}_rates"
    tariff_id_key = f"{config.session_prefix}_tariff_id"

    # Check if we have the right tariff loaded
    current_tariff_id = st.session_state.get(tariff_id_key, "")
    if current_tariff_id != tariff_id:
        return True

    return (
        labels_key not in st.session_state
        or len(st.session_state.get(labels_key, [])) != num_periods
        or len(st.session_state.get(rates_key, [])) != num_periods
    )


def apply_rate_changes(
    tariff_viewer: TariffViewer,
    config: RateEditorConfig,
    edited_labels: List[str],
    edited_rates: List[List[Dict]],
    additional_updates: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Apply rate changes to the modified tariff in session state.

    Args:
        tariff_viewer: TariffViewer instance
        config: Rate editor configuration
        edited_labels: List of edited period labels
        edited_rates: List of edited rate structures
        additional_updates: Additional tariff fields to update
    """
    # Create modified tariff if it doesn't exist
    if not st.session_state.get("modified_tariff"):
        st.session_state.modified_tariff = copy.deepcopy(tariff_viewer.data)

    # Get the tariff data to update
    tariff_data = extract_tariff_data(st.session_state.modified_tariff)

    # Update rate structure
    tariff_data[config.rates_key] = edited_rates

    # Update labels if applicable
    if config.labels_key:
        tariff_data[config.labels_key] = edited_labels

    # Apply any additional updates
    if additional_updates:
        for key, value in additional_updates.items():
            tariff_data[key] = value

    st.session_state.has_modifications = True
    # Persist modified tariff for the currently active tariff file (if available).
    active_file = st.session_state.get("active_tariff_file")
    if active_file:
        modified_map = st.session_state.get("modified_tariffs_by_file", {})
        modified_map[active_file] = st.session_state.modified_tariff
        st.session_state.modified_tariffs_by_file = modified_map


def render_rate_editing_form(
    tariff_viewer: TariffViewer, config: RateEditorConfig, options: Dict[str, Any]
) -> None:
    """
    Render a rate editing form for energy, demand, or flat demand rates.

    Args:
        tariff_viewer: TariffViewer instance
        config: Rate editor configuration
        options: Display options
    """
    # Get current tariff data
    current_tariff = get_current_tariff_data(tariff_viewer)

    # Get rate labels and structure
    rate_labels = current_tariff.get(config.labels_key, []) if config.labels_key else []
    rate_structure = current_tariff.get(config.rates_key, [])

    if not rate_structure:
        st.warning(f"⚠️ No {config.rate_type} rate structure found in this tariff.")
        return

    num_periods = len(rate_structure)

    # Generate tariff identifier for detecting tariff changes
    tariff_id = get_tariff_identifier(current_tariff)
    # Generate a short key suffix unique to this tariff for widget keys
    tariff_key_suffix = get_tariff_key_suffix(current_tariff)

    # Initialize form state if needed (including when tariff changes)
    if check_form_needs_initialization(config, num_periods, tariff_id):
        initialize_form_state(
            config, rate_labels, rate_structure, num_periods, tariff_id
        )

    # Create the form with a tariff-specific key to ensure form state is isolated per tariff
    form_key = f"{config.form_key}_{tariff_key_suffix}"
    with st.form(form_key):
        st.markdown("**Edit the rates below and click 'Apply Changes' to update:**")

        edited_labels = []
        edited_rates = []

        # Column headers
        col_headers = st.columns([3, 2, 2, 1])
        col_headers[0].write(f"**{config.default_label_prefix} Name**")
        col_headers[1].write(f"**Base Rate ({config.rate_unit})**")
        col_headers[2].write(f"**Adjustment ({config.rate_unit})**")
        col_headers[3].write("**Total**")

        # Render each rate period
        for i, rate_struct in enumerate(rate_structure):
            if rate_struct:
                rate_info = rate_struct[0]

                # Get values from session state (populated by initialize_form_state)
                # Session state is the source of truth for the current tariff's values
                labels_key = f"{config.session_prefix}_labels"
                rates_key = f"{config.session_prefix}_rates"
                adjs_key = f"{config.session_prefix}_adjustments"

                # Labels from session state or tariff data
                current_label = (
                    st.session_state[labels_key][i]
                    if i < len(st.session_state.get(labels_key, []))
                    else (
                        rate_labels[i]
                        if rate_labels and i < len(rate_labels)
                        else f"{config.default_label_prefix} {i}"
                    )
                )

                # Rates from session state (which was initialized from tariff data)
                # Session state is refreshed when tariff changes via initialize_form_state
                base_rate = (
                    st.session_state[rates_key][i]
                    if i < len(st.session_state.get(rates_key, []))
                    else float(rate_info.get("rate", 0))
                )

                adjustment = (
                    st.session_state[adjs_key][i]
                    if i < len(st.session_state.get(adjs_key, []))
                    else float(rate_info.get("adj", 0))
                )

                # Create input fields with tariff-specific keys to prevent cross-tariff state leakage
                cols = st.columns([3, 2, 2, 1])

                with cols[0]:
                    new_label = st.text_input(
                        f"Label {i}",
                        value=current_label,
                        key=f"{config.form_key}_label_{tariff_key_suffix}_{i}",
                        label_visibility="collapsed",
                    )
                    edited_labels.append(new_label)

                with cols[1]:
                    new_base_rate = st.number_input(
                        f"Base Rate {i}",
                        value=base_rate,
                        step=0.0001,
                        format="%.4f",
                        key=f"{config.form_key}_base_rate_{tariff_key_suffix}_{i}",
                        label_visibility="collapsed",
                    )

                with cols[2]:
                    new_adjustment = st.number_input(
                        f"Adjustment {i}",
                        value=adjustment,
                        step=0.0001,
                        format="%.4f",
                        key=f"{config.form_key}_adjustment_{tariff_key_suffix}_{i}",
                        label_visibility="collapsed",
                    )

                with cols[3]:
                    total_rate = new_base_rate + new_adjustment
                    st.write(f"${total_rate:.4f}")

                # Store edited rate structure
                edited_rate_info = rate_info.copy()
                edited_rate_info["rate"] = new_base_rate
                edited_rate_info["adj"] = new_adjustment
                edited_rates.append([edited_rate_info])
            else:
                edited_rates.append([])
                edited_labels.append(f"{config.default_label_prefix} {i}")

        # Apply changes button
        if st.form_submit_button("✅ Apply Changes", type="primary"):
            # Update session state
            labels_key = f"{config.session_prefix}_labels"
            rates_key = f"{config.session_prefix}_rates"
            adjs_key = f"{config.session_prefix}_adjustments"

            st.session_state[labels_key] = edited_labels.copy()
            st.session_state[rates_key] = [
                edited_rates[i][0]["rate"] if edited_rates[i] else 0.0
                for i in range(len(edited_rates))
            ]
            st.session_state[adjs_key] = [
                edited_rates[i][0]["adj"] if edited_rates[i] else 0.0
                for i in range(len(edited_rates))
            ]

            # Apply changes to tariff
            apply_rate_changes(tariff_viewer, config, edited_labels, edited_rates)

            st.success(
                f"✅ {config.rate_type.replace('_', ' ').title()} rate changes applied!"
            )
            st.rerun()


def render_flat_demand_editing_form(
    tariff_viewer: TariffViewer, options: Dict[str, Any]
) -> None:
    """
    Render the flat demand rate editing form (monthly rates).

    This is a specialized form for flat demand rates which are organized by month.

    Args:
        tariff_viewer: TariffViewer instance
        options: Display options
    """
    config = FLAT_DEMAND_RATE_CONFIG
    current_tariff = get_current_tariff_data(tariff_viewer)

    flat_demand_rates = current_tariff.get("flatdemandstructure", [])
    flat_demand_months = current_tariff.get("flatdemandmonths", [])

    if not flat_demand_rates or not flat_demand_months:
        st.info("📝 **Note:** No flat demand rate structure found in this tariff JSON.")
        return

    # Generate tariff identifier for detecting tariff changes
    tariff_id = get_tariff_identifier(current_tariff)
    tariff_key_suffix = get_tariff_key_suffix(current_tariff)

    # Initialize form state if needed
    rates_key = f"{config.session_prefix}_rates"
    adjs_key = f"{config.session_prefix}_adjustments"
    tariff_id_key = f"{config.session_prefix}_tariff_id"

    # Check if we need to reinitialize (new tariff or missing state)
    current_tariff_id = st.session_state.get(tariff_id_key, "")
    needs_init = (
        current_tariff_id != tariff_id
        or rates_key not in st.session_state
        or len(st.session_state.get(rates_key, [])) != 12
    )

    if needs_init:
        st.session_state[tariff_id_key] = tariff_id
        st.session_state[rates_key] = []
        st.session_state[adjs_key] = []

        for month_idx in range(12):
            period_idx = (
                flat_demand_months[month_idx]
                if month_idx < len(flat_demand_months)
                else 0
            )
            if period_idx < len(flat_demand_rates) and flat_demand_rates[period_idx]:
                rate = flat_demand_rates[period_idx][0].get("rate", 0)
                adj = flat_demand_rates[period_idx][0].get("adj", 0)
                st.session_state[rates_key].append(float(rate))
                st.session_state[adjs_key].append(float(adj))
            else:
                st.session_state[rates_key].append(0.0)
                st.session_state[adjs_key].append(0.0)

    # Create the form with tariff-specific key
    form_key = f"{config.form_key}_{tariff_key_suffix}"
    with st.form(form_key):
        st.markdown(
            "**Edit the monthly flat demand rates below and click 'Apply Changes' to update:**"
        )

        edited_rates = []
        edited_adjustments = []

        # Column headers
        col_headers = st.columns([2, 2, 2, 1])
        col_headers[0].write("**Month**")
        col_headers[1].write(f"**Base Rate ({config.rate_unit})**")
        col_headers[2].write(f"**Adjustment ({config.rate_unit})**")
        col_headers[3].write("**Total**")

        for month_idx in range(12):
            base_rate = (
                st.session_state[rates_key][month_idx]
                if month_idx < len(st.session_state.get(rates_key, []))
                else 0.0
            )
            adjustment = (
                st.session_state[adjs_key][month_idx]
                if month_idx < len(st.session_state.get(adjs_key, []))
                else 0.0
            )

            cols = st.columns([2, 2, 2, 1])

            with cols[0]:
                st.write(f"**{MONTHS_FULL[month_idx]}**")

            with cols[1]:
                new_base_rate = st.number_input(
                    f"Base Rate {month_idx}",
                    value=base_rate,
                    step=0.0001,
                    format="%.4f",
                    key=f"flat_demand_base_rate_{tariff_key_suffix}_{month_idx}",
                    label_visibility="collapsed",
                )
                edited_rates.append(new_base_rate)

            with cols[2]:
                new_adjustment = st.number_input(
                    f"Adjustment {month_idx}",
                    value=adjustment,
                    step=0.0001,
                    format="%.4f",
                    key=f"flat_demand_adjustment_{tariff_key_suffix}_{month_idx}",
                    label_visibility="collapsed",
                )
                edited_adjustments.append(new_adjustment)

            with cols[3]:
                total_rate = new_base_rate + new_adjustment
                st.write(f"${total_rate:.4f}")

        # Apply changes button
        if st.form_submit_button("✅ Apply Changes", type="primary"):
            st.session_state[rates_key] = edited_rates.copy()
            st.session_state[adjs_key] = edited_adjustments.copy()

            # Create modified tariff
            if not st.session_state.get("modified_tariff"):
                st.session_state.modified_tariff = copy.deepcopy(tariff_viewer.data)

            tariff_data = extract_tariff_data(st.session_state.modified_tariff)

            # Rebuild flat demand structure (one rate per month)
            new_flat_demand_structure = []
            new_flat_demand_months = []

            for month_idx in range(12):
                rate_structure = [
                    {
                        "rate": edited_rates[month_idx],
                        "adj": edited_adjustments[month_idx],
                        "unit": "kW",
                    }
                ]
                new_flat_demand_structure.append(rate_structure)
                new_flat_demand_months.append(month_idx)

            tariff_data["flatdemandstructure"] = new_flat_demand_structure
            tariff_data["flatdemandmonths"] = new_flat_demand_months

            st.session_state.has_modifications = True
            # Persist modified tariff for the currently active tariff file (if available).
            active_file = st.session_state.get("active_tariff_file")
            if active_file:
                modified_map = st.session_state.get("modified_tariffs_by_file", {})
                modified_map[active_file] = st.session_state.modified_tariff
                st.session_state.modified_tariffs_by_file = modified_map
            st.success("✅ Flat demand rate changes applied!")
            st.rerun()
