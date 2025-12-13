"""
Utility functions for the tariff builder.

Contains shared helper functions, validation logic, and data structure creation.
"""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from src.config.settings import Settings


def create_empty_tariff_structure() -> Dict[str, Any]:
    """
    Create an empty tariff structure with default values.
    
    Returns:
        Dict[str, Any]: Empty tariff structure
    """
    return {
        "items": [{
            # Basic information
            "utility": "",
            "name": "",
            "sector": "Commercial",
            "servicetype": "Bundled",
            "description": "",
            "source": "",
            "sourceparent": "",
            "country": "USA",
            
            # Voltage and service parameters
            "voltagecategory": "Secondary",
            "phasewiring": "Single Phase",
            "demandunits": "kW",
            
            # Energy rate structure
            "energyratestructure": [
                [{"unit": "kWh", "rate": 0.0, "adj": 0.0}]
            ],
            "energytoulabels": ["Period 0"],
            "energyweekdayschedule": [[0] * 24 for _ in range(12)],
            "energyweekendschedule": [[0] * 24 for _ in range(12)],
            "energycomments": "",
            
            # Demand rate structure (optional)
            "demandrateunit": "kW",
            "demandratestructure": [],
            "demandweekdayschedule": [],
            "demandweekendschedule": [],
            "demandcomments": "",
            
            # Flat demand structure (optional)
            "flatdemandunit": "kW",
            "flatdemandstructure": [[{"rate": 0.0, "adj": 0.0}]],
            "flatdemandmonths": [0] * 12,
            
            # Fixed charges
            "fixedchargefirstmeter": 0.0,
            "fixedchargeunits": "$/month",
            
            # Metadata
            "approved": True,
            "is_default": False,
            "startdate": int(datetime.now().timestamp()),
        }]
    }


def get_tariff_data() -> Dict[str, Any]:
    """
    Get the current tariff builder data from session state.
    
    Initializes with empty structure if not present.
    
    Returns:
        Dict[str, Any]: Current tariff data
    """
    if 'tariff_builder_data' not in st.session_state:
        st.session_state.tariff_builder_data = create_empty_tariff_structure()
    return st.session_state.tariff_builder_data['items'][0]


def validate_tariff(tariff_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate the tariff configuration.
    
    Args:
        tariff_data: Tariff data dictionary
    
    Returns:
        Tuple of (is_valid, list of validation messages)
    """
    messages = []
    
    # Required fields
    if not tariff_data.get('utility'):
        messages.append("Utility company name is required")
    
    if not tariff_data.get('name'):
        messages.append("Rate schedule name is required")
    
    if not tariff_data.get('description'):
        messages.append("Description is required")
    
    # Energy rates validation
    if not tariff_data.get('energyratestructure'):
        messages.append("At least one energy rate period is required")
    else:
        has_nonzero = any(
            rate[0].get('rate', 0) != 0 
            for rate in tariff_data['energyratestructure']
        )
        if not has_nonzero:
            messages.append("At least one energy rate should be non-zero")
    
    # Check schedules match rate structure
    num_energy_periods = len(tariff_data.get('energyratestructure', []))
    for month_schedule in tariff_data.get('energyweekdayschedule', []):
        if any(period >= num_energy_periods for period in month_schedule):
            messages.append("Energy schedule references non-existent period")
            break
    
    return (len(messages) == 0, messages)


def show_section_validation(section: str, data: Dict) -> None:
    """
    Show validation status for a section.
    
    Args:
        section: Section identifier ('basic_info', 'energy_rates', etc.)
        data: Tariff data dictionary
    """
    if section == "basic_info":
        missing = []
        if not data.get('utility'):
            missing.append("Utility Company Name")
        if not data.get('name'):
            missing.append("Rate Schedule Name")
        if not data.get('description'):
            missing.append("Description")
        
        if missing:
            st.warning(f"⚠️ Required fields missing: {', '.join(missing)}")
        else:
            st.success("✅ All required fields completed!")
    
    elif section == "energy_rates":
        has_rates = any(
            rate[0].get('rate', 0) > 0 
            for rate in data.get('energyratestructure', [])
        )
        if not has_rates:
            st.warning("⚠️ At least one energy rate should be greater than 0")
        else:
            st.success("✅ Energy rates configured!")


def generate_filename(tariff_data: Dict) -> str:
    """
    Generate a filename based on tariff data.
    
    Args:
        tariff_data: Tariff data dictionary
        
    Returns:
        Sanitized filename string
    """
    utility = tariff_data.get('utility', 'Unknown').replace(' ', '_')
    name = tariff_data.get('name', 'Tariff').replace(' ', '_')
    
    filename = f"{utility}_{name}"
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    
    return filename


def save_tariff(data: Dict, filename: str) -> None:
    """
    Save the tariff to a JSON file.
    
    Args:
        data: Complete tariff data (with 'items' wrapper)
        filename: Desired filename (without .json extension)
    """
    try:
        clean_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename.strip())
        if not clean_filename.endswith('.json'):
            clean_filename += '.json'
        
        Settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        filepath = Settings.USER_DATA_DIR / clean_filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Tariff saved successfully as '{clean_filename}'!")
        st.info("🔄 Refresh the page or reselect from the sidebar to view your new tariff.")
        
        # Offer download button
        json_string = json.dumps(data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON File",
            data=json_string,
            file_name=clean_filename,
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"❌ Error saving tariff: {str(e)}")

