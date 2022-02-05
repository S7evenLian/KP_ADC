# -*- coding: utf-8 -*-
"""
Created on Sat Sep  4 19:40:49 2021

@author: ChrisTow
"""
import numpy as np
import matplotlib.pyplot as plt

f5 = "../minerva_sensor/data/pH/ph5_sweep.npy"
f6 = "../minerva_sensor/data/pH/ph6_sweep.npy"
f7 = "../minerva_sensor/data/pH/ph7_sweep.npy"
f8 = "../minerva_sensor/data/pH/ph8_sweep.npy"
f9 = "../minerva_sensor/data/pH/ph9_sweep.npy"

with open(f5, 'rb') as f:
    adc_ph5 = np.load(f)
    
with open(f6, 'rb') as f:
    adc_ph6 = np.load(f)
    
with open(f7, 'rb') as f:
    adc_ph7 = np.load(f)
    
with open(f8, 'rb') as f:
    adc_ph8 = np.load(f)
    
with open(f9, 'rb') as f:
    adc_ph9 = np.load(f)
    
ph5_start_ind = 16150
ph6_start_ind = 6750
ph7_start_ind = 4820
ph8_start_ind = 3000
ph9_start_ind = 100

l = 10000
vg = np.linspace(0.4,1.4,10000)
    
ph5 = adc_ph5[1::8][ph5_start_ind:ph5_start_ind+l]
ph6 = adc_ph6[1::8][ph6_start_ind:ph6_start_ind+l]
ph7 = adc_ph7[1::8][ph7_start_ind:ph7_start_ind+l]
ph8 = adc_ph8[1::8][ph8_start_ind:ph8_start_ind+l]
ph9 = adc_ph9[1::8][ph9_start_ind:ph9_start_ind+l]

plt.figure(figsize=(12,9))
plt.plot(vg, ph5, label='pH=5')
plt.plot(vg, ph6, label='pH=6')
plt.plot(vg, ph7, label='pH=7')
plt.plot(vg, ph8, label='pH=8')
plt.plot(vg, ph9, label='pH=9')
plt.title('ph sweep')
plt.xlim(0.6,1.08)
plt.legend()
plt.ylabel('Output (V)')
plt.xlabel('Vg (V)')
plt.show() 