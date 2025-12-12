# Quick Reference Guide

## Running the Application

```bash
# Option 1: Direct
streamlit run src/main.py

# Option 2: Using launcher script
python run_app.py
```

## Application Tabs

| Tab | Purpose |
|-----|---------|
| 📋 Tariff Information | View energy/demand rates, schedules, basic info |
| 💰 Utility Cost Analysis | Calculate bills, analyze load factors |
| 🔧 Load Profile Generator | Create synthetic load profiles |
| 📊 LP Analysis | Analyze uploaded load profiles |
| 🏗️ Tariff Builder | Create custom tariff JSON files |

## File Locations

| Directory | Contents |
|-----------|----------|
| `data/tariffs/` | Sample tariff JSON files |
| `data/user_data/` | Your imported/created tariffs |
| `data/load_profiles/` | CSV load profile files |

## Keyboard Shortcuts

- **F5**: Refresh page (see new tariffs)
- **Ctrl+F**: Browser search within page

## Common Tasks

### Load a Tariff
1. Select from sidebar dropdown
2. Choose "📁 Sample Tariffs" or "👤 User Tariffs"

### Edit Rates
1. Go to Energy Rates or Demand Rates tab
2. Modify values in the rate table
3. Click "Apply Changes"
4. Download modified JSON

### Calculate Utility Bill
1. Load a tariff
2. Go to "💰 Utility Cost Analysis" → "Utility Bill Calculator"
3. Upload a load profile CSV or use generated profile
4. View cost breakdown

### Create New Tariff
1. Go to "🏗️ Tariff Builder" tab
2. Fill in Basic Info
3. Configure energy rates and schedules
4. Add demand charges (optional)
5. Save to user_data folder

### Import from OpenEI
1. Get API key from openei.org
2. Find tariff ID on OpenEI website
3. Enter in sidebar "🌐 Import from OpenEI" section
4. Click Import, then refresh

## Load Profile Format

CSV files should have columns:
- `timestamp`: ISO format datetime
- `load_kW` or `kW`: Power demand in kilowatts
- `kWh` (optional): Energy consumption

Example:
```csv
timestamp,load_kW
2025-01-01 00:00:00,150.5
2025-01-01 00:15:00,148.2
```

## Rate Structure

### Energy Rates ($/kWh)
- Time-of-Use periods with different rates
- Weekday and weekend schedules
- 24 hours × 12 months matrix

### Demand Charges ($/kW)
- TOU demand: varies by time period
- Flat demand: monthly fixed rate per kW

### Fixed Charges
- Monthly customer/service charges
- Applied regardless of usage

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No tariffs showing | Check `data/tariffs/` has JSON files |
| Import error | Verify JSON format matches URDB schema |
| Calculation error | Ensure load profile has required columns |
| Charts not loading | Try refreshing the page |

## Support

- Check the main README.md for detailed documentation
- Review tariff JSON structure in sample files
- Use validation in Tariff Builder to catch errors
