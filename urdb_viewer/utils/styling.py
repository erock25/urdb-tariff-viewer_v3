"""
Styling utilities for URDB Tariff Viewer.

This module contains all CSS styling and theme management for the Streamlit application.
"""

from typing import Any, Dict

import streamlit as st


def get_theme_colors() -> Dict[str, str]:
    """
    Get the application theme colors.

    Returns:
        Dict[str, str]: Dictionary of theme colors
    """
    return {
        "primary": "#1e40af",
        "secondary": "#7c3aed",
        "background": "#ffffff",
        "text": "#1f2937",
        "text_light": "#374151",
        "border": "#e5e7eb",
        "border_light": "#cbd5e1",
        "surface": "#f8fafc",
        "surface_hover": "#f1f5f9",
        "info_bg": "#eff6ff",
        "info_border": "#bfdbfe",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
    }


def get_custom_css() -> str:
    """
    Get the complete custom CSS for the application.

    Returns:
        str: CSS string for styling the application
    """
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #ffffff;
        color: #1f2937;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Minimize top padding */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    /* Remove extra spacing from top */
    section.main > div {
        padding-top: 0 !important;
    }

    /* Remove default Streamlit top spacing */
    .appview-container .main .block-container {
        padding-top: 0rem !important;
    }

    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
    }

    /* Main header styling */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 0 0 3rem 0;
        padding: 2rem 0;
        position: relative;
    }

    .main-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 4px;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        border-radius: 2px;
    }

    /* Modern metric cards */
    .metric-card {
        background: #ffffff;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.1);
        border-color: #cbd5e1;
    }

    .metric-card h3 {
        color: #1f2937;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0 0 0.5rem 0;
    }

    .metric-card p {
        color: #0f172a;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: #f8fafc !important;
        border-right: 2px solid #cbd5e1 !important;
    }

    .stSidebar > div {
        padding-top: 0.5rem !important;
    }

    .sidebar-header {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* Ensure sidebar is visible */
    .stSidebar[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        width: 300px !important;
        min-width: 300px !important;
    }

    /* Sidebar content styling */
    .stSidebar .stSelectbox label {
        font-weight: 500 !important;
        color: #1f2937 !important;
        font-size: 0.9rem !important;
    }

    .stSidebar .stCheckbox label {
        font-weight: 500 !important;
        color: #1f2937 !important;
    }

    /* Ensure all sidebar text has proper contrast */
    .stSidebar .stSelectbox div,
    .stSidebar .stCheckbox div,
    .stSidebar p,
    .stSidebar span {
        color: #1f2937 !important;
    }

    /* Section headers */
    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e5e7eb;
        position: relative;
    }

    .section-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #f8fafc;
        padding: 6px;
        border-radius: 12px;
        margin-top: 0 !important;
        margin-bottom: 2rem;
        border: 1px solid #cbd5e1;
    }

    .stTabs {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        background-color: transparent;
        border: none;
        color: #374151;
        font-weight: 500;
        padding: 12px 24px;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        color: white !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        border: 2px solid #1e40af;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border-color: #1e3a8a;
    }

    /* Form controls */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stCheckbox > label {
        border-radius: 8px;
        border: 2px solid #cbd5e1;
        font-family: 'Inter', sans-serif;
        background-color: #ffffff !important;
        color: #1f2937 !important;
    }

    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: #1e40af;
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
    }

    /* Light mode selectbox dropdown styling */
    .stSelectbox [data-baseweb="select"] {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        color: #1f2937 !important;
    }

    .stSelectbox [data-baseweb="select"] * {
        color: #1f2937 !important;
        background-color: inherit !important;
    }

    /* Light mode selectbox dropdown options */
    .stSelectbox [data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }

    .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"] {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }

    .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"]:hover {
        background-color: #f8fafc !important;
        color: #1f2937 !important;
    }

    .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"][data-baseweb="menu-item--selected"] {
        background-color: #eff6ff !important;
        color: #1e40af !important;
    }

    /* Info boxes */
    .stInfo {
        background-color: #eff6ff;
        border: 2px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Statistics cards container */
    .stats-container {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 2px solid #e2e8f0;
    }

    /* Ensure proper spacing for metric columns */
    .stats-container .stColumn {
        padding: 0.5rem;
    }

    /* Additional fallback styling for metric text */
    .stMetric {
        color: inherit !important;
    }

    .stMetric div {
        color: inherit !important;
    }

    .stMetric span {
        color: inherit !important;
    }

    /* Base dataframe styling */
    .stDataFrame {
        color: #1f2937 !important;
        border-radius: 6px !important;
        overflow: hidden !important;
    }

    .stDataFrame div {
        color: inherit !important;
    }

    .stDataFrame span {
        color: inherit !important;
    }

    .stDataFrame td {
        color: inherit !important;
        padding: 8px 12px !important;
        border-bottom: 1px solid #f3f4f6 !important;
    }

    .stDataFrame th {
        color: #1f2937 !important;
        font-weight: 600 !important;
        padding: 12px 12px 8px 12px !important;
        border-bottom: 2px solid #e5e7eb !important;
    }

    /* Improve metric layout */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06) !important;
        min-height: 100px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }

    [data-testid="metric-container"] [data-testid="metric-label"],
    [data-testid="metric-container"] .stMetricLabel,
    .stMetric [data-testid="metric-label"] {
        color: #1f2937 !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-value"],
    [data-testid="metric-container"] .stMetricValue,
    .stMetric [data-testid="metric-value"] {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-delta"],
    [data-testid="metric-container"] .stMetricDelta,
    .stMetric [data-testid="metric-delta"] {
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-top: 0.25rem !important;
        line-height: 1.2 !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 8px;
        font-weight: 500;
        border: 1px solid #cbd5e1;
    }

    /* Custom divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #1e40af 50%, transparent 100%);
        border: none;
        margin: 2rem 0;
    }

    /* Chips styling */
    .chips {
        display: flex;
        gap: 8px;
        justify-content: center;
        margin: 8px 0 20px 0;
    }

    .chip {
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid #cbd5e1;
        color: #1f2937;
        padding: 8px 12px;
        border-radius: 9999px;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    </style>
    """


def get_dark_mode_css() -> str:
    """
    Get the comprehensive dark mode CSS for the application.

    Returns:
        str: CSS string for dark mode styling
    """
    return """
    <style>
    /* Dark Mode Styling */
    .stApp {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
    }

    /* Minimize top padding in dark mode */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    /* Remove extra spacing from top */
    section.main > div {
        padding-top: 0 !important;
    }

    /* Remove default Streamlit top spacing */
    .appview-container .main .block-container {
        padding-top: 0rem !important;
    }

    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
    }

    /* Dark mode metric styling */
    .metric-card, .stats-container {
        background: #1e293b !important;
        border-color: #334155 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }

    .metric-card h3, .section-header {
        color: #f1f5f9 !important;
    }

    .metric-card p {
        color: #e2e8f0 !important;
    }

    /* Dark mode tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1e293b !important;
        border-color: #334155 !important;
        margin-top: 0 !important;
    }

    .stTabs {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #cbd5e1 !important;
    }

    .stTabs [aria-selected="true"] {
        box-shadow: 0 2px 10px rgba(0,0,0,0.5) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
    }

    /* Dark mode sidebar */
    .stSidebar {
        background-color: #0f172a !important;
        border-right: 2px solid #334155 !important;
        color: #f1f5f9 !important;
    }

    .stSidebar .sidebar-header {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
    }

    /* Dark mode sidebar text colors for optimal contrast */
    .stSidebar .stSelectbox label,
    .stSidebar .stCheckbox label,
    .stSidebar .stNumberInput label,
    .stSidebar .stSlider label,
    .stSidebar .stFileUploader label,
    .stSidebar .stButton label {
        color: #f1f5f9 !important;
        font-weight: 500 !important;
    }

    .stSidebar .stSelectbox div,
    .stSidebar .stCheckbox div,
    .stSidebar .stNumberInput div,
    .stSidebar .stSlider div,
    .stSidebar p,
    .stSidebar span,
    .stSidebar .stSelectbox,
    .stSidebar .stCheckbox,
    .stSidebar .stMarkdown {
        color: #f1f5f9 !important;
    }

    /* Dark mode sidebar interactive elements */
    .stSidebar .stSelectbox [data-baseweb="select"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }

    .stSidebar .stSelectbox [data-baseweb="select"] *,
    .stSidebar .stSelectbox [data-baseweb="select"] span,
    .stSidebar .stSelectbox [data-baseweb="select"] div {
        color: #f1f5f9 !important;
    }

    .stSidebar .stCheckbox [data-baseweb="checkbox"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }

    .stSidebar .stNumberInput input {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stSidebar .stSlider [data-baseweb="slider"] {
        background-color: #1e293b !important;
    }

    /* Dark mode sidebar info boxes */
    .stSidebar .stInfo {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stSidebar .stInfo *,
    .stSidebar .stInfo p,
    .stSidebar .stInfo span {
        color: #f1f5f9 !important;
    }

    .stSidebar .stSuccess {
        background-color: #134e4a !important;
        border-color: #065f46 !important;
        color: #a7f3d0 !important;
    }

    .stSidebar .stWarning {
        background-color: #451a03 !important;
        border-color: #78350f !important;
        color: #fde68a !important;
    }

    .stSidebar .stError {
        background-color: #450a0a !important;
        border-color: #7f1d1d !important;
        color: #fecaca !important;
    }

    /* Dark mode buttons */
    .stButton > button {
        border-color: #3b82f6 !important;
        box-shadow: 0 4px 16px rgba(59,130,246,0.3) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(59,130,246,0.4) !important;
    }

    /* Dark mode form controls */
    .stSelectbox [data-baseweb="select"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stSelectbox [data-baseweb="select"] * {
        color: #f1f5f9 !important;
        background-color: inherit !important;
    }

    .stNumberInput input {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stCheckbox [data-baseweb="checkbox"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }

    .stRadio [data-baseweb="radio"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }

    .stSlider [data-baseweb="slider"] {
        background-color: #1e293b !important;
    }

    /* Dark mode dropdowns */
    .stSelectbox [data-baseweb="popover"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
    }

    .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"] {
        color: #f1f5f9 !important;
        background-color: #1e293b !important;
    }

    .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"]:hover {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"][data-baseweb="menu-item--selected"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }

    /* Dark mode chips */
    .chips {
        display: flex;
        gap: 8px;
        justify-content: center;
        flex-wrap: wrap;
        margin: 8px 0 20px 0;
    }

    .chip {
        background: rgba(51, 65, 85, 0.8) !important;
        border: 1px solid #475569 !important;
        color: #f1f5f9 !important;
        padding: 8px 12px;
        border-radius: 9999px;
        font-weight: 600;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }

    /* Dark mode headers */
    .main-header {
        background: none !important;
        -webkit-background-clip: initial !important;
        -webkit-text-fill-color: initial !important;
        background-clip: initial !important;
        color: #ffffff !important;
    }

    .section-header {
        color: #f1f5f9 !important;
        border-bottom-color: #334155 !important;
    }

    .custom-divider {
        background: linear-gradient(90deg, transparent 0%, #3b82f6 50%, transparent 100%) !important;
    }

    /* Dark mode info boxes */
    .stInfo {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stSuccess {
        background-color: #134e4a !important;
        border-color: #065f46 !important;
        color: #a7f3d0 !important;
    }

    .stWarning {
        background-color: #451a03 !important;
        border-color: #78350f !important;
        color: #fde68a !important;
    }

    .stError {
        background-color: #450a0a !important;
        border-color: #7f1d1d !important;
        color: #fecaca !important;
    }

    /* Dark mode expanders */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    /* Dark mode metric containers */
    [data-testid="metric-container"] {
        background: #1e293b !important;
        border-color: #334155 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }

    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: #cbd5e1 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #f1f5f9 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-delta"] {
        color: #94a3b8 !important;
    }

    /* Dark mode dataframes */
    .stDataFrame {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border-color: #334155 !important;
    }

    .stDataFrame div {
        color: #f1f5f9 !important;
        background-color: inherit !important;
    }

    .stDataFrame span {
        color: #f1f5f9 !important;
    }

    .stDataFrame td {
        color: #f1f5f9 !important;
        border-bottom: 1px solid #334155 !important;
        background-color: #1e293b !important;
    }

    .stDataFrame th {
        color: #f1f5f9 !important;
        border-bottom: 2px solid #334155 !important;
        background-color: #0f172a !important;
    }

    /* Dark mode file uploader */
    .stFileUploader {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    .stFileUploader div {
        color: #f1f5f9 !important;
        background-color: inherit !important;
    }

    /* Dark mode text areas and inputs */
    .stTextInput input,
    .stTextArea textarea {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    /* Dark mode code blocks */
    .stCode {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }

    /* Dark mode markdown */
    .stMarkdown {
        color: #f1f5f9 !important;
    }

    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6 {
        color: #f1f5f9 !important;
    }

    .stMarkdown p {
        color: #e2e8f0 !important;
    }

    .stMarkdown code {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        padding: 2px 4px;
        border-radius: 4px;
    }

    /* Dark mode captions */
    .caption {
        color: #94a3b8 !important;
    }

    /* Ensure proper contrast for all text elements */
    * {
        color: inherit;
    }
    </style>
    """


def apply_custom_css(dark_mode: bool = False) -> None:
    """
    Apply custom CSS styling to the Streamlit application.

    Args:
        dark_mode (bool): Whether to apply dark mode styling

    This function should be called once at the beginning of the main app.
    """
    # Apply base CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # Apply dark mode CSS if enabled
    if dark_mode:
        st.markdown(get_dark_mode_css(), unsafe_allow_html=True)


def create_metric_card_html(title: str, value: str, description: str = "") -> str:
    """
    Create HTML for a custom metric card.

    Args:
        title (str): The title/label for the metric
        value (str): The metric value to display
        description (str): Optional description text

    Returns:
        str: HTML string for the metric card
    """
    desc_html = (
        f"<p style='color: #6b7280; font-size: 0.875rem; margin-top: 0.5rem;'>{description}</p>"
        if description
        else ""
    )

    return f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <p>{value}</p>
        {desc_html}
    </div>
    """


def create_section_header_html(title: str) -> str:
    """
    Create HTML for a section header.

    Args:
        title (str): The section title

    Returns:
        str: HTML string for the section header
    """
    return f'<h2 class="section-header">{title}</h2>'


def create_sidebar_header_html(title: str) -> str:
    """
    Create HTML for a sidebar header.

    Args:
        title (str): The header title

    Returns:
        str: HTML string for the sidebar header
    """
    return f'<div class="sidebar-header">{title}</div>'


def create_custom_divider_html() -> str:
    """
    Create HTML for a custom divider.

    Returns:
        str: HTML string for the custom divider
    """
    return '<hr class="custom-divider">'
