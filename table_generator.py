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
import equipment.power_meter as pm
from data_aq_lib.equipment import serialcom

class table_gen:
    """
           __INIT__     
           __STR__      
           
    inputs
            para=                - type:dict
            equip=                - type:dict
    """

    def __init__(self, para, equip):
        self.return_str= ''   
        self.par=para
        self.eq=equip
        self.ser=serialcom.SerialCom()
        #self.pcu=equip['SERIAL']

    def __str__(self):
        self.return_str= '\n\n class table_gen \n' 
        self.return_str += '\n data_path : %s  ' %self.par['data_path']
        self.return_str += '\n source_path : %s  ' %self.par['source_path']
        #return_str += '\n save : %s  ' %self.new_file
        return self.return_str    
    
    def generate(self, SAS_volt=32, show ='On', max_power=280):    
        # return flag 'down' in case of failure of boot-up
        global data
        power_limit= 300.0
        d, h, pi,po=[], [], [], []
        """ in case of out of tune, power can flow in opposite direction!! carefull"""

  
        start, end =20, 280    
        hexa=hex(start).split('x')[1]
        self.ser.write(cmd='p %s\r' %hexa)
        time.sleep(3)  # need time to settle down
        
        for i in range(start, end, 1):    
            time.sleep(0.4)  # power is not measured in real time when avg function is on at wt500
            dec=i
            hexa=hex(dec).split('x')[1]
            self.ser.write(cmd='p %s\r' %hexa, delay=0.1)
            #self.pcu.debugger_cmd('p %02X\r' %dec)  
            item=pm.pm_measure(self.eq)            
            d.append({'dec':dec,'hexa':hexa,'p_in':item['p_in'],'p_ac_out':item['p_ac_out']})              
            df=pd.DataFrame(d)    #df should not be declared as global in main script.. kept updated..          
            if show =='On': print '\n pin : %.2f W, pout: %.2f W,  Vdc:%.2f V' %(item['p_in'], item['p_ac_out'], item['volt_in'])
            
            if len(d)>8:
                if int(d[i-start]['p_ac_out']-d[i-start-6]['p_ac_out']) <4 or d[i-start]['p_ac_out']>power_limit:break  #if output power is not increase enough comparing to Po prior to 5 pts                                             
            else:
                pass
            
            if (int(item['p_ac_out'])>max_power): #limite the power at 280W in
                break
        
        name=self.par['source_path']+'/%s.csv' %'command_table'
        print '\n save at %s' %name
        df.to_csv(self.par['source_path']+'/%s.csv' %'command_table') 
        print  '\n %s' %time.strftime("%a, %d %b %Y %H:%M:%S")
