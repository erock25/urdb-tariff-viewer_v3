# Architecture Overview

## Project Structure

```
URDB_JSON_Viewer_v3/
├── urdb_viewer/            # Application source code (Python package)
│   ├── __init__.py
│   ├── main.py             # Application entry point
│   ├── components/         # Streamlit UI components
│   │   ├── cost_calculator.py
│   │   ├── demand_rates.py
│   │   ├── energy_rates.py
│   │   ├── flat_demand_rates.py
│   │   ├── load_generator.py
│   │   ├── sidebar.py
│   │   ├── tariff_builder.py
│   │   └── visualizations.py
│   ├── config/             # Configuration management
│   │   ├── constants.py
│   │   └── settings.py
│   ├── models/             # Data models
│   │   ├── load_profile.py
│   │   └── tariff.py
│   ├── services/           # Business logic
│   │   ├── calculation_engine.py
│   │   ├── calculation_service.py
│   │   ├── file_service.py
│   │   └── tariff_service.py
│   └── utils/              # Utilities
│       ├── exceptions.py
│       ├── helpers.py
│       ├── styling.py
│       └── validators.py
├── data/                   # Data files
│   ├── tariffs/            # Sample tariff JSONs
│   ├── load_profiles/      # Load profile CSVs
│   └── user_data/          # User-created tariffs
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures
│   ├── test_models/
│   └── test_services/
├── docs/                   # Documentation
│   ├── user-guide/
│   └── development/
└── scripts/                # Utility scripts
```

## Component Architecture

### Layers

```
┌─────────────────────────────────────────┐
│           Streamlit UI Layer            │
│      (urdb_viewer/components/*.py)      │
├─────────────────────────────────────────┤
│           Service Layer                 │
│       (urdb_viewer/services/*.py)       │
├─────────────────────────────────────────┤
│           Model Layer                   │
│        (urdb_viewer/models/*.py)        │
├─────────────────────────────────────────┤
│        Config & Utilities               │
│ (urdb_viewer/config/*.py, urdb_viewer/utils/*.py) │
└─────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Sidebar/UI Components
2. **Components** → Call Services for business logic
3. **Services** → Use Models for data operations
4. **Models** → Read/write data files
5. **Results** → Rendered by Components

## Key Components

### Models

#### `TariffViewer`
- Loads and parses URDB JSON files
- Provides access to rate structures
- Handles schedule data (weekday/weekend)

#### `LoadProfileGenerator`
- Creates synthetic load profiles
- Aligns with TOU periods
- Supports customizable parameters

### Services

#### `FileService`
- File I/O operations
- JSON/CSV parsing
- Path management

#### `CalculationService`
- Utility bill calculations
- Load factor analysis
- Cost breakdowns

#### `TariffService`
- Tariff validation
- Rate structure operations
- Schedule manipulation

### Components

Each component is a self-contained Streamlit UI module:

| Component | Responsibility |
|-----------|----------------|
| `sidebar` | Navigation, file selection |
| `energy_rates` | Energy rate display/editing |
| `demand_rates` | Demand charge management |
| `cost_calculator` | Bill calculation UI |
| `load_generator` | Profile generation UI |
| `tariff_builder` | Tariff creation wizard |
| `visualizations` | Charts and heatmaps |

## Configuration

### Settings Class

Centralized configuration in `urdb_viewer/config/settings.py`:

```python
class Settings:
    BASE_DIR = Path(__file__).parent.parent.parent
    TARIFFS_DIR = DATA_DIR / "tariffs"
    USER_DATA_DIR = DATA_DIR / "user_data"
    # ...
```

### Constants

Static values in `urdb_viewer/config/constants.py`:
- Month names
- Default chart dimensions
- Rate unit labels

## Testing Strategy

### Unit Tests
- Model methods
- Service functions
- Utility helpers

### Integration Tests
- Component rendering
- End-to-end workflows

### Fixtures
Shared test data in `tests/conftest.py`:
- Sample tariff data
- Load profile data
- Temporary files

## Development Workflow

```bash
# Install dev dependencies
pip install -r requirements/dev.txt

# Run tests
pytest

# Format code
black urdb_viewer/ tests/
isort urdb_viewer/ tests/

# Type checking
mypy urdb_viewer/

# Run app locally
streamlit run streamlit_app.py
```

## Extending the Application

### Adding a New Component

1. Create `urdb_viewer/components/new_component.py`
2. Add render function: `render_new_component_tab()`
3. Export in `urdb_viewer/components/__init__.py`
4. Import and use in `urdb_viewer/main.py`

### Adding a New Service

1. Create `urdb_viewer/services/new_service.py`
2. Implement service class or functions
3. Export in `urdb_viewer/services/__init__.py`
4. Add tests in `tests/test_services/`

### Adding a New Model

1. Create `urdb_viewer/models/new_model.py`
2. Define data class or model class
3. Export in `urdb_viewer/models/__init__.py`
4. Add tests in `tests/test_models/`
