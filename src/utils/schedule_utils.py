"""
TOU schedule utilities for URDB Tariff Viewer.

This module contains functions for analyzing TOU (Time-of-Use) schedules,
calculating period hour percentages, and determining active periods.
"""

import calendar
from typing import Dict, Any, Set


def get_active_energy_periods_for_month(tariff_data: Dict[str, Any], month: int) -> Set[int]:
    """
    Determine which energy periods are actually present in a given month.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
    
    Returns:
        Set of period indices that appear in the selected month
    """
    active_periods = set()
    
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    if month < len(weekday_schedule):
        active_periods.update(weekday_schedule[month])
    
    if month < len(weekend_schedule):
        active_periods.update(weekend_schedule[month])
    
    return active_periods


def get_active_demand_periods_for_month(tariff_data: Dict[str, Any], month: int) -> Set[int]:
    """
    Determine which demand periods are actually present in a given month.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
    
    Returns:
        Set of period indices that appear in the selected month
    """
    active_periods = set()
    
    weekday_schedule = tariff_data.get('demandweekdayschedule', [])
    weekend_schedule = tariff_data.get('demandweekendschedule', [])
    
    if month < len(weekday_schedule):
        active_periods.update(weekday_schedule[month])
    
    if month < len(weekend_schedule):
        active_periods.update(weekend_schedule[month])
    
    return active_periods


def get_active_demand_periods_for_year(tariff_data: Dict[str, Any]) -> Dict[int, int]:
    """
    Determine which demand periods are present in the year and count months of activity.
    
    Args:
        tariff_data: Tariff data dictionary
    
    Returns:
        Dictionary mapping period index to number of months it's active
    """
    period_month_counts = {}
    
    for month in range(12):
        active_periods = get_active_demand_periods_for_month(tariff_data, month)
        for period in active_periods:
            period_month_counts[period] = period_month_counts.get(period, 0) + 1
    
    return period_month_counts


def get_active_energy_periods_for_year(tariff_data: Dict[str, Any]) -> Dict[int, int]:
    """
    Determine which energy periods are present in the year and count months of activity.
    
    Args:
        tariff_data: Tariff data dictionary
    
    Returns:
        Dictionary mapping period index to number of months it's active
    """
    period_month_counts = {}
    
    for month in range(12):
        active_periods = get_active_energy_periods_for_month(tariff_data, month)
        for period in active_periods:
            period_month_counts[period] = period_month_counts.get(period, 0) + 1
    
    return period_month_counts


def calculate_annual_period_hour_percentages(tariff_data: Dict[str, Any], year: int = 2024) -> Dict[int, float]:
    """
    Calculate what percentage of the year's hours each energy period is present.
    
    Args:
        tariff_data: Tariff data dictionary
        year: Year for calendar calculation (default 2024)
    
    Returns:
        Dictionary mapping period index to percentage of year (0-100)
    """
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    if len(weekday_schedule) < 12 or len(weekend_schedule) < 12:
        return {}
    
    period_hours = {}
    total_hours = 0
    
    for month in range(12):
        cal = calendar.monthcalendar(year, month + 1)
        
        weekday_count = 0
        weekend_count = 0
        
        for week in cal:
            for day_idx, day in enumerate(week):
                if day == 0:
                    continue
                if day_idx < 5:  # Monday-Friday
                    weekday_count += 1
                else:  # Saturday-Sunday
                    weekend_count += 1
        
        for hour in range(24):
            period = weekday_schedule[month][hour]
            period_hours[period] = period_hours.get(period, 0) + weekday_count
        
        for hour in range(24):
            period = weekend_schedule[month][hour]
            period_hours[period] = period_hours.get(period, 0) + weekend_count
        
        total_hours += (weekday_count + weekend_count) * 24
    
    period_percentages = {}
    for period, hours in period_hours.items():
        period_percentages[period] = (hours / total_hours * 100) if total_hours > 0 else 0
    
    return period_percentages


def calculate_period_hour_percentages(tariff_data: Dict[str, Any], month: int, year: int = 2024) -> Dict[int, float]:
    """
    Calculate what percentage of the month's hours each energy period is present.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
        year: Year for calendar calculation (default 2024)
    
    Returns:
        Dictionary mapping period index to percentage of month (0-100)
    """
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    if month >= len(weekday_schedule) or month >= len(weekend_schedule):
        return {}
    
    cal = calendar.monthcalendar(year, month + 1)
    
    weekday_count = 0
    weekend_count = 0
    
    for week in cal:
        for day_idx, day in enumerate(week):
            if day == 0:
                continue
            if day_idx < 5:  # Monday-Friday
                weekday_count += 1
            else:  # Saturday-Sunday
                weekend_count += 1
    
    period_hours = {}
    
    for hour in range(24):
        period = weekday_schedule[month][hour]
        period_hours[period] = period_hours.get(period, 0) + weekday_count
    
    for hour in range(24):
        period = weekend_schedule[month][hour]
        period_hours[period] = period_hours.get(period, 0) + weekend_count
    
    total_hours = (weekday_count + weekend_count) * 24
    
    period_percentages = {}
    for period, hours in period_hours.items():
        period_percentages[period] = (hours / total_hours * 100) if total_hours > 0 else 0
    
    return period_percentages

