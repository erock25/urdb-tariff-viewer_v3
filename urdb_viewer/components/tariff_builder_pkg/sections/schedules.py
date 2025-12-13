"""
Schedule configuration section for tariff builder.

Handles energy and demand TOU schedule configuration, including:
- Simple schedule editor (same for all months)
- Advanced template-based schedule editor
- Schedule visualization (heatmaps)
"""

from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from urdb_viewer.config.constants import HOURS, MONTHS

from ..utils import get_tariff_data

# =============================================================================
# Main Entry Points
# =============================================================================


def render_energy_schedule_section() -> None:
    """Render the energy schedule section of the tariff builder."""
    st.markdown("### 📅 Energy TOU Schedule")
    st.markdown(
        """
    Define when each TOU period applies throughout the year. You can set different
    schedules for weekdays and weekends.
    """
    )

    data = get_tariff_data()
    num_periods = len(data["energyratestructure"])

    schedule_mode = st.radio(
        "How would you like to set the schedule?",
        options=["Simple (same for all months)", "Advanced (different by month)"],
        help="Simple mode applies the same daily pattern to all months",
    )

    if schedule_mode == "Simple (same for all months)":
        _render_simple_schedule_editor(data, num_periods, "energy")
    else:
        _render_advanced_schedule_editor(data, num_periods, "energy")

    # Show schedule preview
    st.markdown("---")
    st.markdown("#### 📊 Schedule Preview")

    tab1, tab2 = st.tabs(["Weekday Schedule", "Weekend Schedule"])

    with tab1:
        _show_schedule_heatmap(
            data["energyweekdayschedule"],
            "Weekday",
            data["energytoulabels"],
            rate_structure=data.get("energyratestructure"),
            rate_type="energy",
        )

    with tab2:
        _show_schedule_heatmap(
            data["energyweekendschedule"],
            "Weekend",
            data["energytoulabels"],
            rate_structure=data.get("energyratestructure"),
            rate_type="energy",
        )


# =============================================================================
# Simple Schedule Editor
# =============================================================================


