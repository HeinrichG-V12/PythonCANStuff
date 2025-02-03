#!/usr/bin/env python3

import can
import csv
import argparse
import time

# message包含以下属性
# arbitration_id:199
# bitrate_switch:False
# channel:0
# data:bytearray(b'\x00\x00\x00\x00\x00\x00\x04\x04')
# dlc:8
# error_state_indicator:False
# id_type:False
# is_error_frame:False
# is_extended_id:False
# is_fd:False
# is_remote_frame:False
# timestamp:1617861021.10497

# str(message):
# 'Timestamp: 1617861021.104970        ID: 00c7    S                DLC:  8    00 00 00 00 00 00 04 04     Channel: 0'

obj = time.localtime()

l_time = time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputFile', '-if', help="input file name, as blf", type=str, required=True)
    parser.add_argument('--outputFile', '-of', help="output file name, as csv", type=str, required=True)
    
    args = parser.parse_args()

    inputFileName = args.inputFile
    outputFileName = args.outputFile

    log = can.BLFReader(inputFileName)
    log = list(log)

    log_output = []

    data_list = []

    l_time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log[0].timestamp))
    
    log_output.append(['Timestamp', 'Channel', 'BusType', 'FrameType', 'CANID', 'DLC', 'Byte0', 'Byte1', 'Byte2', 'Byte3', 'Byte4', 'Byte5', 'Byte6', 'Byte7'])
    
    for msg in log:
        time_secs = msg.timestamp - log[0].timestamp
        time_secs = '%f' % (time_secs)

        if msg.is_fd:
            can_fd = 'CAN FD'
        else:
            can_fd = 'CAN'
        if msg.bitrate_switch:
            can_fd = can_fd + ': Bitrate Switch'

        if msg.is_error_frame:
            frame_type = 'Error'
        elif msg.is_remote_frame:
            frame_type = 'Remote'
        else:
            frame_type = 'Data'

        if msg.is_extended_id:
            can_id = '0x{:08X}'.format(msg.arbitration_id)
        else:
            can_id = '0x{:03X}'.format(msg.arbitration_id)

        data = ''
        for byte in msg.data:
            data_list.append('{:02X}'.format(byte))

        data_block = ','.join(data_list)
        log_output.append([time_secs, msg.channel, can_fd, frame_type, can_id, msg.dlc, data_block])
        data_list.clear()

    with open(outputFileName, "w", newline='') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerows(log_output)

if __name__ == '__main__':
    main()
