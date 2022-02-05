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
from scipy.optimize import curve_fit

f1 = r"R:\Single_Pixel\PT6- chip\Vref_reset_set3_24_hr.h5"
f2 = r"R:\Single_Pixel\PT6- chip\Vref_reset_set2_3_hr.h5"
files=[f1,f2]
#files=[f5,f6,f7,f8,f9]

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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    


# for f in files:
for f in files:
    
    list_pH = Get_List(f,filterstring='pH_')
    print('\n\n pH datasets: \n\n',len(list_pH))
    
    
    Vo_delta=np.empty((len(list_pH)-1))
    stdev_Vo_delta=np.empty((len(list_pH)-1))
    
    # Vo_delta_noedge=np.empty((len(list_pH)-1))
    # stdev_Vo_delta_noedge=np.empty((len(list_pH)-1))
    
    # Vo_delta_noedge_100=np.empty((len(list_pH)-1))
    # stdev_Vo_delta_noedge_100=np.empty((len(list_pH)-1))
    
    
    row_data=np.zeros((512,len(list_pH)))
    # row_data_ratio=np.zeros((512,len(list_pH)))
    # row_Vo_diff=np.zeros((479,223))

    for i,mydataset in enumerate(list_pH):
        
        # print("\n #%u/%u: %s \n" % (i,len(list_pH)-1,mydataset))
        if(i==0):
            t0=Get_Time(f,mydataset)
    
        
        # read the data
            
            myimage = Get_Data(f,
                       mydataset,
                       dataname='image_2d_ph1')
        # myimage_mod=myimage[17:496,17:240]
        # pH=myimage/0.030
        # pH=pH-np.mean(pH)
            V_SW = Get_Attr(f,mydataset,'V_SW')
            V_CM = Get_Attr(f,mydataset,'V_CM')
            V_REF = Get_Attr(f,mydataset,'V_Electrode_Bias')
    #        plt.imshow(myimage)
    #        plt.show()
        
        
        # ph_noedge[j][i] = np.mean(myimage[17:496,17:240]) # Remove the edge rows (16) and columns (16)
        # stdev_noedge[j][i]= np.std(myimage[17:496,17:240]) # Remove the edge rows (16) and columns (16)
        
            base_image=myimage
        
    # #       plt.imshow(base_image)
            n=0
            time_points=[]
            time_points.insert(0,0)
        if(i>=1 and i<len(list_pH)):
            mytime= Get_Time(f, mydataset)
            myimage = Get_Data(f,
                       mydataset,
                       dataname='image_2d_ph1')
            # time_points.append(mytime-t0)
            t=Get_Time(f,mydataset)
            time_points.append((t-t0).total_seconds()/60)
            # print(time_points[i])
            
            delta=myimage-base_image
            Vo_delta[n]=np.mean(delta)
            stdev_Vo_delta[n]=np.std(delta)
            row_data[:,i]=np.transpose(np.mean(delta,axis=1)) #For plotting average of each row 
            # Vo_delta_noedge[n]=np.mean(delta[17:496,17:240])
            # stdev_Vo_delta_noedge[n]=np.std(delta[17:496,17:240])
            # row_data[:,i]=np.transpose(np.mean(Vo_delta,axis=1)) #For plotting average of each row 
    #        ph_ratio=myimage/base_image
    #        ph_ratio_noedge[n]=np.mean(ph_ratio[17:496,17:240])
    #        stdev_ratio_noedge[n]=np.std(ph_ratio[17:496,17:240])
    #        np.zeros((512,len(list_pH)))
           # ph_delta_ratio=(myimage-base_image)/base_image
           # ph_delta_ratio_noedge[j][n]=np.mean(ph_delta_ratio[17:496,17:240])
           # stdev_delta_ratio_noedge[j][n]=np.std(ph_delta_ratio[17:496,17:240])
             # row_data_ratio[:,i]=np.transpose(np.mean(ph_ratio,axis=1)) #For plotting average of each row
            n+=1
        # row_Vo_diff=np.transpose(np.mean(delta,axis=1)) #For pH differentail in a chip
        # plt.plot(row_Vo_diff)
        # plt.show()
    
    #        print("j %u.. i...%u  pH_mean%f" % (j,i,np.mean(myimage)))
    
        
    #print(ph)
    
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #Plot for the delta operator
    
    # time=np.arange(0,3600,10) #Range of Vg applied (V_electode bias)
    # vg_delta.pop(0)
    # time=np.arange(5,60,5)
    Vo_delta=np.insert(Vo_delta,0,0)
    stdev_Vo_delta=np.insert(stdev_Vo_delta,0,0)
    # Vo_delta_noedge=np.insert(Vo_delta_noedge,0,0)
    # stdev_Vo_delta_noedge=np.insert(stdev_Vo_delta_noedge,0,0)
    plt.figure(figsize=(12,9))
    plt.errorbar(time_points, Vo_delta, yerr=stdev_Vo_delta, label='Whole_image', marker='o',markersize=10)
    # plt.errorbar(time_points, Vo_delta_noedge, yerr=stdev_Vo_delta_noedge, label='Without_edge', marker='o',markersize=10)
    # plt.errorbar(vg_delta, ph_delta_noedge[2], yerr=stdev_delta_noedge[2], label='pH=7', marker='<',markersize=10)
    # plt.errorbar(vg_delta, ph_delta_noedge[3], yerr=stdev_delta_noedge[3], label='pH=8', marker='>',markersize=10)
    # plt.errorbar(vg_delta, ph_delta_noedge[4], yerr=stdev_delta_noedge[4], label='pH=9', marker='^',markersize=10)
    plt.title(" V_CM=%u V_SW=%u V_REF=%u " %  
                                            (V_CM,
                                            V_SW,
                                            V_REF),
                                            fontsize=25)
    plt.legend(loc=2,fontsize=18)
    plt.ylabel('Output (dV)',fontsize=25)
    plt.xlabel('time (min)',fontsize=25)
    plt.ylim(-0.175,0.05)
    plt.tick_params(axis='both',labelsize=20)
    
    # z = np.polyfit(time_points, Vo_delta, 1)
    # z=np.squeeze(z)
    # p = np.poly1d(z)
    # plt.plot(time_points,p(time_points),"b--")
    # # the line equation:
    # print ("y=%.6fx+(%.6f)"%(z[0],z[1]))
    #plt.show()
    
