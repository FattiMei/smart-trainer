import time
import numpy as np
import threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from time import perf_counter
from window import SlidingWindow


FPS = 30
FRAME_TIME_SECONDS = 1 / FPS


class AsyncLineSensor:
    def __init__(self, ax, window_size_seconds=3):
        self.window = SlidingWindow(window_size_seconds)
        self.window_size_seconds = window_size_seconds

        self.ax = ax
        self.ax.set_title("Async sensor")
        self.ax.set_ylim((-1.0, 1.0))
        self.line = ax.plot([],[], marker='o')[0]

    def read(self):
        while self.reading == True:
            time.sleep(np.random.uniform())

            timestamp = perf_counter() - self.start_time
            data = np.sin(timestamp) + 0.1*np.random.uniform()

            self.window.push(timestamp, data)
            self.line.set_xdata(self.window.timeq)
            self.line.set_ydata(self.window.dataq)

    def start(self):
        self.window.clear()
        self.start_time = perf_counter()

        self.reading = True
        self.read_thread = threading.Thread(target=self.read)
        self.read_thread.start()

    def stop(self):
        self.reading = False
        self.read_thread.join(timeout=2)

    def update(self, t: float):
        t = t - self.window_size_seconds

        if t < 0:
            t = 0

        self.ax.set_xlim((t, t + self.window_size_seconds))

        return self.line


if __name__ == '__main__':
    fig, ax = plt.subplots(1)

    WINDOW_SIZE_SECONDS = 3

    sensor = AsyncLineSensor(ax, WINDOW_SIZE_SECONDS)
    sensor.start()

    def update(frame):
        t = frame * FRAME_TIME_SECONDS
        return sensor.update(t)

    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False
    )

    plt.show()

    sensor.stop()
