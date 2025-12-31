"""
URDB Tariff Viewer - A comprehensive Streamlit application for viewing and editing utility rate structures.

This package provides a modular structure for processing and visualizing utility tariff data
from the U.S. Utility Rate Database (URDB).

Package Structure:
    - core/: Pure Python business logic (framework-agnostic)
    - components/: Streamlit UI components
    - config/: Settings and constants
    - models/: Data models (TariffViewer, LoadProfileGenerator)
    - services/: Business logic services (orchestration layer)
    - ui/: Streamlit-specific utilities (bootstrap, caching)
    - utils/: Helper utilities (validators, formatters, etc.)
"""

__version__ = "2.1.0"
__author__ = "URDB Tariff Viewer Team"
