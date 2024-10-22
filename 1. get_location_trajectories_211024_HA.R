# Summary -----------------------------------------------------------------

# This script takes as input the "LocationData" csv files for all subject
# at a measurement day (e.g., a single morning in daycare), reads-in the
# location data (X, Y, Z), pre-processes the data while saving intermediate
# files, and finally plots/animates the data

# Packages ----------------------------------------------------------------

library(tidyverse)
library(ggplot2)
library(gganimate)
library(zoo)
library(signal)
library(stringr)
library(dplyr)
library(readr)
library(purrr)
library(gifski)
library(av)

# Define general paths and options ----------------------------------------

setwd("//fileserver.dccn.nl/project/3025010.01/Data/Daycare")

data_path <- file.path("data_raw")
proc_path <- file.path("data_processed")
if (!dir.exists(proc_path)){
  dir.create(proc_path, recursive = TRUE)
  cat("Directory", proc_path, "created")
} else {
  cat("Directory already exists")
}
out_path <- file.path("outdir")
if (!dir.exists(out_path)){
  dir.create(out_path, recursive = TRUE)
  cat("Directory", out_path, "created")
} else {
  cat("Directory already exists")
}

options("digits.secs"=3)


# Define names of daycare visits ----------------------------------------

visit_names <- c("DC-01",
                 "DC-02",
                 "DC-03",
                 "DC-04",
                 "DC-05",
                 "DC-06",
                 "DC-07",
                 "DC-08",
                 "DC-09")

# Import data -------------------------------------------------------------

# Function to read a single file and add subject and type columns
read_file_add_cols <- function(file_name) {
 
   # Construct the full file path
  full_path <- file.path(file_name)
  
  # Extract the subject number from the file name
  subject_number <- as.numeric(str_extract(file_name, "(?<=sub[-_])\\d+"))
  
  # Determine if the subject is a student or a teacher
  subject_type <- if_else(subject_number < 500, "student", "teacher")
  
  #Read the file
  df <- read_csv2(full_path)
  
   # Add subject_number and subject_type columns
  df <- mutate(df, subject_number = subject_number, subject_type = subject_type)
  
  # Convert 'subject_number' and 'subject_type' to factors
  df$subj_nr <- as.factor(df$subject_number)
  df$subj_type <- as.factor(df$subject_type)
 
  #Convert 'X', 'Y', 'Z', to numeric
  df$X <- as.numeric(df$X)
  df$Y <- as.numeric(df$Y)
  df$Z <- as.numeric(df$Z)
  return(df)
}

# Here comes the big loop -------------------------------------------------

