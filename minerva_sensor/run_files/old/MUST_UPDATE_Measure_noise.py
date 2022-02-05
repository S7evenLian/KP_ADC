# -*- coding: utf-8 -*-


import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
import os

from minerva import minerva_old as minerva

plt.rcParams['agg.path.chunksize'] = 10000

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)
 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def Measure():
    
    print('Checking chip connection...')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    # Parameter Definitions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    bitfilename = None   #use default
    
    # create antelope daq instance
    m = minerva(bitfilename=bitfilename)

    # board setup
    m.pset('Vdd', 2.0)
    m.pset('f_sw', 50e6)
    m.pset('f_master', 390625)
    m.pset('samplerate', 390625)
#    m.pset('vectorfrequency', 390625) #12.5e6)
    m.pset('vectorfrequency', 1.25e6) #12.5e6)
    m.pset('ADCbits', 18)
    m.pset('ADCfs', 3.3)

    
    # DAC Settings
    m.pset('V_SW', 700)
    m.pset('V_CM', 600)    
    m.pset('V_Electrode_Bias', 600)
    m.pset('V_STIMU_P', 0)
    m.pset('V_STIMU_N', 0)   
    m.pset('V_STBY', 600)

    
    # code settings
    m.pset('Row_code', 4)
    m.pset('Col_code', 64)
    
    # Others
    #m.pset('Row_Code_Clk', '6.1 kHz')
    #m.pset('Col_Code_Clk', '23.8 Hz')
    #m.pset('Chopping_Clk', '400 kHz')
    
    # dataset name
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    m.pset('timestamp', timestamp)
    #grp_name = 'Optical_'+timestamp
    
    # ~~~~~~~~~~~~~~~~~ Load bit file into FPGA ~~~~~~~~~~~~~~~~~~~~~~~
    m.InitializeFPGA(loadbitfile=True)
    m.InitializeGPIOs()
    m.SetClkDividers(f_adc=m.pget('samplerate'),
                     f_vector=m.pget('vectorfrequency'),
                     f_sw=m.pget('f_sw'),
                     f_master=m.pget('f_master'))
    m.OutOfReset()
    
    # configure data stream paths
    m.StreamSwitch(m.TO_MEM, m.FROM_ADC)
    m.StreamSwitch(m.TO_PC, m.FROM_MEM)
    m.StreamSwitch(m.TO_VECTOR, m.FROM_PC)
    
    # optional, protect scan pins during DAC setup
    #m.ProtectScanPins(True)
    
    # ~~~~~~~~~~~~~~~~~ Configure DAC ~~~~~~~~~~~~~~~~~~~~~~~
    m.DAC_setup()

    # ~~~~~~~~~~~~~~~~~ Output Clocks for chip ~~~~~~~~~~~~~~~~~~~~~~~
    m.StartClkout()
    
    # ~~~~~~~~~~~~~~~~~ Reset ADC FIFO ~~~~~~~~~~~~~~~~~~~~~~~
    #m.FIFO_Reset()
    m.StopADC()
    numtransfers,xferbytes = m.QueueADCAcquisition(sec=12)
    m.StartADC()

    # ~~~~~~~~~~~~~~~~~ Send in scanchain ~~~~~~~~~~~~~~~~~~~~~~~
    #m.SendScanVector(scan_all_int)
    
    m.ProtectScanPins(False)
    
    # ~~~~~~~~~~~~~~~~~ Measurement Steps ~~~~~~~~~~~~~~~~~~~~
    # Reset
    scan_all_reset = minerva.Generate_scan_vector_rst()
    m.SendScanVector_4bit(scan_all_reset)
    time.sleep(0.05)
    
    # Measure output without pixel switchiing
    for ch in range(8):
        # measure
        scan_all_mea_test_col = minerva.Generate_scan_vector_mea_test_col_single_pixel(ch)
        m.SendScanVector_4bit(scan_all_mea_test_col)
        time.sleep(0.6)    
        
    # Enable pixel
    scan_all_set_sensing_mode = minerva.Generate_scan_vector_test_col_sensing_mode()
    m.SendScanVector_4bit(scan_all_set_sensing_mode)
    time.sleep(0.05)    
    
    # Measure output without pixel switchiing
    for ch in range(8):
        # measure
        scan_all_mea_test_col = minerva.Generate_scan_vector_mea_test_col_single_pixel(ch)
        m.SendScanVector_4bit(scan_all_mea_test_col)
        time.sleep(0.6)        
        
    # do not re-protect scan pins right away. If the vector_clk is slower,
    # the vectors may take some time to appear.
    # m.ProtectScanPins(True)
    
    # ~~~~~~~~~~~~~~~~~ Acquire ADC Data ~~~~~~~~~~~~~~~~~~~~~~~    
    m.WaitForDMA(numtransfers)
    
    #m.StopADC()
        
    mydata,mybytes = m.GetDataFromMemory(xferbytes)
    print('acquired data')
    print('bytes',mybytes)
    #for i in range(256):
    #    print(i, bin(mydata[i]))
    
    # NOTE: dtest and scan_x signals are often faster than the ADC sample rate.
    #       Ensure the signals are slow enough to observe.
    dtest_1 = np.array(np.bitwise_and(mydata[::8],   np.uint32(1<<31)),dtype=np.bool).astype(np.int32)
