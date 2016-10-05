"""
Created on 02/24/2016, @author: sbaek
  V00
  - initial release

  V01 07/06/2016
  - def check_fault()

  V02 07/27/2016
  - bootup process has been taken out and moved to main script.  It needs to be there to change registers.

"""

import pandas as pd
from math import *
import sys, time
from os.path import abspath, dirname
sys.path.append(dirname(dirname(__file__)))        
sys.path.append('%s/equipment' % (dirname(dirname(__file__)))) 
import equipment.sas as sas
import equipment.power_meter as pm
import equipment.dvm as dvm
from data_aq_lib.measurement import serial_commands as sc
import data_aq_lib.equipment.ac_source as ac

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
        self.return_str= '\n\n -- Measurement --'
        self.return_str += '\n data_path : %s  ' %self.par['data_path']
        #self.return_str += '\n source_path : %s  ' %self.par['source_path']
        return self.return_str


    def do_measure_pm(self, delay=1, adj=True, check_fault=True, Plim=305, show=False, boot_up=1.0):
        sc.command_p(0.75, self.par, self.eq, adj=False,show=False)
        sas.sas_fixed_adj(self.eq, CURR=14, VOLT=self.par['SAS_volt'], delay=2) # adjust Vdc at 75% load

        data=[]
        if type(self.par['Load_pts']) is str:
            print '\n load pts is not specified'
            self.par['load']=''
            item=pm.pm_measure(self.eq)
            item.update({'scan_time':time.strftime('%H:%M:%S')})
            data.append(item)

        elif type(self.par['Load_pts']) is not str:
            for pts in self.par['Load_pts']:
                Po, Io =sc.command_p(float(pts), self.par, self.eq, adj=adj, delay=1, show=False) #taking data from pm takes time.
                
                ''' fault check '''
                # if power output is abnormally low, it is considered as a fault and shutdown
                if check_fault:
                    for j in range(1, 3):
                        print '.'
                        item, flag=self.check_fault(pts,delay=1)
                        if flag:break
                        else: pass
                        time.sleep(j*0.25) # check 4 time
                else:
                    pass

                load= 100*float(item['p_ac_out'])/float(self.par['p_rated'])
                item.update({'Vdc':self.par['SAS_volt'], 'load_set':int(100*float(pts)),'load':load, 'fault':flag})

                try:
                    temp=dvm.measure_tempc(self.eq)
                    item.update({'Temp':temp})
                except: pass
                data.append(item)

                if show:
                    try:
                        msg = '\n measurement : \n'
                        msg +='  Po : %.1fW, Io : %.2f Arms, Pin : %.1fW, Vdc : %.1fV,\n' %(float(item['p_ac_out']), float(item['amp_ac_out1']),float(item['p_in']),float(item['volt_in']))
                        msg +='  Load : %.1f%% at %.0fW, Eff. : %.1f%% \n' %(100*float(item['p_ac_out'])/self.par['p_rated'], self.par['p_rated'], float(item['eff'])) # put this in try, except. sometimes eff is not available
                        print msg
                        self.par['log'] +=msg
                    except:pass

                if (flag) or (float(item['p_ac_out'])>Plim): # limit output at 310W (default)
                    break
                    
        self.results=data
        return data

    def check_fault(self, pts, delay=0):
        # go to the next voltage if power is smaller than the smallest power requested
        item=pm.pm_measure(self.eq) # to detect fault quickly, get measurement first
        #if float(item['p_ac_out'])< (min(self.par['Load_pts']))*self.par['p_rated']:# does not work, pcu often cannot carry as requested
        #print float(item['p_ac_out']), (0.5*min(self.par['Load_pts']))*self.par['p_rated']
        if float(item['p_ac_out'])< (0.9*pts*self.par['p_rated']):
            self.shutdown()
            msg=' fault..'
            print msg
            self.par['log'] +=msg
            item['eff']= None  #in case of fault, eff does not mean something. flush
            flag=True
        else: flag=False
        time.sleep(delay)

        return item, flag


    def do_measure_tempc(self,time_step=1, duration=1, SAT='off',POWER_METER='On'):
        data = []    #collection of item in dict()  !!!!
        cnt, cnt_max = 0, int(duration/time_step)

        ''' temperature saturation check '''
        if SAT=='On':
            #data, temp_ini, t=self.check_tempc_sat(time_step=time_step, tolerance=0.3)
            data, temp_ini, t=self.check_tempc_sat(time_step=time_step, tolerance=0.1)
        else:pass

        ''' boot-up '''
        ac.set_ac_source(self.eq, mode=self.par['ac_mode'], freq=60.0)
        item=sas.sas_pcu_boot(self.eq, CURR=18, VOLT=self.par['SAS_volt'])      #receive the time of boot-up
        data.append(item)   #inital value when boot-up


        while cnt<cnt_max:
            if (cnt==0 or (time.clock()-t)>time_step*60):
                t=time.clock()  # this update has to be done first, otherwise the processing time is also added.
                cnt=cnt+1

                sc.command_p(float(1.0), self.par, self.eq, adj='Off')          #measurement temperature first before any adjustment.
                temp=dvm.measure_tempc(self.eq)
                item=({'Temp':temp, 'Temp_i':temp_ini, 'Temp_delta':temp-temp_ini})
                timestr=time.strftime("%I:%M:%S")
                datestr=time.strftime(" %m/%d/%Y")
                item.update({'scan_time':timestr, 'scan_date':datestr})

                sas.sas_fixed_adj(self.eq, CURR=18, VOLT=self.par['SAS_volt'])  #adjust Vdc before pm measurement
                sc.command_p(float(1.0), self.par, self.eq, adj='On')           #adjust Po before pm measurement
                if POWER_METER=='On':
                    item.update(pm.pm_measure(self.eq))                         #item in dict
                else: pass
                data.append(item)
        self.results=data                                    #data is list with elements in dict
        return data

    def check_tempc_sat(self, time_step=1, tolerance=0.1):
        #checking temperature is saturated
        data=[]
        t=time.clock()
        cnt, cnt_max=0, 20  #max 20min
        a=[]    #temperary list for temperature

        while (cnt<cnt_max):
            if (cnt==0 or (time.clock()-t)>time_step*60):   #convert time step to minute
                t=time.clock()                              # this update has to be done first, otherwise the processing time is also added.
                cnt=cnt+1
                item=pm.pm_measure(self.eq)                 #item in dict
                timestr=time.strftime("%I:%M:%S")
                datestr=time.strftime(" %m/%d/%Y")
                item.update({'scan_time':timestr})
                item.update({'scan_date':datestr})
                temp=dvm.measure_tempc(self.eq)
                item.update({'Temp':temp})
                data.append(item)

                a.append(temp)
                cnt_rec=3
                if cnt >cnt_rec:
                    diff=max(a[-cnt_rec:])-min(a[-cnt_rec:])
                    if diff<tolerance:
                        temp_ini=sum(a[-cnt_rec:]) / float(len(a[-cnt_rec:]))
                        break
                else:pass
        return data[-cnt_rec:], temp_ini, time.clock()

    def shutdown(self):
        sas.sas_off(self.eq)
        time.sleep(2)
        ac.ac_off(self.eq)
        msg ='\n ================== shut down =================='
        msg +=' %s\n' %time.strftime("%I:%M:%S")
        print msg
        self.par['log'] +=msg
        time.sleep(4)


