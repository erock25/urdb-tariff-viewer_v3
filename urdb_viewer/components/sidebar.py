"""
Sidebar component for URDB Tariff Viewer.

This module contains the sidebar UI components and logic.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from urdb_viewer.config.settings import Settings
from urdb_viewer.models.tariff import TariffViewer
from urdb_viewer.services.file_service import FileService


def create_sidebar() -> Tuple[Optional[Path], Optional[Path], Dict[str, Any]]:
    """
    Create the sidebar with file selection and options.

    Returns:
        Tuple[Optional[Path], Optional[Path], Dict[str, Any]]:
        - Selected tariff file path
        - Selected load profile file path
        - Sidebar options dictionary
    """
    # Sidebar header removed

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
    _render_tariff_modification_section()

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
        _handle_file_upload(uploaded_file)

    st.sidebar.markdown("---")

    # === IMPORT FROM OPENEI SECTION ===
    st.sidebar.markdown("### 🌐 Import from OpenEI")

    _render_openei_import_section()

    st.sidebar.markdown("---")

    # === DOWNLOAD SECTION ===
    st.sidebar.markdown("### 📥 Download Current Tariff")

    if selected_tariff_file:
        _render_download_section(selected_tariff_file)
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


def _handle_file_upload(uploaded_file) -> None:
    """Handle file upload functionality."""
    import json
    import re

    # Validate file size (1MB = 1,048,576 bytes)
    if uploaded_file.size > 1048576:
        st.sidebar.error(
            "❌ File size exceeds 1MB limit. Please upload a smaller file."
        )
        return

    try:
        # Try to parse the JSON to validate it
        file_content = uploaded_file.read()
        json_data = json.loads(file_content.decode("utf-8"))

        # Basic validation - check if it looks like a URDB tariff
        is_valid_tariff = False
        if isinstance(json_data, dict):
            # Check for URDB tariff structure
            if (
                "items" in json_data
                and isinstance(json_data["items"], list)
                and len(json_data["items"]) > 0
            ):
                tariff_item = json_data["items"][0]
                if isinstance(tariff_item, dict) and (
                    "utility" in tariff_item or "name" in tariff_item
                ):
                    is_valid_tariff = True
            # Also accept direct tariff objects (not wrapped in 'items')
            elif "utility" in json_data or "name" in json_data:
                is_valid_tariff = True

        if is_valid_tariff:
            # Create user_data directory if it doesn't exist
            Settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

            # Generate filename (clean the uploaded filename)
            original_name = uploaded_file.name
            if not original_name.endswith(".json"):
                original_name += ".json"

            # Clean filename to remove special characters
            clean_name = re.sub(r"[^\w\-_\.]", "_", original_name)
            filepath = Settings.USER_DATA_DIR / clean_name

            # Check if file already exists
            if filepath.exists():
                if st.sidebar.button(
                    "⚠️ File exists! Click to overwrite", type="secondary"
                ):
                    # Save the file
                    with open(filepath, "wb") as f:
                        f.write(file_content)
                    st.sidebar.success(
                        f"✅ Tariff file '{clean_name}' uploaded and saved successfully!"
                    )
                    st.sidebar.info(
                        "🔄 Please refresh the page or reselect the tariff to see the new file in the dropdown."
                    )
            else:
                # Save the file
                with open(filepath, "wb") as f:
                    f.write(file_content)
                st.sidebar.success(
                    f"✅ Tariff file '{clean_name}' uploaded and saved successfully!"
                )
                st.sidebar.info(
                    "🔄 Please refresh the page or reselect the tariff to see the new file in the dropdown."
                )
        else:
            st.sidebar.error(
                "❌ Invalid tariff format. Please upload a valid URDB tariff JSON file."
            )
            st.sidebar.info(
                "💡 The file should contain either:\n- An 'items' array with tariff objects\n- A direct tariff object with 'utility' or 'name' fields"
            )

    except json.JSONDecodeError as e:
        st.sidebar.error(f"❌ Invalid JSON file: {str(e)}")
    except UnicodeDecodeError:
        st.sidebar.error(
            "❌ File encoding error. Please ensure the file is saved in UTF-8 format."
        )
    except Exception as e:
        st.sidebar.error(f"❌ Error processing file: {str(e)}")


def _render_download_section(selected_tariff_file: Path) -> None:
    """Render the download section for current tariff."""
    import json
    import re

    try:
        # Load tariff data for download
        tariff_viewer = TariffViewer(selected_tariff_file)
        current_tariff_data = (
            tariff_viewer.data if hasattr(tariff_viewer, "data") else {}
        )

        # Generate filename
        current_tariff_name = (
            f"{tariff_viewer.utility_name}_{tariff_viewer.rate_name}".replace(
                " ", "_"
            ).replace("-", "_")
        )

        # Clean the filename
        clean_filename = re.sub(r"[^\w\-_]", "_", current_tariff_name)
        download_filename = f"{clean_filename}.json"

        # Convert to JSON string with proper formatting
        json_string = json.dumps(current_tariff_data, indent=2, ensure_ascii=False)

        st.sidebar.download_button(
            label="📄 Download Tariff JSON",
            data=json_string,
            file_name=download_filename,
            mime="application/json",
            help=f"Download the currently selected tariff: {tariff_viewer.utility_name} - {tariff_viewer.rate_name}",
            use_container_width=True,
        )

        # Show file info
        st.sidebar.caption(
            f"📋 **Current tariff**: {tariff_viewer.utility_name} - {tariff_viewer.rate_name}"
        )

    except Exception as e:
        st.sidebar.error(f"❌ Error preparing download: {str(e)}")


# Tariff info chips live in `urdb_viewer/components/tariff_information.py`


def show_file_upload_section() -> Optional[Path]:
    """
    Show file upload section in sidebar.

    Returns:
        Optional[Path]: Path to uploaded file if successful
    """
    st.sidebar.markdown("### 📤 Upload Files")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Tariff JSON",
        type=["json"],
        help="Upload a URDB format JSON tariff file",
    )

    if uploaded_file is not None:
        try:
            # Save uploaded file to user data directory
            file_path = Settings.USER_DATA_DIR / uploaded_file.name
            Settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")
            return file_path

        except Exception as e:
            st.sidebar.error(f"❌ Upload failed: {str(e)}")
            return None

    return None


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


def _render_openei_import_section() -> None:
    """Render the OpenEI tariff import section in sidebar."""
    import json

    import requests

    from urdb_viewer.config.settings import Settings

    # Get API key from secrets/environment
    configured_api_key = Settings.get_openei_api_key()

    # Show status and allow override
    if configured_api_key:
        st.sidebar.success("✅ API Key configured (using secrets.toml or environment)")
        st.sidebar.caption("💡 Enter a key below to override the configured key")
        api_key_input = st.sidebar.text_input(
            "Override API Key (optional):",
            type="password",
            help="Enter a different API key to override the configured one",
            key="openei_api_key_input",
        )
        # Use user-entered key if provided, otherwise use configured key
        api_key = api_key_input if api_key_input else configured_api_key
    else:
        st.sidebar.info(
            "💡 **API Key**: Add to secrets.toml, set environment variable, or enter below"
        )
        api_key_input = st.sidebar.text_input(
            "OpenEI API Key:",
            type="password",
            help="Enter your OpenEI API key. Get one at https://openei.org/services/api/signup/",
            key="openei_api_key_input",
        )
        api_key = api_key_input

    # Tariff ID input
    tariff_id = st.sidebar.text_input(
        "Tariff ID:",
        placeholder="e.g., 674e0b87201c6bd096007a5a",
        help="Enter the OpenEI tariff ID you want to import",
        key="openei_tariff_id",
    )

    # Import button
    import_clicked = st.sidebar.button(
        "📥 Import Tariff",
        type="primary",
        help="Fetch tariff from OpenEI API and save to user tariffs",
        use_container_width=True,
        disabled=not (api_key and tariff_id),
    )

    # Show link to OpenEI
    st.sidebar.caption(
        "[🔗 Browse tariffs on OpenEI.org](https://openei.org/wiki/Utility_Rate_Database)"
    )

    # Handle import
    if import_clicked and api_key and tariff_id:
        _import_tariff_from_openei(api_key, tariff_id.strip())


def _import_tariff_from_openei(api_key: str, tariff_id: str) -> None:
    """
    Import a tariff from OpenEI API and save to user_data directory.

    Args:
        api_key (str): OpenEI API key
        tariff_id (str): Tariff ID to fetch
    """
    import json

    import requests

    from urdb_viewer.config.settings import Settings

    # Show progress
    with st.spinner(f"🔄 Fetching tariff {tariff_id}..."):
        try:
            # Build API request
            url = Settings.OPENEI_API_URL
            params = {
                "version": Settings.OPENEI_API_VERSION,
                "format": "json",
                "api_key": api_key,
                "getpage": tariff_id,
                "detail": "full",
            }

            # Make API request
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Check if we got valid data
                items = data.get("items", [])
                if items:
                    tariff = items[0]

                    # Sanitize filename
                    def sanitize(s):
                        return "".join(
                            c if c.isalnum() or c in " _-" else "_" for c in str(s)
                        )

                    utility = sanitize(tariff.get("utility", "unknown"))
                    name = sanitize(tariff.get("name", "unknown"))

                    # Create user_data directory if it doesn't exist
                    Settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

                    # Generate filename
                    filename = f"{utility}_{name}.json"
                    filepath = Settings.USER_DATA_DIR / filename

                    # Check if file already exists
                    if filepath.exists():
                        # Add a number suffix if file exists
                        counter = 1
                        while filepath.exists():
                            filename = f"{utility}_{name}_{counter}.json"
                            filepath = Settings.USER_DATA_DIR / filename
                            counter += 1

                    # Save the tariff
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)

                    # Show success message with tariff details
                    st.sidebar.success(f"✅ Imported: {filename}")
                    st.sidebar.info(
                        f"**Tariff Details:**\n"
                        f"- Utility: {tariff.get('utility', 'N/A')}\n"
                        f"- Rate: {tariff.get('name', 'N/A')}\n"
                        f"- Sector: {tariff.get('sector', 'N/A')}"
                    )
                    st.sidebar.info(
                        "🔄 Refresh the page or reselect to see the new tariff in the dropdown."
                    )

                else:
                    st.sidebar.error(f"❌ No tariff found for ID: {tariff_id}")
                    st.sidebar.info("💡 Please check that the tariff ID is correct.")

            elif response.status_code == 401:
                st.sidebar.error(
                    "❌ Invalid API key. Please check your OpenEI API key."
                )
            elif response.status_code == 404:
                st.sidebar.error(f"❌ Tariff not found: {tariff_id}")
            else:
                st.sidebar.error(f"❌ API Error: {response.status_code}")
                st.sidebar.error(f"Details: {response.text}")

        except requests.exceptions.Timeout:
            st.sidebar.error("❌ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.sidebar.error(
                "❌ Connection error. Please check your internet connection."
            )
        except Exception as e:
            st.sidebar.error(f"❌ Error importing tariff: {str(e)}")


def _render_tariff_modification_section() -> None:
    """Render the tariff modification management section in sidebar."""
    import copy
    import json

    from urdb_viewer.config.settings import Settings

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
                except:
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
                                Settings.USER_DATA_DIR.mkdir(
                                    parents=True, exist_ok=True
                                )
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

        st.sidebar.markdown("---")
