"""
TelematicsPro - Vehicle Telematics Data Pipeline
================================================
A professional-grade Streamlit application for processing
vehicle telematics data.

Author: TelematicsPro Team
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import io

# Import custom modules
from src.constants import (
    STANDARD_FEATURES, CRITICAL_FEATURES, AVAILABLE_FEATURES,
    FEATURE_CATEGORIES, MISSING_STRATEGIES, OUTLIER_STRATEGIES,
    MAX_FILE_SIZE_MB, WARNING_FILE_SIZE_MB
)
from src.engine import (
    analyze_column, suggest_mapping, is_complex_field,
    standardize_columns, segment_into_trips,
    extract_feature, extract_selected_features,
    apply_column_cleaning
)
from src.sample_data import generate_sample_data
from src.utils import get_file_size_mb, format_number, generate_processing_report


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TelematicsPro - Vehicle Telematics Pipeline",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headers */
    h1 {
        color: #1F2937;
        font-weight: 700;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #3B82F622, #3B82F611);
        border: 1px solid #3B82F644;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
    }
    
    /* Quality badges */
    .badge-good {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .badge-bad {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 500;
    }
    
    /* Progress indicator */
    .stage-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    
    /* Dataframe styling */
    .dataframe {
        font-size: 12px;
    }
    
    /* File size warning */
    .file-warning {
        background-color: #FEF3C7;
        border: 1px solid #F59E0B;
        border-radius: 8px;
        padding: 12px;
        margin: 12px 0;
    }
    
    .file-error {
        background-color: #FEE2E2;
        border: 1px solid #EF4444;
        border-radius: 8px;
        padding: 12px;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'stage': 1,
        'max_reached': 1,
        'raw_data': None,
        'file_name': None,
        'column_analyses': {},
        'kept_columns': [],
        'dropped_columns': [],
        'column_mappings': {},
        'complex_configs': [],
        'standardized_data': None,
        'trips': [],
        'trip_summaries': [],
        'selected_features': [],
        'trip_level_data': None,
        'cleaning_configs': [],
        'cleaned_data': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session():
    """Reset all session state to start fresh."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()


init_session_state()


# ============================================================
# SIDEBAR - NAVIGATION
# ============================================================

