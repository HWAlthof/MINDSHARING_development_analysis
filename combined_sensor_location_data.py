# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 15:23:22 2024

@author: U013179
"""

# Import necessary libraries
import pandas as pd
import numpy as np
from scipy.signal import butter, lfilter
from datetime import timedelta

# Set path to location and sensor data
location_data_path = "C:\\Users\\u013179\\OneDrive - Radboud Universiteit\\MINDSHARING_development\\Pilots\\sub_01_aligned_location.csv"
sensor_data_path = "C:\\Users\\u013179\\OneDrive - Radboud Universiteit\\MINDSHARING_development\\Pilots\\sub_01_sensor.csv"

# Load the location and sensor data
location_data = pd.read_csv(location_data_path)
sensor_data = pd.read_csv(sensor_data_path, delimiter=';')

## Preprocess accelerometer and gyroscope data
# Convert time column to datetime and calculate delta_t in seconds
sensor_data['time'] = pd.to_datetime(sensor_data['time'])
sensor_data['delta_t'] = (sensor_data['time'] - sensor_data['time'].shift(1)).dt.total_seconds()

# Calculate pitch and roll from accelerometer data
sensor_data['pitch'] = np.arctan2(sensor_data['acc_x'], np.sqrt(sensor_data['acc_y']**2 + sensor_data['acc_z']**2))
sensor_data['roll'] = np.arctan2(sensor_data['acc_y'], np.sqrt(sensor_data['acc_x']**2 + sensor_data['acc_z']**2))

# Convert radians to degrees
sensor_data['pitch_deg'] = np.degrees(sensor_data['pitch'])
sensor_data['roll_deg'] = np.degrees(sensor_data['roll'])

# Initialize the first row of filtered angles based on accelerometer
sensor_data.loc[0, 'filtered_pitch'] = sensor_data.loc[0, 'pitch']
sensor_data.loc[0, 'filtered_roll'] = sensor_data.loc[0, 'roll']

# Complementary filter settings
alpha = 0.98

# Apply the complementary filter
for i in range(1, len(sensor_data)):
    delta_t = sensor_data.loc[i, 'delta_t'] if not pd.isnull(sensor_data.loc[i, 'delta_t']) else 0
    # Gyroscope integration for angle change
    sensor_data.loc[i, 'filtered_pitch'] = alpha * (sensor_data.loc[i-1, 'filtered_pitch'] + sensor_data.loc[i, 'gyro_x'] * delta_t) + (1 - alpha) * sensor_data.loc[i, 'pitch']
    sensor_data.loc[i, 'filtered_roll'] = alpha * (sensor_data.loc[i-1, 'filtered_roll'] + sensor_data.loc[i, 'gyro_y'] * delta_t) + (1 - alpha) * sensor_data.loc[i, 'roll']

# Convert filtered angles from radians to degrees
sensor_data['filtered_pitch_deg'] = np.degrees(sensor_data['filtered_pitch'])
sensor_data['filtered_roll_deg'] = np.degrees(sensor_data['filtered_roll'])

# Display the first few rows of the final dataframe
print(sensor_data[['time', 'pitch_deg', 'roll_deg', 'filtered_pitch_deg', 'filtered_roll_deg']].head())

# Function to resample sensor data to 1-second intervals
def resample_sensor_data(sensor_data):
    """
    Resample data to 1-second intervals using the mean of values within each interval.
    """
    sensor_data.set_index('time', inplace=True)
    resampled_sensor_data = sensor_data.resample('1S').mean().reset_index()
    return resampled_sensor_data

print(resampled_sensor_data)


# Function to align sensor data with location data start and end times
def align_data(sensor_data, location_data):
    """
    Align sensor data with location data by start and end times.
    """
    start_time = location_data['time'].min()
    end_time = location_data['time'].max()
    
    aligned_data = sensor_data[(sensor_data['time'] >= start_time) & (sensor_data['time'] <= end_time)]
    
    return aligned_data

# Function to merge location and sensor data
def merge_data(location_data, sensor_data):
    """
    Merge location data with sensor data based on timestamps.
    """
    merged_data = pd.merge_asof(location_data.sort_values('time'), sensor_data.sort_values('time'), on='time', direction='nearest')
    return merged_data

# Function to apply a low-pass filter to a series
def apply_low_pass_filter(series, order=2, cutoff=0.05, sampling_rate=1):
    """
    Apply a low-pass Butterworth filter to a pandas series.
    """
    nyq = 0.5 * sampling_rate
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_series = lfilter(b, a, series)
    return filtered_series

# Note: This is a skeleton of the Python script. Each function needs to be called
# with the appropriate file paths and data. This script assumes that you have separate
# CSV files for location and sensor data for each participant and that these CSV files
# are structured in a way that can be directly loaded with pd.read_csv().

# Example of how to call these functions will be commented out below:

# location_data_path = "path_to_location_data.csv"
# sensor_data_path = "path_to_sensor_data.csv"

# Load and preprocess the sensor data
# sensor_data = load_and_preprocess_sensor_data(sensor_data_path)

# Load the location data
# location_data = pd.read_csv(location_data_path)

# Resample the sensor data to 1-second intervals
# resampled_sensor_data = resample_data(sensor_data)

# Align the sensor data with the location data by start and end times
# aligned_sensor_data = align_data(resampled_sensor_data, location_data)

# Merge the location and sensor data
# merged_data = merge_data(location_data, aligned_sensor_data)

# Export the merged data to a CSV file
# merged_data.to_csv("aligned_orientation_data.csv", index=False)