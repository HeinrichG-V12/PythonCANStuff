#!/usr/bin/env python3

from canlib import kvadblib
from canlib import canlib
from canlib import Frame
from canlib.canlib import ChannelData
from pprint import pprint

from threading import Timer,Thread,Event

can_timeout_ms = 5

class perpetualTimer():

   def __init__(self,t,hFunction):
      self.t=t
      self.hFunction = hFunction
      self.thread = Timer(self.t,self.handle_function)

   def handle_function(self):
      self.hFunction()
      self.thread = Timer(self.t,self.handle_function)
      self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()

asc_db = kvadblib.Dbc(filename='../DBCs/ASC.dbc')
# dme_db = kvadblib.Dbc(filename = '../DBCs/DME.dbc')
smg_db = kvadblib.Dbc(filename='../DBCs/SMG.dbc')

def createGlobalVariables():
    global ch0
    ch0 = getChannel(channel=0)

    global smg_alive_counter
    smg_alive_counter = 0

    global asc_alive_counter
    asc_alive_counter = 0

    # global smg2
    smg2 = smg_db.get_message_by_name('SMG2')

    # global asc1
    asc1 = asc_db.get_message_by_name('ASC1')

    global bound_smg2
    bound_smg2 = smg2.bind()

    global bound_asc1
    bound_asc1 = asc1.bind()

def getChannel (channel=0,
                 openFlags=canlib.canOPEN_ACCEPT_VIRTUAL,
                 bitrate=canlib.canBITRATE_500K,
                 bitrateFlags=canlib.canDRIVER_NORMAL):
    
    ch = canlib.openChannel(channel, openFlags)
    print("Using channel: %s, EAN: %s" % (ChannelData(channel).channel_name,
                                          ChannelData(channel).card_upc_no)
                                              )
    ch.setBusOutputControl(bitrateFlags)
    ch.setBusParams(bitrate)
    ch.busOn()
    return ch

def tearDownChannel(ch):
    ch.busOff()
    ch.close()


def changeGlobal():
    global smg_alive_counter

    smg_alive_counter += 1

    if smg_alive_counter > 15:
        smg_alive_counter = 0

    print (smg_alive_counter)

def send_smg_message():
    global smg_alive_counter
    global bound_smg2

    bound_smg2.DESIRED_GEAR.phys = 0x00
    bound_smg2.LV_GS.phys = 0
    bound_smg2.GEAR_SEL_AUTO.phys = 0
    bound_smg2.STATE_CLUTCH.phys = 1
    bound_smg2.GEAR_INFO.phys = 0x06
    bound_smg2.GEAL_SEL.phys = 0x01
    bound_smg2.PRG_INF_ANZ.phys = 0x06
    
    bound_smg2.LNG_ACC.phys = 0
    bound_smg2.L_GS.phys = 0
    bound_smg2.Byte5_Bit2.phys = 1
    bound_smg2.DT_REINF.phys = 0x392
    bound_smg2.TQ_CLU.phys = 0xf3

    bound_smg2.ALIVE_COUNTER.phys = smg_alive_counter

    bound_smg2.CHKSM_GEAR_INFO.phys = calc_checksum (bound_smg2.GEAR_INFO.phys, smg_alive_counter)

    smg_alive_counter += 1

    if smg_alive_counter > 15:
        smg_alive_counter = 0

    try:
        ch0.writeWait(bound_smg2._frame, timeout = can_timeout_ms)
    except canlib.exceptions.CanTimeout:
        print('SMG: timeout aquired!')

def send_asc_message():
    global asc_alive_counter
    global bound_asc1

    bound_asc1.ASC_ALIVE.phys = asc_alive_counter

    asc_alive_counter += 1

    if asc_alive_counter > 15:
        asc_alive_counter = 0

    try:
        ch0.writeWait(bound_asc1._frame, timeout = can_timeout_ms)
    except canlib.exceptions.CanTimeout:
        print('ASC: timeout aquired!')


def calc_checksum (gear_info, alive_counter):
    tmp1 = (int(alive_counter) ^ int(gear_info))
    tmp2 = ~(tmp1)
    tmp3 = (tmp2 & 0x0f)
    tmp4 = (tmp3 << 4)
    # tmp5 = (tmp4 | alive_counter)
    return tmp3

def main():
    createGlobalVariables()

    print("--> canlib version:", canlib.dllversion())

    t1 = perpetualTimer(.01, send_smg_message)
    t2 = perpetualTimer(.01, send_asc_message)
    t1.start()
    t2.start()

if __name__ == '__main__':
    main()