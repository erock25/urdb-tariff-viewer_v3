"""
Pytest configuration and shared fixtures for URDB Tariff Viewer tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from urdb_viewer.config.constants import MONTHS
from urdb_viewer.models.load_profile import LoadProfileGenerator
from urdb_viewer.models.tariff import TariffViewer


@pytest.fixture
def sample_tariff_data() -> Dict[str, Any]:
    """Sample tariff data for testing."""
    return {
        "utility": "Test Utility",
        "name": "Test Rate Schedule",
        "sector": "Commercial",
        "description": "Test tariff for unit testing",
        "energyratestructure": [
            [{"rate": 0.1000, "adj": 0.0000}],  # Off-peak
            [{"rate": 0.1500, "adj": 0.0000}],  # Mid-peak
            [{"rate": 0.2000, "adj": 0.0000}],  # Peak
        ],
        "energyweekdayschedule": [
            [0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0]
            for _ in range(12)
        ],
        "energyweekendschedule": [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
            for _ in range(12)
        ],
        "energytoulabels": ["Off-Peak", "Mid-Peak", "Peak"],
        "demandratestructure": [
            [{"rate": 10.00, "adj": 0.00}],  # Off-peak demand
            [{"rate": 15.00, "adj": 0.00}],  # Peak demand
        ],
        "demandweekdayschedule": [
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
            for _ in range(12)
        ],
        "demandweekendschedule": [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for _ in range(12)
        ],
        "flatdemandstructure": [
            [{"rate": 8.00, "adj": 0.00}],  # Winter
            [{"rate": 12.00, "adj": 0.00}],  # Summer
        ],
        "flatdemandmonths": [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0],  # Summer: Apr-Sep
    }


@pytest.fixture
def sample_wrapped_tariff_data(sample_tariff_data) -> Dict[str, Any]:
    """Sample tariff data wrapped in 'items' array."""
    return {"items": [sample_tariff_data]}


@pytest.fixture
def sample_load_profile_data() -> pd.DataFrame:
    """Sample load profile data for testing."""
    # Create 1 week of 15-minute data
    timestamps = pd.date_range(
        "2025-01-01", periods=672, freq="15min"
    )  # 1 week = 672 15-min intervals

    # Create realistic load pattern
    load_kw = []
    for ts in timestamps:
        hour = ts.hour
        weekday = ts.weekday()

        # Base load pattern
        if weekday < 5:  # Weekday
            if 6 <= hour <= 18:  # Business hours
                base_load = 200 + 50 * (1 + 0.5 * (hour - 12) / 6)
            else:
                base_load = 150
        else:  # Weekend
            base_load = 120

        # Add some randomness
        import random

        random.seed(42)  # For reproducible tests
        load_kw.append(base_load * (1 + random.uniform(-0.1, 0.1)))

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "load_kW": load_kw,
            "kWh": [load / 4 for load in load_kw],  # 15-min = 0.25 hours
        }
    )


@pytest.fixture
def temp_tariff_file(sample_wrapped_tariff_data) -> Path:
    """Create a temporary tariff JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_wrapped_tariff_data, f, indent=2)
        return Path(f.name)


@pytest.fixture
def temp_load_profile_file(sample_load_profile_data) -> Path:
    """Create a temporary load profile CSV file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_load_profile_data.to_csv(f.name, index=False)
        return Path(f.name)


@pytest.fixture
def tariff_viewer(temp_tariff_file) -> TariffViewer:
    """TariffViewer instance for testing."""
    return TariffViewer(temp_tariff_file)


@pytest.fixture
def load_profile_generator(sample_tariff_data) -> LoadProfileGenerator:
    """LoadProfileGenerator instance for testing."""
    return LoadProfileGenerator(
        tariff=sample_tariff_data, avg_load=250.0, load_factor=0.7, year=2025
    )


@pytest.fixture
def cleanup_temp_files():
    """Clean up temporary files after tests."""
    temp_files = []

    def _add_temp_file(file_path: Path):
        temp_files.append(file_path)

    yield _add_temp_file

    # Cleanup
    for file_path in temp_files:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors
