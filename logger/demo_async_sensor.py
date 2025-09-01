import time
import numpy as np
import asyncio
import threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from sensor import CollectionState, AbstractSensor
from window import SlidingWindow


class SimulatedLineSensor(AbstractSensor):
    def __init__(self, ax, window_size_seconds: float):
        super().__init__()
        self.window = SlidingWindow(window_size_seconds)
        self.init_visualization(ax)
        self.start_time = None

    async def collect(self, start_time: float, duration_seconds: float):
        self.start_time = start_time
        state = CollectionState.START

        try:
            async with asyncio.timeout(duration_seconds):
                while True:
                    if state == CollectionState.START:
                        state = CollectionState.READ

                    elif state == CollectionState.READ:
                        await asyncio.sleep(np.random.uniform())
                        timestamp = time.perf_counter() - self.start_time
                        data = np.sin(timestamp) + 0.1*np.random.uniform()

                        self.window.push(timestamp, data)
                        self.update_visualization_data((
                            self.window.timeq,
                            self.window.dataq
                        ))

                    elif state == CollectionState.STOP:
                        break

        except (TimeoutError, asyncio.CancelledError):
            print('sensor collection terminated')

    def init_visualization(self, ax):
        ax.set_title('Async line sensor')
        ax.set_xlim((0.0, self.window.seconds))
        ax.set_ylim((-1.2, 1.2))

        self.line = ax.plot([], [], marker='o')[0]
        self.ax = ax

    # bisognerebbe trovare un modo di aggiornare la visualizzazione
    # senza passare per animation.FuncAnimation
    # in questo modo potrei integrare meglio la libreria Vispy
    def update_visualization(self, t: float):
        if self.start_time is not None:
            deltat = np.clip(
                t - self.start_time - self.window.seconds,
                0.0,
                np.inf
            )
            self.ax.set_xlim((deltat, deltat + self.window.seconds))

        return self.line

    def update_visualization_data(self, data):
        self.line.set_xdata(data[0])
        self.line.set_ydata(data[1])


FPS = 30
FRAME_TIME_SECONDS = 1 / FPS


async def create_cancellable_tasks(coroutines, task_set):
    for coro in coroutines:
        task_set.add(asyncio.create_task(coro))

    try:
        for task in task_set:
            await task
    except asyncio.CancelledError:
        # questo è infatti il comportamento che vogliamo ottenere
        pass


def run_background_data_collection(coroutines, task_set):
    asyncio.run(
        create_cancellable_tasks(coroutines, task_set)
    )


async def main():
    WINDOW_DURATION_SECONDS = 10.0
    fig, ax = plt.subplots(1)

    sensor = SimulatedLineSensor(ax, window_size_seconds=3.0)
    sensors = [sensor]

    collectors = [
        sensor.collect(
            start_time=time.perf_counter(),
            duration_seconds=WINDOW_DURATION_SECONDS
        )
        for sensor in sensors
    ]

    task_group = set()

    def cancel_tasks(_):
        for task in task_group:
            task.cancel()

    background_thread = threading.Thread(
        target=run_background_data_collection,
        args=(
            collectors,
            task_group
        )
    )
    background_thread.start()
    fig.canvas.mpl_connect("close_event", cancel_tasks)

    def update(frame):
        return sensor.update_visualization(time.perf_counter())

    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        frames=int(WINDOW_DURATION_SECONDS/FRAME_TIME_SECONDS),
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False,
        repeat=False
    )
    plt.show()
    background_thread.join()


if __name__ == '__main__':
    asyncio.run(main())
