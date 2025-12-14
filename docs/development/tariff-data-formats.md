# Tariff Data Formats

This document describes the different tariff data formats used in the URDB ecosystem and the conversions required when working with tariff data from different sources.

## Overview

There are **two primary tariff data formats** used in this application:

1. **OpenEI API Format** (lowercase field names) - Used by the OpenEI URDB API and this application
2. **Local Database Format** (camelCase field names) - Used by MongoDB exports and the usurdb.parquet file

This application expects tariffs in **OpenEI API Format**. When importing tariffs from other sources (like the parquet database), conversion is required.

## Format Comparison

### OpenEI API Format (Expected by this app)

This is the format returned by the OpenEI URDB API and used by this application's TariffViewer model.

```json
{
  "items": [
    {
      "label": "6757525f259975f54b0eccbf",
      "utility": "Pacific Gas & Electric Co",
      "name": "BEV-2-S Business Electric Vehicle",
      "eiaid": 17609,
      "sector": "Commercial",
      "servicetype": "Bundled",
      "startdate": 1727762400,
      "enddate": null,
      "mindemand": 0,
      "maxdemand": 500,
      "minenergy": null,
      "maxenergy": null,
      "energyratestructure": [
        [{"unit": "kWh", "rate": 0.18081, "adj": 0.00}],
        [{"unit": "kWh", "rate": 0.15754, "adj": 0.00}]
      ],
      "energyweekdayschedule": [[0,0,0,...], ...],
      "energyweekendschedule": [[0,0,0,...], ...],
      "energytoulabels": ["Off-Peak", "Super Off-Peak", "Peak"],
      "demandratestructure": [...],
      "demandweekdayschedule": [[0,0,0,...], ...],
      "demandweekendschedule": [[0,0,0,...], ...],
      "flatdemandstructure": [[{"rate": 1.91, "adj": 0}]],
      "flatdemandmonths": [0,0,0,0,0,0,0,0,0,0,0,0],
      "fixedchargefirstmeter": 447.44,
      "fixedchargeunits": "$/month"
    }
  ]
}
```

### Local Database Format (MongoDB Export / usurdb.parquet)

This is the format used in MongoDB exports and stored in the usurdb.parquet file's `full_tariff_json` column.

```json
{
  "_id": {"$oid": "6757525f259975f54b0eccbf"},
  "utilityName": "Pacific Gas & Electric Co",
  "rateName": "BEV-2-S Business Electric Vehicle",
  "eiaId": 17609,
  "sector": "Commercial",
  "serviceType": "Bundled",
  "effectiveDate": {"$date": "2024-10-01T00:00:00Z"},
  "endDate": null,
  "demandMin": 0,
  "demandMax": 500,
  "energyMin": null,
  "energyMax": null,
  "energyRateStrux": [
    {"energyRateTiers": [{"unit": "kWh", "rate": 0.18081, "adj": 0.00}]},
    {"energyRateTiers": [{"unit": "kWh", "rate": 0.15754, "adj": 0.00}]}
  ],
  "energyWeekdaySched": [[0,0,0,...], ...],
  "energyWeekendSched": [[0,0,0,...], ...],
  "energyTOULabels": ["Off-Peak", "Super Off-Peak", "Peak"],
  "demandRateStrux": [...],
  "demandWeekdaySched": [[0,0,0,...], ...],
  "demandWeekendSched": [[0,0,0,...], ...],
  "flatDemandStrux": [{"flatDemandTiers": [{"rate": 1.91, "adj": 0}]}],
  "flatDemandMonths": [0,0,0,0,0,0,0,0,0,0,0,0],
  "fixedChargeFirstMeter": 447.44,
  "fixedChargeUnits": "$/month"
}
```

## Complete Field Mapping

| Local DB Format (camelCase) | API Format (lowercase) | Description |
|----------------------------|------------------------|-------------|
| `_id.$oid` | `label` | Unique tariff identifier |
| `utilityName` | `utility` | Utility company name |
| `rateName` | `name` | Rate schedule name |
| `eiaId` | `eiaid` | EIA utility ID |
| `serviceType` | `servicetype` | Service type (Bundled/Delivery/Energy) |
| `effectiveDate` | `startdate` | Rate effective date |
| `endDate` | `enddate` | Rate end date (if superseded) |
| `demandMin` | `mindemand` | Minimum demand (kW) |
| `demandMax` | `maxdemand` | Maximum demand (kW) |
| `energyMin` | `minenergy` | Minimum energy (kWh) |
| `energyMax` | `maxenergy` | Maximum energy (kWh) |
| `voltageCategory` | `voltagecategory` | Voltage level |
| `phaseWiring` | `phasewiring` | Phase configuration |
| **Energy Rates** | | |
| `energyRateStrux` | `energyratestructure` | Energy rate tiers by period |
| `energyWeekdaySched` | `energyweekdayschedule` | Weekday schedule (12x24 matrix) |
| `energyWeekendSched` | `energyweekendschedule` | Weekend schedule (12x24 matrix) |
| `energyTOULabels` | `energytoulabels` | TOU period labels |
| `energyComments` | `energycomments` | Energy rate notes |
| **Demand Rates** | | |
| `demandRateStrux` | `demandratestructure` | Demand rate tiers by period |
| `demandWeekdaySched` | `demandweekdayschedule` | Weekday demand schedule |
| `demandWeekendSched` | `demandweekendschedule` | Weekend demand schedule |
| `demandLabels` | `demandtoulabels` | Demand period labels |
| `demandUnits` | `demandunits` | Demand units (kW) |
| `demandRateUnit` | `demandrateunit` | Demand rate unit |
| **Flat Demand** | | |
| `flatDemandStrux` | `flatdemandstructure` | Flat demand rate tiers |
| `flatDemandMonths` | `flatdemandmonths` | Monthly period mapping |
| `flatDemandUnit` | `flatdemandunit` | Flat demand unit |
| **Fixed Charges** | | |
| `fixedChargeFirstMeter` | `fixedchargefirstmeter` | Monthly fixed charge |
| `fixedChargeUnits` | `fixedchargeunits` | Fixed charge units |
| `minMonthlyCharge` | `minmonthlycharge` | Minimum monthly charge |

