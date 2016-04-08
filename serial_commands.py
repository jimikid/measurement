"""
Created on 02/24/2016, @author: sbaek
  V00
  - initial release

  V01 03/02/2016
  - p command has 2 bytes,(8bits) for hormet

  V02 04/06/2016
  - no longer use table.csv.
  - add com_adj(load, para, equip, bit, step)

"""
import sys, time
from os.path import abspath, dirname
sys.path.append(dirname(dirname(__file__)))        
sys.path.append('%s/data_aq_lib' % (dirname(dirname(__file__)))) 

import pandas as pd
from data_aq_lib.equipment import serialcom
import data_aq_lib.equipment.power_meter as pm


def command_p(load, para, equip, adj='On', dec_step=50, tolerence=1.5): #, tolerance in Watt,  asj is added in case simply need to put command
    '''
    requires 'command_table.csv' in folder 'source_file'
    the table has,at most, 187 values   
    pts : list of load condition out of rated power in range 0 and 1.0
        e.g. [0.5,0.75,1.0]
        
    1 bit =0.01/128.0 = 0.078mA
    dc_step=50, 0.01/128.0*50 = 4mA -> 0.96W
    '''
    ser=serialcom.SerialCom()    

    p_rated= para['p_rated']
   
    if para['ac_mode'] =='LL':
        Ipeak=p_rated*load/240.0*2**.5  #'LL' mode, 240Vrm
        #print '\n amp_ac : %.2f Arms' %(Ipeak/2**0.5)        
        bit=int(Ipeak/(0.01/128))   
    
        ser.write(cmd='pt 2\r')
        time.sleep(2)
        
        diff, bit, eff=com_adj(load, para, equip, bit, step=0)  #command as calculated
        time.sleep(1)
    
        if (adj=='On'):        
            for i in range(1, 20):  
                if ( abs(diff) < tolerence ):
                    break
                elif ( diff < -tolerence*3.5 ):
                    diff, bit, eff=com_adj(load, para, equip, bit, step=dec_step*3) 
                elif ( diff < -tolerence*2.5 ):
                    diff, bit, eff=com_adj(load, para, equip, bit, step=dec_step*2)                    
                elif ( diff < -tolerence*1.5 ):
                    diff, bit, eff=com_adj(load, para, equip, bit, step=dec_step*1)                    
                elif ( diff > tolerence*1.5 ):
                    diff, bit, eff=com_adj(load, para, equip, bit, step=-dec_step*1)   
                elif ( diff > tolerence*2.5 ):
                    diff, bit, eff=com_adj(load, para, equip, bit, step=-dec_step*2)
                    
            item=pm.pm_measure(equip)    
            print '\n Load : %.1f%% at P_rated=%sW, Eff.=%.1f%%' %(100*float(item['p_ac_out'])/para['p_rated'], para['p_rated'], float(item['eff']))


def com_adj(load, para, equip, bit, step=0):    
    ser=serialcom.SerialCom()    
    p_rated= para['p_rated']
    bit=bit+step
    
    if bit < 22390:     #~290W max
        p_hex=hex(bit+step)        
        p_hex=p_hex.split('x')[1]
        ser.write(cmd='p %s\r' %p_hex)
        
        time.sleep(1) #pcu reponse is slower than time.sleep(1.0)!!!!        
        item=pm.pm_measure(equip)
        diff=item['p_ac_out']-p_rated*load  #update diff
    return diff, bit, float(item['eff'])
