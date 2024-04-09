# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 17:22:48 2024

@author: U013179
"""

import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)

# Load the data
file_path = 'C:\\Users\\u013179\\OneDrive - Radboud Universiteit\\MINDSHARING_development\\Pilots\\playroom_150324\\sub_01_sensor.csv'
data = pd.read_csv(file_path, delimiter=';')

# Convert time column to datetime and calculate delta_t in seconds
data['time'] = pd.to_datetime(data['time'])
data['delta_t'] = (data['time'] - data['time'].shift(1)).dt.total_seconds()

# Calculate pitch and roll from accelerometer data
data['pitch'] = np.arctan2(data['acc_x'], np.sqrt(data['acc_y']**2 + data['acc_z']**2))
data['roll'] = np.arctan2(data['acc_y'], np.sqrt(data['acc_x']**2 + data['acc_z']**2))

# Convert radians to degrees
data['pitch_deg'] = np.degrees(data['pitch'])
data['roll_deg'] = np.degrees(data['roll'])

# Initialize the first row of filtered angles based on accelerometer
data.loc[0, 'filtered_pitch'] = data.loc[0, 'pitch']
data.loc[0, 'filtered_roll'] = data.loc[0, 'roll']

# Complementary filter settings
alpha = 0.98

# Apply the complementary filter
for i in range(1, len(data)):
    delta_t = data.loc[i, 'delta_t'] if not pd.isnull(data.loc[i, 'delta_t']) else 0
    # Gyroscope integration for angle change
    data.loc[i, 'filtered_pitch'] = alpha * (data.loc[i-1, 'filtered_pitch'] + data.loc[i, 'gyro_x'] * delta_t) + (1 - alpha) * data.loc[i, 'pitch']
    data.loc[i, 'filtered_roll'] = alpha * (data.loc[i-1, 'filtered_roll'] + data.loc[i, 'gyro_y'] * delta_t) + (1 - alpha) * data.loc[i, 'roll']

# Convert filtered angles from radians to degrees
data['filtered_pitch_deg'] = np.degrees(data['filtered_pitch'])
data['filtered_roll_deg'] = np.degrees(data['filtered_roll'])

# Display the first few rows of the final dataframe
print(data[['time', 'pitch_deg', 'roll_deg', 'filtered_pitch_deg', 'filtered_roll_deg']].head())