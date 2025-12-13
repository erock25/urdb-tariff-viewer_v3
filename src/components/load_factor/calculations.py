"""
Load factor calculation functions.

This module contains pure calculation logic for load factor analysis,
separated from UI rendering for better testability and maintainability.
"""

import pandas as pd
from typing import Dict, Any, Optional

from src.utils.helpers import (
    calculate_period_hour_percentages,
    calculate_annual_period_hour_percentages,
    get_active_demand_periods_for_month,
    get_active_energy_periods_for_month,
)


def calculate_max_valid_load_factor(
    energy_percentages: Dict[int, float],
    period_hour_pcts: Dict[int, float]
) -> float:
    """
    Calculate the maximum physically possible load factor based on energy distribution.
    
    For each period: power_required = (energy_pct / hour_pct) * avg_load
    This can't exceed peak_demand, so: LF <= hour_pct / energy_pct for each period
    Maximum LF is the minimum of these ratios across all periods with energy.
    
    Args:
        energy_percentages: Dictionary mapping period index to energy percentage
        period_hour_pcts: Dictionary mapping period index to hour percentage
        
    Returns:
        Maximum valid load factor (0.0 to 1.0)
    """
    max_valid_lf = 1.0
    
    for period_idx, energy_pct in energy_percentages.items():
        if energy_pct > 0 and period_idx in period_hour_pcts:
            hour_pct = period_hour_pcts[period_idx]
            if hour_pct > 0:
                period_max_lf = hour_pct / energy_pct
                max_valid_lf = min(max_valid_lf, period_max_lf)
            else:
                # Period has energy but 0 hours - physically impossible
                max_valid_lf = 0.0
    
    return min(max_valid_lf, 1.0)


def generate_load_factors(max_valid_lf: float) -> list:
    """
    Generate list of load factors from 1% up to max_valid_lf in 1% increments.
    
    Always includes 100% as the final point (uses hour percentages).
    
    Args:
        max_valid_lf: Maximum valid load factor
        
    Returns:
        List of load factor values
    """
    load_factors = []
    for i in range(1, 101):
        lf = i / 100.0
        if lf <= max_valid_lf:
            load_factors.append(lf)
        elif lf == 1.00:
            load_factors.append(1.00)
            break
        else:
            load_factors.append(1.00)
            break
    return load_factors


def calculate_load_factor_rates(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    selected_month: int,
    has_tou_demand: bool,
    has_flat_demand: bool
) -> pd.DataFrame:
    """
    Calculate effective utility rates for different load factors (single month).
    
    Args:
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values for each period
        energy_percentages: Dictionary of energy percentages for each period
        selected_month: Month index (0-11)
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
    
    Returns:
        DataFrame with load factor analysis results
    """
    period_hour_pcts = calculate_period_hour_percentages(tariff_data, selected_month)
    max_valid_lf = calculate_max_valid_load_factor(energy_percentages, period_hour_pcts)
    load_factors = generate_load_factors(max_valid_lf)
    
    # Hours in the selected month (approximate)
    hours_in_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    hours = hours_in_month[selected_month]
    
    # Get fixed charge
    fixed_charge = tariff_data.get('fixedchargefirstmeter', 0)
    
    # Get energy rate structure
    energy_structure = tariff_data.get('energyratestructure', [])
    
    results = []
    
    for lf in load_factors:
        result = _calculate_single_load_factor(
            lf=lf,
            tariff_data=tariff_data,
            demand_inputs=demand_inputs,
            energy_percentages=energy_percentages,
            period_hour_pcts=period_hour_pcts,
            max_valid_lf=max_valid_lf,
            hours=hours,
            fixed_charge=fixed_charge,
            energy_structure=energy_structure,
            has_tou_demand=has_tou_demand,
            has_flat_demand=has_flat_demand,
            selected_month=selected_month
        )
        results.append(result)
    
    return pd.DataFrame(results)


