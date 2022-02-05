# -*- coding: utf-8 -*-
"""


@author: Pushkaraj Joshi
"""
import h5py
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
from datetime import datetime


f5 = r"\\files.brown.edu\Research\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_image_sweep\Dec_5_2021\pH_5_sweep_image.h5"
f6 = r"\\files.brown.edu\Research\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_image_sweep\Dec_5_2021\pH_6_sweep_image.h5"
f7 = r"\\files.brown.edu\Research\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_image_sweep\Dec_5_2021\pH_7_sweep_image.h5"
f8 = r"\\files.brown.edu\Research\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_image_sweep\Dec_5_2021\pH_8_sweep_image.h5"
f9 = r"\\files.brown.edu\Research\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\pH_image_sweep\Dec_5_2021\pH_9_sweep_image.h5"

files=[f5,f6,f7,f8,f9]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Get_Data(logname, exp_name, dataname='image'):
    hf = h5py.File(logname, 'r')
    grp_data = hf.get(exp_name)
    image = grp_data[dataname][:]
    return image    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
# def Get_Attr(logname, exp_name, attrname):
#     hf = h5py.File(logname, 'r')
#     grp_data = hf.get(exp_name)
#     return grp_data.attrs[attrname]
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
# def Get_Time(logname, exp_name):
#     return datetime.strptime(Get_Attr(logname, exp_name, 'timestamp'), "%Y%m%d_%H%M%S")
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
ph_delta_ratio_noedge=np.empty((5,3))
stdev_delta_ratio_noedge=np.empty((5,3))
ph_ratio_noedge=np.empty((5,3))
stdev_ratio_noedge=np.empty((5,3))
ph_delta_noedge=np.empty((5,3))
stdev_delta_noedge=np.empty((5,3))
ph=np.empty((5,5))
stdev=np.empty((5,5))
ph_noedge=np.empty((5,5))
stdev_noedge=np.empty((5,5))
j=0
for f in files:
    
    list_pH = Get_List(f,filterstring='pH_')
#    print('\n\n pH datasets: \n\n',list_pH)
    row_data=np.zeros((512,5))
    for i,mydataset in enumerate(list_pH):
        
#        print("\n #%u/%u: %s \n" % (i,len(list_pH)-1,mydataset))
        
        # read the data
        myimage = Get_Data(f,
                       mydataset,
                       dataname='image_2d_ph1')
        
#        plt.imshow(myimage)
#        plt.show()
        
#        row_data[:,i]=np.transpose(np.mean(myimage,axis=1)) #For plotting average of each row 
        # ph_noedge[j][i] = np.mean(myimage[17:496,17:240]) # Remove the edge rows (16) and columns (16)
        # stdev_noedge[j][i]= np.std(myimage[17:496,17:240]) # Remove the edge rows (16) and columns (16)
        # ph[j][i] = np.mean(myimage) 
        # stdev[j][i]= np.std(myimage)
        if(i==1):
           base_image=myimage
           
           n=0
        if(i>=1 and i<4):
           ph_delta=myimage-base_image
           ph_delta_noedge[j][n]=np.mean(ph_delta[17:496,17:240])
           stdev_delta_noedge[j][n]=np.std(ph_delta[17:496,17:240])
           
           ph_ratio=myimage/base_image
           ph_ratio_noedge[j][n]=np.mean(ph_ratio[17:496,17:240])
           stdev_ratio_noedge[j][n]=np.std(ph_ratio[17:496,17:240])
           
           ph_delta_ratio=(myimage-base_image)/base_image
           ph_delta_ratio_noedge[j][n]=np.mean(ph_delta_ratio[17:496,17:240])
           stdev_delta_ratio_noedge[j][n]=np.std(ph_delta_ratio[17:496,17:240])
           
           n+=1
    
    # plt.figure(figsize=(12,9))  #For plotting average of each row 
    # plt.plot(row_data)
    # plt.xlabel('Rows')
    # plt.ylabel('mean output (V)')
    # plt.show()

#        print("j %u.. i...%u  pH_mean%f" % (j,i,np.mean(myimage)))
    j+=1
    
#print(ph)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Plot for the delta operator

vg_delta=np.arange(1050,1200,50) #Range of Vg applied (V_electode bias)

plt.figure(figsize=(12,9))
plt.errorbar(vg_delta, ph_delta_noedge[0], yerr=stdev_delta_noedge[0], label='pH=5', marker='o',markersize=10)
plt.errorbar(vg_delta, ph_delta_noedge[1], yerr=stdev_delta_noedge[1], label='pH=6', marker='s',markersize=10)
plt.errorbar(vg_delta, ph_delta_noedge[2], yerr=stdev_delta_noedge[2], label='pH=7', marker='<',markersize=10)
plt.errorbar(vg_delta, ph_delta_noedge[3], yerr=stdev_delta_noedge[3], label='pH=8', marker='>',markersize=10)
plt.errorbar(vg_delta, ph_delta_noedge[4], yerr=stdev_delta_noedge[4], label='pH=9', marker='^',markersize=10)
plt.title('ph sweep_noedge_delta_operator')
plt.legend(loc=(0,1))
plt.ylabel('Output (dV)')
plt.xlabel('Vgs (mV)')
plt.show() 
       

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Plot for the Ratio operator

