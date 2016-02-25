"""
Created on 02/24/2016, @author: sbaek
  V00
  - initial release
"""

import pandas as pd

import sys, time
from os.path import abspath, dirname
sys.path.append(dirname(dirname(__file__)))        
sys.path.append('%s/equipment' % (dirname(dirname(__file__)))) 
import equipment.sas as sas
import equipment.power_meter as pm
from data_aq_lib.measurement import serial_commands as sc

class Measurement:
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
        self.results=pd.DataFrame()
        self.flag='up'        
        
        try:self.pcu=equip['pcu']
        except:pass
    
    def __str__(self):
        self.return_str= '\n\n -- class measurement --' 
        self.return_str += '\n data_path : %s  ' %self.par['data_path']
        self.return_str += '\n source_path : %s  ' %self.par['source_path']
        return self.return_str       


    def do_measure(self):     
        ''' initiation '''
        time.sleep(3)
        sas.sas_fixed(self.eq, CURR=15, VOLT=self.par['SAS_volt'])
        time.sleep(1)

        data=[] 
        if type(self.par['Load_pts']) is str:
            print '\n load pts is not specified'
            self.par['load']=''
            item=pm.pm_measure(self.eq)
            item.update({'scan_time':time.strftime('%H:%M:%S')})
            data.append(item) 
                
        elif type(self.par['Load_pts']) is not str:
            for i in self.par['Load_pts']:
                sc.command_p(float(i), self.par, self.eq, adj='On')
                
                item=pm.pm_measure(self.eq)
                item.update({'load_set':int(100*float(i))})  # add load information on para in dict format 
                
                load= 100*float(item['p_ac_out'])/float(self.par['p_rated'])                
                item.update({'load':load})  # add load information on para in dict format 
                item.update({'scan_time':time.strftime('%H:%M:%S')})
                data.append(item)       
                time.sleep(4)
                
        self.results=data 



