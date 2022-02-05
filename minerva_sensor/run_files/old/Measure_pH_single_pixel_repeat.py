# -*- coding: utf-8 -*-


import os
if __name__ == "__main__":
    os.chdir(os.path.split(os.path.dirname(__file__))[0])

import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
#from scipy.signal import correlate2d

from minerva import minerva

plt.rcParams['agg.path.chunksize'] = 10000

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)
 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def Measure(fname=None):
    
    print('Measuring pH single_pixel...')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    # Parameter Definitions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    bitfilename = None   #use default
    
    # create antelope daq instance
    m = minerva(bitfilename=bitfilename)

    # board setup
    m.pset('Vdd', 2.15)
    m.pset('f_sw', 6.25e6)
    m.pset('f_master', 390625)
    m.pset('samplerate', 2000)
#    m.pset('vectorfrequency', 390625) #12.5e6)
    m.pset('vectorfrequency', 1.25e6) #12.5e6)
    m.pset('ADCbits', 18)
    m.pset('ADCfs', 3.3)

    m.pset('PINOUT_CONFIG',1)    # Minerva_v1 = 0; Minerva_v2 = 1; Sidewinder_v1 = 2
    
    # todo: DOUBLE CHECK
    m.pset('T_int',3/m.pget('samplerate'))
    m.pset('C_int',5e-12)
    
    # DAC Settings
    m.pset('V_SW', 0)
    m.pset('V_CM', 400)    
    m.pset('V_Electrode_Bias', 1000)
    m.pset('V_STIMU_P', 0)
    m.pset('V_STIMU_N', 0)   
    m.pset('V_STBY', 0)
    
    
    gain_swcap = np.abs(m.pget('V_SW')-m.pget('V_CM'))*1e-3*m.pget('f_sw')  # Iout/Cin
    gain_integrator = m.pget('T_int')/m.pget('C_int')  # Vout/Iin
    gain_overall = gain_swcap*gain_integrator
    
    
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

    # ~~~~~~~~~~~~~~~~~ Send in scanchain ~~~~~~~~~~~~~~~~~~~~~~~
    #m.SendRawVector(scan_all_int)
    
    m.ProtectScanPins(False)
    # this scan vector will set the measurement mode for test col pixels and trigger DTEST_1 Toggle
    
    # ~~~~~~~~~~~~~~~~~ Set the sensing mode ~~~~~~~~~~~~~~~~~~~~~~~
    vector_reset = np.zeros(64)
    vector_reset_deselect = np.zeros(64) + 8  # de-assert reset
    #scan_all_close_sram = minerva.Generate_scan_vector_close_sram(False)
    scan_all_mea_pH_single_pixel = m.Generate_scan_vector_mea_pH_single_pixel(20,20)
    
    m.SendRawVector(vector_reset)
    time.sleep(0.02)
    
    tstart=time.time()
    for col_addr in range(256):   
        
        # set the sensing mode
        print('\rgenerating scan vector for col %u   (%2.2f sec)' % (col_addr,time.time()-tstart),end='')        
        scan_all_set_sensing_mode = m.Generate_scan_vector_all_pixel_sensing_mode(col_addr)
        
        m.UpdateScanChain(scan_all_set_sensing_mode)  # send as 32 bit vector
        time.sleep(0.02)
    print('')
    
    # ~~~~~~~~~~~~~~~~~ Reset ADC FIFO ~~~~~~~~~~~~~~~~~~~~~~~
#    m.SendScanVector_4bit(scan_all_close_sram)
#    time.sleep(0.1)
    m.SendScanVector_4bit(vector_reset)
    time.sleep(0.1)
    m.SendRawVector(vector_reset_deselect)
    time.sleep(0.1)

    # measure pH
    m.UpdateScanChain(scan_all_mea_pH_single_pixel)
    time.sleep(1)     


    # repeat the acquisition
    adcdata_all = []
    
    for repeat in range(60):
    
        print('acqusition: '+str(repeat))    
    
        #m.FIFO_Reset()
        m.StopADC()
        numtransfers,xferbytes = m.QueueADCAcquisition(sec=20)
        m.StartADC()
    
        # do not re-protect scan pins right away. If the vector_clk is slower,
        # the vectors may take some time to appear.
        # m.ProtectScanPins(True)
        
        # ~~~~~~~~~~~~~~~~~ Acquire ADC Data ~~~~~~~~~~~~~~~~~~~~~~~    
        m.WaitForDMA(numtransfers)
        
        #m.StopADC()
            
        mydata,mybytes = m.GetDataFromMemory(xferbytes)
        print('acquired data')
        print('bytes',mybytes)
        
        # NOTE: dtest and scan_x signals are often faster than the ADC sample rate.
        #       Ensure the signals are slow enough to observe.   
        adcdata1 = np.bitwise_and(mydata, np.uint32(0x0003FFFF)).astype(np.uint32)   #keep 18 bits
        adcdata2 = np.bitwise_or(adcdata1, (adcdata1&0x00020000 != 0) * np.uint32(0xFFFC0000))       #sign extension from 18 bits
        adcdata = 2*3.3*adcdata2.view(np.int32)/2**18    # view as signed integer, scale to volts
        
        # locate the sampling points
        adcdata_ch0 = adcdata[0::8]        
        adcdata_all.append(adcdata_ch0)
        
        print('pausing before next acquisition')
        time.sleep(40)
    
    
    plt.figure(figsize=(8,12))
    plt.plot(adcdata_all[0])
    plt.title('ph ch0')
    plt.show() 
    
    plt.figure(figsize=(8,12))
    plt.plot(adcdata_all[1])
    plt.title('ph ch0')
    plt.show()
    
    with open('ph_1_hr_set_2_fresh_chip_pH9.npy', 'wb') as f:
        np.save(f, np.asarray(adcdata_all))
    


if __name__ == "__main__":
    fname = None
    Measure(fname = fname)

    
