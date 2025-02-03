#!/usr/bin/env python3

from canlib import kvadblib
from canlib import canlib
from canlib.canlib import ChannelData
from canlib import Frame
from pprint import pprint

from threading import Timer,Thread,Event

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

def setup():
    e60_db = kvadblib.Dbc(filename='../DBCs/e60.dbc')
    
    klemmenstatus_msg = e60_db.get_message_by_name('KLEMMENSTATUS')
    global bound_klemmenstatus
    bound_klemmenstatus = klemmenstatus_msg.bind()

    display_transmission_data_msg = e60_db.get_message_by_name('DISPLAY_TRANSMISSION_DATA')
    global bound_display_transmission_data
    bound_display_transmission_data = display_transmission_data_msg.bind()

    transmission_data_1_msg = e60_db.get_message_by_name('TRANSMISSION_DATA_1')
    global bound_transmission_data_1
    bound_transmission_data_1 = transmission_data_1_msg.bind()

    transmission_data_2_msg = e60_db.get_message_by_name('TRANSMISSION_DATA_2')
    global bound_transmission_data_2
    bound_transmission_data_2 = transmission_data_2_msg.bind()

    networkmanagement_egs_msg = e60_db.get_message_by_name('NETZWERKMANAGEMENT_EGS')
    global bound_networkmanagement_egs
    bound_networkmanagement_egs = networkmanagement_egs_msg.bind()

    global ch0
    ch0 = getChannel(channel=0)

    global klemmenstatus_alive_counter
    klemmenstatus_alive_counter = 0

    global display_transmission_data_alive_counter
    display_transmission_data_alive_counter = 0

    global transmission_data_1_alive_counter
    transmission_data_1_alive_counter = 0

    global bound_display_transmission_data_byte0
    bound_display_transmission_data_byte0 = 0

def shutdown():
    global ch0
    ch0.busOff()
    ch0.close()
    print('Shutdown complete')


def get_klemmenstatus_counter():
    global klemmenstatus_alive_counter
    klemmenstatus_alive_counter += 1

    if klemmenstatus_alive_counter > 14:
        klemmenstatus_alive_counter = 0

    return klemmenstatus_alive_counter

def get_display_transmission_data_counter():
    global display_transmission_data_alive_counter
    display_transmission_data_alive_counter += 1

    if display_transmission_data_alive_counter > 14:
        display_transmission_data_alive_counter = 0

    return display_transmission_data_alive_counter

def get_transmission_data_1_alive_counter():
    global transmission_data_1_alive_counter
    transmission_data_1_alive_counter += 1

    if transmission_data_1_alive_counter > 16:
        transmission_data_1_alive_counter = 0

    return transmission_data_1_alive_counter

def calc_klemmenstatus_crc():    
    temp1_uw = bound_klemmenstatus._frame.id + bound_klemmenstatus._frame.data[0] + bound_klemmenstatus._frame.data[1] + bound_klemmenstatus._frame.data[2] + bound_klemmenstatus._frame.data[3] + (bound_klemmenstatus._frame.data[4] & 0x0f )
    temp1_ub = ((temp1_uw >> 8) & 0xFF) + (temp1_uw & 0xFF)
    checksum = (temp1_ub  & 0x0f) + ((temp1_ub >> 4) & 0x0f)
    return (checksum & 0xF) 

def build_cas_msg():
    global bound_klemmenstatus

    bound_klemmenstatus.ST_KL_R.phys = 0
    bound_klemmenstatus.ST_KL_15.phys = 0
    bound_klemmenstatus.ST_KL_50.phys = 0
    bound_klemmenstatus.ST_KEY_VLD.phys = 1

    bound_klemmenstatus._frame.data[0] = 0x45
    bound_klemmenstatus._frame.data[1] = 0x42
    bound_klemmenstatus._frame.data[2] = 0x39
    bound_klemmenstatus._frame.data[3] = 0xbf

    bound_klemmenstatus.ALIV_KL.phys = get_klemmenstatus_counter()
    bound_klemmenstatus.CHKSM_KL.phys = calc_klemmenstatus_crc()

