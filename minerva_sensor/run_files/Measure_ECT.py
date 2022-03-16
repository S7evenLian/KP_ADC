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

def Measure(fname=None,ect_pairs=[(1,1),]):
    
    print('Measuring ECT Image...')
    
    
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

    m.pset('PINOUT_CONFIG',1)    # Minerva_v1 = 0; Minerva_v2 = 1; Sidewinder_v1 = 2
    
    # todo: DOUBLE CHECK
    m.pset('Nsamples_integration', 3)
    m.pset('T_int',m.pget('Nsamples_integration')/m.pget('samplerate'))
    m.pset('C_int',5e-12)
    
    # DAC Settings
    m.pset('V_SW', 350)
    m.pset('V_CM', 350)    
    m.pset('V_Electrode_Bias', 350)
    m.pset('V_STIMU_P', 0)
    m.pset('V_STIMU_N', 0)   
    m.pset('V_STBY', 300)
    
   
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
    
    
    for k,(row_offset,col_offset) in enumerate(ect_pairs):
        
        print('\n\nRunning ECT #%u/%u, offset (%u,%u)' % (k+1,len(ect_pairs),row_offset,col_offset))
        m.pset('row_offset',row_offset)
        m.pset('col_offset',col_offset)
        
        scan_all_mea_ECT = m.Generate_scan_vector_mea_ECT(row_offset=row_offset,
                                                  col_offset=col_offset)

        
        # ~~~~~~~~~~~~~~~~~ Reset ADC FIFO ~~~~~~~~~~~~~~~~~~~~~~~
    #    m.SendScanVector_4bit(scan_all_close_sram)
    #    time.sleep(0.1)
    #    m.SendScanVector_4bit(vector_reset)
    #    time.sleep(0.1)
        #m.SendRawVector(vector_reset_deselect)
        #time.sleep(0.1)
        
        m.SendRawVector(vector_reset)
        time.sleep(0.02)

        #m.FIFO_Reset()
        m.StopADC()
        numtransfers,xferbytes = m.QueueADCAcquisition(sec=6)
        m.StartADC()
            
        # measure impedance
        m.UpdateScanChain(scan_all_mea_ECT)
        time.sleep(1)        
        
        # ~~~~~~~~~~~~~~~~~ Acquire ADC Data ~~~~~~~~~~~~~~~~~~~~~~~    
        m.WaitForDMA(numtransfers)
        
        m.StopADC()
            
        mydata,mybytes = m.GetDataFromMemory(xferbytes)
        print('acquired data')
        print('bytes',mybytes)
        
        dtest_1 = np.array(np.bitwise_and(mydata[::8],   np.uint32(1<<31)),dtype=np.bool).astype(np.int32)
        scan_latch = np.array(np.bitwise_and(mydata[::8],np.uint32(1<<27)),dtype=np.bool).astype(np.int32)
        
        adcdata1 = np.bitwise_and(mydata, np.uint32(0x0003FFFF)).astype(np.uint32)   #keep 18 bits
        adcdata2 = np.bitwise_or(adcdata1, (adcdata1&0x00020000 != 0) * np.uint32(0xFFFC0000))       #sign extension from 18 bits
        adcdata = 2*3.3*adcdata2.view(np.int32)/2**18    # view as signed integer, scale to volts
    
            
        sample_clk=dtest_1
    
        scan_latch_deri = np.diff(scan_latch)
        scan_latch_edge_all_index = np.where(scan_latch_deri == 1)[0]
        
        # the first 8 latch is to set the pixl sensing mode
        start_ind = scan_latch_edge_all_index[-1] - 10
        
        # acquire data for each channel to assemble the impeance image, split to 2 images for two phases
        image_2d_ph1 = np.zeros((512,256))
        image_2d_ph2 = np.zeros((512,256))
        
        
        for ch in range(8):
    #    ch = 0
            
            adcdata_1_ch = adcdata[ch::8]
            adcdata_1_ch = adcdata_1_ch[start_ind:]
            sample_clk_1_ch = sample_clk[start_ind:]
            
            sample_clk_deri = np.diff(sample_clk_1_ch)
            sample_clk_edge_all_index = np.where(sample_clk_deri == -1)[0]    
         
            # calculate the data,
            data_1_ch = adcdata_1_ch[sample_clk_edge_all_index-m.pget('Nsamples_integration')] - adcdata_1_ch[sample_clk_edge_all_index]
            data_1_ch = data_1_ch[0:16*32*512]
            
    #        for i in sample_clk_edge_all_index[10:12]:
    #            plt.figure(figsize=(12,4))
    #            span=min(100,i-1)
    #            plt.plot(np.arange(-span,span),adcdata_1_ch[i-span:i+span],'k')
    #            plt.plot(-3,adcdata_1_ch[i-3],'.r',markersize=10)
    #            plt.plot(0,adcdata_1_ch[i],'.b',markersize=10)
    #            plt.title('ch=%u, i=%u, f_sw=%u' % (ch,i,m.pget('f_sw')))
    #            plt.show()
                
            # drop the first and last data and average every 14 data points
            data_1_ch_avg = data_1_ch.reshape(-1, 16)
            data_1_ch_avg = data_1_ch_avg[:,1:-1]
            
            data_1_ch_avg_ph1 = np.mean(data_1_ch_avg[:,0::2], axis=1)
            data_1_ch_avg_ph2 = np.mean(data_1_ch_avg[:,1::2], axis=1)
            
            # reshape
            image_2d_ph1[:, ch*32:(ch+1)*32] = data_1_ch_avg_ph1.reshape(512, 32)  
            image_2d_ph2[:, ch*32:(ch+1)*32] = data_1_ch_avg_ph2.reshape(512, 32)
        
