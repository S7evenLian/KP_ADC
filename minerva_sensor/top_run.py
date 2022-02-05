# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 15:28:43 2020

@author: Kangping Hu

This script read in a config file and pass the parameters to run the measurements
"""

from run_files import Run_Measure

###################################
##### specify the config file #####
###################################
config_file = "config_files/connection_check.txt"
#config_file = "config_files/single_run.txt"
#config_file = "config_files/multi_run.txt"
#config_file = "config_files/freq_scan_ruqn.txt"
#config_file = "config_files/testing.txt"

# parameters
chip_ID = "NA"
connection_check_only = "NA"
logname = "NA"
measurement_mode = "NA"
measurement_type = "NA"
measurement_duration = "NA"
save_raw = "NA"
show_image = "NA"
ph_electrode_V = "NA"


cf = open(config_file, 'r') 
Lines = cf.readlines()

# extract the parameters
for line in Lines:
    if "//" not in line:
        line = line.rstrip()
        a = line.split(':')
        a[-1] = a[-1].strip()

        if "chip_ID" in line:
            chip_ID = a[-1]
        if "connection_check_only" in line:
            connection_check_only = a[-1]
        if "logname" in line:
            logname = a[-1]
        if "measurement_mode" in line:
            measurement_mode = a[-1]
        if "measurement_type" in line:
            measurement_type = a[-1]
        if "measurement_duration" in line:
            measurement_duration = a[-1]
        if "save_raw" in line:
            save_raw = a[-1]
        if "show_image" in line:
            show_image = a[-1]
        if "ph_electrode_V" in line:
            ph_electrode_V = a[-1]
            
# sanity check to see if all parameters are loaded
if chip_ID == "NA" or connection_check_only == "NA" or logname == "NA" or measurement_mode == "NA" or measurement_type == "NA" or measurement_duration == "NA" or save_raw == "NA" or show_image == "NA" or ph_electrode_V == "NA":
        print("Something wrong with the config file, exiting...")

# run the measurements
else:
    print("========= printing the measurement parameters =======")
    print("config_file: " + str(config_file))
    print("chip_ID: " + str(chip_ID))
    print("connection_check_only: " + str(connection_check_only))
    print("logname: " + str(logname))
    print("measurement_mode: " + str(measurement_mode))
    print("measurement_type: " + str(measurement_type))
    print("measurement_duration: " + str(measurement_duration) + " min")
    print("save raw data: " + str(save_raw))
    print("show image: " + str(show_image))
    print("ph_electrode_V: " + str(ph_electrode_V) + "mV" +"\n")
    
    Run_Measure.main(chip_ID, connection_check_only, logname, measurement_mode, measurement_type, measurement_duration, save_raw, show_image, ph_electrode_V)
    
    