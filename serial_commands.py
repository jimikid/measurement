"""
Created on 02/24/2016, @author: sbaek
  V00
  - initial release
"""
import sys, time
from os.path import abspath, dirname
sys.path.append(dirname(dirname(__file__)))        
sys.path.append('%s/data_aq_lib' % (dirname(dirname(__file__)))) 

import pandas as pd
from data_aq_lib.equipment import serialcom
import data_aq_lib.equipment.power_meter as pm


def command_p(load, para, equip, adj='On'): # asj is added in case simply need to put command
    '''
    requires 'command_table.csv' in folder 'source_file'
    the table has,at most, 187 values   
    pts : list of load condition out of rated power in range 0 and 1.0
        e.g. [0.5,0.75,1.0]
    '''
    ser=serialcom.SerialCom()

    p_rated= para['p_rated']
    command=pd.read_csv(para['source_path']+'\command_table.csv')  #extract command to determine power transfer

#    ''' set pt 2 mode. boot up with pt 40'''

    i=15  # command '0' is troublesome in case of out of tune - power flow in opposite direction can occur
    while((command['p_ac_out'][i] < int(p_rated*load)) and (i<len(command)-1)):
          i+=1
            
    load_dec=command['dec'][i-1]             
    p_hex=hex(load_dec).split('x')[1]  
    #print '\n command p %s\r' %p_hex
    #print '\n command p %02X\r' %p_dec

    ser.write(cmd='p %s\r' %p_hex)

    if (adj=='On'):            
        # check power out and compare with load condition - up to 3 iteration..
        item=pm.pm_measure(equip)
        
        i=1
        while((item['p_ac_out']< (p_rated*load*0.996)) and (i<12) and (load_dec<command['dec'][len(command)-1])):  #temp['p_ac_out'][0] is not a single value (number of sample)
            time.sleep(0.5)
            load_dec=load_dec+i*1
            p_hex=hex(load_dec).split('x')[1]
            ser.write(cmd='p %s\r' %p_hex)
            time.sleep(1) #pcu reponse is slower than time.sleep(1.0)!!!!
            item=pm.pm_measure(equip)                       
            i+=1
        
        i=1
        while((item['p_ac_out']> (p_rated*load*1.012)) and (i<12)):  #temp['p_ac_out'] is not a single value (number of sample)
            time.sleep(0.5)
            load_dec=load_dec-i*1
            p_hex=hex(load_dec).split('x')[1]
            ser.write(cmd='p %s\r' %p_hex)
            time.sleep(1)
            item=pm.pm_measure(equip)
            i+=1
            
        print '\n Load : %.1f%% at P_rated=%sW, Eff.=%.1f%%' %(100*float(item['p_ac_out'])/para['p_rated'], para['p_rated'], float(item['eff']))
