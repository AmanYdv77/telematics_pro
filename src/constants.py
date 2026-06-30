"""
TelematicsPro - Constants and Configuration
============================================
Contains all standard features, thresholds, and configuration values.
"""

# ============================================================
# FILE SIZE LIMITS
# ============================================================

MAX_FILE_SIZE_MB = 200  # Maximum recommended file size
WARNING_FILE_SIZE_MB = 100  # Show warning above this size
MAX_ROWS_FOR_FULL_ANALYSIS = 500000  # Sample above this

# ============================================================
# THE 40 STANDARD TELEMATICS FEATURES
# ============================================================

STANDARD_FEATURES = [
    'vehicle_id',
    'trip_id',
    'timestamp',
    'latitude',
    'longitude',
    'altitude',
    'heading',
    'gps_speed',
    'satellites',
    'hdop',
    'vehicle_speed',
    'engine_rpm',
    'throttle_position',
    'engine_load',
    'manifold_pressure',
    'mass_air_flow',
    'coolant_temp',
    'intake_air_temp',
    'transmission_temp',
    'ambient_temp',
    'fuel_level',
    'instant_fuel_rate',
    'cumulative_fuel_used',
    'battery_voltage',
    'odometer',
    'dtc_code',
    'mil_status',
    'accel_x',
    'accel_y',
    'accel_z',
    'harsh_brake_flag',
    'harsh_accel_flag',
    'ignition_status',
    'engine_running',
    'gear_position',
    'seatbelt_status',
    'driver_id',
    'steering_angle',
    'fuel_rail_pressure',
    'wheel_speed_fl',
]

# Critical features that are most important
CRITICAL_FEATURES = [
    'vehicle_id',
    'trip_id',
    'timestamp',
    'vehicle_speed',
    'latitude',
    'longitude',
]

# ============================================================
# NAME HINTS FOR AUTO-MAPPING
# ============================================================

NAME_HINTS = {
    'vehicle_id': ['vehicleid', 'vehicle', 'vid', 'car_id', 'carid', 'veh_id', 'device_id', 'deviceid'],
    'trip_id': ['tripid', 'trip', 'journey_id', 'journeyid', 'route_id', 'routeid', 'trip_no'],
    'timestamp': ['time', 'datetime', 'date_time', 'ts', 'recorded_at', 'created_at', 'gpstime', 'utc'],
    'latitude': ['lat', 'y', 'gps_lat', 'gpslat', 'pos_lat'],
    'longitude': ['lon', 'lng', 'long', 'x', 'gps_lon', 'gpslon', 'gps_lng', 'pos_lon'],
    'altitude': ['alt', 'elev', 'elevation', 'height', 'gps_alt'],
    'heading': ['bearing', 'direction', 'course', 'azimuth', 'head'],
    'gps_speed': ['gpsspeed', 'gps_spd', 'speed_gps'],
    'satellites': ['sats', 'sat_count', 'numsat', 'sat_num', 'gps_sat'],
    'hdop': ['dop', 'gps_hdop', 'precision'],
    'vehicle_speed': ['speed', 'spd', 'vspeed', 'veh_speed', 'obd_speed', 'obdspeed', 'kph', 'mph'],
    'engine_rpm': ['rpm', 'engine_speed', 'enginespeed', 'enginerpm', 'rev'],
    'throttle_position': ['throttle', 'tps', 'throttle_pos', 'pedal_pos', 'accel_pedal'],
    'engine_load': ['load', 'eng_load', 'engineload', 'calculated_load'],
    'manifold_pressure': ['map', 'intake_pressure', 'manifold', 'boost'],
    'mass_air_flow': ['maf', 'airflow', 'air_flow'],
    'coolant_temp': ['ect', 'engine_temp', 'water_temp', 'coolant', 'enginetemp'],
    'intake_air_temp': ['iat', 'intake_temp', 'air_temp'],
    'transmission_temp': ['trans_temp', 'gearbox_temp'],
    'ambient_temp': ['outside_temp', 'ext_temp', 'exterior_temp', 'air_temperature'],
    'fuel_level': ['fuel', 'fuel_pct', 'fuel_remaining', 'fuellevel'],
    'instant_fuel_rate': ['fuel_rate', 'fuelrate', 'fuel_consumption', 'fuel_flow'],
    'cumulative_fuel_used': ['total_fuel', 'fuel_used', 'fuel_total'],
    'battery_voltage': ['voltage', 'batt', 'battery', 'batt_volt', 'vbatt'],
    'odometer': ['odo', 'mileage', 'total_distance', 'distance', 'km_total'],
    'dtc_code': ['dtc', 'fault_code', 'error_code', 'obd_code', 'trouble_code'],
    'mil_status': ['mil', 'check_engine', 'cel', 'malfunction'],
    'accel_x': ['ax', 'acc_x', 'acceleration_x', 'lateral_accel', 'accx'],
    'accel_y': ['ay', 'acc_y', 'acceleration_y', 'longitudinal_accel', 'accy'],
    'accel_z': ['az', 'acc_z', 'acceleration_z', 'vertical_accel', 'accz'],
    'harsh_brake_flag': ['harsh_brake', 'hard_brake', 'sudden_brake', 'emergency_brake'],
    'harsh_accel_flag': ['harsh_accel', 'hard_accel', 'rapid_accel', 'sudden_accel'],
    'ignition_status': ['ignition', 'ign', 'key_on', 'engine_on'],
    'engine_running': ['eng_running', 'running', 'engine_status'],
    'gear_position': ['gear', 'transmission_gear', 'gear_num'],
    'seatbelt_status': ['seatbelt', 'belt', 'driver_belt'],
    'driver_id': ['driverid', 'driver', 'operator_id', 'operatorid'],
    'steering_angle': ['steer', 'steering', 'wheel_angle', 'steer_angle'],
    'fuel_rail_pressure': ['frp', 'rail_pressure', 'fuel_pressure'],
    'wheel_speed_fl': ['wheel_speed', 'ws_fl', 'front_left_speed'],
}

