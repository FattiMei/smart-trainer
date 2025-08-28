import time
import numpy as np
import matplotlib.pyplot as plt

import asyncio
from devscan import scan_for_devices
from sensor import SerialSensor


COLORS = ['red', 'green', 'blue', 'orange']


class DummySerialSensor(SerialSensor):
    def _interpret_raw_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        return None


async def main():
    window_size_seconds = 10.0
    available_devices = await scan_for_devices()

    if available_devices == []:
        print('No compatible device found')
        exit()

    print('Devices found:')
    for device in available_devices:
        print(f'  * {device.name} at {device.port}')

    sensors = [
        DummySerialSensor(device)
        for device in available_devices
    ]

    print(f'Begin sampling window of {window_size_seconds} seconds')
    start_time = time.perf_counter()
    await asyncio.gather(
        *(
            sensor.start_collection(
                start_time=start_time,
                window_duration_seconds=window_size_seconds
            )
            for sensor in sensors
        )
    )
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


if __name__ == '__main__':
    asyncio.run(main())