def _calculate_single_load_factor(
    lf: float,
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    period_hour_pcts: Dict[int, float],
    max_valid_lf: float,
    hours: int,
    fixed_charge: float,
    energy_structure: list,
    has_tou_demand: bool,
    has_flat_demand: bool,
    selected_month: int
) -> Dict[str, Any]:
    """
    Calculate costs for a single load factor value.
    
    Args:
        lf: Load factor value (0.0 to 1.0)
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values
        energy_percentages: Dictionary of energy percentages
        period_hour_pcts: Dictionary of hour percentages per period
        max_valid_lf: Maximum valid load factor
        hours: Hours in the month
        fixed_charge: Fixed monthly charge
        energy_structure: Energy rate structure from tariff
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        selected_month: Month index (0-11)
        
    Returns:
        Dictionary with calculated values for this load factor
    """
    # Calculate peak demand (use the maximum of all specified demands)
    all_demands = [v for k, v in demand_inputs.items() 
                   if not k.startswith('_') and isinstance(v, (int, float)) and v > 0]
    peak_demand = max(all_demands) if all_demands else 0
    
    if peak_demand == 0:
        avg_load = 0
        total_energy = 0
    else:
        avg_load = peak_demand * lf
        total_energy = avg_load * hours
    
    # Calculate demand charges
    total_demand_cost = _calculate_demand_charges(
        tariff_data=tariff_data,
        demand_inputs=demand_inputs,
        has_tou_demand=has_tou_demand,
        has_flat_demand=has_flat_demand,
        selected_month=selected_month
    )
    
    # Calculate energy charges
    total_energy_cost = _calculate_energy_charges(
        total_energy=total_energy,
        lf=lf,
        max_valid_lf=max_valid_lf,
        energy_percentages=energy_percentages,
        period_hour_pcts=period_hour_pcts,
        energy_structure=energy_structure
    )
    
    # Total cost
    total_cost = total_demand_cost + total_energy_cost + fixed_charge
    
    # Effective rate ($/kWh)
    effective_rate = total_cost / total_energy if total_energy > 0 else 0
    
    return {
        'Load Factor': f"{lf * 100:.0f}%",
        'Load Factor Value': lf,
        'Peak Demand (kW)': peak_demand,
        'Average Load (kW)': avg_load,
        'Total Energy (kWh)': total_energy,
        'Demand Charges ($)': total_demand_cost,
        'Energy Charges ($)': total_energy_cost,
        'Fixed Charges ($)': fixed_charge,
        'Total Cost ($)': total_cost,
        'Effective Rate ($/kWh)': effective_rate
    }


def _calculate_demand_charges(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    has_tou_demand: bool,
    has_flat_demand: bool,
    selected_month: int
) -> float:
    """
    Calculate total demand charges for a month.
    
    Args:
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        selected_month: Month index (0-11)
        
    Returns:
        Total demand cost
    """
    total_demand_cost = 0
    
    # TOU demand charges
    if has_tou_demand:
        demand_structure = tariff_data.get('demandratestructure', [])
        for i, structure in enumerate(demand_structure):
            demand_key = f'tou_demand_{i}'
            if demand_key in demand_inputs and demand_inputs[demand_key] > 0:
                rate = structure[0].get('rate', 0)
                adj = structure[0].get('adj', 0)
                total_demand_cost += demand_inputs[demand_key] * (rate + adj)
    
    # Flat demand charge
    if has_flat_demand:
        if 'flat_demand' in demand_inputs and demand_inputs['flat_demand'] > 0:
            flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
            flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
            
            flat_structure_list = tariff_data['flatdemandstructure']
            if flat_tier < len(flat_structure_list):
                flat_structure = flat_structure_list[flat_tier][0]
            else:
                flat_structure = flat_structure_list[0][0]
            
            rate = flat_structure.get('rate', 0)
            adj = flat_structure.get('adj', 0)
            total_demand_cost += demand_inputs['flat_demand'] * (rate + adj)
    
    return total_demand_cost


