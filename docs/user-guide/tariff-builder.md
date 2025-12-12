# Tariff Builder Guide

## Overview

The **Tariff Builder** is a feature in the URDB JSON Viewer that allows you to create custom utility tariff JSON files from scratch through an intuitive graphical user interface. This eliminates the need to manually edit JSON files and helps ensure your tariffs are properly formatted and valid.

## Accessing the Tariff Builder

1. Launch the application
2. Navigate to the **🏗️ Tariff Builder** tab
3. Start creating your tariff!

## Features

The Tariff Builder is organized into **7 sections** accessible via tabs:

### 1. 📋 Basic Info

Define the essential information about your tariff:

**Required Fields:**
- **Utility Company Name**: Name of the utility provider (e.g., "Pacific Gas & Electric Co")
- **Rate Schedule Name**: Name of the rate (e.g., "TOU-EV-9")
- **Description**: Detailed description of the rate and its applicability

**Optional Fields:**
- **Customer Sector**: Commercial, Residential, Industrial, Agricultural, or Lighting
- **Service Type**: Bundled, Energy Only, or Delivery Only
- **Voltage Category**: Secondary, Primary, or Transmission
- **Phase Wiring**: Single Phase or Three Phase
- **Country**: Default is "USA"
- **Source URLs**: Links to official tariff documents

### 2. ⚡ Energy Rates

Configure your Time-of-Use (TOU) energy rate structure:

1. **Set Number of TOU Periods**: Choose how many different rate periods you need (e.g., 3 for Peak/Mid-Peak/Off-Peak)
2. **For Each Period, Define:**
   - **Label**: Descriptive name (e.g., "Peak", "Off-Peak", "Super Off-Peak")
   - **Base Rate**: Energy rate in $/kWh
   - **Adjustment**: Additional charges or credits in $/kWh
   - **Total Rate**: Automatically calculated as Base + Adjustment

**Example:**
- Period 0: "Off-Peak" - $0.15/kWh
- Period 1: "Peak" - $0.35/kWh
- Period 2: "Super Off-Peak" - $0.10/kWh

### 3. 📅 Energy Schedule

Define when each TOU period applies throughout the year:

**Two Modes Available:**

#### Simple Mode (Recommended for beginners)
- Set one daily pattern for all months
- Choose weekday schedule (24 hourly selections)
- Option to use same schedule for weekends or create separate weekend schedule
- Schedule automatically applied to all 12 months

#### Advanced Mode
- Set different schedules for each month
- Separately configure weekday and weekend schedules
- Copy schedules between months
- Full control over seasonal variations

**Schedule Preview:**
- Visual heatmap showing your complete year schedule
- Legend showing which period applies to each hour/month
- Separate views for weekday and weekend

### 4. 🔌 Demand Charges (Optional)

Configure Time-of-Use demand charges if your tariff includes them:

1. **Enable TOU Demand**: Check if your tariff has time-varying demand charges
2. **Set Number of Demand Periods**: Similar to energy periods
3. **For Each Period:**
   - Base Rate in $/kW
   - Adjustment in $/kW
   - Total Rate (automatically calculated)

**Note:** If you only have flat demand charges, leave this section unchecked and configure them in the next tab.

### 5. 📊 Flat Demand

Define monthly flat demand charges (non-time-varying):

**Two Options:**

#### Same for All Months
- Single demand rate applied year-round
- Simple configuration for consistent charges

#### Seasonal Rates
- Define multiple seasons (e.g., Summer/Winter)
- Set different rates for each season
- Assign months to specific seasons
- Supports up to 12 different seasonal periods

**Example Seasonal Configuration:**
- Season 0 (Winter): $5.00/kW - Jan, Feb, Mar, Nov, Dec
- Season 1 (Summer): $15.00/kW - Jun, Jul, Aug, Sep
- Season 2 (Spring/Fall): $8.00/kW - Apr, May, Oct

### 6. 💰 Fixed Charges

Set fixed monthly charges that don't vary with usage:

- **Fixed Monthly Charge**: Customer charge or service charge in dollars
- **Charge Units**: $/month, $/day, or $/year

These charges apply regardless of energy consumption or demand.

### 7. 🔍 Preview & Save

Review, validate, and save your tariff:

**Features:**
- **Automatic Validation**: Checks for required fields and data consistency
- **JSON Preview**: View the complete JSON structure
- **Tariff Summary**: Quick overview of key configuration details
- **Save Options**: 
  - Save to `data/user_data/` directory
  - Download JSON file directly
  - Automatic filename generation based on utility and rate name

## Step-by-Step Tutorial

### Creating a Simple TOU Tariff

Let's create a basic commercial TOU tariff:

