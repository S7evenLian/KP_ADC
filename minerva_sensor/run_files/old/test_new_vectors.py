#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 18:58:34 2021

@author: jacobrosenstein
"""



import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
import os

from minerva import minerva
from minerva import minerva_new


    
def convert_4bit_to_32bit(scan_vector_4bit):
    tmp32 = np.array(scan_vector_4bit,dtype=np.uint8).view(np.uint32)
    
    scan_vector_32bit = np.zeros(2*len(scan_vector_4bit),dtype=np.uint32)
    
    for i in range(8):
        scan_vector_32bit[i::8] = (tmp32>>(28-4*i)) & 0xF

    return scan_vector_32bit


def Scanval_to_32bit(scanvals,latchenable=True, resetpulse=False):

    vector_len = 0 + 2*6824 + 48
    
    scan_vector_32bit = np.zeros(vector_len, dtype=np.uint32)

    # bit 0: clock
    scan_vector_32bit[1:-48:2] = 1
    
    # bit 1: scan data
    scan_vector_32bit[0:-48] = scan_vector_32bit[0:-48] + scanvals.repeat(2)*2

    # bit 2: scan_latch
    if(latchenable):
        scan_vector_32bit[-48:-8] = scan_vector_32bit[-48:-8] + 4
    
    # bit 3: scan reset
    scan_vector_32bit = scan_vector_32bit + 8
    #if(resetpulse):
    #    scan_vector_32bit[:40] = scan_vector_32bit[:40] - 8

    return scan_vector_32bit



m_old = minerva()
m_new = minerva_new()

for ch in range(8):
    test_col_1_old = convert_4bit_to_32bit(minerva.Generate_scan_vector_test_col_sensing_mode())
    test_col_2_old = convert_4bit_to_32bit(minerva.Generate_scan_vector_mea_test_col(ch))

    test_col_1_new = Scanval_to_32bit(m_new.Generate_scan_vector_test_col_sensing_mode())
    test_col_2_new = Scanval_to_32bit(m_new.Generate_scan_vector_mea_test_col(ch))


    print('ch',ch,'test_col_1 difference',np.sum(np.abs(test_col_1_new-test_col_1_old)))

