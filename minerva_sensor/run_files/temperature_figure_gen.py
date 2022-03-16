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

T_map_phi1 = np.zeros([len(temperature),512,256])
T_map_phi2 = np.zeros([len(temperature),512,256])

for i in range(len(temperature)):
    T = temperature[i]
    fname = 'data/temperature/image_ph1_T'+str(T)+'_VCM'+str(VCM)+'.npy'
    T_map_phi1[i] = np.load(fname)
    fname = 'data/temperature/image_ph2_T'+str(T)+'_VCM'+str(VCM)+'.npy'
    T_map_phi2[i] = np.load(fname)

## randomly pick some pixels to plot ##
pixel_cnt = 50
pixle_x = np.zeros(pixel_cnt)
pixle_y = np.zeros(pixel_cnt)

for i in range(pixel_cnt):
    pixle_x[i] = randrange(512)
    pixle_y[i] = randrange(256)


## get readings for certain pixels ##
pixel_readout = np.zeros((pixel_cnt,len(temperature)))

for i in range(len(temperature)):
    for j in range(pixel_cnt):
        x = int(pixle_x[j])
        y = int(pixle_y[j])
        pixel_readout[j,i] = (T_map_phi1[i,x,y] + T_map_phi2[i,x,y])/2*1000


## plot figure ##
plt.figure(figsize=(6,6))
for i in range(pixel_cnt):
    plt.plot(temperature,pixel_readout[i,:]) # , label = [str(int(pixle_x[i]))+','+str(int(pixle_y[i]))]
    
plt.title('Temperature [15C:50C] VCM='+str(VCM))
plt.legend()
plt.grid()
plt.xlabel('Temperature (\N{DEGREE SIGN}C)')
plt.ylabel('Pixel Readout (mV)')
plt.show() 


## 2-point calibration ##
T_pt1 = 20
T_pt2 = 45

pixel_readout_calib= np.zeros([pixel_cnt,2])
coeff = np.zeros([pixel_cnt,2])
T_expected = np.zeros(pixel_readout.shape)

x1 = np.where(temperature == T_pt1)[0]
x2 = np.where(temperature == T_pt2)[0]


pixel_readout_calib = np.hstack((pixel_readout[:,x1],pixel_readout[:,x2]))

for i in range(pixel_cnt):
    coeff[i,:] = np.polyfit(np.array((T_pt1,T_pt2)),pixel_readout_calib[i,:],1)
    T_expected[i,:] = np.polyval(coeff[i,:],temperature)

error = np.divide((pixel_readout - T_expected), np.reshape(coeff[:,0],(pixel_cnt,-1)))

sigma_3_up = np.mean(error,axis=0) + 3*np.std(error,axis=0)
sigma_3_down = np.mean(error,axis=0) - 3*np.std(error,axis=0)

## plot error ##
plt.figure(figsize=(6,6))
for i in range(pixel_cnt):
    plt.plot(temperature,error[i,:])

plt.plot(temperature,sigma_3_up,'r--',label ='3 sigma')
plt.plot(temperature,sigma_3_down,'r--')
plt.title('Temperature Error, VCM='+str(VCM))
plt.legend()
plt.grid()
plt.xlabel('Temperature (\N{DEGREE SIGN}C)')
plt.ylabel('Error(\N{DEGREE SIGN}C)')
plt.show() 


## calculate slope for resolution ##
slope_mean = np.mean(coeff[:,0])

print('slope mean = ',slope_mean)

######### 2nd order master curve fitting #########
error_coeff = np.zeros([pixel_cnt,3])
error_trimmed = np.zeros(error.shape)

error_mean = np.mean(error,axis=0)
error_coeff = np.polyfit(temperature,error_mean,2)
error_expected = np.polyval(error_coeff,temperature)

## trimming ##
for i in range(pixel_cnt):
    error_trimmed[i,:] = error[i,:] - error_expected

sigma_3_trimmed_error_up = np.mean(error_trimmed,axis=0) + 3*np.std(error_trimmed,axis=0)
sigma_3_trimmed_error_down = np.mean(error_trimmed,axis=0) - 3*np.std(error_trimmed,axis=0)

