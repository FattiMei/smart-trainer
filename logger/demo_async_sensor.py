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

    async def stop_collection(self):
        pass

    async def _run(self):
        state = CollectionState.START

        while self.state != CollectionState.STOP:
            if self.state == CollectionState.WAIT:
                assert(False)

            elif self.state == CollectionState.START:
                self.state = CollectionState.READ

            elif self.state == CollectionState.READ:
                await asyncio.sleep(np.random.uniform())
                timestamp = time.perf_counter() - self.start_time
                data = np.sin(timestamp) + 0.1*np.random.uniform()

                self.window.push(timestamp, data)
                self.update_visualization_data((
                    self.window.timeq,
                    self.window.dataq
                ))

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


def run_data_collection_on_thread(sensors, start_time):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(
            asyncio.gather(
                *(
                    sensor.start_collection(
                        start_time=start_time,
                        window_duration_seconds=10.0
                    )
                    for sensor in sensors
                )
            )
        )
    finally:
        loop.close()


async def main():
    fig, ax = plt.subplots(1)
    sensor = SimulatedLineSensor(ax, window_size_seconds=3.0)

    # qui dovrei far partire l'acquisizione del sensore
    #   * se faccio un await sul sensor.start_collection()
    #     blocco l'esecuzione su questo thread
    #
    #   * dovrei far partire l'esecuzione su un thread in background...
    background_thread = threading.Thread(
        target=run_data_collection_on_thread,
        args=([sensor], time.perf_counter())
    )
    background_thread.start()

    def update(frame):
        return sensor.update_visualization(time.perf_counter())

    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False
    )
    plt.show()
    background_thread.join()


if __name__ == '__main__':
    asyncio.run(main())
