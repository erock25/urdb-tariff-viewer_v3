# URDB Tariff Viewer & Editor

A comprehensive, modular Streamlit application for viewing and editing utility rate structures from the U.S. Utility Rate Database (URDB). This application provides interactive visualizations, editing capabilities, cost calculations, and load profile generation for utility rate analysis.

## ✨ Key Features

- **🏗️ Modular Architecture**: Complete restructure for better team collaboration and maintainability
- **🧪 Comprehensive Testing**: Full test suite with pytest integration
- **💰 Enhanced Cost Calculator**: Advanced utility bill calculations with load profile analysis
- **🔧 Load Profile Generator**: Create synthetic load profiles aligned with TOU periods
- **📊 Advanced Analytics**: Detailed load profile analysis and comparison tools
- **🎨 Modern UI**: Updated styling with improved user experience
- **⚙️ Better Configuration**: Centralized settings and environment management
- **🛠️ Tariff Builder**: NEW! Create custom tariff JSON files from scratch through an intuitive GUI
- **🌐 OpenEI Import**: NEW! Import tariffs directly from OpenEI's API with one click

## Features

### ⚡ Energy Rate Management
- **Time-of-Use Energy Rates**: Interactive heatmaps showing energy rates ($/kWh) by hour and month
- **Weekday vs Weekend**: Separate visualizations for weekday and weekend energy rates
- **Real-time Editing**: Modify energy rates directly through the interface
- **Rate Statistics**: Summary metrics including highest, lowest, and average rates

### 🔌 Demand Charge Management
- **Time-of-Use Demand Rates**: Interactive heatmaps showing demand charges ($/kW) by hour and month
- **Seasonal Flat Demand Rates**: Bar charts displaying monthly flat demand rates
- **Demand Rate Editing**: Modify both time-of-use and flat demand rates
- **Demand Charge Details**: Comprehensive information about demand charge structures

### 💰 Utility Cost Analysis
- **Bill Calculations**: Calculate annual utility costs using real load profiles
- **Cost Breakdowns**: Detailed analysis of energy, demand, and fixed charges
- **Multiple Tariff Comparison**: Compare costs across different rate schedules
- **Export Results**: Download calculation results in multiple formats

### 🔧 Load Profile Generator
- **Synthetic Profiles**: Generate realistic load profiles based on TOU periods
- **Customizable Parameters**: Adjust load factor, seasonal variation, and daily patterns
- **Validation Tools**: Ensure generated profiles meet specified criteria
- **Export Capabilities**: Save generated profiles for use in cost calculations

### 📊 Advanced Visualizations
- **Interactive Heatmaps**: Modern, responsive rate visualizations
- **Load Duration Curves**: Analyze load profile characteristics
- **Cost Comparison Charts**: Visual comparison of tariff options

### 🛠️ Tariff Builder (NEW!)
- **Create Custom Tariffs**: Build new tariff JSON files from scratch through an intuitive GUI
- **Wizard Interface**: 7-section guided workflow for easy tariff creation
- **Visual Schedule Editor**: Set time-of-use schedules with simple or advanced modes
- **Real-time Validation**: Ensure tariff data is complete and properly formatted
- **Schedule Preview**: Visual heatmap showing your complete TOU schedule
- **Save & Export**: Save to user_data directory or download directly
- **URDB Compatible**: Creates properly formatted URDB JSON files
- **No JSON Editing Required**: Build complex tariffs without manual file editing

📚 **Documentation**: See [Tariff Builder Guide](docs/user-guide/tariff-builder.md) for detailed instructions

### 🌐 OpenEI Tariff Import (NEW!)
- **Direct API Integration**: Import tariffs directly from OpenEI's Utility Rate Database
- **Simple ID Entry**: Paste a tariff ID and import with one click
- **Automatic Saving**: Imported tariffs saved automatically to user_data directory
- **Smart Naming**: Files named using utility and rate name for easy identification
- **Flexible Authentication**: Use secrets.toml (recommended), environment variable, or direct input for API key
- **Override Capability**: Temporarily use a different API key without changing configuration

📚 **Documentation**: See [OpenEI Import Guide](docs/user-guide/openei-import.md) for setup and usage

## Installation

### Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd URDB_JSON_Viewer_v3
```

2. Install dependencies:
```bash
pip install -r requirements/base.txt
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

#### Using `uv` (recommended)

If you use `uv`, you can create/sync the environment and run Streamlit like this:

```bash
uv sync
uv run --no-sync streamlit run streamlit_app.py
```

### Development Setup

For development with testing and code quality tools:

```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=urdb_viewer --cov-report=html

# Format code
black urdb_viewer/ tests/
isort urdb_viewer/ tests/

# Type checking
mypy urdb_viewer/
```

## Usage

