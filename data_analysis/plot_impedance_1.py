#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: jacobrosenstein
"""

# -*- coding: utf-8 -*-

import h5py
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
from datetime import datetime
from itertools import chain

#os.chdir(r"R:\projects\minerva")

#from run_files import Check_connection
#from run_files import Measure
#from run_files import Decode

import imageio



logdir = r"/Users/jacobrosenstein/Dropbox/HyBiScIs_data/Larkin Lab Data/Minerva_test_08272021/h5"
lognames = ['D0002_minerva_biofilm_M5.h5',]
#lognames = ['D0002_minerva_biofilm_1.h5',]


mycolormap='Blues'
#mycolormap='viridis'




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Get_Data(logname, exp_name, dataname='image'):
    hf = h5py.File(logname, 'r')
    grp_data = hf.get(exp_name)
    image = grp_data[dataname][:]
    return image    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
def Get_Attr(logname, exp_name, attrname):
    hf = h5py.File(logname, 'r')
    grp_data = hf.get(exp_name)
    return grp_data.attrs[attrname]
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
def Get_Time(logname, exp_name):
    return datetime.strptime(Get_Attr(logname, exp_name, 'timestamp'), "%Y%m%d_%H%M%S")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    




for lognum,logname in enumerate(lognames):

    fullname = os.path.join(logdir,logname)
    
    list_all = Get_List(fullname,sortby='time')
    print('\n\nall\n\n',list_all)
    
    list_impedance = Get_List(fullname,filterstring='impedance')
    print('\n\nimpedance\n\n',list_impedance)
    
    if(lognum==0):
        t0 = Get_Time(fullname,list_impedance[0])
    
    
    
    # plot images
    if(lognum==0):
        myframes=[]
        colonysizes=[[],]*4
        startindex=1
        endindex=len(list_all)
        image_1_ref=None

    for i in range(startindex,endindex,1):

        if 'impedance_' in list_all[i]:        

            V_SW = Get_Attr(fullname,list_all[i],'V_SW')
            V_CM = Get_Attr(fullname,list_all[i],'V_CM')
            f_sw = Get_Attr(fullname,list_all[i],'f_sw')
            T_int = Get_Attr(fullname,list_all[i],'T_int')
            C_int = Get_Attr(fullname,list_all[i],'C_int')
            
            gain_swcap = np.abs(V_SW-V_CM)*1e-3*f_sw  # Iout/Cin
            gain_integrator = T_int/C_int  # Vout/Iin
            gain_overall = gain_swcap*gain_integrator

        
        
        
        
            image_2d_ph1 = Get_Data(fullname,
                                    list_all[i],
                                    dataname='image_2d_ph1')
            image_2d_ph2 = Get_Data(fullname,
                                    list_all[i],
                                    dataname='image_2d_ph2')
            
            #image_1 = image_1[100:350,100:200]


            image_2d_ph1 = image_2d_ph1 / gain_overall
            image_2d_ph2 = image_2d_ph2 / gain_overall

            normrows = range(200,300)
                
            # normalize by channel
            def normalize_by_channel(image):
                ch0mean = np.mean(image[normrows, :32])
                for ch in range(8):
                    image[:, ch*32:(ch+1)*32] = image[:, ch*32:(ch+1)*32] / np.mean(image[normrows, ch*32:(ch+1)*32]) * ch0mean
                image = np.abs(image)
                return image
            image_2d_ph1 = normalize_by_channel(image_2d_ph1)
            image_2d_ph2 = normalize_by_channel(image_2d_ph2)    
    
            # ~~~~~~~~~~~~~~~~~~
            # remove outliers
            def remove_outliers(data,Nstd=5):
                med=np.median(np.ravel(data))
                std=np.std(np.ravel(data))
                data[np.abs(data-med)>(Nstd*std)] = med
                return data
            image_2d_ph1 = remove_outliers(image_2d_ph1)
            image_2d_ph2 = remove_outliers(image_2d_ph2)    
            # ~~~~~~~~~~~~~~~~~~
            
            # re-normalize again
            image_2d_ph1 = normalize_by_channel(image_2d_ph1)
            image_2d_ph2 = normalize_by_channel(image_2d_ph2)    
    
    
    
    
            image_1 = image_2d_ph2
            
            if image_1_ref is None:
                image_1_ref = image_1
                continue
            #image_1 = image_1-image_1_ref
        
            tx = Get_Time(fullname,list_all[i])
            
            # subtract first image as a baseline
            #image_1 = image_1 - image_1_ref
            
            # subtract top row as baseline
            #for c in range(512):
            #    image_1[c,:] = image_1[c,:] - np.median(image_1[c,:])
        
            fig = plt.figure(figsize=(12,6))
            grid = plt.GridSpec(3, 3, hspace=0.2, wspace=0.2)
            ax_main = fig.add_subplot(grid[:, :])
            mycolormap='Blues'    #'Blues_r' #'Greys_r'
            
                
            im1 = ax_main.imshow(np.flip(np.transpose(image_1),axis=1), #-np.median(image_1)), # [50:100,:40]),
                                vmin=np.mean(image_1[normrows,:])-4*np.std(image_1[normrows,:]), 
                                vmax=np.mean(image_1[normrows,:])+1*np.std(image_1[normrows,:]), 
                                cmap=mycolormap)
            fig.colorbar(im1,ax=ax_main)
            ax_main.set_title(str(lognum) + '   ' + str(i) + '   ' + list_all[i] + ' time elapsed ' + str(tx-t0))
            
            plt.show()
            
            # add to frames for animation
            fig.canvas.draw()       # draw the canvas, cache the renderer
            im = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
            im  = im.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            myframes.append(im)


plotdir = os.path.join(logdir,'plots')
if(not os.path.exists(plotdir)):
    os.mkdir(plotdir)
    

# create animation
if 0:
    imageio.mimsave(os.path.join(plotdir,logname+'_1a.gif'), 
                    myframes, fps=10)


if 0:
    # create .mp4 video file
    imageio.mimsave(os.path.join(plotdir,logname+'_1b.mp4'), 
                    myframes, fps=10)


 
