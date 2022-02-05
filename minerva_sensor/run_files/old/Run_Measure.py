# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 17:50:43 2020

@author: Kangping Hu

This script takes in the parameters from the config file, and run the corresponding measurements
"""

from run_files import Check_connection
from run_files import Measure
import time


def main(chip_ID, connection_check_only, logname, measurement_mode, measurement_type, measurement_duration, save_raw, show_image, ph_electrode_V):
        
    # If only check connection
    if connection_check_only == "yes":
        Check_connection.Measure()
        
    else:
        # For single measurement
        if measurement_mode == "single":
            Measure.Single_Measure(chip_ID, logname, measurement_type, save_raw, show_image, ph_electrode_V)
            
        # For long_term measurement
        if measurement_mode == "multiple":
            Measure.Multi_Measure(chip_ID, logname, measurement_duration, save_raw, show_image, ph_electrode_V)
            
        # For frequency scan measurement
        if measurement_mode == "freq_scan":
            D = 32768
            for i in range(16):
                print('Recording at ' + str(100/D) + ' MHz (Sweep Value #'+str(i)+')')
                
                scan_file = 'scan_chain/Impedance_scan_CDM_64x1_mode_1_100M_D'+str(D)+'.h5' 
                Measure.Impedance_Measure(chip_ID, logname, save_raw, show_image, 1, scan_file)
                time.sleep(2)
                
                scan_file = 'scan_chain/Impedance_scan_CDM_64x1_mode_2_100M_D'+str(D)+'.h5'  
                Measure.Impedance_Measure(chip_ID, logname, save_raw, show_image, 2, scan_file)
                time.sleep(2)
                
                D = int(D/2)
        
