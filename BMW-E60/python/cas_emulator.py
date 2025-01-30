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
    cas_db = kvadblib.Dbc(filename='../DBCs/e60.dbc')
    klemmenstatus_msg = cas_db.get_message_by_name('KLEMMENSTATUS')
    global bound_klemmenstatus
    bound_klemmenstatus = klemmenstatus_msg.bind()

    global ch0
    ch0 = getChannel(channel=0)

    global klemmenstatus_alive_counter
    klemmenstatus_alive_counter = 0

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

def calc_klemmenstatus_crc():
    # print('Byte 4: 0x{0:02x}'.format(bound_klemmenstatus._frame.data[4] & 0x0f ))
    
    temp1_uw = bound_klemmenstatus._frame.id + bound_klemmenstatus._frame.data[0] + bound_klemmenstatus._frame.data[1] + bound_klemmenstatus._frame.data[2] + bound_klemmenstatus._frame.data[3] + (bound_klemmenstatus._frame.data[4] & 0x0f )
    
    # print('tmp1: 0x{0:02x}'.format(temp1_uw))

    # high_byte = (({temp1_uw} >> 8) & 0xFF)
    # low_byte = (temp1_uw} & 0xFF)

    temp1_ub = ((temp1_uw >> 8) & 0xFF) + (temp1_uw & 0xFF)

    checksum = (temp1_ub  & 0x0f) + ((temp1_ub >> 4) & 0x0f)

    # print('checksum,: 0x{0:01x}, modified : 0x{1:01x}'.format(checksum, ((checksum) & 0xF)))

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

def build_egs1_msg():
    global egs_message1
    egs_message1 = Frame(id_=466, data=bytearray(b'\xC3\x0C\x8F\x1C\xF0\xFF'))

def can_100ms_task():
    global bound_klemmenstatus
    global ch0

    build_cas_msg()

    build_egs1_msg()

    try:
        i = 0
        ch0.writeWait(bound_klemmenstatus._frame, timeout = 2)
        # ch0.writeWait(egs_message1, timeout = 2)
    except canlib.exceptions.CanTimeout:
        print('CAS: timeout aquired!')


def main():
   setup()
   print("--> canlib version:", canlib.dllversion())
   t1 = perpetualTimer(.1, can_100ms_task)
   t1.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        shutdown()