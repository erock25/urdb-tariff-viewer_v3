"""
Tariff download functionality for the sidebar.

This module handles downloading the currently selected tariff as JSON.
"""

import json
import re
from pathlib import Path

import streamlit as st

from urdb_viewer.models.tariff import TariffViewer


def render_download_section(selected_tariff_file: Path) -> None:
    """
    Render the download section for current tariff.

    Args:
        selected_tariff_file: Path to the currently selected tariff file
    """
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