#### Step 1: Basic Info
```
Utility: My Electric Company
Rate Name: Commercial TOU-1
Sector: Commercial
Description: Basic commercial time-of-use rate for small businesses
```

#### Step 2: Energy Rates
Set up 3 TOU periods:
- **Off-Peak**: $0.12/kWh (base) + $0.02/kWh (adj) = $0.14/kWh
- **Mid-Peak**: $0.18/kWh (base) + $0.02/kWh (adj) = $0.20/kWh
- **Peak**: $0.28/kWh (base) + $0.02/kWh (adj) = $0.30/kWh

#### Step 3: Energy Schedule
Using Simple Mode:

**Weekday Pattern:**
- Hours 0-8: Off-Peak (Period 0)
- Hours 9-11: Mid-Peak (Period 1)
- Hours 12-16: Peak (Period 2)
- Hours 17-21: Mid-Peak (Period 1)
- Hours 22-23: Off-Peak (Period 0)

**Weekend:** Use same as weekday (or all Off-Peak for cheaper weekend rates)

#### Step 4: Demand Charges
Skip if not applicable, or add:
- Single demand period: $10.00/kW

#### Step 5: Flat Demand
- Same for all months: $5.00/kW

#### Step 6: Fixed Charges
- Fixed monthly charge: $25.00
- Units: $/month

#### Step 7: Save
- Review validation (should show ✅)
- Filename: `My_Electric_Company_Commercial_TOU-1`
- Click "💾 Save Tariff"

## Best Practices

### Data Entry
1. **Start with Basic Info**: Complete all required fields before moving to other sections
2. **Work Sequentially**: Follow the tab order for a logical workflow
3. **Use Descriptive Labels**: Make TOU period names clear (e.g., "Summer Peak" vs "Period 3")
4. **Preview Often**: Check the schedule heatmap to verify your configuration

### Validation
- Address all validation warnings before saving
- Ensure at least one energy rate is non-zero
- Verify schedules don't reference non-existent periods
- Check that rates are reasonable (not accidentally too high or low)

### File Management
- Use descriptive filenames: `Utility_RateName_Description`
- Save frequently to avoid losing work
- Download a backup copy of important tariffs
- Saved files appear in the sidebar under "👤 User Tariffs"

## Advanced Features

### Copying Existing Tariffs
1. Load an existing tariff in the app
2. Download it using the sidebar download button
3. Use it as a reference for your new tariff
4. Modify values in the Tariff Builder as needed

### Seasonal Variations
- Use "Advanced Mode" in Energy Schedule for month-specific patterns
- Configure seasonal flat demand rates for summer/winter differentials
- Assign different schedules to summer vs. winter months

### Multi-Tiered Structures
- The current version supports single-tier rates
- For tiered rates, you may need to manually edit the JSON after creation
- Consider creating a base tariff and then modifying it

## Troubleshooting

### Common Issues

**"Required fields missing" error:**
- Solution: Complete all fields marked with * in Basic Info tab

**"Schedule references non-existent period" error:**
- Solution: Check that your schedule periods (0, 1, 2, etc.) match the number of rate periods you defined

**"At least one energy rate should be non-zero" warning:**
- Solution: Ensure you've entered actual rate values, not just zeros

**Saved tariff doesn't appear in sidebar:**
- Solution: Refresh the page (F5) or restart the application

**Changes not saving:**
- Solution: Ensure you clicked the "💾 Save Tariff" button in the Preview & Save tab

## JSON Structure Reference

The Tariff Builder creates JSON files compatible with the U.S. Utility Rate Database (URDB) format. Key fields include:

```json
{
  "items": [{
    "utility": "string",
    "name": "string",
    "sector": "string",
    "description": "string",
    "energyratestructure": [[{"rate": 0.0, "adj": 0.0}]],
    "energytoulabels": ["string"],
    "energyweekdayschedule": [[24 integers per month, 12 months]],
    "energyweekendschedule": [[24 integers per month, 12 months]],
    "flatdemandstructure": [[{"rate": 0.0, "adj": 0.0}]],
    "flatdemandmonths": [12 integers],
    "fixedchargefirstmeter": 0.0,
    "fixedchargeunits": "$/month"
  }]
}
```

## Tips for Accurate Tariffs

1. **Reference Official Documents**: Always use the utility's official tariff sheets
2. **Include All Adjustments**: Add fuel adjustments, transmission charges, etc. in the "adj" field
3. **Verify Schedules**: Double-check that peak hours match the utility's definition
4. **Test with Load Profiles**: After creating your tariff, test it with the Cost Calculator
5. **Document Assumptions**: Use the description and comments fields to note any assumptions
