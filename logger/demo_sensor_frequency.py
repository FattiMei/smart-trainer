import time
import numpy as np
import matplotlib.pyplot as plt

from time import perf_counter
from devscan import scan_for_devices_mt
from sensor import SerialSensor


class DummySerialSensor(SerialSensor):
    def _interpret_raw_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        return None


COLORS = ['red', 'green', 'blue', 'orange']


if __name__ == '__main__':
    window_size_seconds = 10.0
    available_devices = list(scan_for_devices_mt())

    if available_devices != []:
        print('Devices found:')

        for device in available_devices:
            print(f'  * {device.name} at {device.port}')
    else:
        print('No compatible device found')
        exit()

    sensors = [DummySerialSensor(device) for device in available_devices]
    now = time.perf_counter()

    print(f'Begin sampling window of {window_size_seconds} seconds')
    for sensor in sensors:
        sensor.start_collection(now)

    time.sleep(window_size_seconds)

    for sensor in sensors:
        sensor.stop_collection()

    print('Collection completed')
    for i, sensor in enumerate(sensors):
        plt.eventplot(
            sensor.timestamps,
            orientation='horizontal',
            lineoffsets=i,
            label=sensor.device.name,
            colors=COLORS[i]
        )

    plt.title("Sensor measurements arrival time")
    plt.legend()
    plt.show()
