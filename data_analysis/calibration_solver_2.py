#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 14:01:00 2021

@author: jacobrosenstein
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize


    
with open('../minerva_sensor/data/impedance/image_ph1.npy','rb') as f:
    image_ph1 = np.load(f)

with open('../minerva_sensor/data/impedance/image_ph2.npy','rb') as f:
    image_ph2 = np.load(f)

image_ph1 = np.abs(image_ph1)
image_ph2 = np.abs(image_ph2)



def apply_cal(image,coeffs):
    assert(len(coeffs)==8)
    image_cal = image.copy()
    for ch in range(8):
        image_cal[:,ch*32:(ch+1)*32] = image_cal[:,ch*32:(ch+1)*32] * coeffs[ch]
    return image_cal

def eval_mismatch(image,verbose=False,channels=None):
    grad=0
    if channels is None:
        channels = range(1,8)
        
    for ch in channels:
        err = np.abs(np.sum(image[:,ch*32]) - np.sum(image[:,ch*32-1]))
        grad = grad + err
        if verbose:
            print('ch',err)
    return grad

def auto_cal(image,initialcoeffs=np.ones(8)):
    coeffs=initialcoeffs
    
    def apply_cal_and_eval_mismatch(image,coeffs,ch,newcoeff):
        coeffs[ch]=newcoeff
        image_cal = apply_cal(image,coeffs)
        return eval_mismatch(image_cal,channels=[ch,])
    
    for ch in range(1,8):
        res = minimize(lambda onecoeff: apply_cal_and_eval_mismatch(image,coeffs,ch,onecoeff), 
                       coeffs[ch],
                       method = 'Nelder-Mead',
                       options={'disp': True, 'xatol': 1e-6})
        coeffs[ch] = res.x
    return apply_cal(image,coeffs),coeffs
        
        
        
image_ph1=image_ph1[-256:,:]
image_ph2=image_ph2[-256:,:]

initialcoeffs = np.ones(8)
#initialcoeffs[1:] = initialcoeffs[1:] + 0.1*np.random.rand(7)
image_cal_ph1,coeffs1 = auto_cal(image_ph1,initialcoeffs)
image_cal_ph2,coeffs2 = auto_cal(image_ph2,initialcoeffs)

print('new coeffs')
print(coeffs1)
print(coeffs2)

cmap='Blues'
plt.figure(figsize=(18,9))
plt.subplot(1,4,1)
plt.imshow(image_ph1,
           vmin=np.mean(image_ph1)-3*np.std(image_ph1),
           vmax=np.mean(image_ph1)+2*np.std(image_ph1),
           cmap=cmap)
plt.colorbar(orientation="horizontal")
plt.title('ph1')
plt.subplot(1,4,2)
plt.imshow(image_ph2,
           vmin=np.mean(image_ph2)-3*np.std(image_ph2),
           vmax=np.mean(image_ph2)+2*np.std(image_ph2),
           cmap=cmap)
plt.colorbar(orientation="horizontal")
plt.title('ph2')
plt.subplot(1,4,3)
plt.imshow(image_cal_ph1,
           vmin=np.mean(image_cal_ph1)-3*np.std(image_cal_ph1),
           vmax=np.mean(image_cal_ph1)+2*np.std(image_cal_ph1),
           cmap=cmap)
plt.colorbar(orientation="horizontal")
plt.title('ph1 after auto-cal')
plt.subplot(1,4,4)
plt.imshow(image_cal_ph2,
           vmin=np.mean(image_cal_ph2)-3*np.std(image_cal_ph2),
           vmax=np.mean(image_cal_ph2)+2*np.std(image_cal_ph2),
           cmap=cmap)
plt.colorbar(orientation="horizontal")
plt.title('ph2 after auto-cal')
plt.show()



