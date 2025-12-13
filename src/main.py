"""
Main entry point for URDB Tariff Viewer.

This is the new modular main application file that replaces the monolithic app.py.
Updated: 2025-11-23
"""

import streamlit as st
from pathlib import Path
from typing import Optional

# Import our modular components using relative imports when run as module
# or absolute imports when run directly via streamlit
try:
    from src.config.settings import Settings
    from src.utils.styling import apply_custom_css, create_section_header_html, create_custom_divider_html
    from src.services.file_service import FileService
    from src.models.tariff import TariffViewer, create_temp_viewer_with_modified_tariff
    from src.components.sidebar import create_sidebar
    from src.components.energy_rates import render_energy_rates_tab
    from src.components.demand_rates import render_demand_rates_tab
    from src.components.flat_demand_rates import render_flat_demand_rates_tab
    from src.components.cost_calculator import (
        render_cost_calculator_tab,
        render_utility_cost_calculation_tab
    )
    from src.components.load_factor import render_load_factor_analysis_tab
    from src.components.load_generator import render_load_generator_tab
    from src.components.tariff_builder_pkg import render_tariff_builder_tab
except ImportError:
    # Fallback for when running directly with streamlit run src/main.py
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.config.settings import Settings
    from src.utils.styling import apply_custom_css, create_section_header_html, create_custom_divider_html
    from src.services.file_service import FileService
    from src.models.tariff import TariffViewer, create_temp_viewer_with_modified_tariff
    from src.components.sidebar import create_sidebar
    from src.components.energy_rates import render_energy_rates_tab
    from src.components.demand_rates import render_demand_rates_tab
    from src.components.flat_demand_rates import render_flat_demand_rates_tab
    from src.components.cost_calculator import (
        render_cost_calculator_tab,
        render_utility_cost_calculation_tab
    )
    from src.components.load_factor import render_load_factor_analysis_tab
    from src.components.load_generator import render_load_generator_tab
    from src.components.tariff_builder_pkg import render_tariff_builder_tab


def initialize_app(dark_mode: bool = False) -> None:
    """Initialize the Streamlit application.
    
    Args:
        dark_mode (bool): Whether to apply dark mode styling
    """
    # Set page configuration
    st.set_page_config(**Settings.get_streamlit_config())
    
    # Apply custom CSS styling with dark mode support
    apply_custom_css(dark_mode=dark_mode)
    
    # Ensure required directories exist
    Settings.ensure_directories_exist()
    
    # Initialize session state
    if 'modified_tariff' not in st.session_state:
        st.session_state.modified_tariff = None
    if 'has_modifications' not in st.session_state:
        st.session_state.has_modifications = False


def load_tariff_viewer(selected_file: Path) -> Optional[TariffViewer]:
    """
    Load a TariffViewer instance, handling both original and modified tariffs.
    
    Args:
        selected_file (Path): Path to the selected tariff file
        
    Returns:
        Optional[TariffViewer]: TariffViewer instance or None if loading fails
    """
    try:
        # Check if we have modifications for this tariff
        if (st.session_state.get('has_modifications', False) and 
            st.session_state.get('modified_tariff') is not None):
            
            # Use modified tariff data
            return create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
        else:
            # Load original tariff
            return TariffViewer(selected_file)
            
    except Exception as e:
        st.error(f"❌ Error loading tariff: {str(e)}")
        st.info("💡 **Troubleshooting Tips:**")
        st.info("• Check that the JSON file is properly formatted")
        st.info("• Ensure the file contains valid URDB tariff data")
        st.info("• Try selecting a different tariff file")
        return None


