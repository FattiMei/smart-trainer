import numpy as np
import time
import asyncio
import argparse
import threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import sensor
from devscan import scan_for_devices


DEFAULT_WINDOW_SIZE_SECONDS = 10.0


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


def sensor_factory(device_name: str):
    if device_name == 'Arduino_analog':
        return sensor.ArduinoAnalogSensor

    elif device_name.startswith('Arduino'):
        return sensor.ArduinoEventSensor

    elif device_name == 'SR250_ESP32':
        return sensor.SR250Sensor

    elif device_name.startswith('Infineon'):
        return sensor.InfineonSensor

    else:
        return None


def run_asyncio(sensors: dict, collection_tasks, sensor_ready_event: threading.Event, window_size_seconds):
    async def main(sensors, collection_tasks, sensor_ready_event, window_size_seconds):
        print('Begin device discovery')
        available_devices = await scan_for_devices()
        for device in available_devices:
            name = device.name
            sensors[name] = sensor_factory(name)(device)
        sensor_ready_event.set()

        if len(sensors) == 0:
            return

        # TODO: è un problema quando collect prima di init_visualization
        start_time = time.perf_counter()

        for sensor in sensors.values():
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
    sensors = {}
    event_sensors = []
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
        for name, sensor in sensors.items():
            name = sensor.device.name
            print(f'  * {name} at {sensor.device.port}')

            if name.startswith('Arduino'):
                event_sensors.append(sensor)

    if len(event_sensors) > 0:
        plt.ion()
        fig, axes = plt.subplots(len(event_sensors), 1)

        if len(event_sensors) > 1:
            for i, ax in enumerate(axes):
                event_sensors[i].init_visualization(ax)
        else:
            event_sensors[0].init_visualization(axes)

        plt.tight_layout()

        def update(frame):
            print(frame)
            return [
                sensor.update_visualization(time.perf_counter())
                for sensor in event_sensors
            ]

        def cancel_tasks(_):
            print('Submit task cancellation from closing figure')
            for task in collection_tasks:
                task.cancel()

        fig.canvas.mpl_connect("close_event", cancel_tasks)

        # faccio un loop manuale per rendere framerate independent la visualizzazione
        t_old = time.perf_counter()
        t_start = t_old
        while True:
            for sensor in event_sensors:
                sensor.update_visualization(time.perf_counter())

            fig.canvas.draw()
            fig.canvas.flush_events()

            t_new = time.perf_counter()
            delta = t_new - t_old
            t_old = t_new

            if delta < FRAME_TIME_SECONDS:
                time.sleep(FRAME_TIME_SECONDS - delta)

            if t_new - t_start > window_parameters.window_size:
                break

        plt.ioff()
        plt.show()

    background_thread.join()

    # non produciamo le finestre, ma teniamo il dato nella sua forma originale
    # questo permette a utenti generici di fare le loro analisi senza la nostra
    # impostazione
    blob = {}
    for sensor in sensors.values():
        blob.update(sensor.save())

    np.save('out.npy', blob)

    # così si va a leggere
    # read_dictionary = np.load('my_file.npy',allow_pickle='TRUE').item()
