"""
TelematicsPro - Data Processing Engine
=======================================
All data transformation functions - analysis, mapping, segmentation,
feature extraction, and cleaning.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

from .constants import (
    NAME_HINTS, THRESHOLDS, STANDARD_FEATURES,
    MAX_ROWS_FOR_FULL_ANALYSIS
)


# ============================================================
# 1. COLUMN ANALYSIS
# ============================================================

def analyze_column(name: str, series: pd.Series) -> Dict[str, Any]:
    """
    Perform rich analysis on a single column.
    Returns statistics, quality flags, and suggestions.
    """
    total = len(series)
    non_null = series.dropna()
    non_null_count = len(non_null)
    missing_count = total - non_null_count
    missing_pct = (missing_count / total * 100) if total > 0 else 0
    
    # Unique values
    unique_count = non_null.nunique()
    cardinality = unique_count / total if total > 0 else 0
    
    # Infer data type
    inferred_type = 'unknown'
    
    # Check numeric
    numeric_series = pd.to_numeric(non_null, errors='coerce')
    numeric_count = numeric_series.notna().sum()
    numeric_ratio = numeric_count / len(non_null) if len(non_null) > 0 else 0
    
    if numeric_ratio > 0.8:
        inferred_type = 'numeric'
    else:
        # Check datetime
        try:
            sample = non_null.head(50).astype(str)
            datetime_count = sum(1 for v in sample if _is_datetime(v))
            if datetime_count / len(sample) > 0.7:
                inferred_type = 'datetime'
            else:
                inferred_type = 'string'
        except Exception:
            inferred_type = 'string'
    
    result = {
        'name': name,
        'inferred_type': inferred_type,
        'missing_count': missing_count,
        'missing_pct': round(missing_pct, 2),
        'unique_count': unique_count,
        'cardinality': round(cardinality, 4),
        'sample_values': non_null.head(8).tolist(),
        'flags': [],
        'suggestion': '',
    }
    
    # Numeric statistics
    if inferred_type == 'numeric':
        nums = numeric_series.dropna()
        if len(nums) > 0:
            result['min'] = float(nums.min())
            result['max'] = float(nums.max())
            result['mean'] = float(nums.mean())
            result['median'] = float(nums.median())
            result['std'] = float(nums.std())
            
            # Histogram data
            try:
                hist, bin_edges = np.histogram(nums, bins=10)
                result['histogram'] = [
                    {'bin': f"{bin_edges[i]:.1f}", 'count': int(hist[i])}
                    for i in range(len(hist))
                ]
            except Exception:
                result['histogram'] = []
    
    # Top values for low cardinality
    if inferred_type in ['string', 'boolean'] and unique_count <= 50:
        value_counts = non_null.value_counts().head(10)
        result['top_values'] = [
            {'value': str(v), 'count': int(c)}
            for v, c in value_counts.items()
        ]
    
    # String length stats
    if inferred_type == 'string':
        lengths = non_null.astype(str).str.len()
        result['avg_length'] = float(lengths.mean())
        result['max_length'] = int(lengths.max())
    
    # Quality flags
    if missing_pct > 70:
        result['flags'].append('High missingness (>70%)')
    elif missing_pct > 30:
        result['flags'].append('Moderate missingness (>30%)')
    
    if unique_count == 1 and non_null_count > 0:
        result['flags'].append('Possible constant column')
    
    if cardinality > 0.95 and unique_count > 100:
        result['flags'].append('High cardinality')
    
    if inferred_type == 'string':
        if result.get('avg_length', 0) > 50:
            result['flags'].append('Likely encoded string (long values)')
        if result.get('max_length', 0) > 100:
            result['flags'].append('Complex / encoded field detected')
    
    # Suggestion
    lc_name = name.lower()
    useful_keywords = [
        'speed', 'lat', 'lon', 'time', 'fuel', 'rpm', 'accel', 'brake',
        'trip', 'vehicle', 'distance', 'odo', 'temp', 'volt', 'throttle',
        'load', 'heading', 'gear', 'engine'
    ]
    if any(k in lc_name for k in useful_keywords):
        result['suggestion'] = 'Likely useful for trip analysis'
    elif missing_pct > 80 or (unique_count == 1 and non_null_count > 0):
        result['suggestion'] = 'Possibly redundant / technical'
    else:
        result['suggestion'] = 'Review manually'
    
    return result


def _is_datetime(value: str) -> bool:
    """Check if a string value looks like a datetime."""
    if len(value) < 6:
        return False
    try:
        pd.to_datetime(value)
        return True
    except Exception:
        return False


# ============================================================
# 2. COLUMN MAPPING
# ============================================================

def suggest_mapping(column_name: str) -> str:
    """
    Suggest a standard feature name for a given column name
    based on name similarity.
    """
    clean = re.sub(r'[^a-z0-9]', '', column_name.lower())
    
    for feature, hints in NAME_HINTS.items():
        # Exact match
        if clean == feature.replace('_', ''):
            return feature
        # Hint match
        for hint in hints:
            hint_clean = re.sub(r'[^a-z0-9]', '', hint)
            if clean == hint_clean or clean in hint_clean or hint_clean in clean:
                return feature
    
    return 'do_not_map'


# ============================================================
# 3. COMPLEX FIELD PARSING
# ============================================================

def is_complex_field(analysis: Dict[str, Any]) -> bool:
    """Check if a column appears to contain complex/encoded data."""
    if analysis['inferred_type'] != 'string':
        return False
    return (
        analysis.get('avg_length', 0) > 40 or
        analysis.get('max_length', 0) > 80 or
        any('encoded' in f.lower() or 'complex' in f.lower() for f in analysis.get('flags', []))
    )


def parse_complex_value(value: str, method: str, delimiter: str = None) -> Dict[str, Any]:
    """
    Parse a complex field value based on the chosen method.
    Returns a dictionary with extracted key-value pairs.
    """
    if pd.isna(value) or method == 'none':
        return {}
    
    value = str(value)
    
    if method == 'accelerometer':
        # Parse "x;y;z" or "x,y,z" format
        delimiters = [';', ',', '|', ' ', '\t']
        parts = [value]
        for d in delimiters:
            if d in value:
                parts = [p.strip() for p in value.split(d) if p.strip()]
                break
        
        nums = []
        for p in parts:
            try:
                nums.append(float(p))
            except (ValueError, TypeError):
                pass
        
        result = {}
        if len(nums) >= 3:
            result = {'accel_x': nums[0], 'accel_y': nums[1], 'accel_z': nums[2]}
        elif len(nums) == 2:
            result = {'accel_x': nums[0], 'accel_y': nums[1]}
        elif len(nums) == 1:
            result = {'accel_x': nums[0]}
        return result
    
    elif method == 'json':
        try:
            import json
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return {k: v for k, v in parsed.items() if isinstance(v, (int, float, str))}
            elif isinstance(parsed, list):
                return {f'field_{i}': v for i, v in enumerate(parsed)}
        except Exception:
            return {}
    
    elif method == 'delimiter':
        d = delimiter or ','
        parts = [p.strip() for p in value.split(d)]
        result = {}
        for i, p in enumerate(parts):
            try:
                result[f'field_{i}'] = float(p)
            except (ValueError, TypeError):
                result[f'field_{i}'] = p
        return result
    
    return {}


def apply_complex_parsing(df: pd.DataFrame, configs: List[Dict]) -> pd.DataFrame:
    """Apply complex field parsing to dataframe based on configs."""
    df = df.copy()
    
    for config in configs:
        if config['method'] == 'none':
            continue
        
        col = config['column']
        if col not in df.columns:
            continue
        
        # Parse each row
        parsed_data = df[col].apply(
            lambda x: parse_complex_value(x, config['method'], config.get('delimiter'))
        )
        
        # Extract unique keys from parsed data
        all_keys = set()
        for d in parsed_data:
            if isinstance(d, dict):
                all_keys.update(d.keys())
        
        # Add new columns
        for key in all_keys:
            df[key] = parsed_data.apply(lambda x: x.get(key) if isinstance(x, dict) else None)
    
    return df


# ============================================================
# 4. STANDARDIZE COLUMNS
# ============================================================

def standardize_columns(
    df: pd.DataFrame,
    mappings: Dict[str, str],
    complex_configs: List[Dict]
) -> pd.DataFrame:
    """
    Apply column mappings and complex field parsing to create
    a standardized dataset.
    """
    result = df.copy()
    
    # Apply complex field parsing first
    result = apply_complex_parsing(result, complex_configs)
    
    # Apply mappings (rename columns)
    rename_map = {}
    for source, target in mappings.items():
        if target != 'do_not_map' and source in result.columns:
            rename_map[source] = target
    
    result = result.rename(columns=rename_map)
    
    # Keep only mapped columns + parsed columns
    keep_cols = set(mappings.values()) - {'do_not_map'}
    # Add any columns created by complex parsing
    for config in complex_configs:
        if config['method'] == 'accelerometer':
            keep_cols.update(['accel_x', 'accel_y', 'accel_z'])
    
    # Filter to only keep relevant columns
    final_cols = [c for c in result.columns if c in keep_cols or c not in df.columns]
    
    return result[final_cols] if final_cols else result


# ============================================================
# 5. TRIP SEGMENTATION
# ============================================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance in km between two lat/lon points."""
    R = 6371  # Earth's radius in km
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def _has_col(trip_df: pd.DataFrame, mapped_features: set, *col_names: str) -> bool:
    """
    Check if ALL required columns are both mapped AND actually exist
    in the trip dataframe. This prevents KeyError and TypeError.
    """
    for col in col_names:
        if col not in mapped_features:
            return False
        if col not in trip_df.columns:
            return False
    return True