## Rate Structure Format Differences

### Energy Rate Structure

**API Format** (flat array of arrays):
```json
"energyratestructure": [
  [{"unit": "kWh", "rate": 0.18081, "adj": 0.00}],
  [{"unit": "kWh", "rate": 0.15754, "adj": 0.00}]
]
```

**Local DB Format** (nested with tier key):
```json
"energyRateStrux": [
  {"energyRateTiers": [{"unit": "kWh", "rate": 0.18081, "adj": 0.00}]},
  {"energyRateTiers": [{"unit": "kWh", "rate": 0.15754, "adj": 0.00}]}
]
```

### Flat Demand Structure

**API Format**:
```json
"flatdemandstructure": [
  [{"rate": 1.91, "adj": 0}]
]
```

**Local DB Format**:
```json
"flatDemandStrux": [
  {"flatDemandTiers": [{"rate": 1.91, "adj": 0}]}
]
```

### Date Format Differences

**API Format** (Unix timestamp):
```json
"startdate": 1727762400
```

**Local DB Format** (MongoDB date object):
```json
"effectiveDate": {"$date": "2024-10-01T00:00:00Z"}
```

## Conversion Implementation

The conversion is handled by functions in `urdb_viewer/services/tariff_database_service.py`:

- `convert_local_to_api_format()` - Converts field names from camelCase to lowercase
- `normalize_rate_structures()` - Flattens nested tier structures to flat arrays
- `convert_tariff_to_json_format()` - Orchestrates the full conversion and wraps in `{items: []}`

### Key Conversion Steps

1. **Field Name Mapping**: Convert camelCase to lowercase
2. **ID Conversion**: Extract `label` from `_id.$oid`
3. **Date Conversion**: Convert MongoDB date objects to Unix timestamps
4. **Rate Structure Normalization**: Convert nested tier format to flat arrays

### Hybrid Format Handling

Some tariffs in the database have a **hybrid format** - lowercase field names but nested tier structures:

```json
{
  "utility": "Sacramento Municipal Utility District",
  "name": "CI-TOD4",
  "flatdemandstructure": [
    {"flatDemandTiers": [{"rate": 5.539}]}  // Nested - needs normalization!
  ]
}
```

The `normalize_rate_structures()` function handles this by detecting and flattening nested tiers even when field names are already lowercase.

### Usage

```python
from urdb_viewer.services.tariff_database_service import TariffDatabaseService

# Convert a single tariff
api_tariff = TariffDatabaseService.convert_local_to_api_format(local_tariff)

# The convert_tariff_to_json_format method auto-detects and converts if needed
json_data = TariffDatabaseService.convert_tariff_to_json_format(tariff)
# Returns: {"items": [converted_tariff]}
```

## Data Sources

### 1. OpenEI API

- **Format**: API Format (lowercase)
- **Access**: Via OpenEI API with API key
- **Conversion Required**: No

### 2. usurdb.parquet (Database Export)

- **Format**: Local DB Format (camelCase) stored in `full_tariff_json` column
- **Location**: `data/usurdb.parquet`
- **Conversion Required**: Yes - use `convert_local_to_api_format()`

### 3. User-uploaded JSON Files

- **Format**: Usually API Format (from OpenEI downloads)
- **Location**: `data/user_data/`
- **Conversion Required**: Depends on source

### 4. Built-in Tariff Files

- **Format**: API Format
- **Location**: `data/tariffs/`
- **Conversion Required**: No

## TariffViewer Model Field Access

The `TariffViewer` model in `urdb_viewer/models/tariff.py` expects API format fields:

```python
# These are the field names TariffViewer looks for:
energy_rates = self.tariff.get("energyratestructure", [])
weekday_schedule = self.tariff.get("energyweekdayschedule", [])
weekend_schedule = self.tariff.get("energyweekendschedule", [])
demand_rates = self.tariff.get("demandratestructure", [])
flat_demand_rates = self.tariff.get("flatdemandstructure", [])
flat_demand_months = self.tariff.get("flatdemandmonths", [])
```

## Troubleshooting

### "No energy rate structure found"

This error typically means the tariff is in Local DB format but wasn't converted. Check:

1. Is the tariff using camelCase field names (`energyRateStrux` instead of `energyratestructure`)?
2. Was `convert_local_to_api_format()` called before saving?

### Empty rate schedules

Check if the rate structure uses the nested tier format:
- `{"energyRateTiers": [...]}` needs conversion to `[[...]]`

### Missing utility/rate name

The tariff might use `utilityName`/`rateName` instead of `utility`/`name`.

## Best Practices

1. **Always save tariffs in API format** - The app's TariffViewer expects this format
2. **Use the conversion function** when importing from parquet or MongoDB exports
3. **Check format before processing** - Look for `utilityName` vs `utility` to detect format
4. **Test with sample tariffs** - Compare against working files in `data/tariffs/`

## Related Files

- `urdb_viewer/services/tariff_database_service.py` - Conversion functions
- `urdb_viewer/models/tariff.py` - TariffViewer model (expects API format)
- `urdb_viewer/components/tariff_database_search.py` - Database search UI
- `data/tariffs/*.json` - Example tariffs in API format