#    dtest_2 = np.array(np.bitwise_and(mydata[::8],   np.uint32(1<<30)),dtype=np.bool).astype(np.int32)
#    scan_clk = np.array(np.bitwise_and(mydata[::8],  np.uint32(1<<29)),dtype=np.bool).astype(np.int32)
#    scan_din = np.array(np.bitwise_and(mydata[::8],  np.uint32(1<<28)),dtype=np.bool).astype(np.int32)
    scan_latch = np.array(np.bitwise_and(mydata[::8],np.uint32(1<<27)),dtype=np.bool).astype(np.int32)
#    scan_reset = np.array(np.bitwise_and(mydata[::8],np.uint32(1<<26)),dtype=np.bool).astype(np.int32)
    
    adcdata1 = np.bitwise_and(mydata, np.uint32(0x0003FFFF)).astype(np.uint32)   #keep 18 bits
    adcdata2 = np.bitwise_or(adcdata1, (adcdata1&0x00020000 != 0) * np.uint32(0xFFFC0000))       #sign extension from 18 bits
    adcdata = 2*3.3*adcdata2.view(np.int32)/2**18    # view as signed integer, scale to volts
    
    sample_clk=dtest_1

    plt.figure(figsize=(8,8))
    plt.plot(scan_latch)
    plt.title('scan_latch')
    plt.show() 

    plt.figure(figsize=(8,8))
    plt.plot(sample_clk[200000:200100])
    plt.title('sample_clk')
    plt.show() 

    scan_latch_deri = np.diff(scan_latch)
    scan_latch_edge_all_index = np.where(scan_latch_deri == 1)[0]
    
    print(scan_latch_edge_all_index)
    
    # collect non-switchinig data for each channel
    plt.figure(figsize=(8,4))
    
    for ch in range(8):
        start_ind = scan_latch_edge_all_index[ch] + 100
        adcdata_1_ch = adcdata[ch::8]
        adcdata_1_ch = adcdata_1_ch[start_ind:start_ind+200000]
        
        plt.figure(figsize=(8,4))
        plt.plot(adcdata_1_ch)
        plt.title('ch'+str(ch))
        plt.show()
        
        fname = 'data/noise/ch'+str(ch)+'_no_switching.npy'
        with open(fname,'wb') as f:
            np.save(f, adcdata_1_ch)
            
    # collect switchiing data for each channel
    for ch in range(8):
        start_ind = scan_latch_edge_all_index[ch+9] + 100
        print(start_ind)
        adcdata_1_ch = adcdata[ch::8]
        adcdata_1_ch = adcdata_1_ch[start_ind:start_ind+200000]
        
        plt.figure(figsize=(8,4))
        plt.plot(adcdata_1_ch)
        plt.title('ch'+str(ch))
        plt.show()
        
        fname = 'data/noise/ch'+str(ch)+'_with_switching.npy'
        with open(fname,'wb') as f:
            np.save(f, adcdata_1_ch)    


if __name__ == "__main__":
    
    #print('5 sec delay')
    #time.sleep(5)
    print('measure')
    Measure()
    