def _calculate_energy_charges(
    total_energy: float,
    lf: float,
    max_valid_lf: float,
    energy_percentages: Dict[int, float],
    period_hour_pcts: Dict[int, float],
    energy_structure: list
) -> float:
    """
    Calculate total energy charges.
    
    At load factors above max_valid_lf, energy distribution must match the TOU schedule.
    Below max_valid_lf, use user-specified distribution (operational flexibility exists).
    
    Args:
        total_energy: Total energy consumption (kWh)
        lf: Current load factor
        max_valid_lf: Maximum valid load factor
        energy_percentages: User-specified energy percentages
        period_hour_pcts: Hour percentages per period
        energy_structure: Energy rate structure
        
    Returns:
        Total energy cost
    """
    if total_energy <= 0:
        return 0
    
    # Determine effective energy percentages
    if lf > max_valid_lf + 0.005:  # Small tolerance for floating point
        effective_energy_pcts = period_hour_pcts
    else:
        effective_energy_pcts = energy_percentages
    
    total_energy_cost = 0
    for period_idx, percentage in effective_energy_pcts.items():
        if percentage > 0 and period_idx < len(energy_structure):
            period_energy = total_energy * (percentage / 100.0)
            rate = energy_structure[period_idx][0].get('rate', 0)
            adj = energy_structure[period_idx][0].get('adj', 0)
            total_energy_cost += period_energy * (rate + adj)
    
    return total_energy_cost


def calculate_annual_load_factor_rates(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    has_tou_demand: bool,
    has_flat_demand: bool,
    demand_period_month_counts: Dict[int, int],
    energy_period_month_counts: Dict[int, int]
) -> pd.DataFrame:
    """
    Calculate effective utility rates for different load factors over a full year.
    
    Args:
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values for each period
        energy_percentages: Dictionary of energy percentages for each period
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        demand_period_month_counts: Dict mapping demand period index to # months active
        energy_period_month_counts: Dict mapping energy period index to # months active
    
    Returns:
        DataFrame with annual load factor analysis results
    """
    period_hour_pcts_annual = calculate_annual_period_hour_percentages(tariff_data)
    max_valid_lf = calculate_max_valid_load_factor(energy_percentages, period_hour_pcts_annual)
    load_factors = generate_load_factors(max_valid_lf)
    
    # Get fixed charge (annual total)
    fixed_charge_monthly = tariff_data.get('fixedchargefirstmeter', 0)
    fixed_charge_annual = fixed_charge_monthly * 12
    
    # Get rate structures
    energy_structure = tariff_data.get('energyratestructure', [])
    flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
    flat_structure_list = tariff_data.get('flatdemandstructure', []) if has_flat_demand else []
    demand_structure = tariff_data.get('demandratestructure', []) if has_tou_demand else []
    
    # Calculate peak demand
    all_demands = [v for k, v in demand_inputs.items() 
                   if (k.startswith('tou_demand_') or k == 'flat_demand') 
                   and isinstance(v, (int, float)) and v > 0]
    peak_demand = max(all_demands) if all_demands else 0
    
    results = []
    
    for lf in load_factors:
        result = _calculate_annual_load_factor(
            lf=lf,
            tariff_data=tariff_data,
            demand_inputs=demand_inputs,
            energy_percentages=energy_percentages,
            period_hour_pcts_annual=period_hour_pcts_annual,
            max_valid_lf=max_valid_lf,
            peak_demand=peak_demand,
            fixed_charge_annual=fixed_charge_annual,
            energy_structure=energy_structure,
            demand_structure=demand_structure,
            flat_structure_list=flat_structure_list,
            flatdemandmonths=flatdemandmonths,
            has_tou_demand=has_tou_demand,
            has_flat_demand=has_flat_demand
        )
        results.append(result)
    
    return pd.DataFrame(results)


