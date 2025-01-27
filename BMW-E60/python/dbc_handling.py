#!/usr/bin/env python3

from canlib import kvadblib
from canlib import canlib



def main():
    print("--> canlib version:", canlib.dllversion())

    db = kvadblib.Dbc(name = 'e60')

    node = db.new_node(name = 'CAS')

    message = db.new_message(name = 'KLEMMENSTATUS', id = 304, dlc = 5)
    
    message.new_signal(name = 'ALIV_KL', type = kvadblib.SignalType.UNSIGNED, size = kvadblib.ValueSize(startbit= 32, length=4), limits= kvadblib.ValueLimits(min = 0, max = 14))
    message.new_signal(name = 'CHKSM_KL', type = kvadblib.SignalType.UNSIGNED, size = kvadblib.ValueSize(startbit= 36, length=4), limits= kvadblib.ValueLimits(min = 0, max = 15))

    db. write_file ( 'e60.dbc' )
    db. close ()

if __name__ == '__main__':
    main()