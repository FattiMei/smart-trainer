import serial
from serial.tools import list_ports


def scan_com_ports(blacklist=[]):
    com = {}

    for port in list_ports.comports():
        device = port.device

        if device not in blacklist:
            try:
                ser = serial.Serial(device, timeout=1)
                ser.write(b'INFO\r\n')
                res = ser.readlines()

                if len(res) == 2:
                    name = res[1].decode('utf-8')
                    com[name] = device

            except:
                pass

    return com


if __name__ == '__main__':
    print(scan_com_ports())
