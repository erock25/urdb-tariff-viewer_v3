"""
Tariff Builder package.

This package provides a GUI for creating new tariff JSON files from scratch,
with organized sections for each part of the tariff configuration.

Modules:
    - main: Main entry point and tab orchestration
    - utils: Shared utility functions and validation
    - sections/: Individual section renderers
"""

from .main import render_tariff_builder_tab
from .utils import (
    create_empty_tariff_structure,
    generate_filename,
    get_tariff_data,
    save_tariff,
    validate_tariff,
)

__all__ = [
    "render_tariff_builder_tab",
    "create_empty_tariff_structure",
    "get_tariff_data",
    "validate_tariff",
    "generate_filename",
    "save_tariff",
]