def handle_tariff_switching(current_tariff_file: Path) -> None:
    """
    Handle switching between tariffs and clear modification state when needed.
    
    Args:
        current_tariff_file (Path): Currently selected tariff file
    """
    # Check if tariff has changed
    if ('last_tariff_file' not in st.session_state or 
        st.session_state.last_tariff_file != current_tariff_file):
        
        st.session_state.last_tariff_file = current_tariff_file
        
        # Clear form states when switching tariffs
        form_state_keys = [
            'form_labels', 'form_rates', 'form_adjustments',
            'demand_form_labels', 'demand_form_rates', 'demand_form_adjustments',
            'flat_demand_form_rates', 'flat_demand_form_adjustments'
        ]
        
        for key in form_state_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear modification state when switching tariffs (unless it's a user-generated tariff)
        if not str(current_tariff_file).startswith(str(Settings.USER_DATA_DIR)):
            st.session_state.modified_tariff = None
            st.session_state.has_modifications = False


def render_tariff_info_chips(tariff_viewer: TariffViewer) -> None:
    """
    Render the tariff information chips (matches original layout).
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    # Context chips for quick reference (matching original)
    st.markdown(
        f"""
        <div class="chips">
            <div class="chip">🏢 {tariff_viewer.utility_name}</div>
            <div class="chip">⚡ {tariff_viewer.rate_name}</div>
            <div class="chip">🏭 {tariff_viewer.sector}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_load_profile_analysis_tab(selected_load_profile: Optional[Path], options: dict) -> None:
    """
    Render the load profile analysis tab.
    
    Args:
        selected_load_profile (Optional[Path]): Selected load profile file
        options (dict): Display options
    """
    st.markdown(create_section_header_html("📊 Load Profile Analysis"), unsafe_allow_html=True)
    
    if not selected_load_profile:
        st.info("ℹ️ Select a load profile from the sidebar to analyze.")
        return
    
    try:
        # Load and analyze the profile
        from src.services.calculation_service import CalculationService
        
        validation_results = CalculationService.validate_load_profile(selected_load_profile)
        
        if validation_results['is_valid']:
            # Load the profile data
            profile_df = FileService.load_csv_file(selected_load_profile)
            
            # Show analysis
            from src.components.load_generator import show_load_profile_analysis
            show_load_profile_analysis(profile_df, options)
            
        else:
            st.error("❌ Invalid load profile file")
            for error in validation_results.get('errors', []):
                st.error(f"• {error}")
                
    except Exception as e:
        st.error(f"❌ Error analyzing load profile: {str(e)}")


def render_tariff_information_section(tariff_viewer: TariffViewer) -> None:
    """
    Render the tariff information section.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    from datetime import datetime
    
    st.markdown(create_section_header_html("📋 Basic Tariff Information"), unsafe_allow_html=True)
    
    # Basic information metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Utility Company</h3>
            <p>{tariff_viewer.utility_name}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Rate Schedule</h3>
            <p>{tariff_viewer.rate_name}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Customer Sector</h3>
            <p>{tariff_viewer.sector}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Description
    st.markdown(create_section_header_html("📝 Description"), unsafe_allow_html=True)
    st.markdown(tariff_viewer.description)
    
    # Critical Cost Information
    st.markdown(create_section_header_html("💰 Cost Information"), unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fixed_charge = tariff_viewer.tariff.get('fixedchargefirstmeter', None)
        fixed_charge_units = tariff_viewer.tariff.get('fixedchargeunits', '$/month')
        if fixed_charge is not None:
            st.metric("Fixed Monthly Charge", f"${fixed_charge:,.2f}", delta=fixed_charge_units)
        else:
            st.metric("Fixed Monthly Charge", "Not specified")
    
    with col2:
        min_charge = tariff_viewer.tariff.get('mincharge', None)
        min_charge_units = tariff_viewer.tariff.get('minchargeunits', '$/month')
        if min_charge is not None:
            st.metric("Minimum Monthly Charge", f"${min_charge:,.2f}", delta=min_charge_units)
        else:
            st.metric("Minimum Monthly Charge", "Not specified")
    
    with col3:
        start_date = tariff_viewer.tariff.get('startdate', None)
        if start_date:
            # Convert Unix timestamp to readable date
            date_obj = datetime.fromtimestamp(start_date)
            formatted_date = date_obj.strftime('%B %d, %Y')
            st.metric("Effective Date", formatted_date)
        else:
            st.metric("Effective Date", "Not specified")
    
    # Service Requirements
    st.markdown(create_section_header_html("⚙️ Service Requirements"), unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        service_type = tariff_viewer.tariff.get('servicetype', 'Not specified')
        st.markdown(f"""
        <div class="metric-card">
            <h3>Service Type</h3>
            <p>{service_type}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        voltage = tariff_viewer.tariff.get('voltagecategory', 'Not specified')
        st.markdown(f"""
        <div class="metric-card">
            <h3>Voltage Category</h3>
            <p>{voltage}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        phase = tariff_viewer.tariff.get('phasewiring', 'Not specified')
        st.markdown(f"""
        <div class="metric-card">
            <h3>Phase Wiring</h3>
            <p>{phase}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        country = tariff_viewer.tariff.get('country', 'Not specified')
        st.markdown(f"""
        <div class="metric-card">
            <h3>Country</h3>
            <p>{country}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Capacity Requirements (if present)
    min_capacity = tariff_viewer.tariff.get('peakkwcapacitymin', None)
    max_capacity = tariff_viewer.tariff.get('peakkwcapacitymax', None)
    
    if min_capacity is not None or max_capacity is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            if min_capacity is not None:
                st.metric("Minimum Peak Capacity", f"{min_capacity:,.0f} kW")
            else:
                st.metric("Minimum Peak Capacity", "Not specified")
        
        with col2:
            if max_capacity is not None:
                st.metric("Maximum Peak Capacity", f"{max_capacity:,.0f} kW")
            else:
                st.metric("Maximum Peak Capacity", "Not specified")
    
    # Documentation & Sources
    st.markdown(create_section_header_html("📚 Documentation & Sources"), unsafe_allow_html=True)
    
    eiaid = tariff_viewer.tariff.get('eiaid', None)
    if eiaid:
        st.info(f"**EIA Utility ID:** {eiaid}")
    
    source = tariff_viewer.tariff.get('source', None)
    if source:
        st.markdown(f"**📄 Source Document:** [View Tariff PDF]({source})")
    
    source_parent = tariff_viewer.tariff.get('sourceparent', None)
    if source_parent:
        st.markdown(f"**🌐 Utility Tariff Page:** [View All Tariffs]({source_parent})")
    
    uri = tariff_viewer.tariff.get('uri', None)
    if uri:
        st.markdown(f"**🔗 OpenEI Database Entry:** [View on OpenEI]({uri})")
    
    supersedes = tariff_viewer.tariff.get('supersedes', None)
    if supersedes:
        st.info(f"**Supersedes:** Previous tariff version ID: `{supersedes}`")
    
    # Important Notes
    st.markdown(create_section_header_html("📌 Important Notes"), unsafe_allow_html=True)
    
    energy_comments = tariff_viewer.tariff.get('energycomments', None)
    if energy_comments:
        with st.expander("⚡ Energy Rate Comments", expanded=True):
            st.markdown(energy_comments)
    
    demand_comments = tariff_viewer.tariff.get('demandcomments', None)
    if demand_comments:
        with st.expander("🔌 Demand Rate Comments", expanded=True):
            st.markdown(demand_comments)
    
    dg_rules = tariff_viewer.tariff.get('dgrules', None)
    if dg_rules:
        st.success(f"**🔋 Distributed Generation Rules:** {dg_rules}")
    
    # Additional Details
    demand_units = tariff_viewer.tariff.get('demandunits', None)
    flat_demand_unit = tariff_viewer.tariff.get('flatdemandunit', None)
    demand_rate_unit = tariff_viewer.tariff.get('demandrateunit', None)
    reactive_power_charge = tariff_viewer.tariff.get('demandreactivepowercharge', None)
    
    if any([demand_units, flat_demand_unit, demand_rate_unit, reactive_power_charge]):
        with st.expander("⚙️ Additional Technical Details"):
            if demand_units:
                st.write(f"**Demand Units:** {demand_units}")
            if flat_demand_unit:
                st.write(f"**Flat Demand Unit:** {flat_demand_unit}")
            if demand_rate_unit:
                st.write(f"**Demand Rate Unit:** {demand_rate_unit}")
            if reactive_power_charge:
                st.write(f"**Reactive Power Charge:** ${reactive_power_charge:.2f}/kVAR")
    
    # Raw JSON data viewer
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    with st.expander("🔍 View Raw JSON Data"):
        st.json(tariff_viewer.data)


def main() -> None:
    """Main application function."""
    # Initialize the application with basic CSS first
    initialize_app(dark_mode=False)
    
    # Create sidebar and get selections
    selected_tariff_file, selected_load_profile, sidebar_options = create_sidebar()
    
    # Apply dark mode CSS if enabled
    if sidebar_options.get('dark_mode', False):
        from src.utils.styling import get_dark_mode_css
        st.markdown(get_dark_mode_css(), unsafe_allow_html=True)
    
    # Handle case where no tariff file is selected
    if not selected_tariff_file:
        st.error("❌ No tariff file selected. Please select a tariff from the sidebar.")
        st.stop()
    
    # Handle tariff switching
    handle_tariff_switching(selected_tariff_file)
    
    # Load tariff viewer
    tariff_viewer = load_tariff_viewer(selected_tariff_file)
    
    if not tariff_viewer:
        st.error("❌ Failed to load tariff data.")
        st.stop()
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Tariff Information",
        "💰 Utility Cost Analysis", 
        "🔧 Load Profile Generator", 
        "📊 LP Analysis",
        "🏗️ Tariff Builder"
    ])
    
    # Tariff Information tab with sub-tabs
    with tab1:
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "⚡ Energy Rates",
            "🔌 Demand Rates",
            "📊 Flat Demand",
            "📄 Basic Info"
        ])
        
        with subtab1:
            render_energy_rates_tab(tariff_viewer, sidebar_options)
        
        with subtab2:
            render_demand_rates_tab(tariff_viewer, sidebar_options)
        
        with subtab3:
            render_flat_demand_rates_tab(tariff_viewer, sidebar_options)
        
        with subtab4:
            render_tariff_information_section(tariff_viewer)
    
    # Utility Cost Analysis tab with sub-tabs
    with tab2:
        cost_subtab1, cost_subtab2 = st.tabs([
            "Utilization Analysis",
            "Utility Bill Calculator"
        ])
        
        with cost_subtab1:
            render_load_factor_analysis_tab(tariff_viewer, sidebar_options)
        
        with cost_subtab2:
            render_utility_cost_calculation_tab(tariff_viewer, selected_load_profile, sidebar_options)
    
    # Other main tabs
    with tab3:
        render_load_generator_tab(tariff_viewer, sidebar_options)
    
    with tab4:
        render_load_profile_analysis_tab(selected_load_profile, sidebar_options)
    
    with tab5:
        render_tariff_builder_tab()


if __name__ == "__main__":
    main()