def render_sidebar():
    """Render the sidebar with navigation and info."""
    with st.sidebar:
        st.markdown("## TelematicsPro")
        st.markdown("*Vehicle Telematics Pipeline*")
        st.markdown("---")
        
        # Stage navigation
        st.markdown("### Pipeline Stages")
        
        stages = [
            (1, "Upload & Inspect"),
            (2, "Map & Parse"),
            (3, "Segment & Extract"),
            (4, "Clean"),
            (5, "Analyze"),
            (6, "Export"),
        ]
        
        for num, name in stages:
            if num <= st.session_state.max_reached:
                if st.button(
                    f"{'Done: ' if num < st.session_state.stage else '> ' if num == st.session_state.stage else ''}{name}",
                    key=f"nav_{num}",
                    use_container_width=True
                ):
                    st.session_state.stage = num
                    st.rerun()
            else:
                st.button(
                    f"Locked: {name}",
                    key=f"nav_{num}",
                    disabled=True,
                    use_container_width=True
                )
        
        st.markdown("---")
        
        # File info
        if st.session_state.raw_data is not None:
            st.markdown("### Current File")
            st.markdown(f"**{st.session_state.file_name}**")
            st.markdown(f"{len(st.session_state.raw_data):,} rows x {len(st.session_state.raw_data.columns)} cols")
            
            if st.button("Start Over", type="secondary", use_container_width=True):
                reset_session()
                st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        Transform messy telematics CSV files into clean, 
        analysis-ready trip-level datasets.
        
        **Privacy**: All processing happens locally in your browser.
        """)


# ============================================================
# STAGE 1: UPLOAD & INSPECT
# ============================================================

def render_stage1():
    """Render Stage 1: Upload and Inspect."""
    st.markdown("# Stage 1: Upload & Inspect")
    st.markdown("Upload your telematics CSV file and explore the data quality.")
    
    # File upload area
    if st.session_state.raw_data is None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose a CSV file",
                type=['csv'],
                help="Upload a CSV file containing telematics data"
            )
            
            if uploaded_file is not None:
                # Check file size
                file_size_mb = get_file_size_mb(uploaded_file)
                
                if file_size_mb > MAX_FILE_SIZE_MB:
                    st.markdown(f"""
                    <div class="file-error">
                        <strong>File too large!</strong><br>
                        Your file is {file_size_mb:.1f} MB. Maximum recommended size is {MAX_FILE_SIZE_MB} MB.<br>
                        Please reduce file size by sampling or filtering before uploading.
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif file_size_mb > WARNING_FILE_SIZE_MB:
                    st.markdown(f"""
                    <div class="file-warning">
                        <strong>Large file detected!</strong><br>
                        Your file is {file_size_mb:.1f} MB. Processing may be slow.<br>
                        Recommended: Keep files under {WARNING_FILE_SIZE_MB} MB for best performance.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Proceed with Upload", type="primary"):
                        load_file(uploaded_file)
                else:
                    load_file(uploaded_file)
        
        with col2:
            st.markdown("### Try Sample Data")
            if st.button("Load Sample Dataset", use_container_width=True):
                with st.spinner("Generating sample data..."):
                    df = generate_sample_data()
                    st.session_state.raw_data = df
                    st.session_state.file_name = "sample_telematics.csv"
                    analyze_columns(df)
                    st.rerun()
            
            st.markdown("""
            <small>
            Sample includes:
            - 3 vehicles
            - ~15 trips
            - GPS, speed, RPM, fuel data
            - Encoded accelerometer field
            </small>
            """, unsafe_allow_html=True)
    
    else:
        # Data is loaded - show analysis
        render_data_analysis()


def load_file(uploaded_file):
    """Load and analyze the uploaded file."""
    with st.spinner("Loading and analyzing file..."):
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.raw_data = df
            st.session_state.file_name = uploaded_file.name
            analyze_columns(df)
            st.rerun()
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")


def analyze_columns(df: pd.DataFrame):
    """Analyze all columns in the dataframe."""
    analyses = {}
    progress = st.progress(0)
    
    for i, col in enumerate(df.columns):
        analyses[col] = analyze_column(col, df[col])
        progress.progress((i + 1) / len(df.columns))
    
    st.session_state.column_analyses = analyses
    st.session_state.kept_columns = list(df.columns)
    st.session_state.dropped_columns = []


def render_data_analysis():
    """Render the data analysis view."""
    df = st.session_state.raw_data
    analyses = st.session_state.column_analyses
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("File", st.session_state.file_name[:20] + "..." if len(st.session_state.file_name) > 20 else st.session_state.file_name)
    with col2:
        st.metric("Rows", f"{len(df):,}")
    with col3:
        st.metric("Columns", len(df.columns))
    with col4:
        st.metric("Selected", f"{len(st.session_state.kept_columns)}/{len(df.columns)}")
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["Preview Raw Data", "Detailed Column Analysis"])
    
    with tab1:
        st.dataframe(df.head(20), use_container_width=True)
        st.caption(f"Showing first 20 of {len(df):,} rows")
    
    with tab2:
        render_column_analysis(analyses)
    
    # Column selection
    st.markdown("---")
    st.markdown("### Select Columns to Keep")
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Select All"):
            st.session_state.kept_columns = list(df.columns)
            st.rerun()
    with col2:
        if st.button("Deselect All"):
            st.session_state.kept_columns = []
            st.rerun()
    
    # Multi-select for columns
    selected = st.multiselect(
        "Columns to keep:",
        options=list(df.columns),
        default=st.session_state.kept_columns,
        help="Select which columns to include in processing"
    )
    st.session_state.kept_columns = selected
    st.session_state.dropped_columns = [c for c in df.columns if c not in selected]
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Continue to Mapping", type="primary", disabled=len(selected) == 0):
            st.session_state.stage = 2
            st.session_state.max_reached = max(st.session_state.max_reached, 2)
            st.rerun()


def render_column_analysis(analyses: dict):
    """Render detailed column analysis cards."""
    for col_name, analysis in analyses.items():
        is_kept = col_name in st.session_state.kept_columns
        
        with st.expander(
            f"{'[+]' if is_kept else '[-]'} **{col_name}** -- {analysis['inferred_type']} -- {analysis['missing_pct']:.1f}% missing",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Type:** {analysis['inferred_type']}")
                st.markdown(f"**Missing:** {analysis['missing_count']:,} ({analysis['missing_pct']:.1f}%)")
                st.markdown(f"**Unique:** {analysis['unique_count']:,}")
                
                # Quality flags
                if analysis['flags']:
                    st.markdown("**Flags:**")
                    for flag in analysis['flags']:
                        if 'High' in flag or 'constant' in flag:
                            st.markdown(f"<span class='badge-bad'>{flag}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span class='badge-warning'>{flag}</span>", unsafe_allow_html=True)
            
            with col2:
                if analysis['inferred_type'] == 'numeric':
                    st.markdown(f"**Min:** {analysis.get('min', 'N/A')}")
                    st.markdown(f"**Max:** {analysis.get('max', 'N/A')}")
                    st.markdown(f"**Mean:** {analysis.get('mean', 'N/A'):.2f}" if analysis.get('mean') else "**Mean:** N/A")
                    st.markdown(f"**Std:** {analysis.get('std', 'N/A'):.2f}" if analysis.get('std') else "**Std:** N/A")
                
                st.markdown(f"**Suggestion:** {analysis['suggestion']}")
            
            with col3:
                # Histogram for numeric
                if analysis.get('histogram'):
                    hist_df = pd.DataFrame(analysis['histogram'])
                    fig = px.bar(hist_df, x='bin', y='count', height=150)
                    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"hist_{col_name}")
                
                # Top values for categorical
                elif analysis.get('top_values'):
                    top_df = pd.DataFrame(analysis['top_values'][:5])
                    fig = px.bar(top_df, x='count', y='value', orientation='h', height=150)
                    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"bar_{col_name}")
            
            # Sample values
            st.markdown(f"**Sample values:** {', '.join(str(v) for v in analysis['sample_values'][:5])}")


# ============================================================
# STAGE 2: MAP & PARSE
# ============================================================

def render_stage2():
    """Render Stage 2: Column Mapping and Complex Parsing."""
    st.markdown("# Stage 2: Map & Parse")
    st.markdown("Map your columns to standard features and parse complex fields.")
    
    # Initialize mappings if needed
    if not st.session_state.column_mappings:
        mappings = {}
        for col in st.session_state.kept_columns:
            mappings[col] = suggest_mapping(col)
        st.session_state.column_mappings = mappings
    
    # Initialize complex configs if needed
    if not st.session_state.complex_configs:
        configs = []
        for col in st.session_state.kept_columns:
            analysis = st.session_state.column_analyses.get(col, {})
            if is_complex_field(analysis):
                configs.append({
                    'column': col,
                    'method': 'none',
                    'delimiter': None
                })
        st.session_state.complex_configs = configs
    
    # Summary metrics
    mapped_count = sum(1 for v in st.session_state.column_mappings.values() if v != 'do_not_map')
    critical_mapped = sum(1 for f in CRITICAL_FEATURES if f in st.session_state.column_mappings.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Columns to Map", len(st.session_state.kept_columns))
    with col2:
        st.metric("Mapped", mapped_count)
    with col3:
        st.metric("Critical Features", f"{critical_mapped}/{len(CRITICAL_FEATURES)}")
    
    # Critical features status
    st.markdown("### Critical Feature Coverage")
    cols = st.columns(len(CRITICAL_FEATURES))
    for i, feat in enumerate(CRITICAL_FEATURES):
        with cols[i]:
            is_mapped = feat in st.session_state.column_mappings.values()
            st.markdown(
                f"<span class='{'badge-good' if is_mapped else 'badge-bad'}'>"
                f"{'Yes' if is_mapped else 'No'}: {feat}</span>",
                unsafe_allow_html=True
            )
    
    # Tabs
    tab1, tab2 = st.tabs(["Standard Mapping", "Complex Field Parsing"])
    
    with tab1:
        render_mapping_interface()
    
    with tab2:
        render_complex_parsing()
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Back"):
            st.session_state.stage = 1
            st.rerun()
    with col3:
        if st.button("Continue", type="primary"):
            st.session_state.stage = 3
            st.session_state.max_reached = max(st.session_state.max_reached, 3)
            st.rerun()


def render_mapping_interface():
    """Render the column mapping interface."""
    st.markdown("Map your columns to standard telematics features:")
    
    used_features = set(v for v in st.session_state.column_mappings.values() if v != 'do_not_map')
    
    for col in st.session_state.kept_columns:
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            analysis = st.session_state.column_analyses.get(col, {})
            st.markdown(f"**{col}** <small>({analysis.get('inferred_type', 'unknown')})</small>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("-->")
        
        with col3:
            current = st.session_state.column_mappings.get(col, 'do_not_map')
            
            # Build options - exclude already used features except current
            options = ['do_not_map'] + [
                f for f in STANDARD_FEATURES
                if f not in used_features or f == current
            ]
            
            selected = st.selectbox(
                "Map to",
                options=options,
                index=options.index(current) if current in options else 0,
                key=f"map_{col}",
                label_visibility="collapsed"
            )
            
            st.session_state.column_mappings[col] = selected


def render_complex_parsing():
    """Render the complex field parsing interface."""
    if not st.session_state.complex_configs:
        st.info("No complex fields detected in your data.")
        return
    
    st.markdown("""
    <div class="file-warning">
    <strong>Complex Fields Detected</strong><br>
    The following columns appear to contain encoded or multi-value data. Choose a parsing method for each.
    </div>
    """, unsafe_allow_html=True)
    
    for i, config in enumerate(st.session_state.complex_configs):
        col_name = config['column']
        analysis = st.session_state.column_analyses.get(col_name, {})
        
        with st.expander(f"**{col_name}** -- Avg length: {analysis.get('avg_length', 0):.0f} chars", expanded=True):
            # Show sample values
            st.markdown("**Sample values:**")
            for val in analysis.get('sample_values', [])[:3]:
                st.code(str(val)[:100] + ('...' if len(str(val)) > 100 else ''))
            
            # Parsing method selection
            method = st.radio(
                "Parsing method",
                options=['none', 'accelerometer', 'json', 'delimiter'],
                format_func=lambda x: {
                    'none': 'Do not parse (keep as raw string)',
                    'accelerometer': 'Accelerometer/IMU (extract x, y, z)',
                    'json': 'JSON (parse as JSON object)',
                    'delimiter': 'Custom delimiter (split by character)',
                }[x],
                key=f"parse_{col_name}",
                index=['none', 'accelerometer', 'json', 'delimiter'].index(config['method'])
            )
            
            st.session_state.complex_configs[i]['method'] = method
            
            if method == 'delimiter':
                delimiter = st.text_input(
                    "Delimiter character",
                    value=config.get('delimiter', ';'),
                    key=f"delim_{col_name}"
                )
                st.session_state.complex_configs[i]['delimiter'] = delimiter


# ============================================================
# STAGE 3: SEGMENT & EXTRACT
# ============================================================

def render_stage3():
    """Render Stage 3: Trip Segmentation and Feature Extraction."""
    st.markdown("# Stage 3: Segment & Extract")
    st.markdown("Segment data into trips and select features to extract.")
    
    # Run segmentation if not done
    if not st.session_state.trips:
        with st.spinner("Standardizing columns and segmenting trips..."):
            run_segmentation()
    
    # Show trip statistics
    trips = st.session_state.trips
    summaries = st.session_state.trip_summaries
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trips", len(trips))
    with col2:
        avg_points = np.mean([len(t) for t in trips]) if trips else 0
        st.metric("Avg Points/Trip", f"{avg_points:.0f}")
    with col3:
        durations = [s['duration'] for s in summaries if s.get('duration')]
        avg_dur = np.mean(durations) if durations else 0
        st.metric("Avg Duration", f"{avg_dur/60:.1f} min")
    with col4:
        vehicles = set(s['vehicle_id'] for s in summaries if s.get('vehicle_id'))
        st.metric("Unique Vehicles", len(vehicles) if vehicles else "N/A")
    
    # Tabs
    tab1, tab2 = st.tabs(["Trip Details", "Feature Selection"])
    
    with tab1:
        render_trip_details(summaries)
    
    with tab2:
        render_feature_selection()
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Back"):
            st.session_state.stage = 2
            st.rerun()
    with col3:
        selected_count = len(st.session_state.selected_features)
        if st.button(f"Extract {selected_count} Features", type="primary", disabled=selected_count == 0):
            with st.spinner("Extracting features..."):
                run_feature_extraction()
            st.session_state.stage = 4
            st.session_state.max_reached = max(st.session_state.max_reached, 4)
            st.rerun()


def run_segmentation():
    """Run the standardization and segmentation pipeline."""
    df = st.session_state.raw_data[st.session_state.kept_columns].copy()
    
    # Standardize columns
    standardized = standardize_columns(
        df,
        st.session_state.column_mappings,
        st.session_state.complex_configs
    )
    st.session_state.standardized_data = standardized
    
    # Segment into trips
    trips, summaries = segment_into_trips(standardized)
    st.session_state.trips = trips
    st.session_state.trip_summaries = summaries


def render_trip_details(summaries):
    """Render trip details."""
    if not summaries:
        st.info("No trips found.")
        return
    
    # Duration distribution
    durations = [s['duration']/60 for s in summaries if s.get('duration')]
    if durations:
        fig = px.histogram(x=durations, nbins=20, labels={'x': 'Duration (minutes)'})
        fig.update_layout(title="Trip Duration Distribution", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Trip summary table
    st.markdown("### Trip Summary")
    summary_df = pd.DataFrame(summaries)
    if 'duration' in summary_df.columns:
        summary_df['duration_min'] = summary_df['duration'].apply(
            lambda x: f"{x/60:.1f}" if pd.notna(x) else "N/A"
        )
    st.dataframe(summary_df.head(50), use_container_width=True)
    st.caption(f"Showing first 50 of {len(summaries)} trips")


def render_feature_selection():
    """Render the feature selection interface."""
    st.markdown("Select which features to extract from each trip:")
    
    # Get mapped features
    mapped_features = set(
        v for v in st.session_state.column_mappings.values()
        if v != 'do_not_map'
    )
    
    # Add features from complex parsing
    for config in st.session_state.complex_configs:
        if config['method'] == 'accelerometer':
            mapped_features.update(['accel_x', 'accel_y', 'accel_z'])
    
    selected = set(st.session_state.selected_features)
    
    for category in FEATURE_CATEGORIES:
        category_features = [f for f in AVAILABLE_FEATURES if f['category'] == category]
        
        with st.expander(f"**{category}** ({sum(1 for f in category_features if f['name'] in selected)}/{len(category_features)})", expanded=True):
            cols = st.columns(2)
            
            for i, feat in enumerate(category_features):
                # Check if required mappings exist
                required = feat.get('requires', [])
                available = not required or any(r in mapped_features for r in required)
                
                with cols[i % 2]:
                    checked = st.checkbox(
                        f"**{feat['name']}**",
                        value=feat['name'] in selected,
                        disabled=not available,
                        key=f"feat_{feat['name']}"
                    )
                    st.caption(feat['description'])
                    
                    if not available:
                        st.caption(f"Requires: {', '.join(required)}")
                    
                    if checked and available:
                        selected.add(feat['name'])
                    elif feat['name'] in selected:
                        selected.discard(feat['name'])
    
    st.session_state.selected_features = list(selected)


def run_feature_extraction():
    """Run feature extraction for all trips."""
    mapped_features = set(
        v for v in st.session_state.column_mappings.values()
        if v != 'do_not_map'
    )
    
    # Add features from complex parsing
    for config in st.session_state.complex_configs:
        if config['method'] == 'accelerometer':
            mapped_features.update(['accel_x', 'accel_y', 'accel_z'])
    
    trip_level = extract_selected_features(
        st.session_state.trips,
        st.session_state.selected_features,
        mapped_features
    )
    
    st.session_state.trip_level_data = trip_level


# ============================================================
# STAGE 4: CLEAN
# ============================================================

def render_stage4():
    """Render Stage 4: Data Cleaning."""
    st.markdown("# Stage 4: Clean")
    st.markdown("Fine-tune cleaning for each column in your trip dataset.")
    
    df = st.session_state.trip_level_data
    
    if df is None or df.empty:
        st.error("No trip-level data available. Please go back and extract features.")
        return
    
    # Initialize cleaning configs
    if not st.session_state.cleaning_configs:
        configs = []
        for col in df.columns:
            configs.append({
                'column': col,
                'keep': True,
                'missing_strategy': 'leave',
                'zero_strategy': 'leave',
                'outlier_strategy': 'none',
                'custom_value': None
            })
        st.session_state.cleaning_configs = configs
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Trip Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        kept = sum(1 for c in st.session_state.cleaning_configs if c['keep'])
        st.metric("Keeping", kept)
    with col4:
        # Preview cleaned data
        preview = apply_column_cleaning(df, st.session_state.cleaning_configs)
        st.metric("Preview Rows", len(preview))
    
    # Column cleaning interface
    st.markdown("### Per-Column Cleaning Rules")
    
    for i, config in enumerate(st.session_state.cleaning_configs):
        col_name = config['column']
        col_data = df[col_name]
        
        missing_pct = col_data.isna().sum() / len(col_data) * 100
        
        with st.expander(
            f"{'[+]' if config['keep'] else '[-]'} **{col_name}** -- {missing_pct:.1f}% missing",
            expanded=False
        ):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                keep = st.checkbox("Keep column", value=config['keep'], key=f"keep_{col_name}")
                st.session_state.cleaning_configs[i]['keep'] = keep
                
                if keep:
                    missing_strat = st.selectbox(
                        "Missing values:",
                        options=[s[0] for s in MISSING_STRATEGIES],
                        format_func=lambda x: dict(MISSING_STRATEGIES)[x],
                        index=[s[0] for s in MISSING_STRATEGIES].index(config['missing_strategy']),
                        key=f"miss_{col_name}"
                    )
                    st.session_state.cleaning_configs[i]['missing_strategy'] = missing_strat
                    
                    if missing_strat == 'custom':
                        custom_val = st.text_input("Custom value:", key=f"custom_{col_name}")
                        st.session_state.cleaning_configs[i]['custom_value'] = custom_val
                    
                    # Check if numeric
                    if pd.api.types.is_numeric_dtype(col_data):
                        zero_strat = st.selectbox(
                            "Zero values:",
                            options=[s[0] for s in MISSING_STRATEGIES],
                            format_func=lambda x: dict(MISSING_STRATEGIES)[x],
                            index=[s[0] for s in MISSING_STRATEGIES].index(config['zero_strategy']),
                            key=f"zero_{col_name}"
                        )
                        st.session_state.cleaning_configs[i]['zero_strategy'] = zero_strat
                        
                        outlier_strat = st.selectbox(
                            "Outliers:",
                            options=[s[0] for s in OUTLIER_STRATEGIES],
                            format_func=lambda x: dict(OUTLIER_STRATEGIES)[x],
                            index=[s[0] for s in OUTLIER_STRATEGIES].index(config['outlier_strategy']),
                            key=f"out_{col_name}"
                        )
                        st.session_state.cleaning_configs[i]['outlier_strategy'] = outlier_strat
            
            with col2:
                # Distribution chart
                if pd.api.types.is_numeric_dtype(col_data):
                    fig = px.histogram(col_data.dropna(), nbins=20)
                    fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"clean_hist_{col_name}")
    
    # Live preview
    st.markdown("### Live Preview")
    preview = apply_column_cleaning(df, st.session_state.cleaning_configs)
    st.dataframe(preview.head(10), use_container_width=True)
    st.caption(f"Showing first 10 of {len(preview)} rows after cleaning")
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Back"):
            st.session_state.stage = 3
            st.rerun()
    with col3:
        if st.button("Apply & Continue", type="primary"):
            st.session_state.cleaned_data = apply_column_cleaning(df, st.session_state.cleaning_configs)
            st.session_state.stage = 5
            st.session_state.max_reached = max(st.session_state.max_reached, 5)
            st.rerun()


# ============================================================
# STAGE 5: ANALYZE
# ============================================================

def render_stage5():
    """Render Stage 5: Exploratory Data Analysis."""
    st.markdown("# Stage 5: Analyze")
    st.markdown("Explore your cleaned data with interactive visualizations.")
    
    df = st.session_state.cleaned_data
    
    if df is None or df.empty:
        st.error("No cleaned data available.")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Visual Explorer",
        "Data Profiling",
        "Correlation",
        "Analytics"
    ])
    
    with tab1:
        render_visual_explorer(df)
    
    with tab2:
        render_data_profiling(df)
    
    with tab3:
        render_correlation_analysis(df)
    
    with tab4:
        render_analytics(df)
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Back"):
            st.session_state.stage = 4
            st.rerun()
    with col3:
        if st.button("Continue to Export", type="primary"):
            st.session_state.stage = 6
            st.session_state.max_reached = max(st.session_state.max_reached, 6)
            st.rerun()


def render_visual_explorer(df):
    """Render the visual explorer."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        st.info("No numeric columns available for visualization.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        chart_type = st.selectbox(
            "Chart Type",
            options=['Histogram', 'Box Plot', 'Scatter', 'Line']
        )
    
    with col2:
        x_col = st.selectbox("X Axis / Column", options=numeric_cols)
    
    with col3:
        if chart_type == 'Scatter':
            y_col = st.selectbox("Y Axis", options=numeric_cols, index=min(1, len(numeric_cols)-1))
        else:
            y_col = None
    
    with col4:
        if st.button("Add Chart"):
            if 'charts' not in st.session_state:
                st.session_state.charts = []
            st.session_state.charts.append({
                'type': chart_type,
                'x': x_col,
                'y': y_col
            })
    
    # Render stored charts
    if 'charts' in st.session_state and st.session_state.charts:
        cols = st.columns(2)
        for i, chart in enumerate(st.session_state.charts):
            with cols[i % 2]:
                if chart['type'] == 'Histogram':
                    fig = px.histogram(df, x=chart['x'], nbins=30)
                elif chart['type'] == 'Box Plot':
                    fig = px.box(df, y=chart['x'])
                elif chart['type'] == 'Scatter':
                    fig = px.scatter(df, x=chart['x'], y=chart['y'])
                else:
                    fig = px.line(df, y=chart['x'])
                
                fig.update_layout(height=300, title=f"{chart['type']}: {chart['x']}", showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key=f"explorer_{i}")
                
                if st.button(f"Remove", key=f"remove_{i}"):
                    st.session_state.charts.pop(i)
                    st.rerun()


def render_data_profiling(df):
    """Render data profiling view."""
    st.markdown("### Dataset Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Numeric", len(df.select_dtypes(include=[np.number]).columns))
    with col4:
        memory = df.memory_usage(deep=True).sum() / 1024
        st.metric("Memory", f"{memory:.1f} KB")
    
    # Column selector
    selected_col = st.selectbox("Select column to profile", options=df.columns.tolist())
    
    if selected_col:
        col_data = df[selected_col]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Statistics")
            stats = {
                'Count': len(col_data),
                'Missing': col_data.isna().sum(),
                'Missing %': f"{col_data.isna().sum() / len(col_data) * 100:.2f}%",
                'Unique': col_data.nunique(),
            }
            
            if pd.api.types.is_numeric_dtype(col_data):
                numeric = col_data.dropna()
                stats.update({
                    'Mean': f"{numeric.mean():.4f}",
                    'Std': f"{numeric.std():.4f}",
                    'Min': f"{numeric.min():.4f}",
                    'Max': f"{numeric.max():.4f}",
                    'Median': f"{numeric.median():.4f}",
                })
            
            for k, v in stats.items():
                st.markdown(f"**{k}:** {v}")
        
        with col2:
            st.markdown("#### Distribution")
            if pd.api.types.is_numeric_dtype(col_data):
                fig = px.histogram(col_data.dropna(), nbins=30)
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key=f"profile_hist_{selected_col}")
            else:
                value_counts = col_data.value_counts().head(10)
                fig = px.bar(x=value_counts.values, y=value_counts.index, orientation='h')
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key=f"profile_bar_{selected_col}")


