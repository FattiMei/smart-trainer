import time
import asyncio
import argparse
import threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from devscan import scan_for_devices
from sensor import ArduinoAnalogSensor


DEFAULT_WINDOW_SIZE_SECONDS = 10.0
FPS = 30
FRAME_TIME_SECONDS = 1 / FPS


def parse_window_parameters(default_window_size_seconds: float = DEFAULT_WINDOW_SIZE_SECONDS):
    parser = argparse.ArgumentParser(
        prog='logger',
        description='Collects and visualize data from UWB radar and Arduino boards'
    )

    arguments = [
        ('-group'      , str  , 'Group name'                                     ),
        ('-subject'    , str  , 'Subject name'                                   ),
        ('-activity'   , str  , 'Activity name'                                  ),
        ('-info'       , str  , 'Additional information'                         ),
        ('-window_size', float, 'Collection window size in seconds'              ),
        ('-delay'      , float, 'Delay in seconds before starting the collection'),
    ]

    for (name, type, help) in arguments:
        parser.add_argument(name, type=type, help=help)

    args = parser.parse_args()

    if args.window_size is None:
        args.window_size = default_window_size_seconds

    return args


def run_asyncio(sensors, collection_tasks, sensor_ready_event: threading.Event, window_size_seconds):
    async def main(sensors, collection_tasks, sensor_ready_event, window_size_seconds):
        # device discovery
        available_devices = await scan_for_devices()
        for device in available_devices:
            sensors.append(ArduinoAnalogSensor(device))
        sensor_ready_event.set()

        if len(sensors) == 0:
            return

        start_time = time.perf_counter()

        for sensor in sensors:
            collection_tasks.add(
                asyncio.create_task(
                    sensor.collect(
                        start_time=start_time,
                        duration_seconds=window_size_seconds
                    )
                )
            )

        assert(len(collection_tasks) > 0)
        try:
            for task in collection_tasks:
                await task
        except asyncio.CancelledError:
            print('Collection terminated')

    asyncio.run(main(sensors, collection_tasks, sensor_ready_event, window_size_seconds))


FPS = 30
FRAME_TIME_SECONDS = 1 / FPS


if __name__ == '__main__':
    window_parameters = parse_window_parameters()

    # queste strutture condivise tra i due thread ci permettono di comunicare
    sensors = []
    collection_tasks = set()
    sensor_ready_event = threading.Event()

    background_thread = threading.Thread(
        target=run_asyncio,
        args=(
            sensors,
            collection_tasks,
            sensor_ready_event,
            window_parameters.window_size
        )
    )
    background_thread.start()

    # qua dobbiamo aspettare per forza che i sensori siano connessi
    # non c'è async in questo caso, ma è garantito che questo evento
    # si verificherà ad un certo punto
    while not sensor_ready_event.is_set():
        pass

    if len(sensors) == 0:
        print('No devices found... quitting')
        exit()
    else:
        print('Devices found:')
        for sensor in sensors:
            print(f'  * {sensor.device.name} at {sensor.device.port}')

    fig, axes = plt.subplots(1, len(sensors))

    if len(sensors) > 1:
        for i, ax in enumerate(axes):
            sensors[i].init_visualization(ax)
    else:
        sensors[0].init_visualization(axes)

    def update(frame):
        return [
            sensor.update_visualization(time.perf_counter())
            for sensor in sensors
        ]

    def cancel_tasks(_):
        print('Submit task cancellation from closing figure')
        for task in collection_tasks:
            task.cancel()

    fig.canvas.mpl_connect("close_event", cancel_tasks)
    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        frames=int(window_parameters.window_size/FRAME_TIME_SECONDS),
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False,
        repeat=False
    )
    plt.show()
    background_thread.join()
