#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 18:57:51 2021

@author: jacobrosenstein
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

vdd=2.0
f_sw=50e6
samplerate=390625
V_SW=700
V_CM=600
V_Electrode_Bias=600
V_STBY=600


C_int = 5e-12


noswitching=np.empty([8,200000])
withswitching=np.empty([8,200000])
for ch in range(8):
    with open('../minerva_sensor/data/noise/ch%u_no_switching.npy' % (ch,),'rb') as f:
        noswitching[ch,:] = np.load(f)
    with open('../minerva_sensor/data/noise/ch%u_with_switching.npy' % (ch,),'rb') as f:
        withswitching[ch,:] = np.load(f)


###################
# assume gain is still wrong by factor of 2
noswitching=noswitching*2
withswitching=withswitching*2
###################


for ch in range(1):
    f,Pxx_output = scipy.signal.welch(withswitching[ch,:], 
                               fs=samplerate, 
                               window='hann', 
                               nperseg=None, 
                               noverlap=None, 
                               nfft=2**16, 
                               detrend='constant', 
                               return_onesided=True, 
                               scaling='density', 
                               axis=- 1, average='mean')
    
    # discard DC term
    f = f[1:]
    Pxx_output = Pxx_output[1:]
    
    gain_integrator = 1 / (2*np.pi*f *  C_int)   # Vout/Iin
    gain_swcap = np.abs(V_SW-V_CM)*1e-3 *f_sw    # Iout/Cin
    
    
    Pxx_current = Pxx_output / gain_integrator**2
    Pxx_capacitance = Pxx_current / gain_swcap**2
    
    
    rms_current = np.sqrt(np.cumsum(Pxx_current))
    rms_capacitance = np.sqrt(np.cumsum(Pxx_capacitance))
    
    
    
    
    trange=np.arange(1000)
    plt.plot(trange/samplerate,withswitching[0,trange],'.')
    plt.plot(trange/samplerate,noswitching[0,trange],'.')
    plt.xlabel('time (sec)')
    plt.show()
    
    plt.loglog(f,Pxx_output)
    plt.title('output referred PSD (V^2/Hz)')
    plt.grid(which='major')
    plt.show()
    
    plt.loglog(f,Pxx_current)
    plt.title('input referred PSD (A^2/Hz)')
    plt.grid(which='major')
    plt.show()

    plt.loglog(f,np.sqrt(Pxx_current))
    plt.title('input referred noise spectrum (A/sqrt(Hz))')
    plt.grid(which='major')
    plt.show()
    
    
    plt.figure(figsize=(12,4),)
    plt.subplot(1,2,1)
    plt.loglog(f,rms_current)
    plt.title('current RMS (amperes), assume C_int=%2.2f pF' % (C_int*1e12))    
    plt.grid(which='major')
    plt.yticks(10.0**np.arange(-16,-7))
    plt.xlabel('bandwidth (1/T_ramp)')
    plt.ylabel('RMS current (Amperes_rms)')
    
    plt.subplot(1,2,2)    
    plt.loglog(f,rms_capacitance)
    plt.title('capacitance RMS (farads), assume C_int=%2.2f pF' % (C_int*1e12))
    plt.grid(which='major')
    plt.yticks(10.0**np.arange(-22,-13))
    plt.xlabel('bandwidth (1/T_ramp)')
    plt.ylabel('RMS capacitance (Farads_rms)')
    plt.show()
