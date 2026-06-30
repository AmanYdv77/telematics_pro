"""
TelematicsPro - Utility Functions
=================================
Helper functions for the application.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any


def get_file_size_mb(file) -> float:
    """Get file size in megabytes."""
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    return size / (1024 * 1024)


def format_number(num: float) -> str:
    """Format number with appropriate precision."""
    if num is None:
        return '—'
    if abs(num) >= 1000000:
        return f'{num/1000000:.2f}M'
    if abs(num) >= 1000:
        return f'{num/1000:.2f}K'
    if isinstance(num, float):
        return f'{num:.2f}'
    return str(num)


def create_download_link(data: Any, filename: str, file_type: str = 'csv') -> bytes:
    """Create downloadable file content."""
    if file_type == 'csv' and isinstance(data, pd.DataFrame):
        return data.to_csv(index=False).encode('utf-8')
    elif file_type == 'json':
        return json.dumps(data, indent=2, default=str).encode('utf-8')
    return str(data).encode('utf-8')


def generate_processing_report(
    original_file: str,
    original_shape: tuple,
    kept_columns: list,
    dropped_columns: list,
    column_mappings: dict,
    complex_configs: list,
    selected_features: list,
    cleaning_configs: list,
    final_shape: tuple
) -> Dict[str, Any]:
    """Generate a complete processing report."""
    return {
        'original_file': original_file,
        'original_shape': {'rows': original_shape[0], 'cols': original_shape[1]},
        'kept_columns': kept_columns,
        'dropped_columns': dropped_columns,
        'column_mappings': column_mappings,
        'complex_field_configs': complex_configs,
        'selected_features': selected_features,
        'cleaning_configs': cleaning_configs,
        'final_shape': {'rows': final_shape[0], 'cols': final_shape[1]},
        'timestamp': datetime.now().isoformat(),
    }


def style_metric_card(label: str, value: Any, delta: str = None, color: str = 'blue'):
    """Create a styled metric card using HTML."""
    colors = {
        'blue': '#3B82F6',
        'green': '#10B981',
        'purple': '#8B5CF6',
        'amber': '#F59E0B',
        'red': '#EF4444',
        'cyan': '#06B6D4',
    }
    bg_color = colors.get(color, colors['blue'])
    
    html = f'''
    <div style="
        background: linear-gradient(135deg, {bg_color}22, {bg_color}11);
        border: 1px solid {bg_color}44;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
    ">
        <div style="font-size: 12px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em;">
            {label}
        </div>
        <div style="font-size: 24px; font-weight: bold; color: {bg_color}; margin-top: 4px;">
            {value}
        </div>
        {f'<div style="font-size: 12px; color: #6B7280; margin-top: 4px;">{delta}</div>' if delta else ''}
    </div>
    '''
    return html


def render_quality_badge(quality: str) -> str:
    """Render a quality badge HTML."""
    colors = {
        'good': ('bg-emerald-100', 'text-emerald-700', '✓'),
        'warning': ('bg-amber-100', 'text-amber-700', '⚠'),
        'bad': ('bg-red-100', 'text-red-700', '✗'),
    }
    bg, text, icon = colors.get(quality, colors['warning'])
    return f'<span class="{bg} {text} px-2 py-1 rounded-full text-xs font-medium">{icon}</span>'
