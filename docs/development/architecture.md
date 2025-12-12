# Architecture Overview

## Project Structure

```
URDB_JSON_Viewer_v3/
├── src/                    # Application source code
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
│         (src/components/*.py)           │
├─────────────────────────────────────────┤
│           Service Layer                 │
│         (src/services/*.py)             │
├─────────────────────────────────────────┤
│           Model Layer                   │
│          (src/models/*.py)              │
├─────────────────────────────────────────┤
│        Config & Utilities               │
│    (src/config/*.py, src/utils/*.py)    │
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

Centralized configuration in `src/config/settings.py`:

```python
class Settings:
    BASE_DIR = Path(__file__).parent.parent.parent
    TARIFFS_DIR = DATA_DIR / "tariffs"
    USER_DATA_DIR = DATA_DIR / "user_data"
    # ...
```

### Constants

Static values in `src/config/constants.py`:
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
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Run app locally
streamlit run src/main.py
```

## Extending the Application

### Adding a New Component

1. Create `src/components/new_component.py`
2. Add render function: `render_new_component_tab()`
3. Export in `src/components/__init__.py`
4. Import and use in `src/main.py`

### Adding a New Service

1. Create `src/services/new_service.py`
2. Implement service class or functions
3. Export in `src/services/__init__.py`
4. Add tests in `tests/test_services/`

### Adding a New Model

1. Create `src/models/new_model.py`
2. Define data class or model class
3. Export in `src/models/__init__.py`
4. Add tests in `tests/test_models/`