def _render_simple_schedule_editor(
    data: Dict, num_periods: int, rate_type: str
) -> None:
    """
    Render a simple schedule editor that applies the same pattern to all months.

    Args:
        data: Tariff data dictionary
        num_periods: Number of TOU periods
        rate_type: 'energy' or 'demand'
    """
    prefix = rate_type
    weekday_key = f"{prefix}weekdayschedule"
    weekend_key = f"{prefix}weekendschedule"
    labels_key = f"{prefix}toulabels" if rate_type == "energy" else "demandlabels"

    labels = data.get(labels_key, [f"Period {i}" for i in range(num_periods)])

    st.markdown(
        f"#### {'Weekday' if rate_type == 'energy' else 'Demand Weekday'} Schedule"
    )
    st.info(
        "💡 **Tip**: Fill in all hours, then click 'Apply Schedule' at the bottom to update."
    )

    form_key = f"simple_{rate_type}_schedule_form_{num_periods}_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Set hourly rates for a typical weekday:**")
            weekday_pattern = []

            for hour in range(24):
                current_value = (
                    data[weekday_key][0][hour]
                    if hour < len(data[weekday_key][0])
                    else 0
                )
                period = st.selectbox(
                    f"Hour {hour}:00",
                    options=list(range(num_periods)),
                    format_func=lambda x: f"{labels[x]} (Period {x})",
                    key=f"simple_{rate_type}_weekday_{hour}",
                    index=current_value,
                )
                weekday_pattern.append(period)

        with col2:
            st.markdown("**Current Schedule:**")
            current_schedule_df = pd.DataFrame(
                {
                    "Hour": [f"{h}:00" for h in range(24)],
                    "Period": [labels[data[weekday_key][0][h]] for h in range(24)],
                }
            )
            st.dataframe(current_schedule_df, use_container_width=True, height=600)

        st.markdown("---")
        st.markdown("#### Weekend Schedule")

        weekend_same = st.checkbox(
            "Use same schedule for weekends",
            value=True,
            help="If checked, weekend will use the same schedule as weekdays",
            key=f"{rate_type}_weekend_same",
        )

        weekend_pattern = []
        if not weekend_same:
            st.markdown("**Set hourly rates for a typical weekend:**")
            cols = st.columns(4)

            for hour in range(24):
                with cols[hour % 4]:
                    current_value = (
                        data[weekend_key][0][hour]
                        if hour < len(data[weekend_key][0])
                        else 0
                    )
                    period = st.selectbox(
                        f"Hr {hour}",
                        options=list(range(num_periods)),
                        format_func=lambda x: f"P{x}",
                        key=f"simple_{rate_type}_weekend_{hour}",
                        index=current_value,
                        label_visibility="visible",
                    )
                    weekend_pattern.append(period)

        submitted = st.form_submit_button(
            f"✅ Apply {'Energy' if rate_type == 'energy' else 'Demand'} Schedule",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            data[weekday_key] = [weekday_pattern for _ in range(12)]

            if weekend_same:
                data[weekend_key] = [weekday_pattern for _ in range(12)]
            else:
                data[weekend_key] = [weekend_pattern for _ in range(12)]

            st.success("✓ Schedule updated for all months!")


# =============================================================================
# Advanced Template-Based Schedule Editor
# =============================================================================


def _render_advanced_schedule_editor(
    data: Dict, num_periods: int, rate_type: str
) -> None:
    """
    Render an advanced schedule editor with template-based customization.

    Args:
        data: Tariff data dictionary
        num_periods: Number of TOU periods
        rate_type: 'energy' or 'demand'
    """
    st.markdown(
        "Configure schedules using templates. Define 2-3 unique schedules and assign them to months."
    )

    template_key = f"{rate_type}_schedule_templates"
    same_key = f"{rate_type}_schedule_same_for_weekday_weekend"
    weekday_key = f"{rate_type}weekdayschedule"
    weekend_key = f"{rate_type}weekendschedule"

    # Initialize templates in session state
    if template_key not in st.session_state:
        st.session_state[template_key] = {
            "weekday": _initialize_default_templates(data, weekday_key, num_periods),
            "weekend": _initialize_default_templates(data, weekend_key, num_periods),
        }

    if same_key not in st.session_state:
        st.session_state[same_key] = False

    # Same schedule checkbox
    same_schedule = st.checkbox(
        "Weekday and weekend schedules are the same",
        value=st.session_state[same_key],
        key=f"{rate_type}_same_schedule_checkbox",
        help="Check if your tariff has the same schedule for weekdays and weekends.",
    )
    st.session_state[same_key] = same_schedule

    if same_schedule:
        schedule_type_lower = "weekday"
        st.info("ℹ️ You are editing the schedule for both weekdays and weekends.")
    else:
        schedule_type = st.radio(
            "Schedule to edit:",
            ["Weekday", "Weekend"],
            horizontal=True,
            key=f"{rate_type}_schedule_type",
        )
        schedule_type_lower = schedule_type.lower()

    # Three-step process
    st.markdown("---")
    st.markdown("### Step 1: Manage Templates")
    tip_text = (
        "💡 **Tip**: Create a template for each unique schedule (e.g., Summer, Winter, Shoulder)."
        + (
            ""
            if same_schedule
            else " **Remember to do this for both Weekdays and Weekends.**"
        )
    )
    st.info(tip_text)
    _render_template_manager(schedule_type_lower, rate_type, num_periods, data)

    st.markdown("---")
    st.markdown("### Step 2: Edit Templates")
    _render_template_editor(schedule_type_lower, rate_type, num_periods, data)

    st.markdown("---")
    st.markdown("### Step 3: Assign Templates to Months")
    _render_month_assignment(schedule_type_lower, rate_type, data)

    # Apply templates
    _apply_templates_to_schedule(data, rate_type, same_schedule)


def _initialize_default_templates(
    data: Dict, schedule_key: str, num_periods: int
) -> Dict:
    """Initialize default templates from existing schedule data."""
    return {
        "Template 1": {
            "name": "Template 1",
            "schedule": (
                data[schedule_key][0].copy() if data.get(schedule_key) else [0] * 24
            ),
            "assigned_months": [0],
        }
    }


def _render_template_manager(
    schedule_type: str, rate_type: str, num_periods: int, data: Dict
) -> None:
    """Render the template management UI (add, delete templates)."""
    template_key = f"{rate_type}_schedule_templates"
    templates = st.session_state[template_key][schedule_type]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Current {schedule_type.title()} Templates:**")
        if templates:
            for template_id, template in templates.items():
                num_months = len(template.get("assigned_months", []))
                st.write(f"• **{template['name']}** ({num_months} months assigned)")
        else:
            st.info("No templates yet. Add one below!")

    with col2:
        st.markdown("**Add New Template:**")
        new_template_name = st.text_input(
            "Template Name",
            placeholder="e.g., Summer Peak",
            key=f"new_template_name_{rate_type}_{schedule_type}",
        )

        if st.button(
            "➕ Add Template", key=f"add_template_{rate_type}_{schedule_type}"
        ):
            if new_template_name and new_template_name not in templates:
                templates[new_template_name] = {
                    "name": new_template_name,
                    "schedule": [0] * 24,
                    "assigned_months": [],
                }
                st.success(f"✓ Added template '{new_template_name}'")
                st.rerun()
            elif new_template_name in templates:
                st.error("Template name already exists!")
            else:
                st.warning("Please enter a template name.")

    # Delete template option
    if templates:
        st.markdown("**Delete Template:**")
        template_to_delete = st.selectbox(
            "Select template to delete",
            options=list(templates.keys()),
            key=f"delete_template_select_{rate_type}_{schedule_type}",
        )

        if st.button("🗑️ Delete", key=f"delete_template_{rate_type}_{schedule_type}"):
            if len(templates) > 1:
                del templates[template_to_delete]
                st.success(f"✓ Deleted template '{template_to_delete}'")
                st.rerun()
            else:
                st.error("Cannot delete the last template! Add another one first.")


def _render_template_editor(
    schedule_type: str, rate_type: str, num_periods: int, data: Dict
) -> None:
    """Render the template editor UI for defining the 24-hour schedule."""
    template_key = f"{rate_type}_schedule_templates"
    templates = st.session_state[template_key][schedule_type]

    if not templates:
        st.warning("No templates available. Add a template in Step 1.")
        return

    selected_template = st.selectbox(
        "Select template to edit:",
        options=list(templates.keys()),
        key=f"edit_template_select_{rate_type}_{schedule_type}",
    )

    template = templates[selected_template]
    labels_key = "energytoulabels" if rate_type == "energy" else "demandlabels"
    labels = data.get(labels_key, [f"Period {i}" for i in range(num_periods)])

    st.markdown(f"#### Editing: **{template['name']}**")
    st.markdown("**Set the TOU period for each hour:**")

    with st.form(f"template_editor_{rate_type}_{schedule_type}_{selected_template}"):
        cols = st.columns(6)
        new_schedule = []

        for hour in range(24):
            with cols[hour % 6]:
                current_idx = (
                    template["schedule"][hour]
                    if hour < len(template["schedule"])
                    else 0
                )
                period = st.selectbox(
                    f"{hour}:00",
                    options=list(range(num_periods)),
                    format_func=lambda x: (
                        f"{labels[x]}" if x < len(labels) else f"P{x}"
                    ),
                    index=current_idx,
                    key=f"template_hour_{rate_type}_{schedule_type}_{selected_template}_{hour}",
                    label_visibility="visible",
                )
                new_schedule.append(period)

        submitted = st.form_submit_button(
            "✅ Save Template", type="primary", use_container_width=True
        )

        if submitted:
            template["schedule"] = new_schedule
            st.success(f"✓ Saved template '{template['name']}'")

    # Show template preview
    st.markdown("**Template Preview:**")
    preview_df = pd.DataFrame(
        {
            "Hour": [f"{h}:00" for h in range(24)],
            "Period": [template["schedule"][h] for h in range(24)],
        }
    )
    st.dataframe(preview_df, use_container_width=True, height=300)


def _render_month_assignment(schedule_type: str, rate_type: str, data: Dict) -> None:
    """Render the month assignment UI for assigning templates to months."""
    template_key = f"{rate_type}_schedule_templates"
    templates = st.session_state[template_key][schedule_type]

    if not templates:
        st.warning("No templates available. Add a template in Step 1.")
        return

    st.markdown("**Assign each month to a template:**")
    st.info(
        "💡 **Tip**: Typically there are 2-3 unique schedules per year (e.g., Summer, Winter, Shoulder)."
    )

    # Initialize month assignments
    for template in templates.values():
        if "assigned_months" not in template:
            template["assigned_months"] = []

    with st.form(f"month_assignment_{rate_type}_{schedule_type}"):
        cols = st.columns(4)
        month_assignments = {}

        # Get current assignments
        current_assignments = {}
        for template_name, template in templates.items():
            for month in template.get("assigned_months", []):
                current_assignments[month] = template_name

        for month_idx in range(12):
            with cols[month_idx % 4]:
                current_template = current_assignments.get(
                    month_idx, list(templates.keys())[0]
                )

                selected = st.selectbox(
                    MONTHS[month_idx],
                    options=list(templates.keys()),
                    index=(
                        list(templates.keys()).index(current_template)
                        if current_template in templates
                        else 0
                    ),
                    key=f"month_assign_{rate_type}_{schedule_type}_{month_idx}",
                )
                month_assignments[month_idx] = selected

        submitted = st.form_submit_button(
            "✅ Apply Month Assignments", type="primary", use_container_width=True
        )

        if submitted:
            for template in templates.values():
                template["assigned_months"] = []

            for month_idx, template_name in month_assignments.items():
                if template_name in templates:
                    templates[template_name]["assigned_months"].append(month_idx)

            st.success("✓ Month assignments updated!")

    # Show assignment summary
    st.markdown("---")
    st.markdown("**Assignment Summary:**")
    for template_name, template in templates.items():
        assigned_months = template.get("assigned_months", [])
        if assigned_months:
            month_names = [MONTHS[m] for m in sorted(assigned_months)]
            st.write(f"**{template_name}**: {', '.join(month_names)}")
        else:
            st.write(f"**{template_name}**: No months assigned")


def _apply_templates_to_schedule(
    data: Dict, rate_type: str, same_schedule: bool = False
) -> None:
    """Apply templates to generate the final schedule arrays."""
    template_key = f"{rate_type}_schedule_templates"
    weekday_key = f"{rate_type}weekdayschedule"
    weekend_key = f"{rate_type}weekendschedule"

    # Apply weekday templates
    weekday_templates = st.session_state[template_key]["weekday"]

    for month_idx in range(12):
        assigned_template = None
        for template in weekday_templates.values():
            if month_idx in template.get("assigned_months", []):
                assigned_template = template
                break

        if assigned_template:
            data[weekday_key][month_idx] = assigned_template["schedule"].copy()

    # Apply weekend templates
    if same_schedule:
        for month_idx in range(12):
            data[weekend_key][month_idx] = data[weekday_key][month_idx].copy()
    else:
        weekend_templates = st.session_state[template_key]["weekend"]

        for month_idx in range(12):
            assigned_template = None
            for template in weekend_templates.values():
                if month_idx in template.get("assigned_months", []):
                    assigned_template = template
                    break

            if assigned_template:
                data[weekend_key][month_idx] = assigned_template["schedule"].copy()


# =============================================================================
# Schedule Visualization
# =============================================================================


def _show_schedule_heatmap(
    schedule: List[List[int]],
    schedule_type: str,
    labels: List[str],
    rate_structure: List[List[Dict]] = None,
    rate_type: str = "energy",
) -> None:
    """
    Display a heatmap visualization of the schedule.

    Args:
        schedule: 12x24 array of period indices
        schedule_type: Description (e.g., "Weekday", "Weekend")
        labels: Period labels
        rate_structure: Optional rate structure for showing actual values
        rate_type: 'energy' or 'demand' for formatting
    """
    if rate_structure is not None:
        rate_values = []
        for month_schedule in schedule:
            month_rates = []
            for period_idx in month_schedule:
                if period_idx < len(rate_structure):
                    rate = rate_structure[period_idx][0].get("rate", 0.0)
                    adj = rate_structure[period_idx][0].get("adj", 0.0)
                    total_rate = rate + adj
                    month_rates.append(total_rate)
                else:
                    month_rates.append(0.0)
            rate_values.append(month_rates)

        schedule_df = pd.DataFrame(rate_values, index=MONTHS, columns=HOURS)
        value_label = "Rate ($/kW)" if rate_type == "demand" else "Rate ($/kWh)"
    else:
        schedule_df = pd.DataFrame(schedule, index=MONTHS, columns=HOURS)
        value_label = "Period Index"

    try:
        st.dataframe(
            schedule_df.style.background_gradient(cmap="RdYlGn_r", axis=None).format(
                "{:.4f}" if rate_structure else "{:.0f}"
            ),
            use_container_width=True,
        )
    except ImportError:
        st.dataframe(schedule_df, use_container_width=True)
        st.caption("⚠️ Install matplotlib for color-coded heatmap visualization")

    # Show legend
    st.markdown("**Period Legend:**")
    legend_cols = st.columns(min(len(labels), 4))
    for i, label in enumerate(labels):
        with legend_cols[i % 4]:
            if rate_structure is not None and i < len(rate_structure):
                rate = rate_structure[i][0].get("rate", 0.0)
                adj = rate_structure[i][0].get("adj", 0.0)
                total_rate = rate + adj
                if rate_type == "demand":
                    st.markdown(f"**{i}:** {label} (${total_rate:.4f}/kW)")
                else:
                    st.markdown(f"**{i}:** {label} (${total_rate:.5f}/kWh)")
            else:
                st.markdown(f"**{i}:** {label}")
