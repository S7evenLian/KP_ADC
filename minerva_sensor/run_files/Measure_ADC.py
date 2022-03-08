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

def Measure():
    
    print('Measuring Impedance Image...')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    # Parameter Definitions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    bitfilename = None   #use default
    
    # create antelope daq instance
    m = minerva(bitfilename=bitfilename)

    # board setup
    f_sw = 1e5
    f_master = f_sw / 30 / 2
    m.pset('Vdd', 1.8)
    m.pset('f_sw', f_sw)
    # m.pset('f_master', 390625)
    m.pset('f_master', f_master)
    m.pset('samplerate', f_master*2)
    m.pset('vectorfrequency', 1.25e6) #12.5e6)
    m.pset('ADCbits', 18)
    m.pset('ADCfs', 3.3)
    
    m.pset('PINOUT_CONFIG',2)    # Minerva_v1 = 0; Minerva_v2 = 1; Sidewinder_v1 = 2

    # todo: DOUBLE CHECK
    m.pset('Nsamples_integration', 3)
    m.pset('T_int',m.pget('Nsamples_integration')/m.pget('samplerate'))
    m.pset('C_int',5e-12)
    
    # DAC Settings
    m.pset('V_SW', 0)    
    m.pset('V_CM', 900)     # steven mod to 900mV for ADC biasing
    m.pset('V_Electrode_Bias', 1500)
    m.pset('V_STIMU_P', 1500)   # the same as in the simulation
    m.pset('V_STIMU_N', 300)    # the same as in the simulation
    m.pset('V_STBY', 0)
    
    
    gain_swcap = 1  
    gain_integrator = m.pget('T_int')/m.pget('C_int')  # Vout/Iin
    gain_overall = gain_swcap*gain_integrator
    
    
    # Others
    m.pset('Row_Code_Clk', '6.1 kHz')
    m.pset('Col_Code_Clk', '23.8 Hz')
    m.pset('Chopping_Clk', '400 kHz')
    
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

    # ~~~~~~~~~~~~~~~~~ Send in scanchain ~~~~~~~~~~~~~~~~~~~~~~~
    # wait for Kangping to modify scan-chain
    scan_chain_update = m.Generate_scan_vector_KP_ADC()
    m.UpdateScanChain(scan_chain_update, resetpulse = True, latchenable = True)
    
    # scan_in shared with ADC_CAL_RST
    m.ProtectScanPins(False)
    
    # ~~~~~~~~~~~~~~~~~ Reset ADC FIFO ~~~~~~~~~~~~~~~~~~~~~~~
#    m.SendRawVector(vector_reset_deselect)
    time.sleep(0.1)
    
    # ~~~~~~~~~~~~~~~~~ Output Clocks for chip ~~~~~~~~~~~~~~~~~~~~~~~
    m.StartClkout()
    
    #m.FIFO_Reset()
    m.StopADC()
    numtransfers,xferbytes = m.QueueADCAcquisition(sec=6)
    m.StartADC()
    
    # ~~~~~~~~~~~~~~~~~ give sample_en waveform ~~~~~~~~~~~~~~~~~~~~~~~
    adc_clk_f = f_sw
    for i in range(100):
        m.ADC_Sampling(adc_clk_f)
        time.sleep(0.01)
        
    # measure impedance
#    m.UpdateScanChain(scan_all_mea_I)
    time.sleep(1)        
    
    # ~~~~~~~~~~~~~~~~~ Acquire ADC Data ~~~~~~~~~~~~~~~~~~~~~~~    
    m.WaitForDMA(numtransfers)
        
    mydata,mybytes = m.GetDataFromMemory(xferbytes)
    print('acquired data')
    print('bytes',mybytes)
    
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
#    adcdata = 2*3.3*adcdata2.view(np.int32)/2**18    # view as signed integer, scale to volts
#
#        
#    sample_clk=dtest_1
#
#    scan_latch_deri = np.diff(scan_latch)
#    scan_latch_edge_all_index = np.where(scan_latch_deri == 1)[0]



if __name__ == "__main__":
    
    #print('5 sec delay')
    
    Measure()
    