vg_ratio=np.arange(1050,1200,50) #Range of Vg applied (V_electode bias)

plt.figure(figsize=(12,9))
plt.errorbar(vg_ratio, ph_ratio_noedge[0], yerr=stdev_ratio_noedge[0], label='pH=5', marker='o',markersize=10)
plt.errorbar(vg_ratio, ph_ratio_noedge[1], yerr=stdev_ratio_noedge[1], label='pH=6', marker='s',markersize=10)
plt.errorbar(vg_ratio, ph_ratio_noedge[2], yerr=stdev_ratio_noedge[2], label='pH=7', marker='<',markersize=10)
plt.errorbar(vg_ratio, ph_ratio_noedge[3], yerr=stdev_ratio_noedge[3], label='pH=8', marker='>',markersize=10)
plt.errorbar(vg_ratio, ph_ratio_noedge[4], yerr=stdev_ratio_noedge[4], label='pH=9', marker='^',markersize=10)
plt.title('ph sweep_noedge_ratio_operator')
plt.legend(loc=(0,1))
plt.ylabel('Output (V/Vo)')
plt.xlabel('Vgs (mV)')
plt.show() 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Plot for the Delta_Ratio operator

vg_delta_ratio=np.arange(1050,1200,50) #Range of Vg applied (V_electode bias)

plt.figure(figsize=(12,9))
plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[0], yerr=stdev_delta_ratio_noedge[0], label='pH=5', marker='o',markersize=10)
plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[1], yerr=stdev_delta_ratio_noedge[1], label='pH=6', marker='s',markersize=10)
plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[2], yerr=stdev_delta_ratio_noedge[2], label='pH=7', marker='<',markersize=10)
plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[3], yerr=stdev_delta_ratio_noedge[3], label='pH=8', marker='>',markersize=10)
plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[4], yerr=stdev_delta_ratio_noedge[4], label='pH=9', marker='^',markersize=10)
plt.title('ph sweep_noedge_delta_ratio_operator')
plt.legend(loc=(0,1))
plt.ylabel('Output (V-Vo)/Vo')
plt.xlabel('Vgs (mV)')
plt.show() 

# vg=np.arange(1000,1250,50) #Range of Vg applied (V_electode bias)

# plt.figure(figsize=(12,9))
# plt.errorbar(vg, ph[0], yerr=stdev[0], label='pH=5', marker='o',markersize=10)
# plt.errorbar(vg, ph[1], yerr=stdev[1], label='pH=6', marker='s',markersize=10)
# plt.errorbar(vg, ph[2], yerr=stdev[2], label='pH=7', marker='<',markersize=10)
# plt.errorbar(vg, ph[3], yerr=stdev[3], label='pH=8', marker='>',markersize=10)
# plt.errorbar(vg, ph[4], yerr=stdev[4], label='pH=9', marker='^',markersize=10)
# plt.title('ph sweep_entire_image')
# plt.legend()
# plt.ylabel('Output (V)')
# plt.xlabel('Vgs (mV)')
# plt.show() 

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# # Plot without edge

# plt.figure(figsize=(12,9))
# plt.errorbar(vg, ph_noedge[0], yerr=stdev_noedge[0], label='pH=5', marker='o',markersize=10)
# plt.errorbar(vg, ph_noedge[1], yerr=stdev_noedge[1], label='pH=6', marker='s',markersize=10)
# plt.errorbar(vg, ph_noedge[2], yerr=stdev_noedge[2], label='pH=7', marker='<',markersize=10)
# plt.errorbar(vg, ph_noedge[3], yerr=stdev_noedge[3], label='pH=8', marker='>',markersize=10)
# plt.errorbar(vg, ph_noedge[4], yerr=stdev_noedge[4], label='pH=9', marker='^',markersize=10)
# plt.title('ph sweep_without_edge')
# plt.legend()
# plt.ylabel('Output (V)')
# plt.xlabel('Vgs (mV)')
# plt.show() 
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# # pH_sensitivity at fixed V_electrode_Bias

# ph_values=[5.3,6.3,7.3,8.3,9.5] # True values of pH
# plt.figure(figsize=(12,9))
# plt.errorbar(ph_values,ph[:,3:4],yerr=stdev[:,3:4],label='entire_image', marker='o',markersize=10)  #V_bias=1050mV
# plt.errorbar(ph_values,ph_noedge[:,3:4],yerr=stdev_noedge[:,3:4],label='no_edge', marker='s',markersize=10)  #V_bias=1050mV
# plt.ylabel('Output (V)')
# plt.xlabel('pH')
# plt.legend()
# plt.title('pH_sensitivity')

# z = np.polyfit(ph_values, ph[:,3:4], 1)
# z=np.squeeze(z)
# p = np.poly1d(z)
# plt.plot(ph_values,p(ph_values),"b--")
# # the line equation:
# print ("y=%.6fx+(%.6f)"%(z[0],z[1]))
# #plt.show()

# z1 = np.polyfit(ph_values, ph_noedge[:,3:4], 1)
# z1=np.squeeze(z1)
# p1 = np.poly1d(z1)
# plt.plot(ph_values,p1(ph_values),"r--")
# # the line equation:
# print ("y=%.6fx+(%.6f)"%(z1[0],z1[1]))
# plt.show()