def render_correlation_analysis(df):
    """Render correlation analysis."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        st.info("Need at least 2 numeric columns for correlation analysis.")
        return
    
    # Column selector
    selected_cols = st.multiselect(
        "Select columns for correlation:",
        options=numeric_cols,
        default=numeric_cols[:min(10, len(numeric_cols))]
    )
    
    if len(selected_cols) >= 2:
        corr = df[selected_cols].corr()
        
        # Heatmap
        fig = px.imshow(
            corr,
            labels=dict(color="Correlation"),
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top correlations
        st.markdown("### Top Correlated Pairs")
        corr_pairs = []
        for i in range(len(selected_cols)):
            for j in range(i+1, len(selected_cols)):
                corr_pairs.append({
                    'Pair': f"{selected_cols[i]} / {selected_cols[j]}",
                    'Correlation': abs(corr.iloc[i, j])
                })
        
        pairs_df = pd.DataFrame(corr_pairs).sort_values('Correlation', ascending=False).head(10)
        st.dataframe(pairs_df, use_container_width=True)


def render_analytics(df):
    """Render trip analytics."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Auto-detect key metrics
    metrics = []
    
    for col in numeric_cols:
        if 'duration' in col.lower():
            val = df[col].mean()
            metrics.append(('Avg Duration', f"{val:.1f}s", col))
        elif 'speed' in col.lower() and 'avg' in col.lower():
            val = df[col].mean()
            metrics.append(('Avg Speed', f"{val:.1f}", col))
        elif 'distance' in col.lower():
            val = df[col].mean()
            metrics.append(('Avg Distance', f"{val:.2f}", col))
        elif 'harsh' in col.lower() and 'brak' in col.lower():
            val = df[col].mean()
            metrics.append(('Avg Harsh Brakes', f"{val:.1f}", col))
    
    if metrics:
        cols = st.columns(len(metrics[:4]))
        for i, (name, value, source) in enumerate(metrics[:4]):
            with cols[i]:
                st.metric(name, value)
                st.caption(f"From: {source}")
    
    # Distribution charts
    st.markdown("### Feature Distributions")
    chart_cols = st.columns(2)
    
    for i, col in enumerate(numeric_cols[:6]):
        with chart_cols[i % 2]:
            fig = px.histogram(df, x=col, nbins=20, title=col)
            fig.update_layout(height=250, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key=f"analytics_{col}")


