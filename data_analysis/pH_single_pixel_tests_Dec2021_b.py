# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""





import numpy as np
import matplotlib.pyplot as plt


f1 = np.load(r"R:\Single_Pixel\PT6- chip\set-1\ph_1_hr.npy")
f1=f1[:101]
f2= np.load(r"R:\Single_Pixel\PT6- chip\set-2\ph_1_hr_repeat_pH9.npy")
f2=f2[:101]
f3= np.load(r"R:\Single_Pixel\PT6- chip\set-3\ph_1_hr_repeat_3_pH9.npy")
f4= np.load(r"R:\Single_Pixel\ph_1_hr_set_1_fresh_chip_pH9.npy")

# V = V[:101,:]   #limit to first 100pts
V1=V2=V3=V4=[]
t1=t2=t3=t4=[]
files=[f1,f2,f3,f4]
V_means = [V1,V2,V3,V4]
time=[t1,t2,t3,t4]
for i,f in enumerate(files):
    if(i<2):
        
        V_means[i] = np.mean(f,axis=1)
        time[i]=list(np.arange(0,len(f)/3,1/3))
        plt.plot(time[i],(V_means[i]-V_means[i][0]), label='Set-'+str(i+1))
        plt.ylabel('Average output delta-V (Volts)')
        plt.xlabel('Time (min)')
        plt.legend(loc=0)
        # plt.plot(time,V_means)
        # plt.ylabel('Average output Voltage (Volts)')
        # plt.xlabel('Time (min)')
        # plt.savefig("R:\Single_Pixel\set_1_pH9_fresh_chip_raw.jpeg")
        # plt.show()
        
    else:
        V_means[i] = np.mean(f,axis=1)
        time[i]=list(np.arange(0,len(f),1))
        plt.plot(time[i],(V_means[i]-V_means[i][0]), label='Set-'+str(i+1))
        
        # plt.plot(time,(V_means[i]-V_means[i][0]))
        plt.ylabel('Average output delta-V (Volts)')
        plt.xlabel('Time (min)')
        plt.legend(loc=0)
plt.savefig("R:\Single_Pixel\Combined.jpeg")
plt.show()
#---------------------------------------------------------------------------#
# R = 5e3  #guess

# I_means = V_means/R


# plt.plot(I_means)
# plt.ylabel('average I')
# plt.show()





# gm_time_R = 1   #guess

# pH_means = V_means/gm_time_R


# plt.plot(pH_means - pH_means[0])
# plt.ylabel('average delta pH')
# plt.show()



