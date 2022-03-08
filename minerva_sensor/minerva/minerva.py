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

    def __init__(self,bitfilename=None):
        self.scan_lookup = minerva.generate_minerva_scan_lookup()

        super().__init__(bitfilename)
        
        

        
    # ------------------------------------------------------
    
    def InitializeGPIOs(self,PINOUT_CONFIG=1):
        
        
        #PINOUT_CONFIG = 0  # Minerva v1
        #PINOUT_CONFIG = 1  # Minerva v2
        #PINOUT_CONFIG = 2  # Sidewinder v1
        self.xem.SetWireInValue(0x00, int(self.pget('PINOUT_CONFIG')<<18), int(0xF<<18))

        self.GPIO_OutputEnable(32)  # SCAN_CLK
        self.GPIO_OutputEnable(53)  # SCAN_DIN
        self.GPIO_OutputEnable(40)  # SCAN_LATCH
        self.GPIO_OutputEnable(24)  # SCAN_RESET
        
        self.GPIO_OutputEnable(115)  # DAC_SCK
        self.GPIO_OutputEnable(107)  # DAC_SDI
        self.GPIO_OutputEnable(113)  # DAC_CS
        self.GPIO_OutputEnable(117)  # DAC_LDAC
        self.GPIO_OutputEnable(114)  # DAC_CLR
        
        self.GPIO_OutputEnable(43)  # SW_CLK
        self.GPIO_OutputEnable(35)  # MASTER_CLK
                
        self.GPIO_OutputEnable(55)  # ADC_SCLK
        self.GPIO_OutputEnable(54)  # ADC_CONVST

        #self.GPIO_OutputEnable(108)  # AUX_1
        #self.GPIO_Clear(108,True)  # AUX_1=0
                
        self.GPIO_OutputEnable(91)  # STIMU_CLK_P
        self.GPIO_OutputEnable(87)  # STIMU_CLK_N

        
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
    

    def SetClkDividers_Steven(self,f_adc=1e6,f_vector=1e6,f_sw=50e6,f_sw_duty=0.5,f_master=1e6):
        
        # set vector_clk_divider, e.g. 100 for 100MHz/(100)=1MHz
        self.xem.SetWireInValue(0x01, int(100e6/f_vector), self.NO_MASK)
        time.sleep(0.01)
        
        # set adc_clk_divider, e.g. 100 for 100MHz/(100)=1MHz
        self.xem.SetWireInValue(0x02, int(100e6/f_adc-1), self.NO_MASK)
        time.sleep(0.01)
        
        # set MASTER_CLK dividers, e.g. 100 for 100MHz/(100)=1MHz
        self.xem.SetWireInValue(0x03, int(100e6/(f_master*2)), self.NO_MASK)
        
        # set SW_CLK divider. Separate dividers from 100MHz for each phase of the clock
        self.xem.SetWireInValue(0x04, (int(100e6/f_sw*f_sw_duty)<<16) | int(100e6/f_sw*(1-f_sw_duty)), self.NO_MASK)
        time.sleep(0.01)
        
        
    # ------------------------------------------------------
            
    def DAC_setup(self, INTREF=False):
            
        print('Configuring DAC')

        # unmasking DAC pins
        self.GPIO_Clear(115,False)  # DAC_SCK
        self.GPIO_Clear(107,False)  # DAC_SDI
        self.GPIO_Set(113,False)  # DAC_CS
        self.GPIO_Set(117,False)  # DAC_LDAC
        self.GPIO_Set(114,False)  # DAC_CLR        
        self.GPIO_UpdateAll()    

        
        #self.StreamSwitch(self.TO_MEM, self.FROM_ADC)
        #self.StreamSwitch(self.TO_PC, self.FROM_MEM)
        #self.StreamSwitch(self.TO_VECTOR, self.FROM_PC)
            
        if INTREF:
            # change to Internal 3.55V reference
            self.pset('dac_vfs',3550)
            self.DAC_Config(self.DAC_CMD_INTREF,'0000',0, 3550)      
            
        else:
            # use External 1.8V reference for safety    
            self.pset('dac_vfs',1800)
            self.DAC_Config(self.DAC_CMD_EXTREF,'0000',0, 1800)  
        
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
        self.GPIO_Clear(115,True)  # DAC_SCK
        self.GPIO_Clear(107,True)  # DAC_SDI
        self.GPIO_Set(113,True)  # DAC_CS
        self.GPIO_Set(117,True)  # DAC_LDAC
        self.GPIO_Set(114,True)  # DAC_CLR        
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
        self.SendRawVector(scan_vector_32bit)
        #print('done sending vector', time.time()-tstart)
        
        def ADC_Sampling(self,adc_clk_f):
        # set vector lengths, unit is sec
        vector_len = 34/adc_clk_f
        sample_en_pw = 30/adc_clk_f
        sample_en_start = 2/adc_clk_f
        adc_clk_pw = 0.5/adc_clk_f
        
        # convert to vector length
        vector_len = int(vector_len * self.pget('vectorfrequency'))
        sample_en_pw = int(sample_en_pw * self.pget('vectorfrequency'))
        adc_clk_pw = int(adc_clk_pw * self.pget('vectorfrequency'))
        sample_en_start = int(sample_en_start * self.pget('vectorfrequency'))
        
        # create vector
        scan_vector_32bit = np.zeros(vector_len,dtype = np.uint32)
        # sample_en
        scan_vector_32bit[sample_en_start:sample_en_start+sample_en_pw] = scan_vector_32bit[sample_en_start:sample_en_start+sample_en_pw] + (1<<13)
        # adc_clk
        scan_vector_32bit[sample_en_start:sample_en_start+sample_en_pw] = scan_vector_32bit[sample_en_start:sample_en_start+sample_en_pw] + (1<<13)
    
        self.SendRawVector(scan_vector_32bit)


    def UpdateScanChain(self,scanvals,latchenable=True, resetpulse=False):

        if(resetpulse):            
            resetlen=48
        else:
            resetlen=0

        vector_len = resetlen + 2*len(self.scan_lookup) + 48
            
        scan_vector_32bit = np.zeros(vector_len, dtype=np.uint32)

        # bit 0: clock
        scan_vector_32bit[resetlen+1:-48:2] = 1
        
        # bit 1: scan data
        scan_vector_32bit[resetlen:-48] = scan_vector_32bit[resetlen:-48] + scanvals.repeat(2)*2

        # bit 2: scan_latch
        if(latchenable):
            scan_vector_32bit[-48:-8] = scan_vector_32bit[-48:-8] + 4
        
        # bit 3: scan reset
        scan_vector_32bit = scan_vector_32bit + 8
        if(resetpulse):
            scan_vector_32bit[:40] = scan_vector_32bit[:40] - 8

        self.SendRawVector(scan_vector_32bit)
       


        
    def ProtectScanPins(self,mask):
        # unmasking SCAN pins
        self.GPIO_Clear(32,mask)  # SCAN_CLK
        self.GPIO_Clear(53,mask)  # SCAN_DIN        
        self.GPIO_Clear(40,mask)  # SCAN_LATCH
        self.GPIO_Set(24,mask)  # SCAN_RESET
        self.GPIO_UpdateAll()  

        # pulse scan reset
        #self.GPIO_Clear(10,True,update_all=True)  # SCAN_RESET
        #self.GPIO_Clear(10,False,update_all=True)  # SCAN_RESET
        
        
        
    def SendRawVector(self,vector_32bit):
