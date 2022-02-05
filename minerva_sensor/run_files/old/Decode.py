# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 15:54:04 2019

@author: labuser2
"""

import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
import h5py
from scipy.ndimage import gaussian_filter

# this is for plot the images when load a recorded measurement data
def Plot(logname, exp_name, save=False, save_dir=None):
    
    image = Get_Data(logname,exp_name)
    plt.figure(figsize=(48,16))
    Q1 = np.quantile(image.flatten(),0.25);
    Q3 = np.quantile(image.flatten(),0.75)
    k = 3; #1.5;
    plt.imshow(image, vmax=Q3+k*(Q3-Q1),vmin=Q1-k*(Q3-Q1))
    
#    if 'pH' in exp_name:
#        plt.imshow(image, vmax=2.3,vmin=1.6)
#        
#    if 'Impedance' in exp_name:
#        plt.imshow(image, vmax=14,vmin=10)

    plt.colorbar()
    plt.title(exp_name)
    if save==True:
        fname = save_dir+'/'+exp_name+'.png'
        plt.savefig(fname)
    plt.show()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
# This is for plot the images right after a measurement 
def Plot_Image(chip_ID, grp_name, image):
        
    plt.figure(figsize=(48,16))
    
    if 'pH' in grp_name:
        plt.imshow(image, vmax=2.3,vmin=1.6)
        
    if 'Impedance' in grp_name:
#        plt.imshow(image, vmax=14,vmin=10)
        plt.imshow(image)
    plt.colorbar()    
    plt.title("Chip: " + str(chip_ID) + " -- "+grp_name)
    plt.show()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def Get_Data(logname, exp_name):
    hf = h5py.File(logname, 'r')
    
    grp_data = hf.get(exp_name)
    image = grp_data['image'][:]
    
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
def Print_Attributes(logname, exp_name):
    
    # load data    
    hf = h5py.File(logname, 'r')
    base_items = list(hf.items())
    
    for i in range(len(base_items)):
        grp = base_items[i]
        grp_name = grp[0]
    
        if(grp_name == exp_name):
            for key in grp[1].attrs.keys():
                print(key+": "+str(grp[1].attrs[key]))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
def Composite_Image(image_1, image_2):
    image_3 = np.zeros_like(image_1)
    image_3[0:8,:] =  image_1[0:8,:]
    for k in range(0,511,64):
    
        mean_1 = np.mean(image_1[(k+8):(k+24)])
        mean_2 = np.mean(image_2[(k+8):(k+24)])
        image_1[(k+0):,:] = image_1[(k+0):,:] - (mean_1-mean_2)
        
        mean_1 = np.mean(image_1[(k+40):(k+56)])
        mean_2 = np.mean(image_2[(k+40):(k+56)])
        image_2[(k+32):,:] = image_2[(k+32):,:] - (mean_2-mean_1)
        
        image_3[(k+8):(k+56),:] =  image_1[(k+8):(k+56),:]
        image_3[(k+56):(k+72),:] =  image_2[(k+56):(k+72),:]
        
    return image_3

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Print_Summary(logname):
    
    hf = h5py.File(logname, 'r')
    base_items = list(hf.items())
    
    time_list = []
    
    # count the measurements number
    ph_count = 0
    optical_count= 0
    impedance_count = 0
    
    for i in range(len(base_items)):
        grp = base_items[i]
        grp_name = grp[0]
        
        mode,date,time = grp_name.split('_')
        time_list.append(date+"_"+time)
        
        if 'pH' in mode: ph_count = ph_count + 1
        if 'Impedance' in mode: impedance_count = impedance_count + 1
        if 'Optical' in mode: optical_count = optical_count + 1

    time_sort = sorted(time_list)
        
    print("########## Summary ###########")
    print(logname)
    print("start time: "+time_sort[0])
    print("stop time: "+time_sort[-1])
    print("pH:  "+str(ph_count))
    print("Impedance:  "+str(impedance_count))
    print("Optical:  "+str(optical_count))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Print_List(logname):
       
    grp_list = Get_List(logname)
	
    for i in range(len(grp_list)):    
        print(grp_list[i])
    

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
def Decode_Data(log_in, log_out):

    # load data    
    hf1 = h5py.File(log_in, 'r')
    base_items = list(hf1.items())
    
    # write to a new file
    hf2 = h5py.File(log_out, 'a')
    
    for i in range(len(base_items)):
        grp = base_items[i]
        grp_name = grp[0]
        
        # copy the attritubes
        grp_new = hf2.require_group(grp_name)
        grp_new.attrs.update(grp[1].attrs.items())
        
#        print(grp[1].attrs.items())
        print(grp_name)
        
        #### pH image
        if 'pH' in grp_name:
            
            grp_data = hf1.get(grp_name)
            
            data = grp_data['data'][:]
            latch = np.int64(grp_data['scanlatch'][:])
            
            # fing the index of latch
            latch_deri = np.diff(latch)
            latch_edge_ind_all = np.where(latch_deri == 1)[0]
            
#            print(latch_edge_ind_all[10:20])
            
            # remove the redundant elements
            latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(0,17,1)))
            latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(32768,32768+17,1)))
            latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(32768*2,32768*2+17,1)))
            latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(32768*3,32768*3+17,1)))
                        
            # sanity check
            if(len(latch_edge_ind_all)!=131072):
                print("latch number not correct!")
                print(len(latch_edge_ind_all))
                            
            image = np.zeros((512,256),'float32')
            for row_addr in range(512):
                for col_addr in range(256):
                    start_ind = latch_edge_ind_all[col_addr+row_addr*256] + 20
                    stop_ind = start_ind + 100
                    image[row_addr, col_addr] = np.mean(data[start_ind: stop_ind])
                    
                    
            grp_new.create_dataset('image', data=image)
            
        #### Optical image
        if 'Optical' in grp_name:
            grp_data = hf1.get(grp_name)
            
            data = grp_data['data'][:]
            code_clk = np.int64(grp_data['code_clk'][:])
            latch = np.int64(grp_data['scanlatch'][:])
            image = Decode_CDM_256(data, code_clk, latch)
            
            # adjust the baseline
            image[0:256,:] = image[0:256,:] - (np.mean(image[0:256,:]) - np.mean(image[256:512,:]))
            grp_new.create_dataset('image', data=image)
            
        #### Impedance image
        if 'Impedance' in grp_name:
            
            # get the impedance mode
            try:
                mode = grp[1].attrs['Measure_mode']
            except:
                mode = 1 # legacy support

            grp_data = hf1.get(grp_name)            
            data = grp_data['data'][:]
            code_clk = np.int64(grp_data['code_clk'][:])
            latch = np.int64(grp_data['scanlatch'][:])
            image = Decode_CDM_64(data, code_clk, latch, mode)  
            grp_new.create_dataset('image', data=image)
    
    hf1.close()
    hf2.close()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def Decode_ph(data, latch):
    
    # fing the index of latch
    latch_deri = np.diff(latch)
    latch_edge_ind_all = np.where(latch_deri == 1)[0]
    
#            print(latch_edge_ind_all[10:20])
    
    # remove the redundant elements
    latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(0,17,1)))
    latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(32768,32768+17,1)))
    latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(32768*2,32768*2+17,1)))
    latch_edge_ind_all = np.delete(latch_edge_ind_all, list(range(32768*3,32768*3+17,1)))
                
    # sanity check
    if(len(latch_edge_ind_all)==131072):
        image = np.zeros((512,256),'float32')
        for row_addr in range(512):
            for col_addr in range(256):
                start_ind = latch_edge_ind_all[col_addr+row_addr*256] + 20
                stop_ind = start_ind + 100
                image[row_addr, col_addr] = np.mean(data[start_ind: stop_ind])
                
                
        return image   
    else:
        print("latch number not correct!")
        print(len(latch_edge_ind_all))
        
        return 0
                    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Decode_CDM_64(data, code_clk, latch, mode):
    # find the index of code_clk
    code_clk_deri = np.diff(code_clk)
    code_edge_ind_all = np.where(code_clk_deri == -1)[0]
    
    # find the index of the latch edge
    latch_deri = np.diff(latch)
    latch_edge_ind_all = np.where(latch_deri == 1)[0]
    
    # Generate the decoding matrix
    mat_4  = np.matrix([[-1,1,1,1],[1,-1,1,1],[1,1,-1,1],[1,1,1,-1]])
    mat_16 = np.bmat([[-1*mat_4,mat_4,mat_4,mat_4],[mat_4,-1*mat_4,mat_4,mat_4],[mat_4,mat_4,-1*mat_4,mat_4],[mat_4,mat_4,mat_4,-1*mat_4]])
    mat_64 = np.bmat([[-1*mat_16,mat_16,mat_16,mat_16],[mat_16,-1*mat_16,mat_16,mat_16],[mat_16,mat_16,-1*mat_16,mat_16],[mat_16,mat_16,mat_16,-1*mat_16]])
    mat_256 = np.bmat([[-1*mat_64,mat_64,mat_64,mat_64],[mat_64,-1*mat_64,mat_64,mat_64],[mat_64,mat_64,-1*mat_64,mat_64],[mat_64,mat_64,mat_64,-1*mat_64]])
    
    # the complete data array
    data_avg_512x256 = np.zeros((512,256),'float32')
    
    
    for i in range(1,2049,1):
        
        # the 1-D data array
        data_avg_1D = np.zeros(64, 'float32')
        
        # find the first code clock edge after the latch
        code_edge_ind_1 = np.where(code_edge_ind_all > latch_edge_ind_all[i])[0][0]
        
        # skip the first 10 cycle
        code_edge_ind_2 = code_edge_ind_1 + 10
            
        # average inside each code period
        for j in range(len(data_avg_1D)):
            start_ind = code_edge_ind_all[code_edge_ind_2+j] + 10
            stop_ind = start_ind + 100
            data_avg_1D[j] = np.mean(data[start_ind: stop_ind])
            
        # shift the decode index
        decode_shift = code_edge_ind_2 % 64
        mat_decode = np.roll(mat_64, -decode_shift, axis=0)
        
        # decode the data
        data_avg_64 = np.matmul(data_avg_1D, mat_decode)
        
        # assemble the final image
        k = i - 1
        row_addr = int(k / 256)
        col_addr = int(k % 256)
        
        data_avg_512x256[row_addr*64:(row_addr+1)*64,col_addr] = np.flip(data_avg_64,1)
        
    # rearrange the image for mode 2
    if(mode==2):
        image_tmp = np.zeros(data_avg_512x256.shape)
        image_tmp[0*32:1*32,:]   = data_avg_512x256[14*32:15*32,:]
        image_tmp[1*32:2*32,:]   = data_avg_512x256[1*32:2*32,:]
        image_tmp[2*32:3*32,:]   = data_avg_512x256[0*32:1*32,:]
        image_tmp[3*32:4*32,:]   = data_avg_512x256[3*32:4*32,:]
        image_tmp[4*32:5*32,:]   = data_avg_512x256[2*32:3*32,:]
        image_tmp[5*32:6*32,:]   = data_avg_512x256[5*32:6*32,:]
        image_tmp[6*32:7*32,:]   = data_avg_512x256[4*32:5*32,:]
        image_tmp[7*32:8*32,:]   = data_avg_512x256[7*32:8*32,:]
        image_tmp[8*32:9*32,:]   = data_avg_512x256[6*32:7*32,:]
        image_tmp[9*32:10*32,:]  = data_avg_512x256[9*32:10*32,:]
        image_tmp[10*32:11*32,:] = data_avg_512x256[8*32:9*32,:]
        image_tmp[11*32:12*32,:] = data_avg_512x256[11*32:12*32,:]
        image_tmp[12*32:13*32,:] = data_avg_512x256[10*32:11*32,:]
        image_tmp[13*32:14*32,:] = data_avg_512x256[13*32:14*32,:]
        image_tmp[14*32:15*32,:] = data_avg_512x256[12*32:13*32,:]
        image_tmp[15*32:16*32,:] = data_avg_512x256[15*32:16*32,:]
        
    if(mode==2): return image_tmp
    else: return data_avg_512x256


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Decode_CDM_256(data, code_clk, latch):
    # find the index of code_clk
    code_clk_deri = np.diff(code_clk)
    code_edge_ind_all = np.where(code_clk_deri == -1)[0]
    
    # find the index of the latch edge
    latch_deri = np.diff(latch)
    latch_edge_ind_all = np.where(latch_deri == 1)[0]
    
    # Generate the decoding matrix
    mat_4  = np.matrix([[-1,1,1,1],[1,-1,1,1],[1,1,-1,1],[1,1,1,-1]])
    mat_16 = np.bmat([[-1*mat_4,mat_4,mat_4,mat_4],[mat_4,-1*mat_4,mat_4,mat_4],[mat_4,mat_4,-1*mat_4,mat_4],[mat_4,mat_4,mat_4,-1*mat_4]])
    mat_64 = np.bmat([[-1*mat_16,mat_16,mat_16,mat_16],[mat_16,-1*mat_16,mat_16,mat_16],[mat_16,mat_16,-1*mat_16,mat_16],[mat_16,mat_16,mat_16,-1*mat_16]])
    mat_256 = np.bmat([[-1*mat_64,mat_64,mat_64,mat_64],[mat_64,-1*mat_64,mat_64,mat_64],[mat_64,mat_64,-1*mat_64,mat_64],[mat_64,mat_64,mat_64,-1*mat_64]])
    
    # the complete data array
    data_avg_512x256 = np.zeros((512,256),'float32')
    
    
    for i in range(1,513,1):
        
        # the 1-D data array
        data_avg_1D = np.zeros(256, 'float32')
        
        # find the first code clock edge after the latch
        code_edge_ind_1 = np.where(code_edge_ind_all > latch_edge_ind_all[i])[0][0]
        
        # skip the first 15 cycle
        code_edge_ind_2 = code_edge_ind_1 + 15
            
        # average inside each code period
        for j in range(len(data_avg_1D)):
            start_ind = code_edge_ind_all[code_edge_ind_2+j] + 10
            stop_ind = start_ind + 100
            data_avg_1D[j] = np.mean(data[start_ind: stop_ind])
            
        # shift the decode index
        decode_shift = code_edge_ind_2 % 256
        mat_decode = np.roll(mat_256, -decode_shift, axis=0)
        
        # decode the data
        data_avg_256 = np.matmul(data_avg_1D, mat_decode)
        
        # assemble the final image
        k = i - 1
        row_addr = int(k / 256)
        col_addr = int(k % 256)
        
        data_avg_512x256[row_addr*256:(row_addr+1)*256,col_addr] = np.flip(data_avg_256,1)
    
    return data_avg_512x256