## plot error ##
plt.figure(figsize=(6,6))
for i in range(pixel_cnt):
    plt.plot(temperature,error_trimmed[i,:])

plt.plot(temperature,sigma_3_trimmed_error_up,'r--',label ='3 sigma')
plt.plot(temperature,sigma_3_trimmed_error_down,'r--')
plt.title('Temperature Error(After 2nd order master curve fitting), VCM='+str(VCM))
plt.legend()
plt.grid()
plt.xlabel('Temperature (\N{DEGREE SIGN}C)')
plt.ylabel('Trimmed Error(\N{DEGREE SIGN}C)')
plt.show() 


#################### measure temperature drift ############################
fname = 'data/temperature/temperature_drift_time_stamp.npy'
Time_stamp = np.load(fname)
T_map_phi1 = np.zeros([len(Time_stamp),512,256])
T_map_phi2 = np.zeros([len(Time_stamp),512,256])
T_drift = 25

for i in range(len(Time_stamp)):
    fname = 'data/temperature/image_ph1_T'+str(T_drift)+'_VCM'+str(VCM)+'_drift_'+str(int(Time_stamp[i]))+'s.npy' # add 'overnight_time_stamp'
    T_map_phi1[i] = np.load(fname)
    fname = 'data/temperature/image_ph2_T'+str(T_drift)+'_VCM'+str(VCM)+'_drift_'+str(int(Time_stamp[i]))+'s.npy'# add'overnight_time_stamp'
    T_map_phi2[i] = np.load(fname)

## randomly pick some pixels to plot ##
pixel_cnt = 50
pixle_x = np.zeros(pixel_cnt)
pixle_y = np.zeros(pixel_cnt)

for i in range(pixel_cnt):
    pixle_x[i] = randrange(512)
    pixle_y[i] = randrange(256)

## get readings for certain pixels ##
pixel_readout = np.zeros((pixel_cnt,len(Time_stamp)))

for i in range(len(Time_stamp)):
    for j in range(pixel_cnt):
        x = int(pixle_x[j])
        y = int(pixle_y[j])
        pixel_readout[j,i] = (T_map_phi1[i,x,y] + T_map_phi2[i,x,y])/2*1000
        
## plot figure ##
plt.figure(figsize=(6,6))
for i in range(pixel_cnt):
    plt.plot(Time_stamp,pixel_readout[i,:]) # , label = [str(int(pixle_x[i]))+','+str(int(pixle_y[i]))]
    
plt.title('Temperature Drift Plot, VCM='+str(VCM))
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Pixel Readout (mV)')
plt.show() 

plt.figure(figsize=(6,6))
pixel_readout_t = np.divide(pixel_readout, slope_mean)
#pixel_readout_t_error = pixel_readout_t - np.reshape(np.mean(pixel_readout_t,axis=1),(pixel_cnt,-1))
for i in range(pixel_cnt):
    plt.plot(Time_stamp,pixel_readout_t[i,:]-np.mean(pixel_readout_t[i,:])) # , label = [str(int(pixle_x[i]))+','+str(int(pixle_y[i]))]
    
plt.title('Temperature Drift Plot, T = 25\N{DEGREE SIGN}C, VCM='+str(VCM))
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Temperature Drift Error (\N{DEGREE SIGN}C)')
plt.show() 

plt.figure(figsize=(6,6))
pixel_readout_t = np.divide(pixel_readout, slope_mean)
# pixel_readout_t_error = pixel_readout_t - np.reshape(np.mean(pixel_readout_t,axis=1),(pixel_cnt,-1))
for i in range(pixel_cnt):
    pixel_readout_t[i,:] = pixel_readout_t[i,:] - np.mean(pixel_readout_t[i,:])

for i in range(pixel_cnt):
    plt.plot(Time_stamp,np.mean(pixel_readout_t,axis=0))
plt.title('Temperature Drift Plot, T = 25\N{DEGREE SIGN}C, VCM='+str(VCM))
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Temperature Drift Error (\N{DEGREE SIGN}C)')
plt.show() 