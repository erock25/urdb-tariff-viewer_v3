"""
Tests for the TariffViewer model.
"""

from pathlib import Path

import pandas as pd
import pytest

from urdb_viewer.models.tariff import (
    TariffViewer,
    create_temp_viewer_with_modified_tariff,
)


class TestTariffViewer:
    """Test cases for TariffViewer class."""

    def test_init_with_wrapped_data(self, temp_tariff_file):
        """Test initialization with wrapped tariff data."""
        viewer = TariffViewer(temp_tariff_file)

        assert viewer.utility_name == "Test Utility"
        assert viewer.rate_name == "Test Rate Schedule"
        assert viewer.sector == "Commercial"
        assert viewer.description == "Test tariff for unit testing"

    def test_init_with_direct_data(self, sample_tariff_data, tmp_path):
        """Test initialization with direct tariff data."""
        # Create temp file with direct data (not wrapped)
        tariff_file = tmp_path / "direct_tariff.json"
        import json

        with open(tariff_file, "w") as f:
            json.dump(sample_tariff_data, f)

        viewer = TariffViewer(tariff_file)

        assert viewer.utility_name == "Test Utility"
        assert viewer.rate_name == "Test Rate Schedule"

    def test_rate_dataframes_creation(self, tariff_viewer):
        """Test that rate DataFrames are created correctly."""
        # Check weekday energy rates
        assert isinstance(tariff_viewer.weekday_df, pd.DataFrame)
        assert tariff_viewer.weekday_df.shape == (12, 24)  # 12 months, 24 hours
        assert list(tariff_viewer.weekday_df.index) == tariff_viewer.months

        # Check weekend energy rates
        assert isinstance(tariff_viewer.weekend_df, pd.DataFrame)
        assert tariff_viewer.weekend_df.shape == (12, 24)

        # Check demand rates
        assert isinstance(tariff_viewer.demand_weekday_df, pd.DataFrame)
        assert isinstance(tariff_viewer.demand_weekend_df, pd.DataFrame)

        # Check flat demand rates
        assert isinstance(tariff_viewer.flat_demand_df, pd.DataFrame)
        assert tariff_viewer.flat_demand_df.shape == (12, 1)

    def test_get_rate_method(self, tariff_viewer):
        """Test the get_rate method."""
        energy_rates = tariff_viewer.tariff["energyratestructure"]

        # Test valid period
        rate = tariff_viewer.get_rate(0, energy_rates)
        assert rate == 0.1000  # Off-peak rate

        rate = tariff_viewer.get_rate(2, energy_rates)
        assert rate == 0.2000  # Peak rate

        # Test invalid period
        rate = tariff_viewer.get_rate(99, energy_rates)
        assert rate == 0

    def test_get_demand_rate_method(self, tariff_viewer):
        """Test the get_demand_rate method."""
        demand_rates = tariff_viewer.tariff["demandratestructure"]

        # Test valid period
        rate = tariff_viewer.get_demand_rate(0, demand_rates)
        assert rate == 10.00

        rate = tariff_viewer.get_demand_rate(1, demand_rates)
        assert rate == 15.00

        # Test invalid period
        rate = tariff_viewer.get_demand_rate(99, demand_rates)
        assert rate == 0

    def test_create_tou_labels_table(self, tariff_viewer):
        """Test TOU labels table creation."""
        table = tariff_viewer.create_tou_labels_table()

        assert isinstance(table, pd.DataFrame)
        assert not table.empty
        assert "TOU Period" in table.columns
        assert "Total Rate ($/kWh)" in table.columns

        # Check that we have the expected number of periods
        assert len(table) == 3  # Off-peak, Mid-peak, Peak

    def test_create_demand_labels_table(self, tariff_viewer):
        """Test demand labels table creation."""
        table = tariff_viewer.create_demand_labels_table()

        assert isinstance(table, pd.DataFrame)
        assert not table.empty
        assert "Demand Period" in table.columns
        assert "Total Rate ($/kW)" in table.columns

    def test_format_month_range(self, tariff_viewer):
        """Test month range formatting."""
        # Test single month
        result = tariff_viewer._format_month_range(["Jan"])
        assert result == "Jan"

        # Test consecutive months
        result = tariff_viewer._format_month_range(["Jan", "Feb", "Mar"])
        assert result == "Jan-Mar"

        # Test non-consecutive months
        result = tariff_viewer._format_month_range(["Jan", "Mar", "May"])
        assert result == "Jan, Mar, May"


class TestTempTariffViewer:
    """Test cases for temporary tariff viewer."""

    def test_create_temp_viewer(self, sample_wrapped_tariff_data):
        """Test creating a temporary viewer with modified data."""
        temp_viewer = create_temp_viewer_with_modified_tariff(
            sample_wrapped_tariff_data
        )

        assert temp_viewer.utility_name == "Test Utility"
        assert temp_viewer.rate_name == "Test Rate Schedule"

        # Should have same functionality as regular viewer
        assert isinstance(temp_viewer.weekday_df, pd.DataFrame)
        assert temp_viewer.weekday_df.shape == (12, 24)

    def test_temp_viewer_with_modified_rates(self, sample_wrapped_tariff_data):
        """Test temp viewer with modified rate data."""
        # Modify a rate
        modified_data = sample_wrapped_tariff_data.copy()
        modified_data["items"][0]["energyratestructure"][0][0]["rate"] = 0.1234

        temp_viewer = create_temp_viewer_with_modified_tariff(modified_data)

        # Check that the modified rate is reflected
        rate = temp_viewer.get_rate(0, temp_viewer.tariff["energyratestructure"])
        assert rate == 0.1234
