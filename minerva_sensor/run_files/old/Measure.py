# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 15:54:04 2019

@author: labuser2
"""

import numpy as np
import time
from datetime import datetime
from minerva import minerva
import h5py
import timeit
import matplotlib.pyplot as plt
import pickle
from run_files import Decode

#a.verbose = False

def Single_Measure(chip_ID, logname, measurement_type, save_raw, show_image, ph_electrode_V):
    print("Single measurement on: " + measurement_type)
    
    params = {'save_raw': save_raw,
              'measurement_mode' : 'single',
              'show_image' : show_image
              }

    if(measurement_type == "impedance"):
        params['mode']=1
        status = Impedance_Measure(chip_ID, logname, params)
        while status == 0:
            status = Impedance_Measure(chip_ID, logname, params)      
            
        params['mode']=2            
        status = Impedance_Measure(chip_ID, logname, params)
        while status == 0:
            status = Impedance_Measure(chip_ID, logname, params)   

# TEMPORARILY UNSUPPORTED 
#    elif(measurement_type == "optical"):
#        status = Optical_Measure(chip_ID, logname, params)
#        while status == 0:
#            status = Optical_Measure(chip_ID, logname, params)
#            
#    elif(measurement_type == "ph"):
#        pH_Measure(chip_ID, logname, save_raw, show_image, ph_electrode_V)
#               
#    elif(measurement_type == "isfet_rst"):
#        ISFET_RST()
        
    else:
        print("Unsupported measurement type. Please specify optical/ph/impedance. Aborting measurement.")
      
        
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~           
def Multi_Measure(chip_ID, logname, measurement_duration, save_raw, show_image, ph_electrode_V):  
    print("Running multiple measurements with duration: "+str(measurement_duration) + " minutes")

    params = {'save_raw': save_raw,
              'measurement_mode' : 'multiple',
              'show_image' : show_image
              }
    
    # initialize the start time    
    start = timeit.default_timer()  
    time_elasped = 0 # in minute
    loop_num = 1
    
    while(time_elasped < float(measurement_duration)):
    
        # loop optical, ph and impedance measurements
        print("===== Loop #"+str(loop_num)+"======")
              
#        status = Optical_Measure(chip_ID, logname, save_raw, show_image)
#        while status == 0:
#            status = Optical_Measure(chip_ID, logname, save_raw, show_image)
#        
        #ISFET_RST()
        #pH_Measure(chip_ID, logname, save_raw, show_image, ph_electrode_V)
        
        params['mode']=1
        status = 0
        while (status == 0):
            status = Impedance_Measure(chip_ID, logname, params)

        params['mode']=2
        status = 0
        while (status == 0):
            status = Impedance_Measure(chip_ID, logname, params)

            
        stop = timeit.default_timer()
        time_elasped = (stop - start)/60   
        loop_num = loop_num + 1
        
   
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~       
def Impedance_Measure(chip_ID, logname, params, scan_file = None):
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    # Parameter Definitions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    bitfilename = None   #use default

    # create antelope daq instance
    a = antelope(bitfilename=bitfilename)

    # pass through parameters
    a.pset_dict(params)
    
    
    # Scan Chain Data File    
    if not scan_file:
        if(a.pget('mode')==1):
            scan_fname = 'scan_chain/Impedance_scan_CDM_64x1_mode_1.h5'
        else:
            scan_fname = 'scan_chain/Impedance_scan_CDM_64x1_mode_2.h5'
            
    else:
        scan_fname = scan_file
        
#    print(scan_fname)
        
    rst_fname = 'scan_chain/scan_rst.txt'
    a.pset('scan_vector_name', scan_fname)
    
    # chip ID
    a.pset('ID', chip_ID)
    
    # board setup
    a.pset('Vdd', 2.0)
    a.pset('f_sw', 'NA')
    a.pset('samplerate', 390625)
    a.pset('vectorfrequency', 25e6)    
    a.pset('ADCbits', 18)
    a.pset('ADCfs', 3.3)
    
    # VGA setting
    a.pset('VGA_Gain', 2)
    
    # DAC Settings
    a.pset('V_SW', 500)
    a.pset('V_Stdby_1', 500)
    a.pset('V_BGVDD', 0)
    a.pset('V_Stdby_2', 0)
    a.pset('V_PCB_Test_Pin_1', 0)
    a.pset('V_PCB_Test_Pin_2', 0)
    a.pset('V_Electrode_Bias', 500)
    a.pset('V_TIA_Bias', 1200)
    
    # optical settings
    a.pset('Diode_1', 'TIA')
    a.pset('Diode_2', 'TIA')
    a.pset('Diode_3', 'TIA')
    a.pset('Diode_1_Bias', 'V_TIA')
    a.pset('Diode_2_Bias', 'V_TIA')
    a.pset('Diode_3_Bias', 'V_TIA')
    
    # code settings
    a.pset('Row_code', 64)
    a.pset('Col_code', 0)
    
    # Others
    a.pset('Row_Code_Clk', '3 kHz')
    a.pset('Col_Code_Clk', '0')
    a.pset('Chopping_Clk', '400 kHz')
    a.pset('Block_offset', a.pget('mode'))
    
    # dataset name
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    a.pset('timestamp', timestamp)
    grp_name = 'Impedance_'+timestamp
    
    print('Start Impedance Measurement with offset block '+ str(a.pget('mode')) + ' on ' + str(timestamp) + '...')
    
    # ~~~~~~~~~~~~~~~~~ Load bit file into FPGA ~~~~~~~~~~~~~~~~~~~~~~~
    #xem = a.InitializeFPGA(bitfilename)
    a.InitializeFPGA(loadbitfile=True)
    a.InitializeGPIOs()
    a.OutOfReset(ADCsamplerate=a.pget('samplerate'),
                 vectorsamplerate=a.pget('vectorfrequency'))

    # configure data stream paths
    a.StreamSwitch(a.TO_MEM, a.FROM_ADC)
    a.StreamSwitch(a.TO_PC, a.FROM_MEM)
    a.StreamSwitch(a.TO_VECTOR, a.FROM_PC)
        
    # ~~~~~~~~~~~~~~~~~ Configure DAC ~~~~~~~~~~~~~~~~~~~~~~~
    a.DAC_setup()
    
    # ~~~~~~~~~~~~~~~~~ Configure VGA Gain ~~~~~~~~~~~~~~~~~~~~~~~
    a.VGA_Config()
    
    # load the scan data file
    hf = h5py.File(scan_fname, 'r')
    scan_all_int = hf['scan_save'][:]
    scan_rst = np.loadtxt(rst_fname, 'uint8')
    
    # ~~~~~~~~~~~~~~~~~ Reset ADC FIFO ~~~~~~~~~~~~~~~~~~~~~~~
    
    expectedtime = 0.03*len(scan_all_int[0])
    
    #a.FIFO_Reset()
    a.StopADC()
    numtransfers,xferbytes = a.QueueADCAcquisition(sec=1.3*expectedtime)

    # un-protect scan pins
    a.ProtectScanPins(False)

    a.StartADC()
    
    # reset    
    #a.SendScanVector(xem,scan_rst)
    a.SendScanVector_4bit(scan_rst)
    time.sleep(1)
    
    # acquire the data 
    tstart = time.time()   
    for addr in range(len(scan_all_int[0])):   
        
        print('\rscan vector addr %u/%u   (%2.2f sec)' % (addr+1,
                                                          scan_all_int.shape[1],
                                                          time.time()-tstart), flush=True, end='')
         
        # send the data
        a.SendScanVector_4bit(scan_all_int[:,addr])
                
        # 64 /3kHz = 0.021s
        # using daq.sleep, more accurate but blocking and resource intensive
        a.sleep(0.03)     
        
    print('')

    if(time.time()-tstart > 1.25*expectedtime):
        print('WARNING: scan vectors took too long.')

    # re-protect scan pins
    a.ProtectScanPins(True)
        
    # ~~~~~~~~~~~~~~~~~ Acquire ADC Data ~~~~~~~~~~~~~~~~~~~~~~~  
    a.WaitForDMA(numtransfers)
    
    mydata,mybytes = a.GetDataFromMemory(xferbytes)
    
    adcdata = 3.3*np.mod(np.bitwise_and(mydata[:],0x00FFFFFF) + 2**17, 2**18)/2**18
    scanlatch_flag = np.array(np.bitwise_and(mydata[:],0x80000000),dtype=np.bool)
    code_clk = np.array(np.bitwise_and(mydata[:],0x40000000),dtype=np.bool)

    # convert to signed int8 for well-behaved derivatives
    adcdata = np.squeeze(adcdata)
    scanlatch_flag = np.array(np.squeeze(scanlatch_flag),dtype=np.int8)
    code_clk = np.array(np.squeeze(code_clk),dtype=np.int8)


#    from scipy.io import savemat
#    savemat("adcdata.mat", {'adcdata':adcdata,
#                            'scanlatch_flag':scanlatch_flag,
#                            'code_clk':code_clk})
    
    # ~~~~~~~~~~~~~~~~~ Disconnect ~~~~~~~~~~~~~~~~~~~~~~~        
    a.CloseFPGA()


#    #t_latch = np.where(scanlatch_flag==1)[0][0]
#    #print(t_latch)
#    plt.figure(figsize=(8,3))
#    #plotrange = range(t_latch-100,t_latch+100)
#    plotrange=range(len(adcdata))
#    #plotrange=range(int(2e6))
#    #plotrange=range(1400,1460)
#    plt.plot(0.4*scanlatch_flag[plotrange]-1)
#    plt.plot(0.4*code_clk[plotrange] -0.5)
#    plt.plot(adcdata[plotrange])
#    plt.title('ADC data, latch, code clock')
#    plt.show()
    
    
#    plt.figure(figsize=(9,3))
#    plt.plot(adcdata);
#    plt.show()
#    
#    plt.figure(figsize=(9,3))
#    plt.plot(scanlatch_flag);
#    plt.show()   
    
    
    # ================ decode the data ========================
    # Sanity check
    latch_deri = np.diff(scanlatch_flag)
    latch_edge_ind_all = np.where(latch_deri == 1)[0]
    print('number of latch edges found',len(latch_edge_ind_all))
#    print(latch_edge_ind_all)
#
#    plt.figure(figsize=(8,3))
#    plotrange = range(latch_edge_ind_all[0]-100,latch_edge_ind_all[0]+100)
#    #plotrange=range(len(adcdata))
#    #plotrange=range(int(2e6))
#    #plotrange=range(1400,1460)
#    plt.plot(0.4*scanlatch_flag[plotrange]-1)
#    plt.plot(0.4*code_clk[plotrange] -0.5)
#    plt.plot(adcdata[plotrange])
#    plt.title('ADC data, latch, code clock')
#    plt.show()
    
    
    #error(1)
    
    if len(latch_edge_ind_all) != 2049:
        print("Data aquisition failed, try again...\n\n")
        return 0
        


    image = Decode.Decode_CDM_64(adcdata, code_clk, scanlatch_flag, a.pget('mode'))

#     ~~~~~~~~~~~~~~~~~ Save data to log file ~~~~~~~~~~~~~~~~~~~~~~~  
    fname = logname
    
    a.SaveToLogFile(fname,
                    grp_name,
                    dataset_name='image', 
                    data=image,
                    comments='')   
    
    # check if need to save raw data
    if a.pget('save_raw') == "yes":
        a.SaveToLogFile(fname,
                        grp_name,
                        dataset_name='data', 
                        data=adcdata,
                        comments='')
        a.SaveToLogFile(fname,
                        grp_name,
                        dataset_name='scanlatch', 
                        data=scanlatch_flag,
                        comments='')
        a.SaveToLogFile(fname,
                        grp_name,
                        dataset_name='code_clk', 
                        data=code_clk,
                        comments='')
        a.SaveToLogFile(fname,
                        grp_name,
                        dataset_name='scan_all_int', 
                        data=scan_all_int,
                        comments='')
        
    # check if need to plot the data
    if(a.pget('show_image') == "yes"):
        Decode.Plot_Image(chip_ID, grp_name, image)
        
    print("Impedance measurement successfully finished\n")
    return 1
    

    
