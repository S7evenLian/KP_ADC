# -*- coding: utf-8 -*-
"""
Created on Sun Jan 30 21:28:17 2022

@author: Pushkaraj Joshi
"""
import h5py
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
from datetime import datetime
import imageio
from skimage.filters import median, gaussian

mycolormap='Blues'

# pH_5 = r'R:/Eng_Projects/EmbeddedBioelectronics/projects/Minerva/data/pH_image_biofilm/Jan_12_2022/F0159_01122022\expt_Jan_12_2022_1.h5'
pH_6 = r"R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_calib\V_ref-1000mV\pH_6.h5"
pH_7 = r"R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_calib\V_ref-1000mV\pH_7.h5"
pH_8 = r"R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_calib\V_ref-1000mV\pH_8.h5"
pH_9 = r"R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_calib\V_ref-1000mV\pH_9.h5"
pH_10 = r"R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_calib\V_ref-1000mV\pH_10.h5"
files=[pH_6,pH_7,pH_8,pH_9,pH_10]
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Get_Data(logname, exp_name, dataname='image_2d_ph1'):
    hf = h5py.File(logname, 'r')
    grp_data = hf.get(exp_name)
    image = grp_data[dataname][:]
    return image    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
def Get_Attr(logname, exp_name, attrname):
    hf = h5py.File(logname, 'r')
    grp_data = hf.get(exp_name)
    return grp_data.attrs[attrname]
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
def Get_Time(logname, exp_name):
    return datetime.strptime(Get_Attr(logname, exp_name, 'timestamp'), "%Y%m%d_%H%M%S")
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
def Get_List(logname,filterstring=None,sortby=None):
    hf = h5py.File(logname, 'r')
    base_items = list(hf.items())
    grp_list = []
    for i in range(len(base_items)):
        grp = base_items[i]
        grp_list.append(grp[0])
    if filterstring is not None:
        grp_list = [x for x in grp_list if filterstring in x]
    if sortby is 'time':
        grp_list = sorted(grp_list,key=lambda x: Get_Time(logname,x))
    return grp_list	
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vo=[]
# base_image=
for f in files:
    exp = Get_List(f,filterstring='impedance')
    hf = h5py.File(f, 'r')
    grp_data = hf.get(exp)
    pH_image = grp_data['image_2d_ph1'][:]
   
    # plt.imshow(pH_image,cmap=mycolormap)
    
    