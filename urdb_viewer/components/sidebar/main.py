"""
Main sidebar component for URDB Tariff Viewer.

This module contains the primary sidebar creation function that orchestrates
all sidebar sections.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from urdb_viewer.config.settings import Settings
from urdb_viewer.services.file_service import FileService

from .download import render_download_section
from .file_upload import handle_file_upload, show_file_upload_section
from .modification import render_tariff_modification_section
from .openei_import import render_openei_import_section


def create_sidebar() -> Tuple[Optional[Path], Optional[Path], Dict[str, Any]]:
    """
    Create the sidebar with file selection and options.

    Returns:
        Tuple[Optional[Path], Optional[Path], Dict[str, Any]]:
        - Selected tariff file path
        - Selected load profile file path
        - Sidebar options dictionary
    """
    # === TARIFF SELECTION SECTION ===
    st.sidebar.markdown("### 📊 Select Tariff")

    # Get available files and separate by type
    json_files = FileService.find_json_files()

    # Separate tariffs into default and user-generated
    default_tariffs = []
    user_tariffs = []

    for file_path in json_files:
        display_name = FileService.get_display_name(file_path)
        if Settings.USER_DATA_DIR in file_path.parents:
            user_tariffs.append((file_path, display_name))
        else:
            default_tariffs.append((file_path, display_name))

    # Sort each category by display name
    default_tariffs.sort(key=lambda x: x[1])
    user_tariffs.sort(key=lambda x: x[1])

    # Tariff file selection
    if json_files:
        # Create combined options with visual indicators
        tariff_options = []

        # Add default tariffs section
        if default_tariffs:
            tariff_options.append(("", "📁 Default Tariffs"))  # Section header
            for path, name in default_tariffs:
                tariff_options.append((path, f"  📄 {name}"))

        # Add user tariffs section
        if user_tariffs:
            tariff_options.append(("", "👤 User Tariffs"))  # Section header
            for path, name in user_tariffs:
                tariff_options.append((path, f"  ✏️ {name}"))

        # Find current selection index if exists in session state
        current_index = 0
        if "current_tariff" in st.session_state:
            for i, (path, name) in enumerate(tariff_options):
                if path == st.session_state.current_tariff:
                    current_index = i
                    break

        selected_tariff_file = st.sidebar.selectbox(
            "Choose a tariff to analyze:",
            options=[
                option[0] for option in tariff_options if option[0]
            ],  # Filter out section headers
            format_func=lambda x: next(
                name for path, name in tariff_options if path == x
            ),
            label_visibility="collapsed",
            key="sidebar_tariff_select",
            index=current_index,
        )

        # Show tariff count information
        if default_tariffs and user_tariffs:
            st.sidebar.caption(
                f"📊 {len(default_tariffs)} default • {len(user_tariffs)} user-generated"
            )
        elif default_tariffs:
            st.sidebar.caption(f"📊 {len(default_tariffs)} default tariffs")
        elif user_tariffs:
            st.sidebar.caption(f"👤 {len(user_tariffs)} user-generated tariffs")

    else:
        st.sidebar.error("❌ No JSON tariff files found!")
        st.sidebar.info(f"📍 Place JSON files in: {Settings.TARIFFS_DIR}")
        selected_tariff_file = None

    st.sidebar.markdown("---")

    # === LOAD PROFILE SELECTION SECTION ===
    st.sidebar.markdown("### 📈 Select Load Profile")

    csv_files = FileService.find_csv_files()
    selected_load_profile = None

    if csv_files:
        # Create display options for load profile files
        profile_options = []
        for file_path in csv_files:
            display_name = FileService.get_display_name(file_path)
            profile_options.append((file_path, display_name))

        # Sort by display name
        profile_options.sort(key=lambda x: x[1])

        # Find current selection index if exists in session state
        lp_current_index = 0
        if "current_load_profile" in st.session_state:
            for i, (path, name) in enumerate(profile_options):
                if path == st.session_state.current_load_profile:
                    lp_current_index = i
                    break

        selected_load_profile = st.sidebar.selectbox(
            "Choose a load profile:",
            options=[option[0] for option in profile_options],
            format_func=lambda x: next(
                name for path, name in profile_options if path == x
            ),
            label_visibility="collapsed",
            key="sidebar_load_profile_select",
            index=lp_current_index,
        )

        # Show current load profile info
        current_lp_name = next(
            name for path, name in profile_options if path == selected_load_profile
        )
        st.sidebar.caption(f"📊 **Current**: {current_lp_name}")
    else:
        st.sidebar.info("📁 No load profile files found in 'load_profiles' directory")

    st.sidebar.markdown("---")

    # === TARIFF MODIFICATION MANAGEMENT ===
    render_tariff_modification_section()

    # === UPLOAD SECTION ===
    st.sidebar.markdown("### 📁 Upload New Tariff")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Tariff JSON File",
        type=["json"],
        accept_multiple_files=False,
        help="Upload a URDB tariff JSON file (max 1MB) - will be saved to user_data/ directory",
        key="tariff_upload",
    )

    # Display file size limit info
    st.sidebar.caption(
        "📏 **File size limit**: 1MB maximum | 📁 **Saved to**: user_data/ directory"
    )

    if uploaded_file is not None:
        handle_file_upload(uploaded_file)

    st.sidebar.markdown("---")

    # === IMPORT FROM OPENEI SECTION ===
    st.sidebar.markdown("### 🌐 Import from OpenEI")

    render_openei_import_section()

    st.sidebar.markdown("---")

    # === DOWNLOAD SECTION ===
    st.sidebar.markdown("### 📥 Download Current Tariff")

    if selected_tariff_file:
        render_download_section(selected_tariff_file)
    else:
        st.sidebar.info(
            "🔄 No tariff selected. Please select a tariff to enable download."
        )

    st.sidebar.markdown("---")

    # Compile options dictionary
    sidebar_options = {
        "chart_height": 600,  # Default chart height
        "text_size": 12,  # Default text size
        # Dark mode removed; keep key for backwards compatibility with components.
        "dark_mode": False,
        "customer_voltage": 480.0,  # Default customer voltage
        "load_generation": {
            "avg_load": 250.0,
            "load_factor": 0.7,
            "seasonal_variation": 0.1,
            "weekend_factor": 0.8,
        },
    }

    return selected_tariff_file, selected_load_profile, sidebar_options


def show_advanced_options() -> Dict[str, Any]:
    """
    Show advanced options in an expander.

    Returns:
        Dict[str, Any]: Advanced options dictionary
    """
    with st.sidebar.expander("🔬 Advanced Options"):
        # Calculation precision
        precision = st.selectbox(
            "Calculation Precision",
            options=[2, 3, 4, 5, 6],
            index=2,
            help="Number of decimal places for calculations",
        )

        # Time zone handling
        timezone = st.selectbox(
            "Time Zone",
            options=["Local", "UTC", "PST", "EST", "CST", "MST"],
            index=0,
            help="Time zone for timestamp interpretation",
        )

        # Data validation level
        validation_level = st.selectbox(
            "Validation Level",
            options=["Strict", "Standard", "Lenient"],
            index=1,
            help="Level of data validation to apply",
        )

        # Export options
        export_format = st.selectbox(
            "Export Format",
            options=["JSON", "CSV", "Excel"],
            index=0,
            help="Default format for data exports",
        )

    return {
        "precision": precision,
        "timezone": timezone,
        "validation_level": validation_level,
        "export_format": export_format,
    }
