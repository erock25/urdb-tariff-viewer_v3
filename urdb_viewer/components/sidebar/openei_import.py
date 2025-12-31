"""
OpenEI tariff import functionality for the sidebar.

This module handles importing tariffs from the OpenEI API.
"""

import json

import requests
import streamlit as st

from urdb_viewer.config.settings import Settings


def render_openei_import_section() -> None:
    """Render the OpenEI tariff import section in sidebar."""
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
        api_key: OpenEI API key
        tariff_id: Tariff ID to fetch
    """
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