# plt.savefig("R:\Single_Pixel\Combined_image.jpeg")
plt.show()        
#~~~~~~~~~~~Attempt to for sigmoid curve~~~~~~~~~~
# def func(x, p1,p2):
#   return p1*np.cos(p2*x) + p2*np.sin(p1*x)

# a=0.02
# b=0.10
# popt, pcov = curve_fit(func, vg_delta, stdev_delta_noedge,p0=(a,b))

# p1=popt[0]
# p2=popt[1]
# plt.plot(vg_delta, func(vg_delta,p1,p2),'r--',label='pH_9_fit')

#~~~~~~~~~~~Noise curve~~~~~~~~~
# plt.plot(vg_delta, stdev_delta_noedge, marker='s', markersize=10, label='pH_9')
# plt.title('Noise_pH_sweep_delta_operator')
# plt.legend(loc=(0,1))
# plt.ylabel('Noise (V)')
# plt.xlabel('Vgs (mV)')

#~~~~~~~~~~Linear fit before the saturation region~~~~~~~
# z = np.polyfit(vg_delta[:10], stdev_delta_noedge[:10], 1)
# z=np.squeeze(z)
# p = np.poly1d(z)
# plt.plot(vg_delta[:10],p(vg_delta[:10]),"b--")
# # the line equation:
# print ("y=%.6fx+(%.6f)"%(z[0],z[1]))
# plt.show()

#~~~~~~~~~Plotting row averages for delta operator each voltage bias~~~~
plt.figure(figsize=(12,9))  #For plotting average of each row 
plt.plot(row_data)
plt.xlabel('Rows')
plt.ylabel('mean output (dV)')
plt.title('Row means_delta_operator')
plt.show()

#~~~~~~~~~Plotting row averages for raatio operator each voltage bias~~~~
# plt.figure(figsize=(12,9))  #For plotting average of each row 
# plt.plot(row_data_ratio)
# plt.xlabel('Rows')
# plt.ylabel('mean output (V/V0)')
# plt.title('Row means_ratio_operator')
# plt.show()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Plot for the Ratio operator

# vg_ratio=np.arange(1000,1190,10) #Range of Vg applied (V_electode bias)

# plt.figure(figsize=(12,9))
# plt.errorbar(vg_ratio, ph_ratio_noedge, yerr=stdev_ratio_noedge, label='pH=5', marker='o',markersize=10)
# # plt.errorbar(vg_ratio, ph_ratio_noedge[1], yerr=stdev_ratio_noedge[1], label='pH=6', marker='s',markersize=10)
# # plt.errorbar(vg_ratio, ph_ratio_noedge[2], yerr=stdev_ratio_noedge[2], label='pH=7', marker='<',markersize=10)
# # plt.errorbar(vg_ratio, ph_ratio_noedge[3], yerr=stdev_ratio_noedge[3], label='pH=8', marker='>',markersize=10)
# # plt.errorbar(vg_ratio, ph_ratio_noedge[4], yerr=stdev_ratio_noedge[4], label='pH=9', marker='^',markersize=10)
# plt.title('ph sweep_noedge_ratio_operator')
# plt.legend(loc=(0,1))
# plt.ylabel('Output (V/Vo)')
# plt.xlabel('Vgs (mV)')
# plt.show() 

# plt.plot(vg_delta,stdev_ratio_noedge,label='pH=9', marker='s',markersize=10)
# plt.title('Noise_ph sweep_noedge_ratio_operator')
# plt.legend(loc=(0,1))
# plt.ylabel('Noise (V)')
# plt.xlabel('Vgs (mV)')
# plt.show() 

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# #Plot for the Delta_Ratio operator

# vg_delta_ratio=np.arange(1050,1200,50) #Range of Vg applied (V_electode bias)

# plt.figure(figsize=(12,9))
# plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[0], yerr=stdev_delta_ratio_noedge[0], label='pH=5', marker='o',markersize=10)
# plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[1], yerr=stdev_delta_ratio_noedge[1], label='pH=6', marker='s',markersize=10)
# plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[2], yerr=stdev_delta_ratio_noedge[2], label='pH=7', marker='<',markersize=10)
# plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[3], yerr=stdev_delta_ratio_noedge[3], label='pH=8', marker='>',markersize=10)
# plt.errorbar(vg_delta_ratio, ph_delta_ratio_noedge[4], yerr=stdev_delta_ratio_noedge[4], label='pH=9', marker='^',markersize=10)
# plt.title('ph sweep_noedge_delta_ratio_operator')
# plt.legend(loc=(0,1))
# plt.ylabel('Output (V-Vo)/Vo')
# plt.xlabel('Vgs (mV)')
# plt.show() 

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