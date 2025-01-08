import canlib

for dev in canlib.connected_devices():
    print(dev.probe_info())