### Loading Tariff Files
- Place your URDB JSON files in `data/tariffs/` (sample tariffs) or `data/user_data/` (your own)
- The application will automatically detect and list available tariff files
- Select a tariff file from the sidebar to begin analysis

### Editing Rates
1. **Select Rate Type**: Choose between "Energy" or "Demand" rates
2. **Choose Time Period**: Select month, hour, and day type (weekday/weekend)
3. **Modify Rate**: Enter the new rate value
4. **Apply Changes**: Click "Update Rate" to apply modifications
5. **Save Changes**: Use the sidebar **Save As New File** flow (saves to `data/user_data/`)

### Creating New Tariffs (Tariff Builder)
1. **Access the Builder**: Navigate to the "🏗️ Tariff Builder" tab
2. **Basic Information**: Fill in utility name, rate name, sector, and description
3. **Energy Rates**: Define your TOU periods and rates ($/kWh)
4. **Schedule Configuration**: Set when each rate period applies (Simple or Advanced mode)
5. **Optional Charges**: Add demand charges, flat demand, and fixed charges as needed
6. **Validate & Save**: Review your configuration and save to user_data directory
7. **Use Your Tariff**: Refresh the page and select your new tariff from the sidebar

📖 **Detailed Guide**: See [Tariff Builder Guide](docs/user-guide/tariff-builder.md) for comprehensive instructions

### Understanding the Visualizations
- **Energy Rates**: Displayed in $/kWh with blue color gradients
- **Demand Rates**: Displayed in $/kW with similar color schemes
- **Flat Demand Rates**: Monthly bar charts showing seasonal demand charges
- **Combined View**: Comparative analysis and rate distribution charts

## Data Structure Support

The application supports the following URDB JSON fields:

### Energy Rates
- `energyratestructure`: Rate structure with tiers and rates
- `energyweekdayschedule`: Weekday hourly schedule mapping
- `energyweekendschedule`: Weekend hourly schedule mapping

### Demand Charges
- `demandratestructure`: Demand rate structure with tiers and rates
- `demandweekdayschedule`: Weekday demand schedule mapping
- `demandweekendschedule`: Weekend demand schedule mapping
- `flatdemandstructure`: Seasonal/monthly flat demand rates
- `flatdemandmonths`: Month-to-period mapping for flat demand

### Additional Fields
- `demandrateunit`: Unit for demand charges (kW, kVA, etc.)
- `demandwindow`: Demand measurement window in minutes
- `demandratchetpercentage`: Demand ratchet percentages
- `demandreactivepowercharge`: Reactive power charges

## File Format

The application expects URDB JSON files in the standard format:
```json
{
  "items": [
    {
      "utility": "Utility Company Name",
      "name": "Rate Name",
      "sector": "Residential/Commercial/Industrial",
      "energyratestructure": [...],
      "demandratestructure": [...],
      "energyweekdayschedule": [...],
      "demandweekdayschedule": [...],
      ...
    }
  ]
}
```

## Output

Modified tariffs are saved to `data/user_data/` (typically with a `modified_` prefix unless you choose a custom filename).

## Project Structure

```
URDB_JSON_Viewer_v3/
├── streamlit_app.py        # Streamlit entry point (recommended)
├── urdb_viewer/            # Application source code (Python package)
│   ├── main.py             # Composes UI tabs and routes
│   ├── components/         # Streamlit UI components
│   ├── services/           # Business logic (framework-agnostic)
│   ├── models/             # Data models (framework-agnostic)
│   ├── utils/              # Utilities
│   ├── ui/                 # Streamlit-specific glue (session state, caching wrappers)
│   └── config/             # Configuration
├── data/                   # Data files
│   ├── tariffs/            # Sample tariffs
│   ├── load_profiles/      # Load profile CSVs
│   └── user_data/          # User-created tariffs
├── tests/                  # Test suite
├── docs/                   # Documentation
│   ├── user-guide/         # User documentation
│   └── development/        # Developer documentation
└── requirements/           # Dependencies
```

## Documentation

- [Quick Reference](docs/user-guide/quick-reference.md) - Common tasks and shortcuts
- [Tariff Builder Guide](docs/user-guide/tariff-builder.md) - Create custom tariffs
- [OpenEI Import Guide](docs/user-guide/openei-import.md) - Import from OpenEI API
- [Deployment Guide](docs/deployment.md) - Deploy to various platforms
- [Architecture](docs/development/architecture.md) - Technical overview
- [Changelog](CHANGELOG.md) - Version history

## Requirements

- Python 3.9+
- Streamlit 1.28.0+
- Pandas 2.0.0+
- NumPy 1.24.0+
- Plotly 5.15.0+

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black urdb_viewer/ tests/
isort urdb_viewer/ tests/
```

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Data visualization powered by [Plotly](https://plotly.com/)
- Based on the [U.S. Utility Rate Database](https://openei.org/wiki/Utility_Rate_Database) from OpenEI