# ============================================================
# AVAILABLE DERIVED FEATURES
# ============================================================

AVAILABLE_FEATURES = [
    # Time & Duration
    {'name': 'duration_seconds', 'description': 'Total trip duration in seconds', 'category': 'Time & Duration', 'requires': ['timestamp']},
    {'name': 'start_time', 'description': 'Trip start timestamp', 'category': 'Time & Duration', 'requires': ['timestamp']},
    {'name': 'end_time', 'description': 'Trip end timestamp', 'category': 'Time & Duration', 'requires': ['timestamp']},
    {'name': 'hour_of_day', 'description': 'Hour when the trip started (0-23)', 'category': 'Time & Duration', 'requires': ['timestamp']},
    {'name': 'day_of_week', 'description': 'Day of week when trip started (0=Mon)', 'category': 'Time & Duration', 'requires': ['timestamp']},

    # Speed Statistics
    {'name': 'avg_speed', 'description': 'Average vehicle speed during trip', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},
    {'name': 'max_speed', 'description': 'Maximum vehicle speed during trip', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},
    {'name': 'min_speed', 'description': 'Minimum non-zero vehicle speed', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},
    {'name': 'speed_std', 'description': 'Standard deviation of speed', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},
    {'name': 'speed_variability', 'description': 'Coefficient of variation of speed (std/mean)', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},
    {'name': 'pct_time_over_80kph', 'description': 'Percentage of time above 80 km/h', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},
    {'name': 'pct_time_stationary', 'description': 'Percentage of time speed is zero', 'category': 'Speed Statistics', 'requires': ['vehicle_speed']},

    # Acceleration / Driving Behavior
    {'name': 'harsh_braking_count', 'description': 'Count of harsh braking events (accel < -0.3g)', 'category': 'Acceleration / Driving Behavior', 'requires': ['accel_y']},
    {'name': 'harsh_accel_count', 'description': 'Count of harsh acceleration events (accel > 0.3g)', 'category': 'Acceleration / Driving Behavior', 'requires': ['accel_y']},
    {'name': 'harsh_cornering_count', 'description': 'Count of harsh cornering events (lateral > 0.3g)', 'category': 'Acceleration / Driving Behavior', 'requires': ['accel_x']},
    {'name': 'max_abs_accel', 'description': 'Maximum absolute acceleration magnitude', 'category': 'Acceleration / Driving Behavior', 'requires': ['accel_x', 'accel_y', 'accel_z']},
    {'name': 'avg_abs_accel', 'description': 'Average absolute acceleration magnitude', 'category': 'Acceleration / Driving Behavior', 'requires': ['accel_x', 'accel_y', 'accel_z']},

    # Engine & RPM
    {'name': 'avg_rpm', 'description': 'Average engine RPM during trip', 'category': 'Engine & RPM', 'requires': ['engine_rpm']},
    {'name': 'max_rpm', 'description': 'Maximum engine RPM during trip', 'category': 'Engine & RPM', 'requires': ['engine_rpm']},
    {'name': 'rpm_std', 'description': 'Standard deviation of engine RPM', 'category': 'Engine & RPM', 'requires': ['engine_rpm']},
    {'name': 'avg_throttle', 'description': 'Average throttle position', 'category': 'Engine & RPM', 'requires': ['throttle_position']},
    {'name': 'avg_engine_load', 'description': 'Average engine load percentage', 'category': 'Engine & RPM', 'requires': ['engine_load']},

    # Fuel & Efficiency
    {'name': 'start_fuel_level', 'description': 'Fuel level at trip start', 'category': 'Fuel & Efficiency', 'requires': ['fuel_level']},
    {'name': 'end_fuel_level', 'description': 'Fuel level at trip end', 'category': 'Fuel & Efficiency', 'requires': ['fuel_level']},
    {'name': 'fuel_consumed', 'description': 'Estimated fuel consumed during trip', 'category': 'Fuel & Efficiency', 'requires': ['fuel_level']},
    {'name': 'avg_fuel_rate', 'description': 'Average instant fuel rate', 'category': 'Fuel & Efficiency', 'requires': ['instant_fuel_rate']},

    # Location & Distance
    {'name': 'trip_distance_km', 'description': 'Trip distance from odometer readings', 'category': 'Location & Distance', 'requires': ['odometer']},
    {'name': 'trip_distance_gps', 'description': 'Trip distance from GPS coordinates (Haversine)', 'category': 'Location & Distance', 'requires': ['latitude', 'longitude']},
    {'name': 'start_lat', 'description': 'Latitude at trip start', 'category': 'Location & Distance', 'requires': ['latitude']},
    {'name': 'start_lon', 'description': 'Longitude at trip start', 'category': 'Location & Distance', 'requires': ['longitude']},
    {'name': 'end_lat', 'description': 'Latitude at trip end', 'category': 'Location & Distance', 'requires': ['latitude']},
    {'name': 'end_lon', 'description': 'Longitude at trip end', 'category': 'Location & Distance', 'requires': ['longitude']},

    # Event Counts & Status
    {'name': 'idle_time_seconds', 'description': 'Time spent idling (engine on, speed=0)', 'category': 'Event Counts & Status', 'requires': ['vehicle_speed', 'timestamp']},
    {'name': 'idle_pct', 'description': 'Percentage of trip spent idling', 'category': 'Event Counts & Status', 'requires': ['vehicle_speed', 'timestamp']},
    {'name': 'data_point_count', 'description': 'Number of raw data points in trip', 'category': 'Event Counts & Status', 'requires': []},
    {'name': 'avg_battery_voltage', 'description': 'Average battery voltage during trip', 'category': 'Event Counts & Status', 'requires': ['battery_voltage']},
    {'name': 'avg_coolant_temp', 'description': 'Average coolant temperature', 'category': 'Event Counts & Status', 'requires': ['coolant_temp']},
    {'name': 'max_coolant_temp', 'description': 'Maximum coolant temperature', 'category': 'Event Counts & Status', 'requires': ['coolant_temp']},
]