def segment_into_trips(df: pd.DataFrame) -> Tuple[List[pd.DataFrame], List[Dict]]:
    """
    Segment data into trips using trip_id field, or fallback
    to time-gap based segmentation.
    """
    if df.empty:
        return [], []
    
    # Check if trip_id is available
    has_trip_id = 'trip_id' in df.columns and df['trip_id'].notna().any()
    
    if has_trip_id:
        # Group by trip_id
        trips = []
        summaries = []
        
        for tid, group in df.groupby('trip_id'):
            trips.append(group.reset_index(drop=True))
            summaries.append(_create_trip_summary(str(tid), group))
        
        return trips, summaries
    
    # Fallback: time-gap based segmentation
    if 'timestamp' not in df.columns:
        # No way to segment, treat as one trip
        return [df], [_create_trip_summary('trip_1', df)]
    
    # Sort by timestamp
    df = df.copy()
    df['_ts'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.sort_values('_ts').reset_index(drop=True)
    
    # Find gaps
    df['_gap'] = df['_ts'].diff().dt.total_seconds()
    df['_new_trip'] = df['_gap'] > THRESHOLDS['TRIP_GAP_SECONDS']
    df['_trip_num'] = df['_new_trip'].cumsum() + 1
    
    trips = []
    summaries = []
    
    for trip_num, group in df.groupby('_trip_num'):
        clean_group = group.drop(columns=['_ts', '_gap', '_new_trip', '_trip_num'])
        clean_group['trip_id'] = f'trip_{trip_num}'
        trips.append(clean_group.reset_index(drop=True))
        summaries.append(_create_trip_summary(f'trip_{trip_num}', clean_group))
    
    return trips, summaries


def _create_trip_summary(trip_id: str, df: pd.DataFrame) -> Dict:
    """Create a summary for a single trip."""
    summary = {
        'trip_id': trip_id,
        'row_count': len(df),
        'vehicle_id': None,
        'start_time': None,
        'end_time': None,
        'duration': None,
    }
    
    if 'vehicle_id' in df.columns:
        summary['vehicle_id'] = str(df['vehicle_id'].iloc[0]) if df['vehicle_id'].notna().any() else None
    
    if 'timestamp' in df.columns:
        try:
            times = pd.to_datetime(df['timestamp'], errors='coerce').dropna().sort_values()
            if len(times) > 0:
                summary['start_time'] = times.iloc[0].isoformat()
                summary['end_time'] = times.iloc[-1].isoformat()
                summary['duration'] = (times.iloc[-1] - times.iloc[0]).total_seconds()
        except Exception:
            pass
    
    return summary


# ============================================================
# 6. FEATURE EXTRACTION
# ============================================================
def _safe_numeric(trip_df: pd.DataFrame, col: str) -> pd.Series:
    """
    Safely get a numeric series from a dataframe column.
    Returns an empty Series if the column doesn't exist.
    """
    if col not in trip_df.columns:
        return pd.Series(dtype=float)
    try:
        return pd.to_numeric(trip_df[col], errors='coerce').dropna()
    except Exception:
        return pd.Series(dtype=float)


def extract_feature(feature_name: str, trip_df: pd.DataFrame, mapped_features: set) -> Any:
    """
    Extract a single feature value from a trip's raw rows.
    Each feature has explicit, documented logic.
    Safely handles missing columns and bad data.
    """
    try:
        return _extract_feature_inner(feature_name, trip_df, mapped_features)
    except Exception:
        return None


def _extract_feature_inner(feature_name: str, trip_df: pd.DataFrame, mapped_features: set) -> Any:
    """Inner feature extraction logic, wrapped by extract_feature for safety."""
    
    # ---- Time & Duration ----
    if feature_name == 'duration_seconds':
        if not _has_col(trip_df, mapped_features, 'timestamp'):
            return None
        times = pd.to_datetime(trip_df['timestamp'], errors='coerce').dropna().sort_values()
        if len(times) < 2:
            return None
        return int((times.iloc[-1] - times.iloc[0]).total_seconds())
    
    elif feature_name == 'start_time':
        if not _has_col(trip_df, mapped_features, 'timestamp'):
            return None
        times = pd.to_datetime(trip_df['timestamp'], errors='coerce').dropna().sort_values()
        return times.iloc[0].isoformat() if len(times) > 0 else None
    
    elif feature_name == 'end_time':
        if not _has_col(trip_df, mapped_features, 'timestamp'):
            return None
        times = pd.to_datetime(trip_df['timestamp'], errors='coerce').dropna().sort_values()
        return times.iloc[-1].isoformat() if len(times) > 0 else None
    
    elif feature_name == 'hour_of_day':
        if not _has_col(trip_df, mapped_features, 'timestamp'):
            return None
        t = pd.to_datetime(trip_df['timestamp'].iloc[0], errors='coerce')
        return t.hour if pd.notna(t) else None
    
    elif feature_name == 'day_of_week':
        if not _has_col(trip_df, mapped_features, 'timestamp'):
            return None
        t = pd.to_datetime(trip_df['timestamp'].iloc[0], errors='coerce')
        return t.dayofweek if pd.notna(t) else None
    
    # ---- Speed Statistics ----
    elif feature_name == 'avg_speed':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        return round(float(speeds.mean()), 2) if len(speeds) > 0 else None
    
    elif feature_name == 'max_speed':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        return float(speeds.max()) if len(speeds) > 0 else None
    
    elif feature_name == 'min_speed':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        speeds = speeds[speeds > 0]
        return float(speeds.min()) if len(speeds) > 0 else None
    
    elif feature_name == 'speed_std':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        return round(float(speeds.std()), 2) if len(speeds) > 1 else None
    
    elif feature_name == 'speed_variability':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        mean_val = speeds.mean()
        return round(float(speeds.std() / mean_val), 4) if mean_val > 0 else None
    
    elif feature_name == 'pct_time_over_80kph':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        if len(speeds) == 0:
            return None
        over = int((speeds > THRESHOLDS['HIGH_SPEED_KPH']).sum())
        return round(over / len(speeds) * 100, 2)
    
    elif feature_name == 'pct_time_stationary':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        if len(speeds) == 0:
            return None
        stationary = int((speeds < THRESHOLDS['IDLE_SPEED_THRESHOLD']).sum())
        return round(stationary / len(speeds) * 100, 2)
    
    # ---- Acceleration / Driving Behavior ----
    elif feature_name == 'harsh_braking_count':
        if not _has_col(trip_df, mapped_features, 'accel_y'):
            return None
        accels = _safe_numeric(trip_df, 'accel_y')
        return int((accels < THRESHOLDS['HARSH_BRAKING_G']).sum()) if len(accels) > 0 else 0
    
    elif feature_name == 'harsh_accel_count':
        if not _has_col(trip_df, mapped_features, 'accel_y'):
            return None
        accels = _safe_numeric(trip_df, 'accel_y')
        return int((accels > THRESHOLDS['HARSH_ACCEL_G']).sum()) if len(accels) > 0 else 0
    
    elif feature_name == 'harsh_cornering_count':
        if not _has_col(trip_df, mapped_features, 'accel_x'):
            return None
        accels = _safe_numeric(trip_df, 'accel_x')
        return int((accels.abs() > THRESHOLDS['HARSH_CORNERING_G']).sum()) if len(accels) > 0 else 0
    
    elif feature_name == 'max_abs_accel':
        has_any = any(_has_col(trip_df, mapped_features, f) for f in ['accel_x', 'accel_y', 'accel_z'])
        if not has_any:
            return None
        ax = _safe_numeric(trip_df, 'accel_x') if 'accel_x' in trip_df.columns else pd.Series([0])
        ay = _safe_numeric(trip_df, 'accel_y') if 'accel_y' in trip_df.columns else pd.Series([0])
        az = _safe_numeric(trip_df, 'accel_z') if 'accel_z' in trip_df.columns else pd.Series([0])
        # Align lengths
        n = min(len(ax), len(ay), len(az))
        if n == 0:
            return None
        magnitude = np.sqrt(ax.iloc[:n].values**2 + ay.iloc[:n].values**2 + az.iloc[:n].values**2)
        return round(float(magnitude.max()), 4)
    
    elif feature_name == 'avg_abs_accel':
        has_any = any(_has_col(trip_df, mapped_features, f) for f in ['accel_x', 'accel_y', 'accel_z'])
        if not has_any:
            return None
        ax = _safe_numeric(trip_df, 'accel_x') if 'accel_x' in trip_df.columns else pd.Series([0])
        ay = _safe_numeric(trip_df, 'accel_y') if 'accel_y' in trip_df.columns else pd.Series([0])
        az = _safe_numeric(trip_df, 'accel_z') if 'accel_z' in trip_df.columns else pd.Series([0])
        n = min(len(ax), len(ay), len(az))
        if n == 0:
            return None
        magnitude = np.sqrt(ax.iloc[:n].values**2 + ay.iloc[:n].values**2 + az.iloc[:n].values**2)
        return round(float(magnitude.mean()), 4)
    
    # ---- Engine & RPM ----
    elif feature_name == 'avg_rpm':
        if not _has_col(trip_df, mapped_features, 'engine_rpm'):
            return None
        rpms = _safe_numeric(trip_df, 'engine_rpm')
        return int(rpms.mean()) if len(rpms) > 0 else None
    
    elif feature_name == 'max_rpm':
        if not _has_col(trip_df, mapped_features, 'engine_rpm'):
            return None
        rpms = _safe_numeric(trip_df, 'engine_rpm')
        return int(rpms.max()) if len(rpms) > 0 else None
    
    elif feature_name == 'rpm_std':
        if not _has_col(trip_df, mapped_features, 'engine_rpm'):
            return None
        rpms = _safe_numeric(trip_df, 'engine_rpm')
        return round(float(rpms.std()), 2) if len(rpms) > 1 else None
    
    elif feature_name == 'avg_throttle':
        if not _has_col(trip_df, mapped_features, 'throttle_position'):
            return None
        vals = _safe_numeric(trip_df, 'throttle_position')
        return round(float(vals.mean()), 2) if len(vals) > 0 else None
    
    elif feature_name == 'avg_engine_load':
        if not _has_col(trip_df, mapped_features, 'engine_load'):
            return None
        vals = _safe_numeric(trip_df, 'engine_load')
        return round(float(vals.mean()), 2) if len(vals) > 0 else None
    
    # ---- Fuel & Efficiency ----
    elif feature_name == 'start_fuel_level':
        if not _has_col(trip_df, mapped_features, 'fuel_level'):
            return None
        vals = _safe_numeric(trip_df, 'fuel_level')
        return float(vals.iloc[0]) if len(vals) > 0 else None
    
    elif feature_name == 'end_fuel_level':
        if not _has_col(trip_df, mapped_features, 'fuel_level'):
            return None
        vals = _safe_numeric(trip_df, 'fuel_level')
        return float(vals.iloc[-1]) if len(vals) > 0 else None
    
    elif feature_name == 'fuel_consumed':
        if not _has_col(trip_df, mapped_features, 'fuel_level'):
            return None
        vals = _safe_numeric(trip_df, 'fuel_level')
        if len(vals) < 2:
            return None
        return round(float(vals.iloc[0] - vals.iloc[-1]), 2)
    
    elif feature_name == 'avg_fuel_rate':
        if not _has_col(trip_df, mapped_features, 'instant_fuel_rate'):
            return None
        vals = _safe_numeric(trip_df, 'instant_fuel_rate')
        return round(float(vals.mean()), 2) if len(vals) > 0 else None
    
    # ---- Location & Distance ----
    elif feature_name == 'trip_distance_km':
        if not _has_col(trip_df, mapped_features, 'odometer'):
            return None
        odos = _safe_numeric(trip_df, 'odometer')
        odos = odos[odos > 0]
        if len(odos) < 2:
            return None
        return round(float(odos.iloc[-1] - odos.iloc[0]), 2)
    
    elif feature_name == 'trip_distance_gps':
        if not _has_col(trip_df, mapped_features, 'latitude') or not _has_col(trip_df, mapped_features, 'longitude'):
            return None
        lats = _safe_numeric(trip_df, 'latitude')
        lons = _safe_numeric(trip_df, 'longitude')
        n = min(len(lats), len(lons))
        if n < 2:
            return None
        lat_vals = lats.iloc[:n].values
        lon_vals = lons.iloc[:n].values
        total_dist = 0.0
        for i in range(1, n):
            total_dist += haversine(lat_vals[i-1], lon_vals[i-1], lat_vals[i], lon_vals[i])
        return round(total_dist, 2)
    
    elif feature_name == 'start_lat':
        if not _has_col(trip_df, mapped_features, 'latitude'):
            return None
        vals = _safe_numeric(trip_df, 'latitude')
        return float(vals.iloc[0]) if len(vals) > 0 else None
    
    elif feature_name == 'start_lon':
        if not _has_col(trip_df, mapped_features, 'longitude'):
            return None
        vals = _safe_numeric(trip_df, 'longitude')
        return float(vals.iloc[0]) if len(vals) > 0 else None
    
    elif feature_name == 'end_lat':
        if not _has_col(trip_df, mapped_features, 'latitude'):
            return None
        vals = _safe_numeric(trip_df, 'latitude')
        return float(vals.iloc[-1]) if len(vals) > 0 else None
    
    elif feature_name == 'end_lon':
        if not _has_col(trip_df, mapped_features, 'longitude'):
            return None
        vals = _safe_numeric(trip_df, 'longitude')
        return float(vals.iloc[-1]) if len(vals) > 0 else None
    
    # ---- Event Counts & Status ----
    elif feature_name == 'idle_time_seconds':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed', 'timestamp'):
            return None
        df_work = trip_df[['vehicle_speed', 'timestamp']].copy()
        df_work['_speed'] = pd.to_numeric(df_work['vehicle_speed'], errors='coerce')
        df_work['_ts'] = pd.to_datetime(df_work['timestamp'], errors='coerce')
        df_work = df_work.dropna(subset=['_speed', '_ts']).sort_values('_ts')
        if len(df_work) < 2:
            return 0
        df_work['_idle'] = df_work['_speed'] < THRESHOLDS['IDLE_SPEED_THRESHOLD']
        df_work['_dt'] = df_work['_ts'].diff().dt.total_seconds()
        idle_time = df_work.loc[df_work['_idle'], '_dt'].sum()
        return int(idle_time) if not pd.isna(idle_time) else 0
    
    elif feature_name == 'idle_pct':
        if not _has_col(trip_df, mapped_features, 'vehicle_speed'):
            return None
        speeds = _safe_numeric(trip_df, 'vehicle_speed')
        if len(speeds) == 0:
            return None
        idle = int((speeds < THRESHOLDS['IDLE_SPEED_THRESHOLD']).sum())
        return round(idle / len(speeds) * 100, 2)
    
    elif feature_name == 'data_point_count':
        return len(trip_df)
    
    elif feature_name == 'avg_battery_voltage':
        if not _has_col(trip_df, mapped_features, 'battery_voltage'):
            return None
        vals = _safe_numeric(trip_df, 'battery_voltage')
        return round(float(vals.mean()), 2) if len(vals) > 0 else None
    
    elif feature_name == 'avg_coolant_temp':
        if not _has_col(trip_df, mapped_features, 'coolant_temp'):
            return None
        vals = _safe_numeric(trip_df, 'coolant_temp')
        return round(float(vals.mean()), 2) if len(vals) > 0 else None
    
    elif feature_name == 'max_coolant_temp':
        if not _has_col(trip_df, mapped_features, 'coolant_temp'):
            return None
        vals = _safe_numeric(trip_df, 'coolant_temp')
        return float(vals.max()) if len(vals) > 0 else None
    
    return None


def extract_selected_features(
    trips: List[pd.DataFrame],
    selected_features: List[str],
    mapped_features: set
) -> pd.DataFrame:
    """Extract selected features for all trips. Returns trip-level dataset."""
    
    rows = []
    
    for idx, trip_df in enumerate(trips):
        row = {'trip_index': idx + 1}
        
        # Add identifiers if available
        if 'trip_id' in trip_df.columns:
            row['trip_id'] = trip_df['trip_id'].iloc[0]
        if 'vehicle_id' in trip_df.columns and trip_df['vehicle_id'].notna().any():
            row['vehicle_id'] = trip_df['vehicle_id'].iloc[0]
        
        # Extract each selected feature
        for feat_name in selected_features:
            row[feat_name] = extract_feature(feat_name, trip_df, mapped_features)
        
        rows.append(row)
    
    return pd.DataFrame(rows)


# ============================================================
# 7. COLUMN CLEANING
# ============================================================

def apply_column_cleaning(df: pd.DataFrame, configs: List[Dict]) -> pd.DataFrame:
    """Apply cleaning configuration to the trip-level dataset."""
    if df.empty:
        return df
    
    result = df.copy()
    
    # Drop columns marked for removal
    drop_cols = [c['column'] for c in configs if not c.get('keep', True)]
    result = result.drop(columns=[c for c in drop_cols if c in result.columns], errors='ignore')
    
    # Apply strategies for kept columns
    for config in configs:
        if not config.get('keep', True):
            continue
        
        col = config['column']
        if col not in result.columns:
            continue
        
        # Missing value strategy
        missing_strategy = config.get('missing_strategy', 'leave')
        if missing_strategy != 'leave':
            result = _apply_missing_strategy(result, col, missing_strategy, config.get('custom_value'))
        
        # Zero value strategy
        zero_strategy = config.get('zero_strategy', 'leave')
        if zero_strategy != 'leave':
            result = _apply_zero_strategy(result, col, zero_strategy)
        
        # Outlier treatment
        outlier_strategy = config.get('outlier_strategy', 'none')
        if outlier_strategy != 'none':
            result = _apply_outlier_treatment(result, col, outlier_strategy)
    
    return result


def _apply_missing_strategy(df: pd.DataFrame, col: str, strategy: str, custom_value=None) -> pd.DataFrame:
    """Apply missing value strategy to a column."""
    df = df.copy()
    
    if strategy == 'drop_rows':
        df = df.dropna(subset=[col])
    
    elif strategy == 'mean':
        mean_val = pd.to_numeric(df[col], errors='coerce').mean()
        df[col] = df[col].fillna(mean_val)
    
    elif strategy == 'median':
        median_val = pd.to_numeric(df[col], errors='coerce').median()
        df[col] = df[col].fillna(median_val)
    
    elif strategy == 'mode':
        mode_val = df[col].mode()
        if len(mode_val) > 0:
            df[col] = df[col].fillna(mode_val.iloc[0])
    
    elif strategy == 'zero':
        df[col] = df[col].fillna(0)
    
    elif strategy == 'ffill':
        df[col] = df[col].ffill()
    
    elif strategy == 'bfill':
        df[col] = df[col].bfill()
    
    elif strategy == 'custom' and custom_value is not None:
        df[col] = df[col].fillna(custom_value)
    
    return df


def _apply_zero_strategy(df: pd.DataFrame, col: str, strategy: str) -> pd.DataFrame:
    """Apply zero value strategy by converting zeros to NaN and applying missing strategy."""
    df = df.copy()
    numeric = pd.to_numeric(df[col], errors='coerce')
    df.loc[numeric == 0, col] = np.nan
    return _apply_missing_strategy(df, col, strategy)


def _apply_outlier_treatment(df: pd.DataFrame, col: str, strategy: str) -> pd.DataFrame:
    """Apply outlier treatment to a column."""
    df = df.copy()
    numeric = pd.to_numeric(df[col], errors='coerce')
    
    if numeric.isna().all() or len(numeric.dropna()) < 4:
        return df
    
    if strategy == 'iqr':
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        df[col] = numeric.clip(lower, upper)
    
    elif strategy == 'zscore':
        mean = numeric.mean()
        std = numeric.std()
        if std > 0:
            z_scores = (numeric - mean) / std
            df.loc[z_scores.abs() > 3, col] = mean + np.sign(z_scores[z_scores.abs() > 3]) * 3 * std
    
    return df
