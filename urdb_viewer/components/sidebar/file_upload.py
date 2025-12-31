"""
File upload functionality for the sidebar.

This module handles tariff file uploads including validation and saving.
"""

import json
import re
from pathlib import Path
from typing import Optional

import streamlit as st

from urdb_viewer.config.settings import Settings


def handle_file_upload(uploaded_file) -> None:
    """
    Handle file upload functionality.

    Validates the uploaded file and saves it to the user_data directory.

    Args:
        uploaded_file: Streamlit UploadedFile object
    """
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
