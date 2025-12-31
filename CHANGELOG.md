# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Reorganized project structure to follow best practices
- Consolidated 47 documentation files into organized `docs/` folder
- Added pre-commit hooks for code quality

### Added
- LICENSE file (MIT)
- `.pre-commit-config.yaml` for automated code quality checks
- `urdb_viewer/py.typed` marker for PEP 561 compliance
- Proper `CHANGELOG.md` (this file)
- Consolidated documentation in `docs/` folder

### Fixed
- Fixed `sys.path` manipulation in main.py
- Updated package configuration in pyproject.toml

## [2.0.0] - 2025-11-23

### Added
- **Modular Architecture**: Complete restructure from monolithic app.py
- **Tariff Builder**: Create custom tariff JSON files through GUI
- **OpenEI Import**: Import tariffs directly from OpenEI API
- **Comprehensive Testing**: Full test suite with pytest integration
- **Enhanced Cost Calculator**: Advanced utility bill calculations
- **Load Profile Generator**: Create synthetic load profiles
- **Advanced Analytics**: Detailed load profile analysis tools
- **Modern UI**: Updated styling and improved user experience
- **Centralized Configuration**: Settings management in `urdb_viewer/config/`

### Changed
- Split monolithic `app.py` (3,333 lines) into modular components
- Reorganized data files into `data/` directory structure
- Moved from single requirements.txt to split requirements (base/dev/prod)

### Technical Details
- Components in `urdb_viewer/components/`
- Core business logic in `urdb_viewer/core/`
- Service layer in `urdb_viewer/services/`
- Data models in `urdb_viewer/models/`
- Utilities in `urdb_viewer/utils/`
- Configuration in `urdb_viewer/config/`

## [1.0.0] - 2024-09-06

### Added
- Initial release
- URDB JSON file viewing
- Energy rate visualization with heatmaps
- Demand charge display
- Rate editing capabilities
- Basic cost calculations