for (i in 1:length(visit_names)){
  # debugging
  #i = 1 # comment-out when using the big loop
  print(i)
  
  visit <- visit_names[i]
 
   # where are the csv files located
  files_path <- file.path(data_path, visit, "location_data")
 
   # create a list of location files
  file_list <- list.files(path = files_path,
                          pattern = "sub-.*\\.csv$",
                          full.names = TRUE)
 
  # Use map_dfr to read all files and row-bind them into a single tibble
  combined_df <- map_dfr(file_list, read_file_add_cols)

  # Rearrange the columns in the desired order
  combined_df <- combined_df[, c("subject_number", "subject_type", "TimeStamp", "X", "Y", "Z")]

  # Write the combined_df tibble to a CSV file
  # optional
  w = TRUE # do not write intermediary dataframes to csv; set w = TRUE to save
  if (w){
    out_file_path <- file.path(proc_path, paste0(visit, "_combined_data", ".csv"))
    write_csv(combined_df, out_file_path)
  }

#  # Resample time series to 1 Hz regular -------------------------------------

#  # Convert 'TimeStamp' to POSIXct datetime format
#  combined_df$TimeStamp <- parse_date_time(combined_df$TimeStamp, orders = "mdy HMS")
  
#  # Ensure 'TimeStamp' is a datetime object
#  combined_df$TimeStamp <- as.POSIXct(combined_df$TimeStamp)
  
#  # Create a complete sequence of 1-second timestamps for each subject_number
#  resampled_df <- combined_df %>%
#    group_by(subject_number) %>%
#    # Complete fills missing timestamps with NA
#    complete(TimeStamp = seq(min(TimeStamp), max(TimeStamp), by = "1 sec")) %>%
#    # Compute mean for X, Y, Z values while ignoring NAs
#    group_by(subject_number, TimeStamp) %>%
#    summarize(
#      X = mean(X, na.rm = TRUE),
#      Y = mean(Y, na.rm = TRUE),
#      Z = mean(Z, na.rm = TRUE),
#      .groups = 'drop'
#    )
  
  ###RESAMPLED DATA DOES NOT WORK YET --> ONLY ONE TIMEPOINT PER SUBJECT. TRYING TO IMPLEMENT PYTHON RESMPALING SCRIPT, 
  ###SO WE DON'T LOOSE THE MISSING DATA
  ###ABOVE IS NEW SCRIPT, BELOW IS OLD SCRIPT.
  
  # Convert 'TimeStamp' to POSIXct datetime format
  combined_df$Time <- parse_date_time(combined_df$TimeStamp, orders = "mdy HMS")
  resampled_df <- combined_df %>%
    mutate(time_s = floor_date(Time, "second")) %>%
    group_by(subject_number, subject_type, time_s) %>%
    summarize(
      X = mean(X, na.rm = TRUE),
      Y = mean(Y, na.rm = TRUE),
      Z = mean(Z, na.rm = TRUE),
      .groups = 'drop' # This option drops the grouping, so the result is not grouped
    )
  
  # Write the resampled_df tibble to a CSV file
  # optional, see above
  if (w){
    out_file_path <- file.path(proc_path, paste0(visit, "_resampled_data_", ".csv"))
    write_csv(resampled_df, out_file_path)
  }
  
  # Align start times -------------------------------------------------------
  
  # Identify the latest start time among all subjects
  latest_start_time <- resampled_df %>%
    group_by(subject_number) %>%
    summarise(start_time = min(time_s)) %>%
    summarise(latest_start = max(start_time)) %>%
    pull(latest_start)
  
  # Filter out rows that start before the latest start time for any subject
  aligned_df <- resampled_df %>%
    dplyr::filter(time_s >= latest_start_time)
  
  # Identify the earliest end time among all subjects
  earliest_end_time <- aligned_df %>%
    group_by(subject_number) %>%
    summarise(end_time = max(time_s)) %>%
    summarise(earliest_end = min(end_time)) %>%
    pull(earliest_end)
  
  # Filter out rows that end after the earliest end time for any subject
  df_fin <- aligned_df %>%
    dplyr::filter(time_s <= earliest_end_time)
  
  # Write the final aligned_df tibble to a CSV file
  # optional
  if (w){
    out_file_path <- file.path(proc_path, paste0(visit, "_aligned_data", ".csv"))
    write_csv(df_fin, out_file_path)
  }
  
  # Preprocess the time series -------------------------------------------------------
  
  # Function to replace spikes with the median of their neighbors
  # Note: Might need refinements
  replace_spike_with_neighbors_median <- function(series) {
    n <- length(series)
    for(i in 1:length(series)) {
      start_index <- max(1, i - 5)
      end_index <- min(length(series), i + 5)
      
      if(series[i] > mean(series, na.rm = TRUE) + 1.5*IQR(series, na.rm = TRUE) | 
         series[i] < mean(series, na.rm = TRUE) - 1.5*IQR(series, na.rm = TRUE)) {
        series[i] <- median(series[start_index:end_index])
      }
    }
    return(series)
  }
  
  # Replace spikes in X and Y for each subject separately
  df_fin <- df_fin %>%
    group_by(subject_number) %>%
    mutate(
      X_despiked = replace_spike_with_neighbors_median(X),
      Y_despiked = replace_spike_with_neighbors_median(Y)
    )
  # df_fin$X_despiked <- replace_spike_with_neighbors_median(df_fin$X)
  # df_fin$Y_despiked <- replace_spike_with_neighbors_median(df_fin$Y)
  
  # Function to apply a low-pass Butterworth filter
  apply_low_pass_filter <- function(series, order, cutoff, sampling_rate) {
    # Design a Butterworth low-pass filter
    w <- cutoff / (sampling_rate / 2) # Normalize the frequency
    b <- butter(order, w, type = "low")
    
    # Apply the filter
    filtered_series <- signal::filter(b, series)
    return(filtered_series)
  }
  
  # Assuming a sampling rate in Hz
  sampling_rate <- 1
  
  # Filter parameters: order and cutoff frequency (in Hz)
  order <- 2 # Order of the filter
  cutoff <- 0.05 # Cutoff frequency in Hz
  
  # Apply the low-pass filter to X and Y
  df_fin <- df_fin %>%
    group_by(subject_number) %>%
    mutate(
      X_filtered = apply_low_pass_filter(X_despiked, order, cutoff, sampling_rate),
      Y_filtered = apply_low_pass_filter(Y_despiked, order, cutoff, sampling_rate)
    )
  #df_fin$X_filtered <- apply_low_pass_filter(df_fin$X_despiked, order, cutoff, sampling_rate)
  #df_fin$Y_filtered <- apply_low_pass_filter(df_fin$Y_despiked, order, cutoff, sampling_rate)
  
  # create a dataframe with timestamps that occur in every subject
  # (might need adjustment to getting timestamps that occur
  # at least in one subject and writing NAs in subjects
  # that do not have this timepoint)
  # Step 1: Group by subject and collect timestamps
  subject_timestamps <- df_fin %>%
    group_by(subject_number) %>%
    summarise(timestamps = list(time_s)) %>%
    ungroup()
  
  # Step 2: Find common timestamps
  # Initialize a variable with the timestamps of the first subject
  common_timestamps <- subject_timestamps$timestamps[[1]]
  
  # Use Reduce to find the intersection across all subjects
  for (i in 2:nrow(subject_timestamps)) {
    common_timestamps <- intersect(common_timestamps, subject_timestamps$timestamps[[i]])
  }
  
  # Step 3: Filter the original dataset to include only the common timestamps
  common_df_fin <- df_fin %>%
    dplyr::filter(time_s %in% common_timestamps)
  
  # Write the preprocessed data to a CSV file
  out_file_path <- file.path(proc_path, paste0(visit, "_data_preproc", ".csv"))
  write_csv(df_fin, out_file_path) #common_df_fin if last 3 preprocess steps are applied

  # Plot trajectories -------------------------------------------------------
  
  # Convert time_s to numeric scale for plotting
  df_fin$time_numeric <- as.numeric(df_fin$time_s) #common_df_fin if last 3 preprocess steps are applied
  df_fin$time_numeric <- df_fin$time_numeric - min(df_fin$time_numeric) #common_df_fin if last 3 preprocess steps are applied
  
  # Plot each subject separately
  p <- ggplot(df_fin,  #common_df_fin if last 3 preprocess steps are applied
              aes(x = X_filtered, y = Y_filtered, 
                  color = time_numeric, group = subject_number)) +
    geom_point(size = 1) +
   
     # scale_color_gradient(low = "blue", high = "red") +
    scale_color_viridis_c()+
    labs(title = "Trajectories by Subject", x = "X", y = "Y", color = "Time") +
    theme_minimal()+
    facet_wrap(~subject_number) +
    theme(panel.spacing = unit(1, "lines"))+ # Adjust spacing between panels
    theme(plot.title = element_text(size = 20),  # Increase title size
          axis.title.x = element_text(size = 14),  # Increase X axis title size
          axis.title.y = element_text(size = 14),  # Increase Y axis title size
          axis.text.x = element_text(size = 12),  # Increase X axis text/label size
          axis.text.y = element_text(size = 12),
          strip.text.x = element_text(size = 16))  # Increase Y axis text/label size
  p
  ggsave(filename = file.path(out_path, paste0(visit, ".png")),
         plot = p, dpi = 400, width = 10, height = 10, bg = "white")
  
  ## Create animation
  # optional
  ani = TRUE # set to TRUE if you want to create an animation
  # Plot all subjects within one square
  if(ani){
    p_one <- ggplot(df_fin %>% dplyr::filter(time_numeric <= 600), #common_df_fin if last 3 preprocess steps are applied
                    aes(x = X_filtered, y = Y_filtered, color = subject_number, group = subject_number)) +
      geom_point(size = 4) +
      
      # scale_color_gradient(low = "blue", high = "red") +
      labs(title = "Trajectories by Subject", x = "X", y = "Y", color = "Subject") +
      theme_minimal()+
      theme(panel.spacing = unit(1, "lines"))+ # Adjust spacing between panels
      theme(plot.title = element_text(size = 20),  # Increase title size
            axis.title.x = element_text(size = 14),  # Increase X axis title size
            axis.title.y = element_text(size = 14),  # Increase Y axis title size
            axis.text.x = element_text(size = 12),  # Increase X axis text/label size
            axis.text.y = element_text(size = 12),
            strip.text.x = element_text(size = 16),  # Increase Y axis text/label size
            legend.text = element_text(size = 14), # Increase legend text size
            legend.title = element_text(size = 16)) # Increase legend title size
    p_one
    
    # Add animation with gganimate
    animated_p <- p_one +
      transition_reveal(time_numeric) +
      labs(title = 'Time in s: {round(frame_along, 0)}', subtitle = "Trajectories by Subject") # Update title to show current time
    
    # make the animation as long as the timeseries
    # len_animation <- max(common_df_fin$time_numeric)
    len_animation <- 600
    # To save the animation, use the animate function and then save it with anim_save
    anim <- animate(animated_p, height = 10, width = 10, units = "in", res = 300,
                    duration = round(len_animation/10, 0), nframes = round(len_animation/1, 0))
    anim_save(file.path(out_path, paste0(visit, "_animated.gif")), animation = anim)
  }
  # end of big loop
}