#        print('Sending scan vector','length',len(scan_vector_32bit))
        
        self.WriteVector(np.uint32(vector_32bit), 
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


    def generate_minerva_scan_lookup(): 
      # ~~~~~~~~~~~~~~~~~ Chip Scan Chain ~~~~~~~~~~~~~~~~~~~~~~~

        # left Additional Scan Bit
        scan_bit_left = ['SCAN_BIT_L<0>', 
                         'SCAN_BIT_L<1>']
        
        # Clk Ctrl
        clk_ctrl = ['MASTER_CLK_EN',
                    'clk_ctrl_NA',
                    'GLBL_ADDR_CLK_SEL<1>',
                    'GLBL_ADDR_CLK_SEL<0>',
                    'CHOP_CLK_SEL<0>',
                    'CHOP_CLK_SEL<1>',
                    'CHOP_CLK_SEL<2>',
                    'GLBL_ADDR_CLK_SEL<2>',
                    'CHOP_CLK_SEL<3>',
                    'GLBL_ADDR_CLK_SEL<3>',
                    'CHOP_CLK_EN',
                    'GLBL_ADDR_CLK_EN']
       
        # Readout Ctrl
        readout_ctrl = []
        for ch in range(8):
            readout_ctrl.extend(['CAL_IN_EN_'+str(ch),
                                'C_COMPEN_EN_'+str(ch),
                                'C_DUMMY_GAIN<2>_'+str(ch),
                                'STDBY_EXT_EN_'+str(ch),
                                'C_GAIN<2>_'+str(ch),
                                'R_GAIN<0>_'+str(ch),
                                'R_GAIN<1>_'+str(ch),
                                'R_GAIN<2>_'+str(ch),
                                'INT_EN_'+str(ch),
                                'STDBY_DUMMY_EN_'+str(ch),
                                'C_GAIN<1>_'+str(ch),
                                'C_GAIN<0>_'+str(ch),
                                'C_DUMMY_GAIN<0>_'+str(ch),
                                'C_DUMMY_GAIN<1>_'+str(ch) ])
        
        
        # --------  Array Ctrl ---------
        # Test Column
        test_col_ctrl = ['testcol_C0_OUT',
                        'testcol_C1_OUT',
                        'testcol_Mode_2',
                        'testcol_Mode_0',
                        'testcol_Mode_1',
                        'testcol_SRAM_OUT']
                
        # Col Ctrl
        c0_out = ['c0_out_'+str(c) for c in range(256)]
        c1_out = ['c1_out_'+str(c) for c in range(256)]
        c_mode_2 = ['c_mode_2_'+str(c) for c in range(256)]
        c_mode_0 = ['c_mode_0_'+str(c) for c in range(256)]
        c_mode_1 = ['c_mode_1_'+str(c) for c in range(256)]
        c_sram_out = ['c_sram_out_'+str(c) for c in range(256)]
        
        # ADDR_CLK Ctrl
        addr_clk_ctrl = ['ADDR_COL_CLK_EN',
                         'ADDR_CLK_EN',
                         'ADDR_COL_CLK_PRE_HIGH',
                         'ADDR_CLK_SEL<1>',
                         'ADDR_CLK_SEL<0>',
                         'ADDR_ROW_CLK_EN',
                         'COL_MODE_SEL',
                         'ROW_MODE_SEL' ]        
        
        # Switching Clocks
        sw_clk_ctrl = ['OUT_P_HIGH',
                        'OUT_P_LOW',
                        'OUT_N_HIGH',
                        'OUT_N_LOW',
                        'DELAY_EN<0>',
                        'DELAY_EN<1>',
                        'DELAY_EN<2>',
                        'DELAY_EN<3>' ]
        
        # Row Left Ctrl
        phi_en = ['phi_en_'+str(r) for r in range(512)]
        r0_out = ['r0_out_'+str(r) for r in range(512)]
        r1_out = ['r1_out_'+str(r) for r in range(512)]
        r_stdby_en = ['r_stdby_en_'+str(r) for r in range(512)]
        r_out_en = ['r_out_en_'+str(r) for r in range(512)]
        r_isfet_en = ['r_isfet_en_'+str(r) for r in range(512)]
        
        # Row Right Ctrl
        i_en = ['i_en_'+str(r) for r in range(512)]
        v_en = ['v_en_'+str(r) for r in range(512)]
        r_sram_1 = ['r_sram_1_'+str(r) for r in range(512)]
        r_sram_2 = ['r_sram_2_'+str(r) for r in range(512)]
                
        # -------------------------------
        # Stimulation Ctrl
        stimu_ctrl = ['Row_Mirror_En',
                        'stimu_ctrl_NA',
                        'I_STIMU_EN<0>',
                        'I_STIMU_EN<1>',
                        'I_STIMU_EN<2>',
                        'I_STIMU_EN<3>',
                        'I_STIMU_EN<4>',
                        'I_STIMU_EN<5>' ]

        # Right additional Scan Bit
        scan_bit_right = ['SCAN_BIT_R<0>',
                            'SCAN_BIT_R<1>',
                            'SCAN_BIT_R<2>',
                            'SCAN_BIT_R<3>',
                            'SCAN_BIT_R<4>',
                            'SCAN_BIT_R<5>',
                            'SCAN_BIT_R<6>',
                            'SCAN_BIT_R<7>',
                            'SCAN_BIT_R<8>',
                            'SCAN_BIT_R<9>',
                            'SCAN_BIT_R<10>',
                            'SCAN_BIT_R<11>']
            
        # ------ Combine the row/col control ------
        Col_Ctrl = countList6(c0_out, c1_out, c_mode_2, c_mode_0, c_mode_1, c_sram_out)
        Row_Ctrl_Left = countList6(phi_en, r0_out, r1_out, r_stdby_en, r_out_en, r_isfet_en)
        Row_Ctrl_Right = countList4(r_sram_2, i_en, v_en, r_sram_1)
        
        # Combine all scan data
        scan_data = np.concatenate((scan_bit_left, clk_ctrl, readout_ctrl, test_col_ctrl, Col_Ctrl, addr_clk_ctrl, sw_clk_ctrl, Row_Ctrl_Left, Row_Ctrl_Right, stimu_ctrl, scan_bit_right))
        
        #  reverse the order
        scan_data_r = np.flip(scan_data, 0)

        return {v: k for k, v in enumerate(scan_data_r)}


        
    def Generate_scan_vector_test_col_sensing_mode(self):
        
        scanvals = np.zeros(len(self.scan_lookup))
        
        # enable the test col sram
        scanvals[self.scan_lookup['testcol_SRAM_OUT']]=1
        
        # enable all r_sram_2
        for r in range(512):
            scanvals[self.scan_lookup['r_sram_2_'+str(r)]] = 1
        
        return scanvals
        
    
    def Generate_scan_vector_all_pixel_sensing_mode(self,col_addr):

        scanvals = np.zeros(len(self.scan_lookup))

        # enable one col sram        
        scanvals[self.scan_lookup['c_sram_out_'+str(col_addr)]] = 1        

        # enable all r_sram_2
        for r in range(512):
            scanvals[self.scan_lookup['r_sram_2_'+str(r)]] = 1
        
        return scanvals      
    

    def Generate_scan_vector_all_pixel_stimulus_mode(self,col_addr):

        scanvals = np.zeros(len(self.scan_lookup))

        # enable one col sram        
        scanvals[self.scan_lookup['c_sram_out_'+str(col_addr)]] = 1        

        # enable all r_sram_2
        for r in range(512):
            scanvals[self.scan_lookup['r_sram_1_'+str(r)]] = 1
        
        return scanvals    


    def Generate_scan_vector_all_pixel_sensing_stimulus_mode(self,col_addr):

        scanvals = np.zeros(len(self.scan_lookup))

        # enable one col sram        
        scanvals[self.scan_lookup['c_sram_out_'+str(col_addr)]] = 1        

        # enable all r_sram_2
        for r in range(512):
            scanvals[self.scan_lookup['r_sram_1_'+str(r)]] = 1
            scanvals[self.scan_lookup['r_sram_2_'+str(r)]] = 1
        
        return scanvals 
        
    
    def Generate_scan_vector_pixel_stimu_mode_checkerboard(self, block_size, mode, col_addr):

        scanvals = np.zeros(len(self.scan_lookup))

        # enable one col sram        
        scanvals[self.scan_lookup['c_sram_out_'+str(col_addr)]] = 1        

        # enable all r_sram_1 for every 32 rows
        for r in range(512):
            if mode == 'even':
                if (int(r/block_size) % 2) == 0:
                    scanvals[self.scan_lookup['r_sram_1_'+str(r)]] = 1
                
            elif mode == 'odd':
                if (int(r/block_size) % 2) == 1:
                    scanvals[self.scan_lookup['r_sram_1_'+str(r)]] = 1
                    
            else:
                print('error!!!! mode must be even or odd')
        
        return scanvals          


    def Generate_scan_vector_pixel_stimu_mode_arbitrary_pattern(self, pattern_1d, col_addr):

        scanvals = np.zeros(len(self.scan_lookup))

        # enable one col sram        
        scanvals[self.scan_lookup['c_sram_out_'+str(col_addr)]] = 1 
        
        for r in range(len(pattern_1d)):
            if pattern_1d[r] != 0:
                scanvals[self.scan_lookup['r_sram_1_'+str(r)]] = 1                
            
        return scanvals
       


    def Generate_scan_vector_voltage_stimu(self):

        scanvals = np.zeros(len(self.scan_lookup))       

        # enable all v_en
        for r in range(512):
            scanvals[self.scan_lookup['v_en_'+str(r)]] = 1
            
        # enable all C0/C1/R0/R1 and phi_en to high
        for row_addr in range(512):
            scanvals[self.scan_lookup['phi_en_'+str(row_addr)]]=1    
            scanvals[self.scan_lookup['r0_out_'+str(row_addr)]]=1  
            scanvals[self.scan_lookup['r1_out_'+str(row_addr)]]=1
            
        for col_addr in range(256):
            scanvals[self.scan_lookup['c0_out_'+str(col_addr)]]=1  
            scanvals[self.scan_lookup['c1_out_'+str(col_addr)]]=1  
            
        # set phi_1/2 clock to constant high
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        
        return scanvals  
        
    
    def Generate_scan_vector_mea_test_col(self,ch):

        # flip the channel number to align with ADC
        ch = 7 - ch

        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable one channel
        scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
        scanvals[self.scan_lookup['C_COMPEN_EN_'+str(ch)]] = 1
        scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
        scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable the test col
        scanvals[self.scan_lookup['testcol_C0_OUT']] = 1
        scanvals[self.scan_lookup['testcol_Mode_0']] = 1
                
        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 1        
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 0
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 1                
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['phi_en_0']] = 1        
        scanvals[self.scan_lookup['r0_out_0']] = 1        
        scanvals[self.scan_lookup['r_out_en_0']] = 1                

        
        return scanvals


    

    def Generate_scan_vector_mea_test_col_single_pixel(self,ch, latchenable=True):
        # flip the channel number to align with ADC
        ch = 7 - ch

        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable one channel
        scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
        scanvals[self.scan_lookup['C_COMPEN_EN_'+str(ch)]] = 1
        scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
        scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 1        
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 0
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 0              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable the test col
        scanvals[self.scan_lookup['testcol_SRAM_OUT']]=1
        scanvals[self.scan_lookup['testcol_Mode_2']]=1
        
        # enable clocks and first row
        scanvals[self.scan_lookup['phi_en_0']]=1        
        scanvals[self.scan_lookup['r0_out_0']]=1        
        scanvals[self.scan_lookup['r_out_en_0']]=1  
        
        
        return scanvals


    
    def Generate_scan_vector_mea_impedance(self):
        
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
            #scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['C_COMPEN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c0_out_'+str(ch*32)]] = 1
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32)]] = 1

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 0
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 1
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 1              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['phi_en_0']]=1        
        scanvals[self.scan_lookup['r0_out_0']]=1        
        scanvals[self.scan_lookup['r_out_en_0']]=1  
        
        
        return scanvals        
        
    
    
    def Generate_scan_vector_mea_pH(self):      
            
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
#        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<2>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
#        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<2>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
            #scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['R_GAIN<2>_'+str(ch)]] = 1
