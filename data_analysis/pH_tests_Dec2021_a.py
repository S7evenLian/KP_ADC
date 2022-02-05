# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""





import numpy as np
import matplotlib.pyplot as plt



V = np.load(r"R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\Single_Pixel\ph_1_hr_repeat_3_pH9.npy")


# V = V[:101,:]   #limit to first 100pts


V_means = np.mean(V,axis=1)


# plt.plot(V_means)
# plt.ylabel('average output V')
# plt.savefig("R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\Single_Pixel\set_3_pH9_raw.jpeg")
# plt.show()


# plt.plot(V_means-V_means[0])
# plt.ylabel('average output delta-V')
# plt.savefig("R:\Eng_Projects\EmbeddedBioelectronics\projects\Minerva\data\Single_Pixel\set_3_pH9_delta.jpeg")

time=list(np.arange(0,60,1))
plt.plot(time,V_means)
plt.ylabel('Average output Voltage (Volts)')
plt.xlabel('Time (min)')
plt.savefig("R:\Single_Pixel\set_1_pH9_fresh_chip_raw.jpeg")
plt.show()


plt.plot(time,(V_means-V_means[0]))
plt.ylabel('Average output delta-V (Volts)')
plt.xlabel('Time (min)')
plt.savefig("R:\Single_Pixel\set_1_pH9_fresh_chip_delta.jpeg")

plt.show()

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



