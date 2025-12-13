# Migration Guide: v1 → v2

This guide explains changes in version 2.0 and how to migrate from the old monolithic structure to the new modular architecture.

## Overview of Changes

Version 2.0 represents a complete architectural overhaul, transforming from a single large file into a well-organized, modular application.

## Directory Structure Changes

### Before (v1.x)
```
URDB_JSON_Viewer/
├── app.py (3,333 lines - everything!)
├── calculate_utility_bill.py
├── tariffs/
├── load_profiles/
└── requirements.txt
```

### After (v2.0)
```
URDB_JSON_Viewer_v3/
├── urdb_viewer/
│   ├── main.py (entry point)
│   ├── models/
│   ├── services/
│   ├── components/
│   ├── utils/
│   └── config/
├── data/
├── tests/
├── docs/
├── requirements/
└── pyproject.toml
```

## Running the Application

**Old way:**
```bash
streamlit run app.py
```

**New way:**
```bash
# Option 1: Direct
streamlit run streamlit_app.py
# Option 3: Development mode
pip install -e .
urdb-viewer
```

## Component Mapping

Where old code moved:

| Old Location | New Location |
|--------------|--------------|
| TariffViewer class | `urdb_viewer/models/tariff.py` |
| Load profile generation | `urdb_viewer/models/load_profile.py` |
| CSS styling | `urdb_viewer/utils/styling.py` |
| Main UI logic | `urdb_viewer/components/*.py` |
| File operations | `urdb_viewer/services/file_service.py` |
| Calculations | `urdb_viewer/services/calculation_service.py` |

## Configuration Changes

### Dependencies

**Old:** Single `requirements.txt`

**New:** Organized in `requirements/`:
- `base.txt` - Core dependencies
- `dev.txt` - Development tools
- `prod.txt` - Production-specific

### Settings

**Old:** Hardcoded values throughout code

**New:** Centralized in `urdb_viewer/config/`:
- `settings.py` - Application settings
- `constants.py` - Constants and defaults

## Migration Checklist

If migrating custom changes from v1:

- [ ] Move custom tariffs to `data/user_data/`
- [ ] Move load profiles to `data/load_profiles/`
- [ ] Identify which module custom code belongs in
- [ ] Update dependencies to use new requirements structure
- [ ] Update automation scripts for new entry point

## Benefits of New Structure

### For Development
- Faster development with smaller files
- Better IDE support
- Easier debugging
- Code reuse

### For Teams
- Parallel development
- Cleaner merges
- Focused code reviews
- Faster onboarding

### For Maintenance
- Isolated changes
- Better test coverage
- Organized documentation
- Flexible deployment

## Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'src'`
**Solution:** Run from project root directory

**Issue:** Import errors
**Solution:** Check `__init__.py` files exist in all packages

**Issue:** Missing dependencies
**Solution:** `pip install -r requirements/base.txt`
