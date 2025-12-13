"""
Streamlit caching wrappers.

Core services are intentionally kept free of Streamlit dependencies; cache those
operations here for the Streamlit app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Union

import streamlit as st

from urdb_viewer.services.calculation_service import CalculationService


@st.cache_data(ttl=60)
def validate_load_profile(load_profile_path: Union[str, Path]) -> Dict[str, Any]:
    """Cached wrapper for `CalculationService.validate_load_profile`."""
    return CalculationService.validate_load_profile(load_profile_path)
