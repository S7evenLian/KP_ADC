# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 16:42:38 2022

@author: Pushkaraj Joshi
"""
import serial
import time
from datetime import datetime

def Operate(valve_number,duration):
    valve_code=str('\nF'+ str(valve_number)+'\r')
    port.write(valve_code.encode())
    time.sleep(int(duration))
    port.write(valve_code.encode())
    port.close()

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
port = serial.Serial('COM3', 19200)

Operate(valve_number= 1, duration = 3)
