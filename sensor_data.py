# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 17:22:48 2024

@author: U013179
"""

import pandas as pd
import numpy as np
import re
import os
from glob import glob

# Import data ----------------------------------------------------------------

# Define the paths for data and output directories
data_path = 'C:\\Users\\u013179\\OneDrive - Radboud Universiteit\\MINDSHARING_development\\Sensor_data\\data'
out_path = 'C:\\Users\\u013179\\OneDrive - Radboud Universiteit\\MINDSHARING_development\\Sensor_data\\outdir'

# Define visit names or similar categorization as in your R example
visit_names = ["pilot_150324"]

# Function to read a single file and process it
def read_file_add_cols(file_path):
    # Extract the subject number from the file name
    subj_nr = int(re.search(r"sub[-_](\d+)", file_path).group(1))
    # Determine if the subject is a student or a teacher
    subj_type = "student" if subj_nr < 500 else "teacher"
    
    # Read the CSV file
    sensor_data = pd.read_csv(file_path, delimiter=';')
    
    # Add subject_number and subject_type columns
    sensor_data['subj_nr'] = subj_nr
    sensor_data['subj_type'] = subj_type
    
    return sensor_data 

# Initialize an empty list to store DataFrames
all_data = []

# Iterate over each visit and concatenate the files
for visit in visit_names:
    files_path = os.path.join(data_path, visit)
    # List all CSV files in the directory matching the pattern
    file_list = glob(os.path.join(files_path, "sub_**_sensor.csv"))
    
    # Read all files and append to list
    for file_path in file_list:
        sensor_data  = read_file_add_cols(file_path)
        all_data.append(sensor_data )

# Concatenate all DataFrames into one
combined_sensor_data  = pd.concat(all_data, ignore_index=True)

# Drop the columns related to the magnetometer
combined_sensor_data.drop(['mag_x', 'mag_y', 'mag_z'], axis=1, inplace=True)
    
# Add subj_nr, subj_type, and TagID columns 
combined_sensor_data['TagID'] = "Unknown"  # Needs specification on where to retrieve it
    
# Reorder columns to match the specified order
combined_sensor_data = combined_sensor_data[['subj_nr', 'subj_type', 'TagID', 'time', 'gyro_x', 'gyro_y', 'gyro_z', 'acc_x', 'acc_y', 'acc_z']]

# Write the combined DataFrame to a CSV file in the output directory
output_file_path = os.path.join(out_path, "combined_sensor_data.csv")
combined_sensor_data.to_csv(output_file_path, index=False)

print(f'Combined data saved to {output_file_path}')

# Resample timeseries to 1 Hz ------------------------------------------------

# Convert 'time' to datetime format
combined_sensor_data['time'] = pd.to_datetime(combined_sensor_data['time'])

# Set 'time' as the data's index
combined_sensor_data.set_index('time', inplace=True)

# Resample the data to a 1-second frequency, grouping by 'subj_nr', 'subj_type', and 'TagID' before resampling
resampled_sensor_data = combined_sensor_data.groupby(['subj_nr', 'subj_type', 'TagID']).resample('1S').mean().reset_index()

# Write resampled data to a csv file
resampled_filename = 'resampled_sensor_data.csv'
resampled_file_path = os.path.join(out_path, resampled_filename)
resampled_sensor_data.to_csv(resampled_file_path, index=False)

print(f'Resampled data saved to {resampled_file_path}')

# Get orientation from x, y, z coordinates per timestamp --------------------

# Calculate pitch and roll from accelerometer data
resampled_sensor_data['pitch'] = np.arctan2(resampled_sensor_data['acc_x'], np.sqrt(resampled_sensor_data['acc_y']**2 + resampled_sensor_data['acc_z']**2))
resampled_sensor_data['roll'] = np.arctan2(resampled_sensor_data['acc_y'], np.sqrt(resampled_sensor_data['acc_x']**2 + resampled_sensor_data['acc_z']**2))

# Convert radians to degrees
resampled_sensor_data['pitch_deg'] = np.degrees(resampled_sensor_data['pitch'])
resampled_sensor_data['roll_deg'] = np.degrees(resampled_sensor_data['roll'])

# Initialize the first row of filtered angles based on accelerometer
resampled_sensor_data.loc[0, 'filtered_pitch'] = resampled_sensor_data.loc[0, 'pitch']
resampled_sensor_data.loc[0, 'filtered_roll'] = resampled_sensor_data.loc[0, 'roll']

# Complementary filter settings
alpha = 0.98


### Due to this code snippet the data in filtered_orentation_data.csv stops after 10.47.45 seconds, because there are missing data points in 
### resampled_sensor_data, due to not-measured seconds. Therefore, there are no datapoints to after halfway subject 1.
### Needs to be fixed!
 
# Apply the complementary filter 
for i in range(1, len(resampled_sensor_data)):
    # Gyroscope integration for angle change assumes delta_t = 1
    resampled_sensor_data.loc[i, 'filtered_pitch'] = alpha * (resampled_sensor_data.loc[i-1, 'filtered_pitch'] + resampled_sensor_data.loc[i, 'gyro_x']) + (1 - alpha) * resampled_sensor_data.loc[i, 'pitch']
    resampled_sensor_data.loc[i, 'filtered_roll'] = alpha * (resampled_sensor_data.loc[i-1, 'filtered_roll'] + resampled_sensor_data.loc[i, 'gyro_y']) + (1 - alpha) * resampled_sensor_data.loc[i, 'roll']

# Convert filtered angles from radians to degrees
resampled_sensor_data['filtered_pitch_deg'] = np.degrees(resampled_sensor_data['filtered_pitch'])
resampled_sensor_data['filtered_roll_deg'] = np.degrees(resampled_sensor_data['filtered_roll'])

# Write new data to resampled_data csv file
resampled_file_path = os.path.join(out_path, 'resampled_data.csv')
resampled_sensor_data.to_csv(resampled_file_path, index=False)
print(f'Resampled data has been updated and saved to {resampled_file_path}')

# Write filtered pitch and roll degrees to new csv file
selected_data = resampled_sensor_data[['subj_nr', 'subj_type', 'TagID', 'time', 'filtered_pitch_deg', 'filtered_roll_deg']]
new_filename = 'filtered_orientation_data.csv'

# Construct the full path to where the file will be saved
new_file_path = os.path.join(out_path, new_filename)

# Write the selected data to a csv file
selected_data.to_csv(new_file_path, index=False)

print(f'Filtered orientation data saved to {new_file_path}')




