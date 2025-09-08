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

    elif device_name.startswith('Arduino_heartbeat'):
        return sensor.ArduinoHeartbeatSensor

    elif device_name == 'SR250_ESP32':
        return sensor.SR250Sensor

    elif device_name.startswith('Infineon'):
        return sensor.InfineonSensor

    else:
        return None


def run_asyncio(sensors, collection_tasks, sensor_ready_event: threading.Event, window_size_seconds):
    async def main(sensors, collection_tasks, sensor_ready_event, window_size_seconds):
        print('Begin device discovery')
        available_devices = await scan_for_devices()
        for device in available_devices:
            sensor_type = sensor_factory(device.name)
            sensors.append(sensor_type(device))
        sensor_ready_event.set()

        if len(sensors) == 0:
            return

        # TODO: è un problema quando collect prima di init_visualization
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

    plt.ion()
    fig, axes = plt.subplots(len(sensors), 1)

    if len(sensors) > 1:
        for i, ax in enumerate(axes):
            sensors[i].init_visualization(ax)
    else:
        sensors[0].init_visualization(axes)

    def update(frame):
        print(frame)
        return [
            sensor.update_visualization(time.perf_counter())
            for sensor in sensors
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
        for sensor in sensors:
            sensor.update_visualization(time.perf_counter())

        fig.canvas.draw()
        fig.canvas.flush_events()

        t_new = time.perf_counter()
        delta = t_new - t_old

        if delta < FRAME_TIME_SECONDS:
            time.sleep(FRAME_TIME_SECONDS - delta)

        if t_new - t_start > window_parameters.window_size:
            break

    plt.ioff()
    plt.show()
    background_thread.join()

    # salvare tutti i dati in un singolo file
    sensor_map = {}
    for sensor in sensors:
        sensor_map[sensor.device.name] = sensor

    blob = {}

    if 'Arduino_heartbeat' in sensor_map:
        blob['heartbeat'] = np.array(sensor_map['Arduino_heartbeat'].timestamps)

    if 'Infineon_ESP32' in sensor_map:
        sensor = sensor_map['Infineon_ESP32']

        blob['t_infineon'] = np.array(sensor.timestamps)
        blob['frame_infineon'] = np.array(sensor.frames)

    if 'SR250_ESP32' in sensor_map:
        sensor = sensor_map['SR250_ESP32']

        blob['t_sr250'] = np.array(sensor.timestamps)
        blob['frame_sr250'] = np.array(sensor.frames)

    if 'Arduino_breath' in sensor_map:
        blob['breath'] = np.array(sensor_map['Arduino_breath'].timestamps)

    np.savez(
        'out',
        Arduino_heartbeat=blob['heartbeat'],
        t_infineon=blob['t_infineon'],
        frame_infineon=blob['frame_infineon'],
        t_sr250=blob['t_sr250'],
        frame_sr250=blob['frame_sr250'],
        # breath=blob['breath']
    )