def build_display_transmission_data_msg():
    global bound_display_transmission_data
    global bound_display_transmission_data_byte0

    bound_display_transmission_data._frame.data[0] = 0x78   # 0x78 (D), 0xb4 (N), 0xc3 (P), 0xd2 (R), 0xe1 (P)
    bound_display_transmission_data._frame.data[1] = 0x0C   # immer 0x0c

    # bound_display_transmission_data._frame.data[2] = 0x8f   # 0x8b, 0x8d, 0x8f (keine Auswirkungen)

    bound_display_transmission_data._frame.data[2] = bound_display_transmission_data_byte0

    bound_display_transmission_data._frame.data[4] = 0xF0   # immer 0xf0
    bound_display_transmission_data._frame.data[5] = 0xFF   # immer 0xff
    bound_display_transmission_data.DISPLAY_TRANSMISSION_ALIV.phys = get_display_transmission_data_counter()
    bound_display_transmission_data.DISPLAY_TRANSMISSION_CONST1.phys = 0xC

def build_transmission_data_1():
    global bound_transmission_data_1

    bound_transmission_data_1.ST_GR_GRB.phys = 3
    bound_transmission_data_1.ST_GRLV_ACV.phys = 0
    bound_transmission_data_1.ST_CCLT.phys = 0
    bound_transmission_data_1.GRDT_REIN.phys = 511.8750
    bound_transmission_data_1.CHKSM_GRB.phys = 0x48
    bound_transmission_data_1.ALIV_GRB.phys = 0xB
    bound_transmission_data_1.ST_MOD_GRB.phys = 0
    bound_transmission_data_1.BLAH.phys = 1
    bound_transmission_data_1.ST_HYPP_ACV.phys = 0x3


    # bound_transmission_data_1.ALIV_GRB.phys = get_transmission_data_1_alive_counter()

def build_transmission_data_2():
    global bound_transmission_data_2

    bound_transmission_data_2.RPM_GRB_TURB.phys = 659
    bound_transmission_data_2.Byte2.phys = 0x00
    bound_transmission_data_2.Byte3.phys = 0xFF

def build_networkmanagement_egs():
    global bound_networkmanagement_egs

    bound_networkmanagement_egs.Byte0.phys = 0x21
    bound_networkmanagement_egs.Byte1.phys = 0x42
    bound_networkmanagement_egs.Byte2.phys = 0xFF
    bound_networkmanagement_egs.Byte3.phys = 0xFF
    bound_networkmanagement_egs.Byte4.phys = 0xFF
    bound_networkmanagement_egs.Byte5.phys = 0xFF
    bound_networkmanagement_egs.Byte6.phys = 0xFF
    bound_networkmanagement_egs.Byte6.phys = 0xFF

def my2s_counter():
    global bound_display_transmission_data_byte0
    bound_display_transmission_data_byte0 += 1

def can_100ms_task():
    global bound_klemmenstatus
    global bound_display_transmission_data
    global bound_transmission_data_1
    global bound_transmission_data_2
    global bound_networkmanagement_egs
    global ch0

    build_cas_msg()

    build_display_transmission_data_msg()

    build_transmission_data_1()

    build_transmission_data_2()

    build_networkmanagement_egs()

    try:
        # ch0.writeWait(bound_klemmenstatus._frame, timeout = 2)
        ch0.writeWait(bound_display_transmission_data._frame, timeout = 2)
        # ch0.writeWait(bound_transmission_data_1._frame, timeout = 2)
        # ch0.writeWait(bound_transmission_data_2._frame, timeout = 2)
        ch0.writeWait(bound_networkmanagement_egs._frame, timeout = 2)
    except canlib.exceptions.CanTimeout:
        print('CAS: timeout aquired!')


def main():
   setup()
   print("--> canlib version:", canlib.dllversion())
   t1 = perpetualTimer(.1, can_100ms_task)
   t2 = perpetualTimer(1, my2s_counter)
   t1.start()
   t2.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        shutdown()