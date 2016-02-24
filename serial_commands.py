"""
Created on 02/04/2016, @author: sbaek
  V00
  - initial release
"""

import sys, time
from os.path import abspath, dirname
sys.path.append(dirname(dirname(__file__)))        
sys.path.append('%s/data_aq_lib' % (dirname(dirname(__file__)))) 

import pandas as pd
import time
from data_aq_lib.testlib.enphase_pcu_serial.pcu_serial import PCU as pcuSerial

import data_aq_lib.equipment.sas as sas
import data_aq_lib.equipment.power_meter as pm


def command_power_SerialCom(pcu, load, para, equip, adj='On'): # asj is added in case simply need to put command
    '''
    requires 'command_table.csv' in folder 'source_file'
    the table has,at most, 187 values   
    pts : list of load condition out of rated power in range 0 and 1.0
        e.g. [0.5,0.75,1.0]
    '''
    p_rated= para['p_rated']
    command=pd.read_csv(para['source_path']+'\command_table.csv')  #extract command to determine power transfer

#    ''' set pt 2 mode. boot up with pt 40'''
    pcu.debugger_cmd('pt 2\r')   
    time.sleep(2)
    pcu.debugger_cmd('pt 40\r')   
    time.sleep(2)
        
    i=15  # command '0' is troublesome in case of out of tune - power flow in opposite direction can occur
    while((command['p_ac_out'][i] < int(p_rated*load)) and (i<len(command)-1)):
          i+=1
            
    load_dec=command['dec'][i-1]             
    p_hex=hex(load_dec).split('x')[1]  
    print '\n command p %s\r' %p_hex
    #print '\n command p %02X\r' %p_dec
    pcu.debugger_cmd('p %s\r' %p_hex)   
    time.sleep(1)

    if (adj=='On'):            
        # check power out and compare with load condition - up to 3 iteration..
        item=pm.pm_measure(equip)
        
        i=1
        while((item['p_ac_out']< (p_rated*load*0.996)) and (i<12) and (load_dec<command['dec'][len(command)-1])):  #temp['p_ac_out'][0] is not a single value (number of sample)
            time.sleep(0.5)
            load_dec=load_dec+i*1
            p_hex=hex(load_dec).split('x')[1]  
            print ' command p %s\r' %p_hex
            pcu.debugger_cmd('p %s\r' %p_hex)              
            time.sleep(1.5) #pcu reponse is slower than time.sleep(1.0)!!!!
            item=pm.pm_measure(equip)                       
            i+=1
        
        i=1
        while((item['p_ac_out']> (p_rated*load*1.012)) and (i<12)):  #temp['p_ac_out'] is not a single value (number of sample)
            time.sleep(0.5)
            load_dec=load_dec-i*1
            p_hex=hex(load_dec).split('x')[1]  
            print ' command p %s\r' %p_hex
            pcu.debugger_cmd('p %s\r' %p_hex)              
            time.sleep(1.5)
            item=pm.pm_measure(equip)
            i+=1
            
        print '\n Load : %.1f%% at P_rated=%sW, Eff.=%.1f%%' %(100*float(item['p_ac_out'])/para['p_rated'], para['p_rated'], float(item['eff']))
