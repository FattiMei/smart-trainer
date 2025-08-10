import time
import serial
import numpy as np
import threading
import matplotlib.pyplot as plt

from time import perf_counter
from devscan import scan_for_devices, Device


class Sensor:
    def __init__(self, device: Device, responds_after_start=False):
        self.name = device.name
        self.timestamps = []
        self.ser = device.serial_obj

        self.responds_after_start = responds_after_start

    def read(self):
        while self.reading:
            begin = self.ser.readline().strip(b'\n\r')
            assert(begin == b'BEGIN')

            timestamp = perf_counter() - self.start_time
            self.timestamps.append(timestamp)

            while True:
                data = self.ser.readline()
                possible_end = data.strip(b'\n\r')

                if possible_end == b'END':
                    break

    def start(self, start_time):
        self.ser.write(b'START')
        self.ser.send_break()
        self.start_time = start_time

        if self.responds_after_start:
            _ = self.ser.readline()

        self.reading = True
        self.read_thread = threading.Thread(target=self.read)
        self.read_thread.start()

    def stop(self):
        self.reading = False
        self.read_thread.join(timeout=2)
        self.ser.write(b'STOP')
        self.ser.send_break()


WINDOW_SIZE_SECONDS = 4
COLORS = ['red', 'green', 'blue', 'orange']


if __name__ == '__main__':
    com = scan_for_devices()
    sensors = []

    if com == []:
        print('No compatible devices found... quitting')
        exit()

    print('Devices found:')
    for device in com:
        responds_after_start = (device.name == 'SR250_ESP32')
        print(f'  * {device.name} at {device.port}, {responds_after_start}')

        sensors.append(Sensor(device, responds_after_start))
    print()

    print(f'Begin sample collection for {WINDOW_SIZE_SECONDS} seconds')
    start_time = perf_counter()
    for sensor in sensors:
        sensor.start(start_time)

    time.sleep(WINDOW_SIZE_SECONDS)

    for sensor in sensors:
        sensor.stop()

    print('Collection completed')
    for i, sensor in enumerate(sensors):
        plt.eventplot(
            sensor.timestamps,
            orientation='horizontal',
            lineoffsets=i,
            label=sensor.name,
            colors=COLORS[i]
        )

    plt.title("Sensor measurements arrival time")
    plt.legend()
    plt.show()