#            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
#            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32)]] = 1

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 1
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 1
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 1              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['r_isfet_en_0']]=1        
        scanvals[self.scan_lookup['r_out_en_0']]=1  
        
        
        return scanvals        


    def Generate_scan_vector_mea_temperature(self):
        
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
            #scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['C_COMPEN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c0_out_'+str(ch*32)]] = 1
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32)]] = 1

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 0
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 1
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 1              
        
        # Switching Clocks
        # set P to constant low, and N to constant high
        # P -> phi_2
        # N -> phi_1
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_N_LOW']] = 1
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['phi_en_0']]=1        
        scanvals[self.scan_lookup['r0_out_0']]=1        
        scanvals[self.scan_lookup['r_out_en_0']]=1  
        scanvals[self.scan_lookup['r_isfet_en_0']]=1
        
        
        return scanvals        


    
    def Generate_scan_vector_mea_pH_single_pixel(self, row_addr=10, col_addr=10):      
            
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
#        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<2>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
#        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<2>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=0
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
            #scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['R_GAIN<2>_'+str(ch)]] = 1
#            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
#            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32+col_addr)]] = 1

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 1
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 0
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 0              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['r_isfet_en_'+str(row_addr)]]=1        
        scanvals[self.scan_lookup['r_out_en_'+str(row_addr)]]=1  
        
        return scanvals        
        
    
        
    def Generate_scan_vector_mea_ECT(self, row_offset=1, col_offset=1, block=5):

        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
            scanvals[self.scan_lookup['C_COMPEN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['STDBY_EXT_EN_'+str(ch)]] = 1            
            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1
        
        # c_mode_0: signal_out -> readout
        # c_mode_1: signal_out -> stdby
        # c_mode_2: stdby_out -> stdby
        
        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c0_out_'+str(ch*32 + block)]] = 1
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32 + block)]] = 1
            
            scanvals[self.scan_lookup['c1_out_'+str(ch*32 + col_offset + block)]] = 1    # COL OFFSET  
            
            if row_offset != 0:
                scanvals[self.scan_lookup['c_mode_2_'+str(ch*32 + col_offset + block)]] = 1   # COL OFFSET  
            else:
                scanvals[self.scan_lookup['c_mode_1_'+str(ch*32 + col_offset + block)]] = 1   # COL OFFSET  

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 0
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 1
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 1              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['phi_en_'+str(block)]]=1        
        scanvals[self.scan_lookup['phi_en_'+str(row_offset + block)]]=1      # ROW OFFSET             
        scanvals[self.scan_lookup['r0_out_'+str(block)]]=1        
        scanvals[self.scan_lookup['r1_out_'+str(row_offset + block)]]=1      # ROW OFFSET
        
        # avoid enabling both "r_out_en" and "r_stdby_en" at the same time
        if row_offset != 0:    
            scanvals[self.scan_lookup['r_stdby_en_'+str(row_offset + block)]]=1   # ROW OFFSET  
        scanvals[self.scan_lookup['r_out_en_'+str(block)]]=1  
              
        return scanvals  

    
    def Generate_scan_vector_mea_V_stimulation_current_single_pixel(self, row_addr=10, col_addr=10):      
            
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<2>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<2>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=0
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
#            scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['R_GAIN<0>_'+str(ch)]] = 1
#            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
#            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c0_out_'+str(ch*32+col_addr)]] = 1
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32+col_addr)]] = 1    

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 1
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 0
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 0              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_P_LOW']] = 1
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 1
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable the switching clock and output
        scanvals[self.scan_lookup['phi_en_'+str(row_addr)]]=1    
        scanvals[self.scan_lookup['r_out_en_'+str(row_addr)]]=1  
        scanvals[self.scan_lookup['r0_out_'+str(row_addr)]]=1
        
        return scanvals      
    

    def Generate_scan_vector_mea_I(self):
        
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['MASTER_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<0>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_SEL<1>']]=1
        scanvals[self.scan_lookup['CHOP_CLK_EN']]=1
        scanvals[self.scan_lookup['GLBL_ADDR_CLK_EN']]=1
        
        # enable all 8 channels
        for ch in range(8):
            #scanvals[self.scan_lookup['CAL_IN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['C_COMPEN_EN_'+str(ch)]] = 1
            scanvals[self.scan_lookup['C_GAIN<2>_'+str(ch)]] = 1
            scanvals[self.scan_lookup['INT_EN_'+str(ch)]] = 1

        # enable 8 of the columns
        for ch in range(8):
            scanvals[self.scan_lookup['c0_out_'+str(ch*32)]] = 1
            scanvals[self.scan_lookup['c1_out_'+str(ch*32)]] = 1
            scanvals[self.scan_lookup['c_mode_0_'+str(ch*32)]] = 1

        # ADDR_CLK Ctrl
        scanvals[self.scan_lookup['ADDR_COL_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_CLK_EN']] = 1        
        scanvals[self.scan_lookup['ADDR_COL_CLK_PRE_HIGH']] = 0
        scanvals[self.scan_lookup['ADDR_CLK_SEL<1>']] = 0     
        scanvals[self.scan_lookup['ADDR_CLK_SEL<0>']] = 0
        scanvals[self.scan_lookup['ADDR_ROW_CLK_EN']] = 1        
        scanvals[self.scan_lookup['COL_MODE_SEL']] = 1
        scanvals[self.scan_lookup['ROW_MODE_SEL']] = 1              
        
        # Switching Clocks
        scanvals[self.scan_lookup['OUT_P_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_P_LOW']] = 0
        scanvals[self.scan_lookup['OUT_N_HIGH']] = 0
        scanvals[self.scan_lookup['OUT_N_LOW']] = 0
        scanvals[self.scan_lookup['DELAY_EN<0>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<1>']] = 1
        scanvals[self.scan_lookup['DELAY_EN<2>']] = 0
        scanvals[self.scan_lookup['DELAY_EN<3>']] = 0
        
        # enable clocks and first row
        scanvals[self.scan_lookup['phi_en_0']]=1        
        scanvals[self.scan_lookup['r0_out_0']]=1    
        scanvals[self.scan_lookup['phi_en_1']]=1        
        scanvals[self.scan_lookup['r0_out_1']]=1 
        scanvals[self.scan_lookup['r_out_en_0']]=1  
        
        
        return scanvals
    
    def Generate_scan_vector_KP_ADC(self):
        
        scanvals = np.zeros(len(self.scan_lookup))
        
        scanvals[self.scan_lookup['SCAN_BIT_R<0>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<1>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<2>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<3>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<4>']]=1
#        scanvals[self.scan_lookup['SCAN_BIT_R<5>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<6>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<7>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<8>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<9>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<10>']]=1
        scanvals[self.scan_lookup['SCAN_BIT_R<11>']]=1
        
        return scanvals        