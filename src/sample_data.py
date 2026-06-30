"""
TelematicsPro - Sample Data Generator
=====================================
Generates realistic telematics data for testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io


def generate_sample_data() -> pd.DataFrame:
    """
    Generate a realistic telematics CSV dataset for demo/testing.
    Creates 3 vehicles with 3-5 trips each.
    """
    np.random.seed(42)
    
    vehicles = ['VH-001', 'VH-002', 'VH-003']
    rows = []
    
    odo = 45000
    trip_counter = 0
    
    for vehicle_id in vehicles:
        # 3-5 trips per vehicle
        num_trips = np.random.randint(3, 6)
        base_date = datetime(2024, 3, 15, 6, 0, 0)
        
        for t in range(num_trips):
            trip_counter += 1
            trip_id = f'T{trip_counter:03d}'
            trip_duration = np.random.randint(300, 1800)  # 5-30 min
            num_points = trip_duration // 2  # ~1 point per 2 seconds
            
            lat = 40.7128 + (np.random.random() - 0.5) * 0.1
            lon = -74.006 + (np.random.random() - 0.5) * 0.1
            speed = 0
            rpm = 800
            fuel = 50 + np.random.random() * 40
            heading = np.random.randint(0, 360)
            coolant_base = 85 + np.random.random() * 10
            
            for i in range(num_points):
                time = base_date + timedelta(seconds=i * 2)
                
                # Simulate realistic speed profile
                phase = i / num_points
                if phase < 0.1:
                    speed = min(speed + np.random.random() * 5, 30)  # accelerating
                elif phase < 0.8:
                    target_speed = 40 + np.random.random() * 50  # cruising
                    speed = speed + (target_speed - speed) * 0.05 + (np.random.random() - 0.5) * 3
                    speed = max(0, min(speed, 120))
                else:
                    speed = max(0, speed - np.random.random() * 5)  # decelerating
                
                rpm = 800 + speed * 30 + (np.random.random() - 0.5) * 200
                throttle = min(100, speed * 0.8 + np.random.random() * 10)
                load = min(100, speed * 0.5 + np.random.random() * 15)
                coolant = coolant_base + np.random.random() * 5
                fuel -= 0.001 * speed * 0.01
                voltage = 13.5 + (np.random.random() - 0.5) * 0.8
                odo += speed / 3600 * 2
                heading = (heading + (np.random.random() - 0.5) * 10 + 360) % 360
                
                # Move GPS position
                lat += (np.random.random() - 0.5) * 0.0002
                lon += (np.random.random() - 0.5) * 0.0002
                
                # Generate accelerometer data (complex encoded field)
                ax = (np.random.random() - 0.5) * 0.4
                ay = (np.random.random() - 0.5) * 0.6
                az = 0.98 + (np.random.random() - 0.5) * 0.1
                acc_data = f'{ax:.4f};{ay:.4f};{az:.4f}'
                
                # Harsh brake flag (occasional)
                harsh_brake = '1' if np.random.random() < 0.02 else '0'
                
                # Some rows with missing values
                has_missing = np.random.random() < 0.03
                
                rows.append({
                    'vehicleId': vehicle_id,
                    'tripId': trip_id,
                    'timestamp': time.isoformat(),
                    'latitude': round(lat, 6),
                    'longitude': round(lon, 6),
                    'speed': '' if has_missing else round(speed, 1),
                    'engineRPM': round(rpm, 0),
                    'throttlePos': round(throttle, 1),
                    'engineLoad': round(load, 1),
                    'coolantTemp': round(coolant, 1),
                    'fuelLevel': round(fuel, 2),
                    'batteryVoltage': round(voltage, 2),
                    'odometer': round(odo, 1),
                    'heading': round(heading, 0),
                    'accData': acc_data,
                    'harshBrake': harsh_brake,
                    'ignitionStatus': '1',
                })
            
            # Gap between trips
            base_date = base_date + timedelta(seconds=trip_duration) + timedelta(seconds=np.random.randint(600, 3600))
    
    return pd.DataFrame(rows)


def get_sample_csv_string() -> str:
    """Get sample data as a CSV string."""
    df = generate_sample_data()
    return df.to_csv(index=False)


def get_sample_bytes() -> bytes:
    """Get sample data as bytes for file-like operations."""
    return get_sample_csv_string().encode('utf-8')