def _calculate_annual_load_factor(
    lf: float,
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    period_hour_pcts_annual: Dict[int, float],
    max_valid_lf: float,
    peak_demand: float,
    fixed_charge_annual: float,
    energy_structure: list,
    demand_structure: list,
    flat_structure_list: list,
    flatdemandmonths: list,
    has_tou_demand: bool,
    has_flat_demand: bool
) -> Dict[str, Any]:
    """
    Calculate costs for a single load factor value over a full year.
    """
    if peak_demand == 0:
        avg_load = 0
    else:
        avg_load = peak_demand * lf
    
    # Aggregate annual values
    total_energy_annual = 0
    total_demand_cost_annual = 0
    total_energy_cost_annual = 0
    
    hours_in_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    
    for month in range(12):
        hours = hours_in_month[month]
        month_energy = avg_load * hours if peak_demand > 0 else 0
        total_energy_annual += month_energy
        
        # Get active periods for this month
        active_demand_periods = get_active_demand_periods_for_month(tariff_data, month)
        active_energy_periods = get_active_energy_periods_for_month(tariff_data, month)
        period_hour_pcts_month = calculate_period_hour_percentages(tariff_data, month)
        
        # TOU demand charges
        if has_tou_demand:
            for i, structure in enumerate(demand_structure):
                if i in active_demand_periods:
                    demand_key = f'tou_demand_{i}'
                    if demand_key in demand_inputs and demand_inputs[demand_key] > 0:
                        rate = structure[0].get('rate', 0)
                        adj = structure[0].get('adj', 0)
                        total_demand_cost_annual += demand_inputs[demand_key] * (rate + adj)
        
        # Flat demand charge
        if has_flat_demand and 'flat_demand' in demand_inputs and demand_inputs['flat_demand'] > 0:
            flat_tier = flatdemandmonths[month] if month < len(flatdemandmonths) else 0
            if flat_tier < len(flat_structure_list):
                flat_structure = flat_structure_list[flat_tier][0]
            else:
                flat_structure = flat_structure_list[0][0]
            
            rate = flat_structure.get('rate', 0)
            adj = flat_structure.get('adj', 0)
            total_demand_cost_annual += demand_inputs['flat_demand'] * (rate + adj)
        
        # Energy charges for this month
        if month_energy > 0:
            if lf > max_valid_lf + 0.005:
                effective_energy_pcts = period_hour_pcts_month
            else:
                effective_energy_pcts = {k: v for k, v in energy_percentages.items() 
                                         if k in active_energy_periods}
                total_active_pct = sum(effective_energy_pcts.values())
                if total_active_pct > 0:
                    effective_energy_pcts = {k: (v / total_active_pct * 100) 
                                             for k, v in effective_energy_pcts.items()}
                else:
                    effective_energy_pcts = period_hour_pcts_month
            
            for period_idx, percentage in effective_energy_pcts.items():
                if percentage > 0 and period_idx < len(energy_structure):
                    period_energy = month_energy * (percentage / 100.0)
                    rate = energy_structure[period_idx][0].get('rate', 0)
                    adj = energy_structure[period_idx][0].get('adj', 0)
                    total_energy_cost_annual += period_energy * (rate + adj)
    
    total_cost_annual = total_demand_cost_annual + total_energy_cost_annual + fixed_charge_annual
    effective_rate = total_cost_annual / total_energy_annual if total_energy_annual > 0 else 0
    
    return {
        'Load Factor': f"{lf * 100:.0f}%",
        'Load Factor Value': lf,
        'Peak Demand (kW)': peak_demand,
        'Average Load (kW)': avg_load,
        'Total Energy (kWh)': total_energy_annual,
        'Demand Charges ($)': total_demand_cost_annual,
        'Energy Charges ($)': total_energy_cost_annual,
        'Fixed Charges ($)': fixed_charge_annual,
        'Total Cost ($)': total_cost_annual,
        'Effective Rate ($/kWh)': effective_rate
    }


