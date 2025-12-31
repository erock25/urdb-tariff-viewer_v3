"""
Streamlit caching wrappers.

Core services are intentionally kept free of Streamlit dependencies; cache those
operations here for the Streamlit app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

import streamlit as st

from urdb_viewer.utils.validators import validate_load_profile as _validate_load_profile


@st.cache_data(ttl=60)
def validate_load_profile(load_profile_path: Union[str, Path]) -> Dict[str, Any]:
    """Cached wrapper for load profile validation.

    Delegates to `urdb_viewer.utils.validators.validate_load_profile`.
    """
    return _validate_load_profile(load_profile_path)
