"""
Tariff Database Search Component for URDB Tariff Viewer.

This component provides a UI for searching the USURDB parquet database,
filtering tariffs, and importing selected tariffs as JSON files.

Flow:
1. User searches for a utility by name
2. Matching utilities are displayed for selection
3. User selects a utility
4. Tariffs for that utility are loaded with filter options
5. User can filter, select, and import tariffs

Performance Optimizations:
- Uses @st.fragment for filter sections to prevent full page reruns
- Caches display DataFrame creation
- Uses session state to avoid recomputation
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from urdb_viewer.config.settings import Settings
from urdb_viewer.services.tariff_database_service import TariffDatabaseService

# Default sectors for filtering
DEFAULT_SECTORS = ["Commercial", "Industrial"]

# Sort columns for tariff results
SORT_COLUMNS = [
    "Effective Date",
    "Tariff Name",
    "Sector",
    "Min kW",
    "Max kW",
    "Min kWh",
    "Max kWh",
]


def _extract_date(date_val) -> str:
    """Extract date string from various formats."""
    if date_val is None:
        return ""
    if isinstance(date_val, dict):
        return date_val.get("$date", "")
    if isinstance(date_val, (int, float)):
        # Unix timestamp
        try:
            from datetime import datetime

            return datetime.fromtimestamp(date_val).strftime("%Y-%m-%d")
        except Exception:
            return str(date_val)
    return str(date_val)


def _create_display_df_for_utility(utility_tariffs: List[Dict]) -> pd.DataFrame:
    """
    Create display DataFrame for a utility's tariffs.
    Uses session state caching to avoid recreation on filter changes.

    Args:
        utility_tariffs: List of tariff dicts

    Returns:
        Display DataFrame
    """
    records = []
    for t in utility_tariffs:
        records.append(
            {
                "label": (
                    t.get("_id", {}).get("$oid", "")
                    if isinstance(t.get("_id"), dict)
                    else t.get("_id", t.get("label", ""))
                ),
                "utility_name": t.get("utilityName") or t.get("utility", ""),
                "rate_name": t.get("rateName") or t.get("name", ""),
                "sector": t.get("sector", ""),
                "service_type": t.get("serviceType") or t.get("servicetype", ""),
                "demand_min": t.get("demandMin") or t.get("mindemand"),
                "demand_max": t.get("demandMax") or t.get("maxdemand"),
                "energy_min": t.get("energyMin") or t.get("minenergy"),
                "energy_max": t.get("energyMax") or t.get("maxenergy"),
                "effective_date": _extract_date(
                    t.get("effectiveDate") or t.get("startdate")
                ),
                "end_date": _extract_date(t.get("endDate") or t.get("enddate")),
                "description": t.get("description", ""),
            }
        )

    return TariffDatabaseService._create_display_dataframe(pd.DataFrame(records))


def render_tariff_database_search_tab() -> None:
    """Render the tariff database search tab content."""
    st.header("🔍 Tariff Database Search")
    st.markdown(
        """
        Search the USURDB (Utility Rate Database) for tariffs and import them into the app.
        Search by utility name, select a utility, then filter and import tariffs.
        """
    )

    # Check if database is available
    if not TariffDatabaseService.check_database_available():
        _render_database_not_found()
        return

    # Show database statistics
    _render_database_stats()

    st.divider()

    # Step 1: Search for utilities
    _render_utility_search_section()

    # Step 2: Utility selection (only if search has results)
    selected_utility = _render_utility_selection()

    # Step 3: Tariff results with filters (only if utility is selected)
    if selected_utility:
        _render_tariff_results_section(selected_utility)


def _render_database_not_found() -> None:
    """Render message when database is not found."""
    st.error("❌ Tariff database not found!")
    st.markdown(
        f"""
        ### Setup Instructions

        To use this feature, you need to add the USURDB parquet database file:

        1. Obtain the `usurdb.parquet` file from the Tariff_Playground project or OpenEI
        2. Place it in: `{Settings.TARIFF_DB_PATH}`
        3. Optionally, add `utilities_index.parquet` for faster utility lookups

        The parquet file contains pre-processed tariff data from the OpenEI URDB API.
        """
    )


def _render_database_stats() -> None:
    """Render database statistics."""
    stats = TariffDatabaseService.get_database_stats()

    if stats.get("available"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Tariffs", f"{stats.get('total_tariffs', 0):,}")
        with col2:
            st.metric("🏢 Unique Utilities", f"{stats.get('unique_utilities', 0):,}")
        with col3:
            sectors = stats.get("sectors", [])
            st.metric("📁 Sectors", len(sectors))


def _render_utility_search_section() -> None:
    """Render the utility search section."""
    st.subheader("🔎 Step 1: Search for Utility")

    # Search input
    col1, col2 = st.columns([3, 1])

    with col1:
        utility_name = st.text_input(
            "Utility Name",
            placeholder="e.g., Pacific Gas & Electric, Con Edison, etc.",
            help="Enter the full or partial name of the utility company",
            key="db_search_utility_name",
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer for alignment
        search_clicked = st.button(
            "🔍 Search",
            type="primary",
            use_container_width=True,
            key="db_search_button",
        )

    # Handle search
    if search_clicked:
        if utility_name.strip():
            _perform_utility_search(utility_name)
        else:
            st.warning("⚠️ Please enter a utility name to search")

    # Clear button if we have results
    if (
        "db_matching_utilities" in st.session_state
        and st.session_state.db_matching_utilities
    ):
        if st.button("🗑️ Clear Search", key="db_clear_button"):
            _clear_search_results()
            st.rerun()


def _perform_utility_search(utility_name: str) -> None:
    """Search for utilities matching the search term."""
    with st.spinner("🔍 Searching utilities..."):
        # Search for matching utilities
        display_df, tariffs = TariffDatabaseService.search_tariffs(
            utility_name=utility_name,
            sectors=None,
            years=None,
            name_contains=None,
            exclude_terms=None,
            min_kw_filter=0.0,
            max_kw_filter=0.0,
            include_superseded=True,  # Include all to get full utility list
        )

        if tariffs:
            # Extract unique utilities from results
            utilities = set()
            for tariff in tariffs:
                util = tariff.get("utilityName") or tariff.get("utility", "")
                if util:
                    utilities.add(util)

            matching_utilities = sorted(list(utilities))

            # Store in session state
            st.session_state.db_matching_utilities = matching_utilities
            st.session_state.db_all_tariffs = tariffs
            st.session_state.db_last_search = utility_name
            st.session_state.db_selected_utility = None  # Reset selection

            st.success(
                f"✅ Found {len(matching_utilities)} utility/utilities matching '{utility_name}'"
            )
        else:
            st.session_state.db_matching_utilities = []
            st.session_state.db_all_tariffs = []
            st.warning(f"No utilities found for '{utility_name}'")
            _render_suggestions(utility_name)


def _render_suggestions(search_term: str) -> None:
    """Render utility name suggestions."""
    suggestions = TariffDatabaseService.find_similar_utilities(search_term)
    if suggestions:
        st.markdown("### 💡 Did you mean one of these utilities?")
        for utility in suggestions:
            st.write(f"- {utility}")


def _render_utility_selection() -> Optional[str]:
    """Render utility selection dropdown and return selected utility."""
    if (
        "db_matching_utilities" not in st.session_state
        or not st.session_state.db_matching_utilities
    ):
        return None

    st.divider()
    st.subheader("🏢 Step 2: Select Utility")

    matching_utilities = st.session_state.db_matching_utilities

    st.markdown(
        f"Found **{len(matching_utilities)}** utility/utilities. Select one to view its tariffs:"
    )

    selected_utility = st.selectbox(
        "Choose a utility:",
        options=matching_utilities,
        key="db_utility_selector",
        help="Select a utility from the list to view its tariffs",
    )

    # Store selection
    st.session_state.db_selected_utility = selected_utility

    return selected_utility


def _clear_search_results() -> None:
    """Clear all search results from session state."""
    keys_to_clear = [
        "db_matching_utilities",
        "db_all_tariffs",
        "db_last_search",
        "db_selected_utility",
        "db_filtered_tariffs",
        "db_filtered_df",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Also clear utility-specific cached data
    keys_to_remove = [
        k
        for k in st.session_state.keys()
        if k.startswith("db_utility_tariffs_") or k.startswith("db_display_df_")
    ]
    for key in keys_to_remove:
        del st.session_state[key]


def _render_tariff_results_section(selected_utility: str) -> None:
    """Render the tariff results section with filters for selected utility."""
    st.divider()
    st.subheader("📋 Step 3: Filter and Select Tariffs")

    # Get tariffs for selected utility
    all_tariffs = st.session_state.get("db_all_tariffs", [])

    # Filter to selected utility and cache the result
    utility_key = f"db_utility_tariffs_{selected_utility}"
    if utility_key not in st.session_state:
        utility_tariffs = []
        for tariff in all_tariffs:
            util = tariff.get("utilityName") or tariff.get("utility", "")
            if util == selected_utility:
                utility_tariffs.append(tariff)
        st.session_state[utility_key] = utility_tariffs
    else:
        utility_tariffs = st.session_state[utility_key]

    if not utility_tariffs:
        st.warning(f"No tariffs found for {selected_utility}")
        return

    # Create display DataFrame - cache in session state to avoid recreation
    display_df_key = f"db_display_df_{selected_utility}"
    if display_df_key not in st.session_state:
        st.session_state[display_df_key] = _create_display_df_for_utility(
            utility_tariffs
        )
    display_df = st.session_state[display_df_key]

    st.info(f"📊 Found **{len(utility_tariffs)}** tariff(s) for **{selected_utility}**")

    # Use fragment for filter section to prevent full page reruns
    _render_filters_and_table(display_df, utility_tariffs)


@st.fragment
def _render_filters_and_table(
    display_df: pd.DataFrame, utility_tariffs: List[Dict]
) -> None:
    """
    Render the filters and table section as a fragment.
    This prevents full page reruns when filters are changed.
    """
    # Filters section
    st.markdown("#### 🔧 Filters")

    # Row 1: Sector, Year, Name Contains
    col1, col2, col3 = st.columns(3)

    with col1:
        available_sectors = sorted(display_df["Sector"].dropna().unique().tolist())
        default_sectors = [s for s in DEFAULT_SECTORS if s in available_sectors]

        selected_sectors = st.multiselect(
            "Sector",
            options=available_sectors,
            default=default_sectors if default_sectors else [],
            help="Filter by sector(s). Leave empty to show all.",
            key="db_filter_sectors",
        )

    with col2:
        # Extract years from effective date
        df_with_year = display_df.copy()
        df_with_year["Effective Year"] = pd.to_datetime(
            df_with_year["Effective Date"], errors="coerce"
        ).dt.year
        available_years = sorted(
            [int(y) for y in df_with_year["Effective Year"].dropna().unique()],
            reverse=True,
        )

        selected_years = st.multiselect(
            "Effective Year",
            options=available_years,
            default=[],
            help="Filter by effective year(s)",
            key="db_filter_years",
        )

    with col3:
        name_filter = st.text_input(
            "Tariff Name Contains",
            placeholder="e.g., TOU, EV, Commercial",
            help="Filter tariffs by name (case-insensitive)",
            key="db_filter_name_contains",
        )

    # Row 2: Exclude filter
    exclude_filter = st.text_input(
        "Exclude Names Containing",
        placeholder="e.g., transmission, substation (comma-separated)",
        help="Comma-separated list of terms. Tariffs with names containing any of these will be excluded.",
        key="db_filter_exclude",
    )

    # Row 3: kW range and sorting
    col4, col5, col6, col7 = st.columns(4)

    with col4:
        min_kw_filter = st.number_input(
            "Min kW ≤",
            min_value=0.0,
            max_value=1000000.0,
            value=0.0,
            step=10.0,
            help="Filter tariffs where Min kW ≤ this value",
            key="db_filter_min_kw",
        )

    with col5:
        max_kw_filter = st.number_input(
            "Max kW ≥",
            min_value=0.0,
            max_value=1000000.0,
            value=0.0,
            step=10.0,
            help="Filter tariffs where Max kW ≥ this value (0 = no filter)",
            key="db_filter_max_kw",
        )

    with col6:
        sort_by = st.selectbox("Sort by", SORT_COLUMNS, index=0, key="db_sort_by")

    with col7:
        sort_order = st.radio(
            "Order",
            ["Descending", "Ascending"],
            index=0,
            horizontal=True,
            key="db_sort_order",
        )

    # Apply filters using the copy with year column
    filtered_df = _apply_filters(
        df_with_year,
        name_filter=name_filter,
        exclude_filter=exclude_filter,
        sectors=selected_sectors,
        years=selected_years,
        min_kw=min_kw_filter,
        max_kw=max_kw_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Filter the tariff list to match
    filtered_labels = set(filtered_df["Label"].tolist())
    filtered_tariffs = []
    for tariff in utility_tariffs:
        label = (
            tariff.get("_id", {}).get("$oid", "")
            if isinstance(tariff.get("_id"), dict)
            else tariff.get("_id", tariff.get("label", ""))
        )
        if label in filtered_labels:
            filtered_tariffs.append(tariff)

    # Show results count
    st.metric("Filtered Results", len(filtered_df))

    # Flag legend
    with st.expander("🏳️ Flag Legend", expanded=False):
        st.markdown(
            """
            | Flag | Meaning |
            |------|---------|
            | ✅ | No issues detected |
            | 📛 | **Superseded** - This tariff has been replaced by a newer version |
            | 🚚 | **Delivery Only** - Does not include energy/generation charges |
            | ⚡ | **Energy Only** - Does not include delivery/distribution charges |
            | 📅 | **Outdated** - Effective date is over 2 years old |
            """
        )

    st.info(
        "💡 **Tip:** Select tariffs from the table below to import them into the app."
    )

    # Prepare display DataFrame
    display_copy = filtered_df.copy()
    display_copy["Max kW"] = display_copy["Max kW"].replace(float("inf"), "Unlimited")
    display_copy["Max kWh"] = display_copy["Max kWh"].replace(float("inf"), "Unlimited")

    # Remove the temporary year column for display
    if "Effective Year" in display_copy.columns:
        display_copy = display_copy.drop(columns=["Effective Year"])

    # Display the dataframe with selection
    selected_rows = st.dataframe(
        display_copy,
        use_container_width=True,
        height=500,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="large"),
        },
        on_select="rerun",
        selection_mode="multi-row",
        key="db_results_table",
    )

    # Handle selection
    selected_indices = (
        selected_rows.selection.rows if selected_rows.selection.rows else []
    )

    if selected_indices:
        st.markdown(f"**Selected: {len(selected_indices)} tariff(s)**")

        # Get selected tariffs
        selected_labels = [filtered_df.iloc[idx]["Label"] for idx in selected_indices]
        selected_tariffs = []
        for label in selected_labels:
            for tariff in filtered_tariffs:
                tariff_label = (
                    tariff.get("_id", {}).get("$oid", "")
                    if isinstance(tariff.get("_id"), dict)
                    else tariff.get("_id", tariff.get("label", ""))
                )
                if tariff_label == label:
                    selected_tariffs.append(tariff)
                    break

        # Show selected tariff names
        with st.expander("📋 Selected Tariffs", expanded=True):
            for tariff in selected_tariffs:
                utility = (
                    tariff.get("utility") or tariff.get("utilityName") or "Unknown"
                )
                name = tariff.get("name") or tariff.get("rateName") or "Unknown"
                st.write(f"• {utility} - {name}")

        # Import section
        _render_import_section(selected_tariffs)


def _apply_filters(
    df: pd.DataFrame,
    name_filter: str,
    exclude_filter: str,
    sectors: List[str],
    years: List[int],
    min_kw: float,
    max_kw: float,
    sort_by: str,
    sort_order: str,
) -> pd.DataFrame:
    """Apply filters and sorting to the DataFrame."""
    filtered_df = df.copy()

    # Apply tariff name filter (include)
    if name_filter:
        filtered_df = filtered_df[
            filtered_df["Tariff Name"].str.contains(name_filter, case=False, na=False)
        ]

    # Apply tariff name filter (exclude)
    if exclude_filter:
        exclude_terms = [
            term.strip() for term in exclude_filter.split(",") if term.strip()
        ]
        for term in exclude_terms:
            filtered_df = filtered_df[
                ~filtered_df["Tariff Name"].str.contains(term, case=False, na=False)
            ]

    # Apply sector filter
    if sectors:
        filtered_df = filtered_df[filtered_df["Sector"].isin(sectors)]

    # Apply year filter
    if years and "Effective Year" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Effective Year"].isin(years)]

    # Apply Min kW filter
    if min_kw > 0:
        filtered_df = filtered_df[filtered_df["Min kW"] <= min_kw]

    # Apply Max kW filter
    if max_kw > 0:
        filtered_df = filtered_df[
            (filtered_df["Max kW"] >= max_kw) | (filtered_df["Max kW"] == float("inf"))
        ]

    # Apply sorting
    ascending = sort_order == "Ascending"

    if sort_by == "Effective Date":
        filtered_df["_sort_date"] = pd.to_datetime(
            filtered_df["Effective Date"], errors="coerce"
        )
        filtered_df = filtered_df.sort_values(
            by=["_sort_date", "Tariff Name"],
            ascending=[not ascending, True],
            na_position="last",
        )
        filtered_df = filtered_df.drop(columns=["_sort_date"])
    else:
        filtered_df = filtered_df.sort_values(
            by=[sort_by], ascending=[ascending], na_position="last"
        )

    return filtered_df.reset_index(drop=True)


def _render_import_section(selected_tariffs: List[Dict[str, Any]]) -> None:
    """Render the import section for selected tariffs."""
    st.divider()
    st.subheader("📥 Import Selected Tariffs")

    # Target directory selection
    col1, col2 = st.columns([2, 1])

    with col1:
        target_options = {
            "Default Tariffs": Settings.TARIFFS_DIR,
            "User Data": Settings.USER_DATA_DIR,
        }
        target_choice = st.selectbox(
            "Save to:",
            options=list(target_options.keys()),
            index=0,
            help="Choose where to save the imported tariffs",
            key="db_import_target",
        )
        target_dir = target_options[target_choice]

    with col2:
        st.markdown(f"**Path:** `{target_dir.relative_to(Settings.BASE_DIR)}`")

    # Import button
    if st.button(
        f"📥 Import {len(selected_tariffs)} Tariff(s)",
        type="primary",
        use_container_width=True,
        key="db_import_button",
    ):
        _perform_import(selected_tariffs, target_dir)


def _perform_import(tariffs: List[Dict[str, Any]], target_dir) -> None:
    """Perform the tariff import."""
    with st.spinner(f"📥 Importing {len(tariffs)} tariff(s)..."):
        successful, errors = TariffDatabaseService.save_tariffs_to_files(
            tariffs, target_dir
        )

        if successful:
            st.success(f"✅ Successfully imported {len(successful)} tariff(s)!")
            with st.expander("📁 Imported Files", expanded=True):
                for filename in successful:
                    st.write(f"• {filename}")

            st.info(
                "🔄 **Tip:** Refresh the page or use the sidebar to select the newly imported tariffs."
            )

        if errors:
            st.error(f"❌ Failed to import {len(errors)} tariff(s)")
            with st.expander("⚠️ Errors", expanded=True):
                for error in errors:
                    st.write(f"• {error}")