def calculate_comprehensive_breakdown(
    results: pd.DataFrame,
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    selected_month: Optional[int],
    has_tou_demand: bool,
    has_flat_demand: bool,
    analysis_period: str = "Single Month",
    demand_period_month_counts: Optional[Dict[int, int]] = None,
    energy_period_month_counts: Optional[Dict[int, int]] = None
) -> pd.DataFrame:
    """
    Calculate comprehensive breakdown table with all load factors and detailed rate components.
    
    Args:
        results: Original results DataFrame
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values for each period
        energy_percentages: Dictionary of energy percentages for each period
        selected_month: Month index (0-11, or None for annual)
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        analysis_period: "Single Month" or "Full Year"
        demand_period_month_counts: Dict mapping demand period to # months active (for annual)
        energy_period_month_counts: Dict mapping energy period to # months active (for annual)
    
    Returns:
        DataFrame with comprehensive breakdown for all load factors
    """
    # Calculate max valid load factor
    if analysis_period == "Single Month" and selected_month is not None:
        period_hour_pcts = calculate_period_hour_percentages(tariff_data, selected_month)
    else:
        period_hour_pcts = calculate_annual_period_hour_percentages(tariff_data)
    
    max_valid_lf = calculate_max_valid_load_factor(energy_percentages, period_hour_pcts)
    
    # Get structures
    energy_structure = tariff_data.get('energyratestructure', [])
    energy_labels = tariff_data.get('energyweekdaylabels', [])
    
    # Calculate peak demand
    all_demands = [v for k, v in demand_inputs.items() 
                   if not k.startswith('_') and isinstance(v, (int, float)) and v > 0]
    peak_demand = max(all_demands) if all_demands else 0
    
    comprehensive_rows = []
    
    for idx, row in results.iterrows():
        load_factor = row['Load Factor Value']
        avg_load = row['Average Load (kW)']
        total_energy = row['Total Energy (kWh)']
        
        comprehensive_row = {
            'Load Factor': row['Load Factor'],
            'Average Load (kW)': avg_load,
            'Total Energy (kWh)': total_energy
        }
        
        # Determine effective energy percentages
        if load_factor > max_valid_lf + 0.005:
            effective_energy_pcts = period_hour_pcts
        else:
            effective_energy_pcts = energy_percentages
        
        # Add energy period columns
        comprehensive_row = _add_energy_period_columns(
            comprehensive_row, energy_structure, energy_labels,
            effective_energy_pcts, total_energy
        )
        
        # Add TOU demand columns
        if has_tou_demand:
            comprehensive_row = _add_tou_demand_columns(
                comprehensive_row, tariff_data, demand_inputs,
                analysis_period, demand_period_month_counts
            )
        
        # Add flat demand columns
        if has_flat_demand:
            comprehensive_row = _add_flat_demand_columns(
                comprehensive_row, tariff_data, demand_inputs,
                selected_month, analysis_period
            )
        
        # Add summary columns
        comprehensive_row['Total Demand Charges ($)'] = row['Demand Charges ($)']
        comprehensive_row['Total Energy Charges ($)'] = row['Energy Charges ($)']
        comprehensive_row['Fixed Charges ($)'] = row['Fixed Charges ($)']
        comprehensive_row['Total Cost ($)'] = row['Total Cost ($)']
        comprehensive_row['Effective Rate ($/kWh)'] = row['Effective Rate ($/kWh)']
        
        comprehensive_rows.append(comprehensive_row)
    
    return pd.DataFrame(comprehensive_rows)


def _add_energy_period_columns(
    row: Dict[str, Any],
    energy_structure: list,
    energy_labels: list,
    effective_energy_pcts: Dict[int, float],
    total_energy: float
) -> Dict[str, Any]:
    """Add energy period columns to a comprehensive breakdown row."""
    for period_idx in range(len(energy_structure)):
        period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
        
        rate = energy_structure[period_idx][0].get('rate', 0)
        adj = energy_structure[period_idx][0].get('adj', 0)
        total_rate = rate + adj
        
        percentage = effective_energy_pcts.get(period_idx, 0)
        period_energy = total_energy * (percentage / 100.0) if percentage > 0 else 0
        period_cost = period_energy * total_rate if period_energy > 0 else 0
        
        row[f'{period_label} (kWh)'] = period_energy
        row[f'{period_label} Rate ($/kWh)'] = total_rate
        row[f'{period_label} Cost ($)'] = period_cost
    
    return row


