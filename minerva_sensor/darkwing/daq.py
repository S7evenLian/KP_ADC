# -*- coding: utf-8 -*-

import sys,os
import numpy as np
import time
import matplotlib.pyplot as plt
from datetime import datetime
import time
import h5py

# these drivers require python 3.6
assert(sys.version_info.major==3 and sys.version_info.minor==6)

if(sys.platform=='darwin'):
    import ok_mac as ok  # MAC OS
else:
    import ok_pc as ok  # WINDOWS
    
class daq:

    NO_MASK = 0xFFFF_FFFF
    BLOCK_SIZE=1024
    ADDR_REGISTERBANK_BASE = 0x0000_0000
    ADDR_AXILITE_BASE = 0x0100_0000
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ADDR_SWITCH_BASE = ADDR_AXILITE_BASE + 0x0000_2000
    TO_MEM = 0x40
    TO_PC = 0x44
    TO_VECTOR = 0x48        
    FROM_PC = 0
    FROM_ADC = 1
    FROM_MEM = 2
    SWITCH_UPDATE = 0x0000_0002
    SWITCH_DISABLE = 0x8000_0000
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ADDR_SPI_BASE = 0x0200_0000
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ADDR_S2MM_STATUSFIFO_BASE = 0x0300_0000
    ADDR_S2MM_STATUSFIFO_READ = ADDR_S2MM_STATUSFIFO_BASE + 0x0
    ADDR_S2MM_STATUSFIFO_STATUS = ADDR_S2MM_STATUSFIFO_BASE + 0x4
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    ADDR_MM2S_STATUSFIFO_BASE = 0x0400_0000
    ADDR_MM2S_STATUSFIFO_READ = ADDR_MM2S_STATUSFIFO_BASE + 0x0
    ADDR_MM2S_STATUSFIFO_STATUS = ADDR_MM2S_STATUSFIFO_BASE + 0x4
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



        
    #########################################################################
    def __init__(self,bitfilename=None):
        if(bitfilename is None):
            bitfilename=os.path.join(os.path.dirname(__file__), r"fpga_top.bit")
        self.bitfilename = bitfilename
        self.xem = None
        self.settings = {}
        self.gpio_oen = np.zeros(128,dtype=np.uint32)
        self.gpio_set = np.zeros(128,dtype=np.uint32)
        self.gpio_clear = np.zeros(128,dtype=np.uint32)

    #########################################################################
    
    # set user parameter
    def pset(self, param, value):
        self.settings[param] = value

    # get user parameter
    def pget(self, param):
        return self.settings[param]    
    
    # set multiple parameters at once    
    def pset_dict(self, param_dict):
        self.settings.update(param_dict)


    #########################################################################
    # more accurate sleep function, but more resource intensive. Blocking.
    def sleep(self,duration, get_now=time.perf_counter):
        now = get_now()
        end = now + duration
        while now < end:
            now = get_now()
    
    #########################################################################

    def SaveToLogFile(self,fname,grp_name,dataset_name,data,comments=''):
        # save data to file
        now = datetime.now()
        timestamp = now.strftime("_%Y%m%d_%H%M%S")

        if(not os.path.exists(os.path.dirname(fname))):
            os.mkdir(os.path.dirname(fname))
            print('Log file directory did not exist. Created directory: ',os.path.dirname(fname))
        
        hf = h5py.File(fname, 'a')
        grp=hf.require_group(grp_name)
        grp.attrs['timestamp']=timestamp
        grp.attrs['comments']=comments
        grp.create_dataset(dataset_name,data=data)
        grp.attrs.update(self.settings)
        hf.close()
        
    #########################################################################
    
    def InitializeFPGA(self,loadbitfile=True):
        
        if self.xem is None:
            self.xem = ok.okCFrontPanel()
            
            if(self.xem.OpenBySerial("") != self.xem.NoError):
            	raise Exception("Failed to open device.")
            
            # get the OK device details
            devInfo = ok.okTDeviceInfo()
            if(self.xem.GetDeviceInfo(devInfo) != self.xem.NoError):
            	raise Exception("Failed to get device info.")
            else:
            	print("Product: " + devInfo.productName)
            	print("Serial Number: " + devInfo.serialNumber)
            
            if loadbitfile:  # DISABLE IF PROGRAMMING THROUGH VIVADO/CHIPSCOPE
                # download the FPGA .bit file
                if(self.xem.ConfigureFPGA(self.bitfilename) != self.xem.NoError):
                	raise Exception("Failed to load FPGA .bit file")
                else:
                	print("Successfully loaded bitfile " + self.bitfilename)
            else:
                print("User disabled loading bitfile.")
                
            #self.xem.SetTimeout(1000)
    
    #########################################################################
    
    def CloseFPGA(self):
        # CLOSE THE CONNECTION
        self.xem.Close()
    
    #########################################################################
    
    def ToggleLEDs(self):   # TOGGLE LEDS
        print("toggling LEDs")
        for i in range(16):
            self.xem.SetWireInValue(0x00, i<<28, 0xF000_0000)   
            self.xem.UpdateWireIns()
            time.sleep(0.1)
    
    #########################################################################
    
    def AssertReset(self):
        # RESET
        self.xem.SetWireInValue(0x00, 0xF000_000D, self.NO_MASK)   
        self.xem.UpdateWireIns()
        time.sleep(0.01)
    
    #########################################################################
        
    def OutOfReset(self):

        # # before coming out of reset, set S2MM XFER_BYTES  (controls PipeIn TLAST counter)
        # self.xem.SetWireInValue(0x02, int(self.DMA_S2MM_XFER_BYTES/2), self.NO_MASK)   
        # self.xem.UpdateWireIns()
        # time.sleep(0.01)
        
        # TAKE OUT OF RESET   (except RESET_ADC)
        self.xem.SetWireInValue(0x00, 0b0000_0000_0000_0000_0000_0000_0001_1101, 0x0000_001F)   
        self.xem.UpdateWireIns()
        time.sleep(0.01)
        self.xem.SetWireInValue(0x00, 0b0000_0000_0000_0000_0000_0000_0001_1100, 0x0000_001F)   
        self.xem.UpdateWireIns()
        time.sleep(0.01)
        self.xem.SetWireInValue(0x00, 0b0000_0000_0000_0000_0000_0000_0001_1000, 0x0000_001F)   
        self.xem.UpdateWireIns()
        time.sleep(0.01)
        
        ddr_init_done=0
        tstart = time.clock()
        print("waiting for DDR init")
        while(ddr_init_done==0):
            self.xem.UpdateWireOuts()
            ddr_init_done = self.xem.GetWireOutValue(0x20) & 0x0000_0001
        print("DDR init done at time ",time.clock()-tstart)        
        time.sleep(0.1)
    
    #########################################################################

    def ADCReset(self,adc_reset):
        self.xem.SetWireInValue(0x00, 0b1000*adc_reset, 0b1000)   
        self.xem.UpdateWireIns()        
    
    def StartADC(self):
        self.ADCReset(False)
    
    def StopADC(self):
        self.ADCReset(True)

    #########################################################################

    def ClkOutReset(self,clkout_reset):
        self.xem.SetWireInValue(0x00, 0b10000*clkout_reset, 0b10000)   
        self.xem.UpdateWireIns()        
    
    def StartClkout(self):
        self.ClkOutReset(False)
    
    def StopClkout(self):
        self.ClkOutReset(True)        
    
    #########################################################################
    
    def DataToDAQ(self, data_to_write):
        assert(data_to_write.nbytes>=self.BLOCK_SIZE)
        assert(np.mod(data_to_write.nbytes, self.BLOCK_SIZE)==0)
        
        buf_write = bytearray(data_to_write.view(np.uint8))
        
        tstart=time.time()
        bytes_sent = self.xem.WriteToBlockPipeIn(0x80, self.BLOCK_SIZE, buf_write)
        #bytes_sent = self.xem.WriteToPipeIn(0x80, buf_write)
        #print('DataToDAQ bytes_sent %u   elapsed %f' % (bytes_sent,time.time()-tstart))
        
        if(bytes_sent<0):
        	raise Exception("DataToDAQ error. bytes_sent = " + str(bytes_sent))

        
    #########################################################################
        
    def DataFromDAQ(self, numbytes, dt=np.uint16):
        buf_read = bytearray(numbytes)
        self.xem.ReadFromBlockPipeOut(0xa0, self.BLOCK_SIZE, buf_read)
        return np.array(buf_read,dtype=np.uint8).view(dt)       
    
    #########################################################################
    
    def StreamSwitch(self,dest,source,update=True):
        #print('stream register write',hex(self.ADDR_SWITCH_BASE+dest), hex(source))
        self.xem.WriteRegister(int(self.ADDR_SWITCH_BASE+dest), int(source))  # write MUX
        if(update):
            #print('stream register write',hex(self.ADDR_SWITCH_BASE), hex(self.SWITCH_UPDATE))
            self.xem.WriteRegister(int(self.ADDR_SWITCH_BASE), int(self.SWITCH_UPDATE))  # write REG_UPDATE

    #########################################################################
    
    def UpdateIRQs(self):
        self.xem.UpdateTriggerOuts()

    def CheckIRQByName(self, myIRQ):
        assert(myIRQ in ('ADC_OVERFLOW','ADC_UNDERFLOW'))
        
        if(myIRQ == 'ADC_OVERFLOW'):
            ep=0x6A
            mask=0x0000_0001
        if(myIRQ == 'ADC_UNDERFLOW'):
            ep=0x6A
            mask=0x0000_0002
        
        return self.xem.IsTriggered(ep,mask)

        
    #########################################################################

    # dmatype is either 'FROM_MEM' or 'TO_MEM'        
    # base address
    # number of bytes
    # transfer ID tag
    def QueueMemoryTransfer(self, dmatype, baseaddr, numbytes, tag=0):
        assert(dmatype in ('TO_MEM','FROM_MEM'))
        assert(numbytes<2**23 and numbytes>0)
        assert(tag<16 and tag>=0)
        
        if dmatype=='TO_MEM':
            ep_cmd = 0x81
        if dmatype=='FROM_MEM':
            ep_cmd = 0x82

        mycmd = np.uint32([int(0x0080_0000 + numbytes), int(baseaddr), int(tag), 0])  # 128-bit commands
        buf_write = bytearray(mycmd)
        self.xem.WriteToPipeIn(ep_cmd, buf_write)

    
    
    #########################################################################
    
    def CheckDMAStatus(self, dmatype, verbose=False, readall=True):
        assert(dmatype in ('TO_MEM','FROM_MEM'))
        
        if dmatype=='TO_MEM':
            addr_status = daq.ADDR_S2MM_STATUSFIFO_STATUS
            addr_read = daq.ADDR_S2MM_STATUSFIFO_READ
        if dmatype=='FROM_MEM':
            addr_status = daq.ADDR_MM2S_STATUSFIFO_STATUS
            addr_read = daq.ADDR_MM2S_STATUSFIFO_READ
        
        fifo_status = self.xem.ReadRegister(int(addr_status))
        
        fifo_empty = bool(fifo_status & 0x1)
        fifo_full = bool(fifo_status & 0x2)
        fifo_rdcount = (fifo_status>>12) & 0xFF

        if(verbose):
            print('%s status %x empty=%u full=%u count=%u' % (dmatype,fifo_status,fifo_empty,fifo_full,fifo_rdcount))


        if(readall):
            for i in range(fifo_rdcount):
                read_status = self.xem.ReadRegister(int(addr_read))        
                xfer_success = bool(read_status & 0x80)
                xfer_tag = read_status & 0xF
            
                if(not xfer_success):
                    print('WARNING: FAILED DMA TRANSFER %s val=0x%x tag=%u' % (dmatype,read_status,xfer_tag))
            
                if(verbose):
                    print('%s xfer success=%u tag=%u' % (dmatype,xfer_success,xfer_tag))
        
        return fifo_rdcount
    
    #########################################################################
    
    def WriteSPI(self,addr=0,data=0,verbose=False):
        reg = ok.okTRegisterEntry()
        
        reg.address = 0x0200_0000
        reg.data = int(np.uint32(addr<<16) + np.uint16(data))
        self.xem.WriteRegister(reg.address, reg.data)
        
        if verbose:
            print('RegisterBridge addr',hex(reg.address),'write',hex(reg.data))
        
        time.sleep(0.01)
   
    
    #########################################################################
    
    def ReadSPI(self,verbose=False):
        reg = ok.okTRegisterEntry()
        
        reg.address = 0x0200_0000
        reg.data = self.xem.ReadRegister(reg.address)        
        
        if verbose:
            print('RegisterBridge addr',hex(reg.address),'read',hex(reg.data))
    
        time.sleep(0.01)
        
        return reg.data
    

    #########################################################################
    
    def WriteVector(self,myvector,use_dram_buffer=False,verbose=False,plotvectors=False):    
        
        #tstart=time.time()
        
        # extend vector to full block size
        myvector = np.append(myvector,np.repeat(myvector[-1], 
                                                (self.BLOCK_SIZE-myvector.nbytes%self.BLOCK_SIZE)/myvector.itemsize) )

        ##### DEBUG
        #print('DEBUG: sending a counter instead of the vector. len =',len(myvector))
        #myvector = myvector | (np.arange(len(myvector),dtype=np.uint32)<<16)
        ##### /DEBUG
        
        ##### DEBUG
        #with open("writevector.log", "ab") as f:
        #    f.write(b"\nwriting vector\n")
        #    np.savetxt(f, myvector, fmt='%u')
        ##### /DEBUG
        
        #print('writing vector','bytes',myvector.nbytes)
        
        if(plotvectors):
            plt.figure(figsize=(8,8))
            colors='krbm'
            for b in range(32):
                plt.step( range(len(myvector)), 
                         b + 0.6*((np.uint32(myvector) & np.uint32(1<<b))>0),
                         color=colors[b%4])
            #plt.xlim(8400/2,8500/2)
            #plt.xlim(len(myvector)-10,len(myvector)+10)
            plt.show()
        
        
        
        if(use_dram_buffer):
            # transfer PC->MEM and then MEM->vector
            
            # set data stream routing
            #self.StreamSwitch(self.TO_MEM, self.FROM_PC)
            #self.StreamSwitch(self.TO_PC, self.SWITCH_DISABLE)
            #self.StreamSwitch(self.TO_VECTOR, self.FROM_MEM)
        
            self.QueueMemoryTransfer('TO_MEM', 
                                     baseaddr=0x8000_0000, 
                                     numbytes=myvector.nbytes)
            self.DataToDAQ(myvector)
        
            self.QueueMemoryTransfer('FROM_MEM', 
                                     baseaddr=0x8000_0000, 
                                     numbytes=myvector.nbytes)
            
        else:
            # transfer PC->vector
            
            # set data stream routing
            # don't touch, would disturb ADC self.StreamSwitch(self.TO_MEM, self.SWITCH_DISABLE)
            # don't change, would disturb ADC self.StreamSwitch(self.TO_PC, self.SWITCH_DISABLE)
            #self.StreamSwitch(self.TO_VECTOR, self.FROM_PC)
        
            self.DataToDAQ(myvector)
        
        #print('WriteVector bytes %u   elapsed %f' % (myvector.nbytes, time.time()-tstart))

    #########################################################################
    
    def GPIO_OutputEnable(self,gpio_number,enable_output=True,update_all=False):
        self.gpio_oen[gpio_number] = enable_output
        if(update_all):
            self.GPIO_UpdateAll()
    
    def GPIO_Set(self,gpio_number,set_enable=True,update_all=False):
        self.gpio_set[gpio_number] = set_enable
        if(update_all):
            self.GPIO_UpdateAll()

    def GPIO_Clear(self,gpio_number,clear_enable=True,update_all=False):
        self.gpio_clear[gpio_number] = clear_enable
        if(update_all):
            self.GPIO_UpdateAll()

    def GPIO_UpdateAll(self):
        # 4 bits per GPIO, 8 GPIOs per 32-bit word
        for g in range(0,128,8):
            new_val = 0
            for k in range(8):
                new_val = new_val + ((self.gpio_clear[g+k]<<2)<<(k*4))
                new_val = new_val + ((self.gpio_set[g+k]<<1)<<(k*4))
                new_val = new_val + ((self.gpio_oen[g+k]<<0)<<(k*4))            
            #print('writing register',int(self.ADDR_REGISTERBANK_BASE + g//8),hex(new_val))
            self.xem.WriteRegister(int(self.ADDR_REGISTERBANK_BASE + g//8), int(new_val))
        
    #########################################################################