FEATURE_CATEGORIES = [
    'Time & Duration',
    'Speed Statistics',
    'Acceleration / Driving Behavior',
    'Engine & RPM',
    'Fuel & Efficiency',
    'Location & Distance',
    'Event Counts & Status',
]

# ============================================================
# THRESHOLDS FOR CALCULATIONS
# ============================================================

THRESHOLDS = {
    'HARSH_BRAKING_G': -0.3,
    'HARSH_ACCEL_G': 0.3,
    'HARSH_CORNERING_G': 0.3,
    'HIGH_SPEED_KPH': 80,
    'TRIP_GAP_SECONDS': 300,  # 5 minutes gap = new trip
    'IDLE_SPEED_THRESHOLD': 2,  # km/h
}

# ============================================================
# CLEANING STRATEGIES
# ============================================================

MISSING_STRATEGIES = [
    ('leave', 'Leave as-is'),
    ('drop_rows', 'Drop rows with missing'),
    ('mean', 'Fill with mean'),
    ('median', 'Fill with median'),
    ('mode', 'Fill with mode'),
    ('zero', 'Fill with 0'),
    ('ffill', 'Forward fill'),
    ('bfill', 'Backward fill'),
    ('custom', 'Custom value'),
]

OUTLIER_STRATEGIES = [
    ('none', 'None'),
    ('iqr', 'IQR clipping (1.5×IQR)'),
    ('zscore', 'Z-score clipping (3σ)'),
]