def _add_tou_demand_columns(
    row: Dict[str, Any],
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    analysis_period: str,
    demand_period_month_counts: Optional[Dict[int, int]]
) -> Dict[str, Any]:
    """Add TOU demand columns to a comprehensive breakdown row."""
    demand_structure = tariff_data.get('demandratestructure', [])
    demand_labels = tariff_data.get('demandtoulabels', [])
    
    for i in range(len(demand_structure)):
        period_label = demand_labels[i] if i < len(demand_labels) else f"TOU Period {i}"
        demand_key = f'tou_demand_{i}'
        
        rate = demand_structure[i][0].get('rate', 0)
        adj = demand_structure[i][0].get('adj', 0)
        total_rate = rate + adj
        
        if demand_key in demand_inputs:
            demand_value = demand_inputs[demand_key]
            if demand_value > 0:
                if analysis_period == "Full Year" and demand_period_month_counts:
                    num_months = demand_period_month_counts.get(i, 0)
                    demand_cost = demand_value * total_rate * num_months
                else:
                    demand_cost = demand_value * total_rate
            else:
                demand_cost = 0
        else:
            demand_value = 0
            demand_cost = 0
        
        if analysis_period == "Full Year" and demand_period_month_counts:
            num_months = demand_period_month_counts.get(i, 0)
            row[f'{period_label} # Months'] = num_months
        
        row[f'{period_label} Demand (kW)'] = demand_value
        row[f'{period_label} Rate ($/kW)'] = total_rate
        row[f'{period_label} Demand Cost ($)'] = demand_cost
    
    return row


def _add_flat_demand_columns(
    row: Dict[str, Any],
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    selected_month: Optional[int],
    analysis_period: str
) -> Dict[str, Any]:
    """Add flat demand columns to a comprehensive breakdown row."""
    flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
    flat_structure_list = tariff_data['flatdemandstructure']
    
    if analysis_period == "Single Month" and selected_month is not None:
        flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
        
        if flat_tier < len(flat_structure_list):
            flat_structure = flat_structure_list[flat_tier][0]
        else:
            flat_structure = flat_structure_list[0][0]
        
        rate = flat_structure.get('rate', 0)
        adj = flat_structure.get('adj', 0)
        total_rate = rate + adj
        
        if 'flat_demand' in demand_inputs:
            demand_value = demand_inputs['flat_demand']
            demand_cost = demand_value * total_rate if demand_value > 0 else 0
        else:
            demand_value = 0
            demand_cost = 0
        
        row['Flat Demand (kW)'] = demand_value
        row['Flat Demand Rate ($/kW)'] = total_rate
        row['Flat Demand Cost ($)'] = demand_cost
    else:
        # Annual - separate columns for each unique tier
        tier_month_counts = {}
        for month_tier in flatdemandmonths:
            tier_month_counts[month_tier] = tier_month_counts.get(month_tier, 0) + 1
        
        for tier_idx in sorted(tier_month_counts.keys()):
            if tier_idx < len(flat_structure_list):
                flat_structure = flat_structure_list[tier_idx][0]
            else:
                flat_structure = flat_structure_list[0][0]
            
            rate = flat_structure.get('rate', 0)
            adj = flat_structure.get('adj', 0)
            total_rate = rate + adj
            num_months = tier_month_counts[tier_idx]
            
            if 'flat_demand' in demand_inputs:
                demand_value = demand_inputs['flat_demand']
                demand_cost = demand_value * total_rate * num_months if demand_value > 0 else 0
            else:
                demand_value = 0
                demand_cost = 0
            
            tier_label = f"Flat Demand (Tier {tier_idx})"
            row[f'{tier_label} # Months'] = num_months
            row[f'{tier_label} Demand (kW)'] = demand_value
            row[f'{tier_label} Rate ($/kW)'] = total_rate
            row[f'{tier_label} Cost ($)'] = demand_cost
    
    return row

