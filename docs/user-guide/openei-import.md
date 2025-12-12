# OpenEI Tariff Import Guide

## Overview

The OpenEI Import feature allows you to import tariffs directly from the OpenEI Utility Rate Database API with one click.

## Quick Start (3 Steps)

### Step 1: Get an API Key (2 minutes)

1. Visit: https://openei.org/services/api/signup/
2. Fill out the simple registration form
3. Copy your API key

### Step 2: Configure Your API Key

Choose **ONE** method:

#### Option A: Streamlit Secrets (Recommended - Persistent)

1. Create/edit `.streamlit/secrets.toml` in your project root
2. Add your API key:

```toml
OPENEI_API_KEY = "paste_your_api_key_here"
```

**Why this is best:**
- ✅ Persistent across sessions
- ✅ Secure (not in git)
- ✅ Standard Streamlit approach

#### Option B: Environment Variable (Session-based)

**Windows PowerShell:**
```powershell
$env:OPENEI_API_KEY = "paste_your_api_key_here"
```

**Windows Command Prompt:**
```cmd
set OPENEI_API_KEY=paste_your_api_key_here
```

**Mac/Linux:**
```bash
export OPENEI_API_KEY="paste_your_api_key_here"
```

#### Option C: Enter in App (Temporary)

If you skip Step 2, the app will show an input field where you can paste your API key directly.

#### Option D: Override (Testing)

Even with a configured key, you can enter a different key in the app to temporarily override it.

### Step 3: Import a Tariff

1. **Find a tariff** on OpenEI.org:
   - Go to: https://openei.org/wiki/Utility_Rate_Database
   - Search for your utility and rate
   - Copy the tariff ID (24-character code)

2. **Import in app**:
   - Open URDB Tariff Viewer
   - Find the "🌐 Import from OpenEI" section in the sidebar
   - Paste your tariff ID
   - Click "📥 Import Tariff"
   - Wait for success message

3. **View your tariff**:
   - Refresh the page
   - Select from "👤 User Tariffs" dropdown
   - Analyze!

## Example

**Example Tariff ID:** `674e0b87201c6bd096007a5a`

1. Paste this ID in the "Tariff ID" field
2. Click "📥 Import Tariff"
3. You'll see: "✅ Imported: Utility_Name_Rate_Name.json"
4. Refresh and select your new tariff

## Pro Tips

- **Save API Key**: Use secrets.toml so you don't have to enter it every time
- **Bookmark IDs**: Keep a list of frequently used tariff IDs
- **Check Details**: Read the success message to verify correct tariff imported
- **Remember to Refresh**: New tariffs appear after page refresh

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Button is disabled | Enter both API key and tariff ID |
| "Invalid API key" | Check for typos or extra spaces |
| "Tariff not found" | Verify the tariff ID is correct |
| Don't see new tariff | Refresh the page |

## Important Links

- **Get API Key**: https://openei.org/services/api/signup/
- **Browse Tariffs**: https://openei.org/wiki/Utility_Rate_Database
- **OpenEI Home**: https://openei.org/
