#!/usr/bin/env python3

import argparse
import threading
from time import sleep
from canlib import canlib, kvadblib

def get_can_message (msg_name):
    global canDBC
    return canDBC.get_message_by_name(msg_name)

def get_display_transmission_data_counter():
    global display_transmission_data_alive_counter
    display_transmission_data_alive_counter += 1

    if display_transmission_data_alive_counter > 14:
        display_transmission_data_alive_counter = 0

    return display_transmission_data_alive_counter

def consumer_thread(timerSleep, args):
    thread_name = threading.current_thread().name
    canChannel = canlib.openChannel(channel=args.channel, bitrate=canlib.canBITRATE_500K)
    canChannel.iocontrol.local_txecho = False
    canChannel.setBusOutputControl(canlib.canDRIVER_NORMAL)
    canChannel.busOn()
    
    while True:
        try:
            message = canChannel.read()
            # print('Received message with id %X, timestamp: %i' % (message.id, message.timestamp))
        except canlib.exceptions.CanNoMsg:
            # rx buffer is empty
            pass
        except KeyboardInterrupt:
            print('Killing thread %s' % thread_name)
            break

        sleep(timerSleep)
    
    canChannel.busOff()
    canChannel.close()
    
def thread_10ms(timerSleep, args):
    thread_name = threading.current_thread().name
    canChannel = canlib.openChannel(channel=args.channel, bitrate=canlib.canBITRATE_500K)
    canChannel.iocontrol.local_txecho = False
    canChannel.setBusOutputControl(canlib.canDRIVER_NORMAL)
    canChannel.busOn()

    while True:
        try:
            print('blupp')
            sleep(timerSleep)
        except KeyboardInterrupt:
            print('Killing thread %s' % thread_name)
            break

    canChannel.busOff()
    canChannel.close()

def thread_network_egs(timerSleep, args):
    thread_name = threading.current_thread().name
    canChannel = canlib.openChannel(channel=args.channel, bitrate=canlib.canBITRATE_500K)
    canChannel.iocontrol.local_txecho = False
    canChannel.setBusOutputControl(canlib.canDRIVER_NORMAL)
    canChannel.busOn()

    while True:
        try:
            can_message = get_can_message('NETZWERKMANAGEMENT_EGS')
            bound_msg = can_message.bind()
            bound_msg.Byte0.phys = 0x21
            bound_msg.Byte1.phys = 0x42
            bound_msg.Byte2.phys = 0xFF
            bound_msg.Byte3.phys = 0xFF
            bound_msg.Byte4.phys = 0xFF
            bound_msg.Byte5.phys = 0xFF
            bound_msg.Byte6.phys = 0xFF
            bound_msg.Byte6.phys = 0xFF
            
            canChannel.writeWait(bound_msg._frame, timeout = 10)
            sleep(timerSleep)
        except canlib.exceptions.CanTimeout:
            print('%s: timeout aquired!' % thread_name)

        except KeyboardInterrupt:
            print('Killing thread %s' % thread_name)
            break

    canChannel.busOff()
    canChannel.close()

def thread_display_egs_data(timerSleep, args):
    thread_name = threading.current_thread().name
    canChannel = canlib.openChannel(channel=args.channel, bitrate=canlib.canBITRATE_500K)
    canChannel.iocontrol.local_txecho = False
    canChannel.setBusOutputControl(canlib.canDRIVER_NORMAL)
    canChannel.busOn()

    while True:
        try:
            can_message = get_can_message('DISPLAY_TRANSMISSION_DATA')
            bound_msg = can_message.bind()
            bound_msg.Byte0.phys = 0x78
            bound_msg.Byte1.phys = 0x0c
            bound_msg.Byte2.phys = 0x8f
            bound_msg.Byte4.phys = 0xf0
            bound_msg.Byte5.phys = 0xFF

            bound_msg.DISPLAY_TRANSMISSION_CONST1.phys = 0xC
            bound_msg.DISPLAY_TRANSMISSION_ALIV.phys = get_display_transmission_data_counter()
            
            canChannel.writeWait(bound_msg._frame, timeout = 10)
            sleep(timerSleep)
        except canlib.exceptions.CanTimeout:
            print('%s: timeout aquired!' % thread_name)

        except KeyboardInterrupt:
            print('Killing thread %s' % thread_name)
            break

    canChannel.busOff()
    canChannel.close()

if __name__ =="__main__":
    parser = argparse.ArgumentParser(description="Emulates some functionality of E60/E65 EGS")
    parser.add_argument('--channel', '-ch', type=int, default=1, help=('The channel to work with.'), required=True)
    args = parser.parse_args()

    global canDBC
    global display_transmission_data_alive_counter
    canDBC = kvadblib.Dbc(filename='../DBCs/e60.dbc')
    display_transmission_data_alive_counter = 0

    thread1 = threading.Thread(target = consumer_thread, name='consumer_thread', args=(.01,args, ))

    thread2 = threading.Thread(target = thread_10ms, name='producer_thread_10ms', args=(1,args, ))

    thread3 = threading.Thread(target = thread_network_egs, name='thread_network_egs', args=(.9,args, ))

    thread4 = threading.Thread(target = thread_display_egs_data, name='thread_display_egs_data', args=(.2, args,))

    thread1.daemon = True
    thread2.daemon = True
    thread3.daemon = True
    thread4.daemon = True

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()

    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()
    