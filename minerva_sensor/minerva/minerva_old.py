# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 09:36:53 2019

@author: labuser
"""

import sys, os

import numpy as np
import math
import time
import h5py
from datetime import datetime
import itertools
import matplotlib.pyplot as plt

import darkwing


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
def countList2(lst1, lst2): 
    return list(itertools.chain(*zip(lst1, lst2)))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def countList4(lst1, lst2, lst3, lst4): 
    return list(itertools.chain(*zip(lst1, lst2, lst3, lst4)))

def countList6(lst1, lst2, lst3, lst4, lst5, lst6): 
    return list(itertools.chain(*zip(lst1, lst2, lst3, lst4, lst5, lst6)))


# ~~~~~~~~~~~~~~ DEFINE CLASS ~~~~~~~~~~~~~~~~~~~~~~~

class minerva(darkwing.daq):     # inherits from darkwing.daq

    
    # ~~~~~~~~~~~~~~ DEFINE CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~
    
    # DAC ADDRESS LIST:
    DAC_CH_A = '0000'     # '0000' -> Channel A V_SW
    DAC_CH_B = '0001'     # '0001' -> Channel B V_Stdby_1
    DAC_CH_C = '0010'     # '0010' -> Channel C V_BGVDD
    DAC_CH_D = '0011'     # '0011' -> Channel D V_Stdby_2
    DAC_CH_E = '0100'     # '0100' -> Channel E PCB Test Pin
    DAC_CH_F = '0101'     # '0101' -> Channel F PCB Test Pin
    DAC_CH_G = '0110'     # '0110' -> Channel G Electrode Bias
    DAC_CH_H = '0111'     # '0111' -> Channel H V_TIA_Bias   
        
    # DAC CMD LIST
    DAC_CMD_WRITE = '0000'    # '0000' -> Write to an input registor
    DAC_CMD_EXTREF = '0111'   # '0111' -> Select External Reference   
    DAC_CMD_INTREF = '0110'   # '0110' -> Select Internal Reference
    
    ####

        
    # ------------------------------------------------------
    
    def InitializeGPIOs(self):
        
        self.GPIO_OutputEnable(49)  # SCAN_CLK
        self.GPIO_OutputEnable(53)  # SCAN_DIN
        self.GPIO_OutputEnable(58)  # SCAN_LATCH
        self.GPIO_OutputEnable(54)  # SCAN_RESET
        
        self.GPIO_OutputEnable(98)  # DAC_SCK
        self.GPIO_OutputEnable(115)  # DAC_SDI
        self.GPIO_OutputEnable(90)  # DAC_CS
        self.GPIO_OutputEnable(94)  # DAC_LDAC
        self.GPIO_OutputEnable(102)  # DAC_CLR
        
        self.GPIO_OutputEnable(42)  # SW_CLK
        self.GPIO_OutputEnable(35)  # MASTER_CLK
                
        self.GPIO_OutputEnable(107)  # ADC_SCLK
        self.GPIO_OutputEnable(104)  # ADC_CONVST

        self.GPIO_OutputEnable(108)  # AUX_1
        self.GPIO_Clear(108,True)  # AUX_1=0
                
        self.GPIO_OutputEnable(120)  # STIMU_CLK_P
        self.GPIO_OutputEnable(123)  # STIMU_CLK_N

        
        self.GPIO_UpdateAll()
        
        
    def SetClkDividers(self,f_adc=1e6,f_vector=1e6,f_sw=50e6,f_master=1e6):
        
        # set vector_clk_divider, e.g. 100 for 100MHz/(100)=1MHz
        self.xem.SetWireInValue(0x01, int(100e6/f_vector), self.NO_MASK)
        time.sleep(0.01)
        
        # set adc_clk_divider, e.g. 100 for 100MHz/(100)=1MHz
        self.xem.SetWireInValue(0x02, int(100e6/f_adc-1), self.NO_MASK)
        time.sleep(0.01)
        
        # set SW_CLK and MASTER_CLK dividers, e.g. 100 for 100MHz/(100)=1MHz
        self.xem.SetWireInValue(0x03, (int(100e6/(f_sw*2))<<16) | int(100e6/(f_master*2)), self.NO_MASK)
        time.sleep(0.01)
        
        
    # ------------------------------------------------------
            
    def DAC_setup(self):
            
        print('Configuring DAC')

        # unmasking DAC pins
        self.GPIO_Clear(98,False)  # DAC_SCK
        self.GPIO_Clear(115,False)  # DAC_SDI
        self.GPIO_Set(90,False)  # DAC_CS
        self.GPIO_Set(94,False)  # DAC_LDAC
        self.GPIO_Set(102,False)  # DAC_CLR        
        self.GPIO_UpdateAll()    

        
        #self.StreamSwitch(self.TO_MEM, self.FROM_ADC)
        #self.StreamSwitch(self.TO_PC, self.FROM_MEM)
        #self.StreamSwitch(self.TO_VECTOR, self.FROM_PC)
            
        # use External 1.8V reference for safety    
        self.pset('dac_vfs',1800)
        self.DAC_Config(self.DAC_CMD_EXTREF,'0000',0)  
        
        # change to Internal 2.5V reference
        #self.pset('dac_vfs',2500)
        #self.DAC_Config(self.DAC_CMD_INTREF,'0000',0)    
        
        # Configure each channels
        self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_A,self.pget('V_SW'))  
        self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_B,self.pget('V_CM'))  
        #self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_C,self.pget('V_BGVDD'))  
        #self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_D,self.pget('V_Stdby_2'))  
        self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_E,self.pget('V_Electrode_Bias'))  
        self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_F,self.pget('V_STIMU_P'))  
        self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_G,self.pget('V_STIMU_N'))  
        self.DAC_Config(self.DAC_CMD_WRITE,self.DAC_CH_H,self.pget('V_STBY'))  
    
        # masking DAC pins
        self.GPIO_Clear(98,True)  # DAC_SCK
        self.GPIO_Clear(115,True)  # DAC_SDI
        self.GPIO_Set(90,True)  # DAC_CS
        self.GPIO_Set(94,True)  # DAC_LDAC
        self.GPIO_Set(102,True)  # DAC_CLR        
        self.GPIO_UpdateAll()        
        
    
    # ------------------------------------------------------
        
    def DAC_Config(self, CMD, ADDR, VOLT, dac_vfs=1800):
        # Format: DAC_Config(CMD,ADDRESS,VOLTAGE(in mV))
        
        VOLT = math.floor(float(VOLT)/self.pget('dac_vfs')*1023)
        Volt = np.binary_repr(VOLT,10)
    
        scan_data = CMD + ADDR + Volt + '000000'
        
        # pull cs low
        v1 = np.array(['11000'])
        v1 = np.repeat(v1, 20)
        
        # the scan data
        v2 = np.empty((0))
        for i in range(24):
            v2 = np.append(v2, '110' + scan_data[i] + '0')
            v2 = np.append(v2, '110' + scan_data[i] + '1')
        
        # pull cs high
        v3 = np.array(['11100'])
        v3 = np.repeat(v3, 20)
        
        # LDAC Neg Pulse
        v4 = np.array(['10100'])
        v4 = np.repeat(v4, 20)
        
        v5 = np.array(['11100'])
        v5 = np.repeat(v5, 20)
        
        scan_all_bin = np.concatenate((v1, v2, v3, v4, v5))
        scan_all_int = np.zeros(len(scan_all_bin))
        for i in range(len(scan_all_bin)):
            scan_all_int[i] = int(scan_all_bin[i],2)
        
        
        # send the data
        # bit [8] = clk
        # bit [9] = data
        # bit [10] = cs
        # bit [11] = ldac
        # bit [12] = clr
        print('Sending DAC vector')
#        plt.figure(figsize=(8,8))
#        for b in range(8):
#            plt.plot(b + ((np.uint32(scan_all_int) & (1<<b))!=0))
#        plt.show()
            
        self.WriteVector(np.uint32(scan_all_int)<<8, 
                         use_dram_buffer=False,
                         plotvectors=False)
        
        
    
            
            
    
    
    # ------------------------------------------------------
    
    def SendScanVector_4bit(self,scan_vector_4bit):
        #print('Converting from 4bit to 32bit vector')
        tstart=time.time()
        tmp32 = np.array(scan_vector_4bit,dtype=np.uint8).view(np.uint32)
        
        scan_vector_32bit = np.zeros(2*len(scan_vector_4bit),dtype=np.uint32)
        
        for i in range(8):
            scan_vector_32bit[i::8] = (tmp32>>(28-4*i)) & 0xF

        # # elongate SCAN_LATCH pulse
        # holdlatch = 200  # extra clock cycles to hold latch high
        # findlatch = np.where(scan_vector_32bit&(1<<2)>0)[0]
        # if(len(findlatch)>0):
        #     scan_vector_32bit = np.insert(scan_vector_32bit,
        #                                   findlatch[0],
        #                                   np.repeat(scan_vector_32bit[findlatch], holdlatch))
                        
        #print('converted to 32bit', time.time()-tstart)
        #print('bytes',scan_vector_32bit.nbytes)
        self.SendScanVector(scan_vector_32bit)
        #print('done sending vector', time.time()-tstart)

        
    def ProtectScanPins(self,mask):
        # unmasking SCAN pins
        self.GPIO_Clear(49,mask)  # SCAN_CLK
        self.GPIO_Clear(53,mask)  # SCAN_DIN        
        self.GPIO_Clear(58,mask)  # SCAN_LATCH
        self.GPIO_Set(54,mask)  # SCAN_RESET
        self.GPIO_UpdateAll()  

        # pulse scan reset
        #self.GPIO_Clear(10,True,update_all=True)  # SCAN_RESET
        #self.GPIO_Clear(10,False,update_all=True)  # SCAN_RESET
        
        
        
    def SendScanVector(self,scan_vector_32bit):
#        print('Sending scan vector','length',len(scan_vector_32bit))
        
        self.WriteVector(np.uint32(scan_vector_32bit), 
                         use_dram_buffer=False,
                         plotvectors=False)

        
        
    
    def QueueADCAcquisition(self,xferbytes=None,sec=None,BASE_ADDR=0x8000_0000,bytespertransfer=None):
        
        if(sec is not None):
            xferbytes = sec * self.pget('samplerate')*4 *8   #4 bytes per sample, 8 channels
        
        if(bytespertransfer is None):
            bytespertransfer = 2**int(np.log2(xferbytes)) // 4
        bytespertransfer = min(2**22, bytespertransfer)
        
        
        # set data stream routing
        #self.StreamSwitch(self.TO_MEM, self.FROM_ADC)
        #self.StreamSwitch(self.TO_PC, self.FROM_MEM)
        # don't change; would disturb scan vector self.StreamSwitch(self.TO_VECTOR, self.SWITCH_DISABLE)

        numtransfers = math.ceil(xferbytes / bytespertransfer)

        if(numtransfers>100):
            print('WARNING: queuing many DMA transfers. possible overflow. recommend streaming in smaller blocks.')
        
        
        # tell DMA to move data from ADC to DRAM
        for n in range(numtransfers):
            self.QueueMemoryTransfer('TO_MEM', 
                                     baseaddr=BASE_ADDR + n*bytespertransfer, 
                                     numbytes=bytespertransfer)
    
        return numtransfers,xferbytes
    
    
    def WaitForDMA(self,numtransfers):
        # wait for DMA to complete
        xfers_done=0
        tstart = datetime.now()
        while(xfers_done<numtransfers):            
            x=self.CheckDMAStatus('TO_MEM',verbose=False,readall=True)
            xfers_done = xfers_done + x
            if(x>0):
                elapsed = (datetime.now()-tstart).total_seconds()
                print('\rWaiting for data transfers. (%u/%u) (%2.2f sec)' % (xfers_done,numtransfers,elapsed),end='')
        print('')


    def GetDataFromMemory(self,xferbytes,BASE_ADDR=0x8000_0000,bytespertransfer=None):
        
        if(bytespertransfer is None):
            bytespertransfer = 2**int(np.log2(xferbytes)) // 4
        bytespertransfer = min(2**22, bytespertransfer)
            
        numtransfers = math.ceil(xferbytes / bytespertransfer)
        actualxferbytes = bytespertransfer * numtransfers

        # move data from DRAM to PC
        for n in range(numtransfers):        
            self.QueueMemoryTransfer('FROM_MEM', 
                                     baseaddr=0x8000_0000 + n*bytespertransfer, 
                                     numbytes=bytespertransfer)

        mydata_uint32 = self.DataFromDAQ(numbytes=actualxferbytes, dt=np.uint32)
            
        #print(mydata_uint32[:100])
        #print([hex(x) for x in mydata_uint32[:100]])
        
        return mydata_uint32, actualxferbytes


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SaveToLogFile(self,fname,grp_name,dataset_names,datasets,comments=''):
        # save data to file
        now = datetime.now()
        timestamp = now.strftime("_%Y%m%d_%H%M%S")

        grp_name = grp_name+timestamp
    
        hf = h5py.File(fname, 'a')
        grp=hf.require_group(grp_name)
        grp.attrs['timestamp']=timestamp
        grp.attrs['comments']=comments
        for name,data in zip(dataset_names,datasets):
            grp.create_dataset(name,data=data)
        grp.attrs.update(self.settings)
        hf.close()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # helper functions for scan vector generation
    # this belongs to the minerva class, not an individual object

        
    def Generate_scan_vector_test_col_sensing_mode(latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~

        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
#        clk_ctrl[0]  = 1 # MASTER_CLK_EN
#        clk_ctrl[1]  = 0 # NA
#        clk_ctrl[2]  = 0 # ADDR_CLK_SEL<1>
#        clk_ctrl[3]  = 0 # ADDR_CLK_SEL<0>
#        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
#        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
#        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
#        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
#        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
#        clk_ctrl[9]  = 1 # ADDR_CLK_SEL<3>
#        clk_ctrl[10] = 0 # CHOP_CLK_EN
#        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # enable the test col sram
        test_col_ctrl[5] = 1
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
#        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
#        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
#        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
#        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
#        addr_clk_ctrl[4] = 1 # ADDR_CLK_SEL<0>
#        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
#        addr_clk_ctrl[6] = 0 # COL_MODE_SEL
#        addr_clk_ctrl[7] = 0 # ROW_MODE_SEL
        
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # enable all r_sram_2
        r_sram_2[:] = 1
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)
    
    
    def Generate_scan_vector_all_pixel_sensing_mode(col_addr, latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~
        #tstart=time.time()
        #print('start Generate_scan_vector_all_pixel_sensing_mode')
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
#        clk_ctrl[0]  = 1 # MASTER_CLK_EN
#        clk_ctrl[1]  = 0 # NA
#        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
#        clk_ctrl[3]  = 0 # ADDR_CLK_SEL<0>
#        clk_ctrl[4]  = 0 # CHOP_CLK_SEL<0>
#        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
#        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
#        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
#        clk_ctrl[8]  = 1 # CHOP_CLK_SEL<3>
#        clk_ctrl[9]  = 1 # ADDR_CLK_SEL<3>
#        clk_ctrl[10] = 0 # CHOP_CLK_EN
#        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        c_sram_out[col_addr] = 1
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
#        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
#        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
#        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
#        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
#        addr_clk_ctrl[4] = 0 # ADDR_CLK_SEL<0>
#        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
#        addr_clk_ctrl[6] = 1 # COL_MODE_SEL
#        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
        
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
#        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
#        sw_clk_ctrl[1] = 0 # OUT_P LOW
#        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
#        sw_clk_ctrl[3] = 0 # OUT_N_LOW
#        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
#        sw_clk_ctrl[5] = 0 # DELAY_EN<1>
#        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
#        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # enable all r_sram_2
        r_sram_2[:] = 1
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
        
        #print('finished scan_all', time.time()-tstart)
        #print(scan_all[:10])
        return np.uint32([int(x,2) for x in scan_all])

    
    def Generate_scan_vector_close_sram(latchenable=True):
#      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~
#        #tstart=time.time()
#        #print('start Generate_scan_vector_all_pixel_sensing_mode')
#        
#        # left Additional Scan Bit
#        scan_bit_left = np.zeros(2)
#        
#        # Clk Ctrl
#        clk_ctrl = np.zeros(12)
##        clk_ctrl[0]  = 1 # MASTER_CLK_EN
##        clk_ctrl[1]  = 0 # NA
##        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
##        clk_ctrl[3]  = 0 # ADDR_CLK_SEL<0>
##        clk_ctrl[4]  = 0 # CHOP_CLK_SEL<0>
##        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
##        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
##        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
##        clk_ctrl[8]  = 1 # CHOP_CLK_SEL<3>
##        clk_ctrl[9]  = 1 # ADDR_CLK_SEL<3>
##        clk_ctrl[10] = 0 # CHOP_CLK_EN
##        clk_ctrl[11] = 1 # ADDR_CLK_EN
#        
#        
#        # Readout Ctrl
#        readout_ctrl = np.zeros(112)
#        
#        # --------  Array Ctrl ---------
#        # Test Column
#        test_col_ctrl = np.zeros(6)
#        
#        # Col Ctrl
#        c0_out = np.zeros(256)
#        c1_out = np.zeros(256)
#        c_mode_2 = np.zeros(256)
#        c_mode_0 = np.zeros(256)
#        c_mode_1 = np.zeros(256)
#        c_sram_out = np.zeros(256)
#                
#        # ADDR_CLK Ctrl
#        addr_clk_ctrl = np.zeros(8)
##        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
##        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
##        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
##        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
##        addr_clk_ctrl[4] = 0 # ADDR_CLK_SEL<0>
##        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
##        addr_clk_ctrl[6] = 1 # COL_MODE_SEL
##        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
#        
#        
#        # Switching Clocks
#        sw_clk_ctrl = np.zeros(8)
##        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
##        sw_clk_ctrl[1] = 0 # OUT_P LOW
##        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
##        sw_clk_ctrl[3] = 0 # OUT_N_LOW
##        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
##        sw_clk_ctrl[5] = 0 # DELAY_EN<1>
##        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
##        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
#        
#        # Row Left Ctrl
#        phi_en = np.zeros(512)
#        r0_out = np.zeros(512)
#        r1_out = np.zeros(512)
#        r_stdby_en = np.zeros(512)
#        r_out_en = np.zeros(512)
#        r_isfet_en = np.zeros(512)
#        
#        # Row Right Ctrl
#        i_en = np.zeros(512)
#        v_en = np.zeros(512)
#        r_sram_1 = np.zeros(512)
#        r_sram_2 = np.zeros(512)
#        
#        # enable all r_sram_2
##        r_sram_2[:] = 1
#        
#        # -------------------------------
#        # Stimulation Ctrl
#        stimu_ctrl = np.zeros(8)
#        
#        # Right additional Scan Bit
#        scan_bit_right = np.zeros(12)
#            
#        # ------ Combine the row/col control ------
#        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
#        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
#        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
#        
#        # Combine all scan data
#        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
#        
#        # Convert int to string and reverse the order
#        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
#            
#        # scan data format:
#        # scan_rst, scan_latch, scan_data, scan_clk
#        scan_all = np.empty(13648, dtype='<U4')
#        for i in range(len(scan_data_r)):
#            scan_all[i*2] = '10' + scan_data_r[i] + '0'
#            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
#        
#        # Raise scan_latch for a few cycles, then lower it down
#        scan_latch = np.empty(48, dtype='<U4')
#        if latchenable:
#            scan_latch[0:40] = '1100'
#            scan_latch[40:48] = '1000'
#        else:
#            scan_latch[0:48] = '0000'
            
#        # Combine all scan in data
#        scan_all = np.concatenate((scan_all, scan_latch))
        
        scan_all = np.empty(64, dtype='<U4')
        for i in range(32):
            scan_all[i*2] = '1000'
            scan_all[i*2+1] = '1001'
            
        
        #print('finished scan_all', time.time()-tstart)
        #print(scan_all[:10])
        return np.uint32([int(x,2) for x in scan_all])
    
    
    def Generate_scan_vector_mea_test_col(ch, latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~

        # flip the channel number to align with ADC
        ch = 7 - ch
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
        clk_ctrl[0]  = 1 # MASTER_CLK_EN
        clk_ctrl[1]  = 0 # NA
        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
        clk_ctrl[3]  = 1 # ADDR_CLK_SEL<0>
        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
        clk_ctrl[9]  = 0 # ADDR_CLK_SEL<3>
        clk_ctrl[10] = 1 # CHOP_CLK_EN
        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # enable one channel
        readout_ctrl[ch*14] = 1 # CAL_IN_EN
        readout_ctrl[ch*14+1] = 1 # Compensation_EN
        readout_ctrl[ch*14+4] = 1 # C_GAIN<2>
        readout_ctrl[ch*14+8] = 1 # INT_EN
        
#        readout_ctrl[ch*14+10] = 1 # C_GAIN<0>
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # enable the test col
        test_col_ctrl[0] = 1
        test_col_ctrl[3] = 1
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
        addr_clk_ctrl[4] = 1 # ADDR_CLK_SEL<0>
        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
        addr_clk_ctrl[6] = 0 # COL_MODE_SEL
        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
        sw_clk_ctrl[1] = 0 # OUT_P LOW
        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
        sw_clk_ctrl[3] = 0 # OUT_N_LOW
        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
        sw_clk_ctrl[5] = 0 # DELAY_EN<1>
        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        phi_en[0] = 1
        r0_out[0] = 1
#        r1_out[0:64] = 1
#        r_stdby_en[0:64] = 1
        r_out_en[0] = 1
#        r_isfet_en[0:64] = 1
        
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)
    

    def Generate_scan_vector_mea_test_col_single_pixel(ch, latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~

        # flip the channel number to align with ADC
        ch = 7 - ch
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
        clk_ctrl[0]  = 1 # MASTER_CLK_EN
        clk_ctrl[1]  = 0 # NA
        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
        clk_ctrl[3]  = 1 # ADDR_CLK_SEL<0>
        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
        clk_ctrl[9]  = 0 # ADDR_CLK_SEL<3>
        clk_ctrl[10] = 1 # CHOP_CLK_EN
        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # enable one channel
        readout_ctrl[ch*14] = 1 # CAL_IN_EN
        readout_ctrl[ch*14+1] = 1 # Compensation_EN
        readout_ctrl[ch*14+4] = 1 # C_GAIN<2>
        readout_ctrl[ch*14+8] = 1 # INT_EN
        
#        readout_ctrl[ch*14+10] = 1 # C_GAIN<0>
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # enable the test col
        test_col_ctrl[0] = 1
        test_col_ctrl[3] = 1
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
        addr_clk_ctrl[4] = 1 # ADDR_CLK_SEL<0>
        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
        addr_clk_ctrl[6] = 0 # COL_MODE_SEL
        addr_clk_ctrl[7] = 0 # ROW_MODE_SEL
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
        sw_clk_ctrl[1] = 0 # OUT_P LOW
        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
        sw_clk_ctrl[3] = 0 # OUT_N_LOW
        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
        sw_clk_ctrl[5] = 0 # DELAY_EN<1>
        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        phi_en[0] = 1
        r0_out[0] = 1
#        r1_out[0:64] = 1
#        r_stdby_en[0:64] = 1
        r_out_en[0] = 1
#        r_isfet_en[0:64] = 1
        
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)

    
    def Generate_scan_vector_mea_impedance(latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
        clk_ctrl[0]  = 1 # MASTER_CLK_EN
        clk_ctrl[1]  = 0 # NA
        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
        clk_ctrl[3]  = 1 # ADDR_CLK_SEL<0>
        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
        clk_ctrl[9]  = 0 # ADDR_CLK_SEL<3>
        clk_ctrl[10] = 1 # CHOP_CLK_EN
        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # enable one channel
        readout_ctrl[1:112:14] = 1 # Compensation_EN
        readout_ctrl[4:112:14] = 1 # C_GAIN<2>
        readout_ctrl[8:112:14] = 1 # INT_EN
#        readout_ctrl[10:112:14] = 1 # C_GAIN<1>
#        readout_ctrl[11:112:14] = 1 # C_GAIN<0>
        
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        c0_out[0:256:32] = 1
        c_mode_0[0:256:32] = 1
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
        addr_clk_ctrl[4] = 0 # ADDR_CLK_SEL<0>
        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
        addr_clk_ctrl[6] = 1 # COL_MODE_SEL
        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
        sw_clk_ctrl[1] = 0 # OUT_P LOW
        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
        sw_clk_ctrl[3] = 0 # OUT_N_LOW
        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
        sw_clk_ctrl[5] = 1 # DELAY_EN<1>
        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        phi_en[0] = 1
        r0_out[0] = 1
        r_out_en[0] = 1
        
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '00'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '10'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)
    
    
    def Generate_scan_vector_mea_pH_single_pixel(latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
        clk_ctrl[0]  = 1 # MASTER_CLK_EN
        clk_ctrl[1]  = 0 # NA
        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
        clk_ctrl[3]  = 1 # ADDR_CLK_SEL<0>
        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
        clk_ctrl[9]  = 0 # ADDR_CLK_SEL<3>
        clk_ctrl[10] = 1 # CHOP_CLK_EN
        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # enable one channel
        readout_ctrl[1:112:14] = 1 # Compensation_EN
        readout_ctrl[4:112:14] = 1 # C_GAIN<2>
        readout_ctrl[8:112:14] = 1 # INT_EN
#        readout_ctrl[10:112:14] = 1 # C_GAIN<1>
#        readout_ctrl[11:112:14] = 1 # C_GAIN<0>
        
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
#        c0_out[0:256:32] = 1
        c_mode_0[0:256:32] = 1
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
        addr_clk_ctrl[4] = 0 # ADDR_CLK_SEL<0>
        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
        addr_clk_ctrl[6] = 1 # COL_MODE_SEL
        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
        sw_clk_ctrl[1] = 0 # OUT_P LOW
        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
        sw_clk_ctrl[3] = 0 # OUT_N_LOW
        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
        sw_clk_ctrl[5] = 1 # DELAY_EN<1>
        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
#        phi_en[0] = 1
#        r0_out[0] = 1
        r_isfet_en[0] = 1
        r_out_en[0] = 1
        
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)
    
    def Generate_scan_vector_mea_temperature_single_pixel(latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
        clk_ctrl[0]  = 1 # MASTER_CLK_EN
        clk_ctrl[1]  = 0 # NA
        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
        clk_ctrl[3]  = 1 # ADDR_CLK_SEL<0>
        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
        clk_ctrl[9]  = 0 # ADDR_CLK_SEL<3>
        clk_ctrl[10] = 1 # CHOP_CLK_EN
        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # enable one channel
        readout_ctrl[1:112:14] = 1 # Compensation_EN
        readout_ctrl[4:112:14] = 1 # C_GAIN<2>
        readout_ctrl[8:112:14] = 1 # INT_EN
#        readout_ctrl[10:112:14] = 1 # C_GAIN<1>
#        readout_ctrl[11:112:14] = 1 # C_GAIN<0>
        
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        c0_out[0:256:32] = 1
        c_mode_0[0:256:32] = 1
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
        addr_clk_ctrl[4] = 0 # ADDR_CLK_SEL<0>
        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
        addr_clk_ctrl[6] = 1 # COL_MODE_SEL
        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        sw_clk_ctrl[0] = 0 # OUT_P_HIGH
        sw_clk_ctrl[1] = 1 # OUT_P LOW
        sw_clk_ctrl[2] = 0 # OUT_N_HIGH
        sw_clk_ctrl[3] = 0 # OUT_N_LOW
        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
        sw_clk_ctrl[5] = 1 # DELAY_EN<1>
        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        r_isfet_en[0] = 1
        r0_out[0] = 1
        r_out_en[0] = 1
        
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)

    def Generate_scan_vector_mea_ECT(latchenable=True):
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~
        
        # left Additional Scan Bit
        scan_bit_left = np.zeros(2)
        
        # Clk Ctrl
        clk_ctrl = np.zeros(12)
        clk_ctrl[0]  = 1 # MASTER_CLK_EN
        clk_ctrl[1]  = 0 # NA
        clk_ctrl[2]  = 1 # ADDR_CLK_SEL<1>
        clk_ctrl[3]  = 1 # ADDR_CLK_SEL<0>
        clk_ctrl[4]  = 1 # CHOP_CLK_SEL<0>
        clk_ctrl[5]  = 1 # CHOP_CLK_SEL<1>
        clk_ctrl[6]  = 0 # CHOP_CLK_SEL<2>
        clk_ctrl[7]  = 0 # ADDR_CLK_SEL<2>
        clk_ctrl[8]  = 0 # CHOP_CLK_SEL<3>
        clk_ctrl[9]  = 0 # ADDR_CLK_SEL<3>
        clk_ctrl[10] = 1 # CHOP_CLK_EN
        clk_ctrl[11] = 1 # ADDR_CLK_EN
        
        
        # Readout Ctrl
        readout_ctrl = np.zeros(112)
        
        # enable one channel
        readout_ctrl[1:112:14] = 1 # Compensation_EN
        readout_ctrl[3:112:14] = 1 # STDBY_EXT_EN
        readout_ctrl[4:112:14] = 1 # C_GAIN<2>
        readout_ctrl[8:112:14] = 1 # INT_EN
#        readout_ctrl[10:112:14] = 1 # C_GAIN<1>
#        readout_ctrl[11:112:14] = 1 # C_GAIN<0>
        
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = np.zeros(6)
        
        # Col Ctrl
        c0_out = np.zeros(256)
        c1_out = np.zeros(256)
        c_mode_2 = np.zeros(256)
        c_mode_0 = np.zeros(256)
        c_mode_1 = np.zeros(256)
        c_sram_out = np.zeros(256)
        
        c0_out[0:256:32] = 1
        c1_out[1:256:32] = 1
        c_mode_0[0:256:32] = 1
#        c_mode_1[1:256:32] = 1
        c_mode_2[1:256:32] = 1
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = np.zeros(8)
        addr_clk_ctrl[0] = 1 # ADDR_COL_CLK_EN
        addr_clk_ctrl[1] = 1 # ADDR_CLK_EN
        addr_clk_ctrl[2] = 0 # ADDR_COL_CLK_PRE_HIGH
        addr_clk_ctrl[3] = 0 # ADDR_CLK_SEL<1>
        addr_clk_ctrl[4] = 0 # ADDR_CLK_SEL<0>
        addr_clk_ctrl[5] = 1 # ADDR_ROW_CLK_EN
        addr_clk_ctrl[6] = 1 # COL_MODE_SEL
        addr_clk_ctrl[7] = 1 # ROW_MODE_SEL
        
        # Switching Clocks
        sw_clk_ctrl = np.zeros(8)
        sw_clk_ctrl[0] = 1 # OUT_P_HIGH
        sw_clk_ctrl[1] = 0 # OUT_P LOW
        sw_clk_ctrl[2] = 1 # OUT_N_HIGH
        sw_clk_ctrl[3] = 0 # OUT_N_LOW
        sw_clk_ctrl[4] = 1 # DELAY_EN<0>
        sw_clk_ctrl[5] = 1 # DELAY_EN<1>
        sw_clk_ctrl[6] = 0 # DELAY_EN<2>
        sw_clk_ctrl[7] = 0 # DELAY_EN<3>
        
        # Row Left Ctrl
        phi_en = np.zeros(512)
        r0_out = np.zeros(512)
        r1_out = np.zeros(512)
        r_stdby_en = np.zeros(512)
        r_out_en = np.zeros(512)
        r_isfet_en = np.zeros(512)
        
        phi_en[0] = 1
        phi_en[1] = 1
        r0_out[0] = 1
        r1_out[1] = 1
        r_stdby_en[1] = 1
        r_out_en[0] = 1
        
        
        # Row Right Ctrl
        i_en = np.zeros(512)
        v_en = np.zeros(512)
        r_sram_1 = np.zeros(512)
        r_sram_2 = np.zeros(512)
        
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = np.zeros(8)
        
        # Right additional Scan Bit
        scan_bit_right = np.zeros(12)
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        # Convert int to string and reverse the order
        scan_data_r = np.char.mod('%d', np.flip(scan_data, 0))
            
        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(13648, dtype='<U4')
        for i in range(len(scan_data_r)):
            scan_all[i*2] = '10' + scan_data_r[i] + '0'
            scan_all[i*2+1] = '10' + scan_data_r[i] + '1'
        
        # Raise scan_latch for a few cycles, then lower it down
        scan_latch = np.empty(48, dtype='<U4')
        scan_latch[0:40] = '1100'
        scan_latch[40:48] = '1000'
            
        # Combine all scan in data
        scan_all = np.concatenate((scan_all, scan_latch))
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)

    
        
    def Generate_scan_vector_rst():
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~

        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(64, dtype='<U4')
        for i in range(len(scan_all)):
            scan_all[i] = '0000'
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)
    
    def Generate_scan_vector_rst_deselect():
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~

        # scan data format:
        # scan_rst, scan_latch, scan_data, scan_clk
        scan_all = np.empty(64, dtype='<U4')
        for i in range(len(scan_all)):
            scan_all[i] = '1000'
            
        # combine every eight 4-bits into 32-bit
        scan_all_32 = np.empty(int(len(scan_all)/8), dtype='<U32')
        for i in range(len(scan_all_32)):
            array_tmp = scan_all[i*8:(i+1)*8]
            scan_all_32[i] = ''.join(map(str, array_tmp))
            
        scan_all_int = np.zeros(len(scan_all_32))
        for i in range(len(scan_all_32)):
            scan_all_int[i] = int(scan_all_32[i],2)
        
        return np.uint32(scan_all_int).view(np.uint8)