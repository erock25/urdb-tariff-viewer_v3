"""
Backward compatibility shim for sidebar module.

This module has been refactored into a sub-package at `urdb_viewer.components.sidebar/`.
All imports are re-exported here for backward compatibility.

New code should import directly from the sidebar package:
    from urdb_viewer.components.sidebar import create_sidebar
"""

# Re-export everything from the new location for backward compatibility
from urdb_viewer.components.sidebar.download import render_download_section
from urdb_viewer.components.sidebar.file_upload import (
    handle_file_upload,
    show_file_upload_section,
)
from urdb_viewer.components.sidebar.main import create_sidebar, show_advanced_options
from urdb_viewer.components.sidebar.modification import (
    render_tariff_modification_section,
)
from urdb_viewer.components.sidebar.openei_import import render_openei_import_section

# Private function aliases for backward compatibility
_handle_file_upload = handle_file_upload
_render_download_section = render_download_section
_render_openei_import_section = render_openei_import_section
_render_tariff_modification_section = render_tariff_modification_section

__all__ = [
    "create_sidebar",
    "show_file_upload_section",
    "show_advanced_options",
    # Re-export internal functions for any code that depends on them
    "handle_file_upload",
    "render_download_section",
    "render_openei_import_section",
    "render_tariff_modification_section",
]
