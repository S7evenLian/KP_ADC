# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 15:46:06 2021

@author: labuser
"""

import numpy as np
import matplotlib.pyplot as plt
from random import randrange
from datetime import datetime

## pick temeprature points ## 
temperature = np.array((15,20,25,30,35,40,45,50))
VCM = 300

T_map_phi1 = np.zeros(len(temperature))
T_map_phi2 = np.zeros(len(temperature))

for i in range(len(temperature)):
    T = temperature[i]
    fname = 'data/temperature/image_ph1_T'+str(T)+'_VCM'+str(VCM)+'.npy'
    T_map_phi1[i] = np.mean(np.load(fname))
    fname = 'data/temperature/image_ph2_T'+str(T)+'_VCM'+str(VCM)+'.npy'
    T_map_phi2[i] = np.mean(np.load(fname))

## get readings for certain pixels ##
chip_readout_average = (T_map_phi1 + T_map_phi2)/2*1000/4*(-1)

## plot figure ##
plt.figure(figsize=(10,9))
plt.plot(temperature,chip_readout_average, linewidth=4) 
plt.xticks(fontsize=30)
plt.yticks(fontsize=30)
plt.grid()
plt.savefig('data/temperature/readout_vs_temperature.pdf')
plt.title('Temperature Plot, VCM='+str(VCM))
plt.xlabel('Temperature (\N{DEGREE SIGN}C)')
plt.ylabel('Current (nA)')
plt.show()

## 2-point calibration ##
T_pt1 = 20
T_pt2 = 45

pixel_readout_calib= np.zeros(2)
coeff = np.zeros(2)
T_expected = np.zeros(chip_readout_average.shape)

x1 = np.where(temperature == T_pt1)[0]
x2 = np.where(temperature == T_pt2)[0]

pixel_readout_calib = np.hstack((chip_readout_average[x1],chip_readout_average[x2]))
coeff = np.polyfit(np.array((T_pt1,T_pt2)),pixel_readout_calib,1)

print(coeff)

#################### measure temperature drift ############################
fname = 'data/temperature/temperature_drift_overnight_time_stamp.npy'
Time_stamp = np.load(fname)
T_map_phi1 = np.zeros(len(Time_stamp))
T_map_phi2 = np.zeros(len(Time_stamp))
T_drift = 25

for i in range(len(Time_stamp)):
    fname = 'data/temperature/image_ph1_T'+str(T_drift)+'_VCM'+str(VCM)+'_drift_'+str(int(Time_stamp[i]))+'s.npy' # add 'overnight_time_stamp'
    T_map_phi1[i] = np.mean(np.load(fname))
    fname = 'data/temperature/image_ph2_T'+str(T_drift)+'_VCM'+str(VCM)+'_drift_'+str(int(Time_stamp[i]))+'s.npy'# add'overnight_time_stamp'
    T_map_phi2[i] = np.mean(np.load(fname))

## get readings for certain pixels ##
chip_readout_average = (T_map_phi1 + T_map_phi2)/2*1000
pixel_readout_t = np.divide(chip_readout_average, coeff[0])
Time_stamp = Time_stamp-43

# ## plot figure ##
plt.figure(figsize=(10,9))
plt.plot(Time_stamp/60,pixel_readout_t-np.mean(pixel_readout_t), linewidth=4)
plt.grid()
plt.xticks(fontsize=30)
plt.yticks(fontsize=30)
plt.savefig('data/temperature/temperature_drift_3h.pdf')
plt.title('Temperature Drift Plot, VCM='+str(VCM))
plt.xlabel('Time (min)')
plt.ylabel('Temperature Drift Error (\N{DEGREE SIGN}C)')
plt.show()

# plt.figure(figsize=(6,6))
# pixel_readout_t = np.divide(pixel_readout, slope_mean)
# #pixel_readout_t_error = pixel_readout_t - np.reshape(np.mean(pixel_readout_t,axis=1),(pixel_cnt,-1))
# for i in range(pixel_cnt):
#     plt.plot(Time_stamp,pixel_readout_t[i,:]-np.mean(pixel_readout_t[i,:])) # , label = [str(int(pixle_x[i]))+','+str(int(pixle_y[i]))]
    
# plt.title('Temperature Drift Plot, T = 25\N{DEGREE SIGN}C, VCM='+str(VCM))
# plt.grid()
# plt.xlabel('Time (s)')
# plt.ylabel('Temperature Drift Error (\N{DEGREE SIGN}C)')
# plt.show() 