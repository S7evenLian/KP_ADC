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

def Run(block_size, V_stimu, pulse_period, fname=None):
    
    print('Start Voltage Stimulation')
    
    
    if fname is None:
        fname = r"X:\EmbeddedBioelectronics\projects\Minerva\data\D0001_yeast\yeast_4.h5"
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    # Parameter Definitions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    bitfilename = None   #use default
    
    # create antelope daq instance
    m = minerva(bitfilename=bitfilename)

    # board setup
    m.pset('Vdd', 2.15)
    m.pset('f_sw', 390625*16)
    m.pset('f_master', 390625)
    m.pset('samplerate', 390625)
#    m.pset('vectorfrequency', 390625) #12.5e6)
    m.pset('vectorfrequency', 1.25e6) #12.5e6)
    m.pset('ADCbits', 18)
    m.pset('ADCfs', 3.3)

    # todo: DOUBLE CHECK
    m.pset('T_int',4/m.pget('samplerate'))
    m.pset('C_int',5e-12)

    m.pset('PINOUT_CONFIG',1)    # Minerva_v1 = 0; Minerva_v2 = 1; Sidewinder_v1 = 2
    
    # DAC Settings
    m.pset('V_SW', 0)
    m.pset('V_CM', 0)    
    m.pset('V_Electrode_Bias', 0)
    m.pset('V_STIMU_P', V_stimu)
    m.pset('V_STIMU_N', 0)   
    m.pset('V_STBY', 0)
    
    
    gain_swcap = np.abs(m.pget('V_STBY')-m.pget('V_CM'))*1e-3*m.pget('f_sw')  # Iout/Cin
    gain_integrator = m.pget('T_int')/m.pget('C_int')  # Vout/Iin
    gain_overall = gain_swcap*gain_integrator
    
    
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
    # use internal 3.55V reference
    m.DAC_setup(INTREF=True)

    # ~~~~~~~~~~~~~~~~~ Output Clocks for chip ~~~~~~~~~~~~~~~~~~~~~~~
    m.StartClkout()

    # ~~~~~~~~~~~~~~~~~ Send in scanchain ~~~~~~~~~~~~~~~~~~~~~~~
    #m.SendRawVector(scan_all_int)
    
    m.ProtectScanPins(False)
    # this scan vector will set the measurement mode for test col pixels and trigger DTEST_1 Toggle
    
    # ~~~~~~~~~~~~~~~~~ Set the sensing mode ~~~~~~~~~~~~~~~~~~~~~~~    
    tstart=time.time()
    for col_addr in range(256):   
        
        # set the sensing mode
        print('\rgenerating scan vector for col %u   (%2.2f sec)' % (col_addr,time.time()-tstart),end='')    
        if (int(col_addr/block_size) % 2) == 0:
            scan_all_set_stimu_mode = m.Generate_scan_vector_pixel_stimu_mode_checkerboard(block_size, 'even', col_addr)
        else:
            scan_all_set_stimu_mode = m.Generate_scan_vector_pixel_stimu_mode_checkerboard(block_size, 'odd', col_addr)
        
        m.UpdateScanChain(scan_all_set_stimu_mode)  # send as 32 bit vector
        time.sleep(0.02)
    print('')
    
    # enable the voltage stimulation
    scan_all_V_stimu = m.Generate_scan_vector_voltage_stimu()
    m.UpdateScanChain(scan_all_V_stimu)  # send as 32 bit vector


    # pulse STIMU_CLK_P and STIMU_CLK_N in a software loop
    stimduration = 5*60 #seconds
    stimstart = time.time()
    while time.time()-stimstart < stimduration:
#        print('stimulation pulsing (%2.2f sec)' % (time.time()-stimstart,))
        m.GPIO_Set(120,True,update_all=True)  # STIMU_CLK_P = 1
        time.sleep(pulse_period/2)
        m.GPIO_Set(120,False,update_all=True)  # STIMU_CLK_P = 0
        m.GPIO_Set(123,True,update_all=True)  # STIMU_CLK_N = 1
        time.sleep(pulse_period/2)
        m.GPIO_Set(123,False,update_all=True)  # STIMU_CLK_N = 0        


if __name__ == "__main__":
    print('stimulation')
    block_size = 32 # size can be any of 2^n
    V_stimu = 1800 # stimulate voltage ranges from 0-3550mV
    pulse_period = 5 # set the pulsing period in s
    Run(block_size, V_stimu, pulse_period)
    
