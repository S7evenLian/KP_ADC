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

def Run(pattern, pulse_period, duty, duration, fname=None):
    
    print('Start Resisive Heating')
    
    
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
    m.pset('V_STIMU_P', 2000)
    m.pset('V_STIMU_N', 0)   
    m.pset('V_STBY', 0)
    
    # stimulation setting
    m.pset('pattern', pattern)
    m.pset('pulse_period', pulse_period)
    
    
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
        
        # set the sensing mode for each col
        print('\rgenerating scan vector for col %u   (%2.2f sec)' % (col_addr,time.time()-tstart),end='')
        scan_all_set_stimu_mode = m.Generate_scan_vector_pixel_stimu_mode_arbitrary_pattern(pattern[:,col_addr], col_addr)        
        m.UpdateScanChain(scan_all_set_stimu_mode)  # send as 32 bit vector
        time.sleep(0.02)
        
    print('')
    
    # enable the voltage stimulation
    scan_all_V_stimu = m.Generate_scan_vector_voltage_stimu()
    m.UpdateScanChain(scan_all_V_stimu)  # send as 32 bit vector


    # pulse STIMU_CLK_P and STIMU_CLK_N in a software loop
    stimduration = duration #seconds
    stimstart = time.time()
    while time.time()-stimstart < stimduration:
#        print('stimulation pulsing (%2.2f sec)' % (time.time()-stimstart,))
        m.GPIO_Set(120,True,update_all=True)  # STIMU_CLK_P = 1
        m.GPIO_Set(123,True,update_all=True)  # STIMU_CLK_N = 1
        time.sleep(pulse_period*duty)
        
        m.GPIO_Set(120,False,update_all=True)  # STIMU_CLK_P = 0
        m.GPIO_Set(123,False,update_all=True)  # STIMU_CLK_N = 0        
        time.sleep(pulse_period*(1-duty))


if __name__ == "__main__":
    print('stimulation')
    # define the stimulation pattern
    pattern = np.zeros((512, 256))
    pattern[25:26,60:110] = 1
    pattern[30:34,60:110] = 1
    pattern[40:50,60:110] = 1
    pattern[70:90,60:110] = 1
    pattern[110:150,60:110] = 1
    pattern[180:260,60:110] = 1
    pattern[320:480,60:110] = 1

    pattern[25:26,150:200] = 1
    pattern[30:34,150:200] = 1
    pattern[40:50,150:200] = 1
    pattern[70:90,150:200] = 1
    pattern[110:150,150:200] = 1
    pattern[180:260,150:200] = 1
    pattern[320:480,150:200] = 1
    
    # plt.imshow(pattern)
    
    pulse_period = 1 # set the pulsing period in s
    duty = 0.5
    duration = 10 # in sec
    Run(pattern, pulse_period, duty, duration, fname=None)
    
