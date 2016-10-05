"""
Created on 02/24/2016, @author: sbaek
  V00
  - initial release

  V01 03/02/2016
  - p command has 2 bytes,(8bits) for hormet

  V02 04/06/2016
  - no longer use table.csv.
  - 1 bit =0.01/128.0 = 0.078mA, e.g. dc_step=50, 0.01/128.0*50 = 4mA -> 0.96W
  - add com_adj(load, para, equip, bit, step)

  V03 07/06/2016
  - write(cmd, delay)

  V04 08/9/2016
  - para['ac_mode'] =='LL', 'LL_HVRT', 'LN'

"""
import sys, time
from os.path import abspath, dirname
sys.path.append(dirname(dirname(__file__)))        
sys.path.append('%s/data_aq_lib' % (dirname(dirname(__file__)))) 

import pandas as pd
from data_aq_lib.equipment import serialcom
import data_aq_lib.equipment.power_meter as pm


def command_p(load, para, equip, adj=True, dec_step=50, tolerence=1.5, delay=1, show=True): #,
    '''
    :param load: float portion of para['p_rated']  e.g. 0.5
    :param para: dict() with para['p_rated']
    :param equip: dict()
    :param adj: Bool
    :param dec_step: int
    :param tolerence: float
    :return: None

    - tolerance in Watt,  asj is added in case simply need to put command
    - it takes time to receive data from pm.  it can be skipped by setting show.
    '''
    ser=serialcom.SerialCom()
    p_rated= para['p_rated']
    bits=7
    #bits=6
   
    if para['ac_mode'] =='LL':
        Po=p_rated*load
        Io=Po/240.0  #[rms], 'LL' mode, 240Vrms
        Ipeak=Io*2**0.5
        #print '\n Po : %.1f, amp_ac : %.2f Arms at %.1fW, P_rated=%.1fW ' %(Po, Ipeak/2**0.5, Po, p_rated)        
        p_dec=int(Ipeak/(0.01/2**bits))
        ser.write(cmd='pt 2\r', delay=delay)

    elif para['ac_mode'] =='LL_p10':
        Po=p_rated*load
        Io=Po/(240.0*1.1)  #[rms] 'LL_HVRT' mode, 240*1.1=264V
        Ipeak=Io*2**0.5
        #print '\n Po : %.1f, amp_ac : %.2f Arms at %.1fW, P_rated=%.1fW ' %(Po, Ipeak/2**0.5, Po, p_rated)
        p_dec=int(Ipeak/(0.01/2**bits))
        ser.write(cmd='pt 2\r', delay=delay)

    elif para['ac_mode'] =='LN':
        Po=p_rated*load
        Io=Po/208.0  #[rms], 'LN' mode, 208V
        Ipeak=Io*2**0.5
        #print '\n Po : %.1f, amp_ac : %.2f Arms at %.1fW, P_rated=%.1fW ' %(Po, Ipeak/2**0.5, Po, p_rated)
        p_dec=int(Ipeak/(0.01/2**bits))
        ser.write(cmd='pt 2\r', delay=delay)

    elif para['ac_mode'] =='LN_n10':
        Po=p_rated*load
        Io=Po/(208.0*0.9)  #[rms], 'LN' mode, 208V
        Ipeak=Io*2**0.5
        #print '\n Po : %.1f, amp_ac : %.2f Arms at %.1fW, P_rated=%.1fW ' %(Po, Ipeak/2**0.5, Po, p_rated)
        p_dec=int(Ipeak/(0.01/2**bits))
        ser.write(cmd='pt 2\r', delay=delay)
        
    msg = '\n command :\n'
    msg += '  Po : %.1f, Io : %.2f Arms, load: %.2f\n' %(Po, Io, load)

    print msg
    para['log'] +=msg

    if adj:
        diff, p_dec, eff=com_adj(ser, load, para, equip, p_dec, step=0, delay=delay)  #command as calculated
        for i in range(1, 20):
            if ( abs(diff) < tolerence ):
                break
            elif ( diff < -tolerence*3.5 ):
                diff, p_dec, eff=com_adj(ser,load, para, equip, p_dec, step=dec_step*3, delay=delay)
            elif ( diff < -tolerence*2.5 ):
                diff, p_dec, eff=com_adj(ser,load, para, equip, p_dec, step=dec_step*2, delay=delay)
            elif ( diff < -tolerence*1.5 ):
                diff, p_dec, eff=com_adj(ser,load, para, equip, p_dec, step=dec_step*1, delay=delay)
            elif ( diff > tolerence*1.5 ):
                diff, p_dec, eff=com_adj(ser,load, para, equip, p_dec, step=-dec_step*1, delay=delay)
            elif ( diff > tolerence*2.5 ):
                diff, p_dec, eff=com_adj(ser,load, para, equip, p_dec, step=-dec_step*2, delay=delay)
            else:pass
    else:
        p_hex=hex(p_dec)
        p_hex=p_hex.split('x')[1]
        ser.write(cmd='p %s\r' %p_hex, delay=delay)

    if show:show(equip)      # taking data from pm takes time.
    else:pass
    ser.close()
    return Po, Io

def com_adj(ser,load, para, equip, bit, step=0, delay=1):
    p_rated= para['p_rated']
    bit=bit+step

    #if bit < 22390:     #~290W max    
    p_hex=hex(bit+step)
    p_hex=p_hex.split('x')[1]
    ser.write(cmd='p %s\r' %p_hex, delay=delay)

    time.sleep(1) #pcu reponse is slower than time.sleep(1.0)!!!!
    item=pm.pm_measure(equip)
    diff=item['p_ac_out']-p_rated*load  #update diff
    return diff, bit, float(item['eff'])

def show(equip):
    item=pm.pm_measure(equip)
    try:        
        print '\n measurement :'
        print '  Po : %.1fW, Io : %.2fArms, Pin : %.1fW, Vdc : %.1fV,' %(float(item['p_ac_out']), float(item['amp_ac_out1']),float(item['p_in']),float(item['volt_in']))
        print '  Load : %.1f%% at %sW, Eff. : %.1f%%' %(100*float(item['p_ac_out'])/para['p_rated'], para['p_rated'], float(item['eff']))
    except:pass