# ============================================================
# STAGE 6: EXPORT
# ============================================================

def render_stage6():
    """Render Stage 6: Export."""
    st.markdown("# Stage 6: Export")
    st.markdown("Download your cleaned dataset and processing documentation.")
    
    df = st.session_state.cleaned_data
    
    if df is None or df.empty:
        st.error("No cleaned data available.")
        return
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Original Rows", len(st.session_state.raw_data) if st.session_state.raw_data is not None else 0)
    with col2:
        st.metric("Final Rows", len(df))
    with col3:
        st.metric("Final Columns", len(df.columns))
    with col4:
        st.metric("Features Extracted", len(st.session_state.selected_features))
    
    # Download buttons
    st.markdown("### Downloads")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Cleaned Dataset (CSV)")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"telematics_cleaned_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption(f"{len(df)} rows x {len(df.columns)} columns")
    
    with col2:
        st.markdown("#### Processing Report (JSON)")
        report = generate_processing_report(
            original_file=st.session_state.file_name,
            original_shape=(len(st.session_state.raw_data), len(st.session_state.raw_data.columns)) if st.session_state.raw_data is not None else (0, 0),
            kept_columns=st.session_state.kept_columns,
            dropped_columns=st.session_state.dropped_columns,
            column_mappings=st.session_state.column_mappings,
            complex_configs=st.session_state.complex_configs,
            selected_features=st.session_state.selected_features,
            cleaning_configs=st.session_state.cleaning_configs,
            final_shape=(len(df), len(df.columns))
        )
        
        report_json = json.dumps(report, indent=2, default=str).encode('utf-8')
        st.download_button(
            label="Download Report",
            data=report_json,
            file_name=f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        st.caption("Complete audit trail of all processing steps")
    
    # Processing summary
    st.markdown("### Processing Summary")
    
    with st.expander("Column Mappings"):
        mapped = {k: v for k, v in st.session_state.column_mappings.items() if v != 'do_not_map'}
        st.json(mapped)
    
    with st.expander("Complex Field Parsing"):
        active = [c for c in st.session_state.complex_configs if c['method'] != 'none']
        if active:
            st.json(active)
        else:
            st.info("No complex fields were parsed.")
    
    with st.expander("Selected Features"):
        st.write(st.session_state.selected_features)
    
    with st.expander("Cleaning Rules"):
        st.json(st.session_state.cleaning_configs)
    
    # Final data preview
    st.markdown("### Final Dataset Preview")
    st.dataframe(df.head(15), use_container_width=True)
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Back to Analysis"):
            st.session_state.stage = 5
            st.rerun()
    with col3:
        st.success("Pipeline complete.")


# ============================================================
# MAIN APP
# ============================================================

def main():
    """Main application entry point."""
    render_sidebar()
    
    # Render current stage
    stage = st.session_state.stage
    
    if stage == 1:
        render_stage1()
    elif stage == 2:
        render_stage2()
    elif stage == 3:
        render_stage3()
    elif stage == 4:
        render_stage4()
    elif stage == 5:
        render_stage5()
    elif stage == 6:
        render_stage6()


if __name__ == "__main__":
    main()