#        plt.figure(figsize=(8,12))
#        plt.plot(adcdata[0::8])
#        plt.title('adcdata 1')
#        plt.show() 
        
    #    plt.figure(figsize=(8,12))
    #    plt.imshow(image_2d_ph1)
    #    plt.title('impedance image ph1')
    #    plt.colorbar()
    #    plt.show() 
    #    
    #    plt.figure(figsize=(8,12))
    #    plt.imshow(image_2d_ph2)
    #    plt.title('impedance image ph2')
    #    plt.colorbar()
    #    plt.show() 
    #    
    #    with open('data/impedance/image_ph1.npy','wb') as f:
    #        np.save(f, image_2d_ph1)
    #
    #    with open('data/impedance/image_ph2.npy','wb') as f:
    #        np.save(f, image_2d_ph2)
    
        
        grp_name = 'ECT'
        m.SaveToLogFile(fname,
                        grp_name,
                        dataset_names=('image_2d_ph1','image_2d_ph2'),
                        datasets=(image_2d_ph1,image_2d_ph2),
                        comments='') 
        
        # fix column alignment ECT offset
        coloffset=5
        for ch in range(8):
            image_2d_ph1[:, ch*32:(ch+1)*32] = image_2d_ph1[:, ch*32+np.mod(-coloffset + np.arange(32),32)]
            image_2d_ph2[:, ch*32:(ch+1)*32] = image_2d_ph2[:, ch*32+np.mod(-coloffset + np.arange(32),32)]


        # normalize by channel
        ch0mean = np.mean(image_2d_ph1[-16:, :32])
        for ch in range(8):
            image_2d_ph1[:, ch*32:(ch+1)*32] = image_2d_ph1[:, ch*32:(ch+1)*32] / np.mean(image_2d_ph1[-16:, ch*32:(ch+1)*32]) * ch0mean / gain_overall
            image_2d_ph2[:, ch*32:(ch+1)*32] = image_2d_ph2[:, ch*32:(ch+1)*32] / np.mean(image_2d_ph2[-16:, ch*32:(ch+1)*32]) * ch0mean / gain_overall
        image_2d_ph1 = np.abs(image_2d_ph1)
        image_2d_ph2 = np.abs(image_2d_ph2)
        
        plt.figure(figsize=(16,8))
        plt.subplot(1,2,1)
        plt.imshow(image_2d_ph1,
                   vmin=np.mean(image_2d_ph1)-3*np.std(image_2d_ph1),
                   vmax=np.mean(image_2d_ph1)+1*np.std(image_2d_ph1),
                   cmap='Blues')               
        plt.title('ECT (%u,%u) phase1 (normalized, Farads)' % (row_offset,col_offset) )
        plt.colorbar()
        
        plt.subplot(1,2,2)
        plt.imshow(image_2d_ph2,
                   vmin=np.mean(image_2d_ph2)-3*np.std(image_2d_ph2),
                   vmax=np.mean(image_2d_ph2)+1*np.std(image_2d_ph2),
                   cmap='Blues')
        plt.title('ECT (%u,%u) phase2 (normalized, Farads)' % (row_offset,col_offset) )
        plt.colorbar()
        plt.show() 
    
        plt.figure(figsize=(8,8))
        plt.imshow(image_2d_ph2[350:450,150:250],
                   vmin=np.mean(image_2d_ph2)-3*np.std(image_2d_ph2),
                   vmax=np.mean(image_2d_ph2)+1*np.std(image_2d_ph2),
                   cmap='Blues')
        plt.title('ECT (%u,%u) phase2 (normalized, Farads)' % (row_offset,col_offset) )
        plt.colorbar()
        plt.show() 
        
    #    plt.figure(figsize=(8,4))
    #    plt.plot(image_2d_ph2[250,:])
    #    plt.title('row slice')
    #    plt.show() 
    #    
    #    plt.figure(figsize=(8,4))
    #    plt.plot(image_2d_ph2[:,75])
    #    plt.title('col slice')
    #    plt.show() 
    #    
    #    plt.figure(figsize=(8,4))
    #    def autocorr(x):
    #        return np.correlate(x-np.mean(x),x-np.mean(x),mode='full')
    #    plt.plot(autocorr(image_2d_ph2[:,75]))
    #    plt.title('col correlation')
    #    plt.show() 
        
    
    #    plt.figure(figsize=(8,8))
    #    plt.imshow(correlate2d(image_2d_ph2,image_2d_ph2))
    #    plt.title('2D correlation')
    #    plt.colorbar()
    #    plt.show()     



if __name__ == "__main__":
    
    #print('5 sec delay')
    
#    for loop in range(1000):
    print('measure')
    
    fname = r"C:\Users\larki\Documents\minerva_data\F0095_09022021_minerva_biofilm_M7_ECT.h5"
    #fname = r"X:\EmbeddedBioelectronics\projects\Minerva\data\D0001_yeast\yeast_revisit_ECT_6b.h5"
    
    import itertools
    ect_pairs = list(itertools.product(range(-4,5,2),range(-4,5,2)))

    print('Running ECT for offsets:',ect_pairs)    
    Measure(fname=fname,
            ect_pairs=ect_pairs)
    
#    print('sleeping')
#    time.sleep(60)
    
