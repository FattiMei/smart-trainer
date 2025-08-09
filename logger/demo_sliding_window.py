import time
import numpy as np
import itertools

import matplotlib.pyplot as plt
import matplotlib.animation as animation


FPS = 30
FRAME_TIME_SECONDS = 1 / FPS


class RollingLine:
    def __init__(self, ax, window_size_seconds=3):
        self.window_size_seconds = window_size_seconds

        # conosciamo già a priori l'intera misurazione
        # facciamo in modo di far scorrere la finestra sulla misura
        t = np.linspace(0, 4, num=10000)
        y = 0.5 * (np.sin(t) + np.sin(3*t))

        self.ax = ax
        self.ax.set_title("Rolling line")
        self.ax.set_ylim((-1.0, 1.0))
        self.line = ax.plot(t, y)[0]

        self.update(frame=0)

    def update(self, frame):
        # non si cambiano i punti, ma il sistema di riferimento
        # questo implica la necessità di avere a disposizione
        # il wall time
        self.ax.set_xlim((
            FRAME_TIME_SECONDS * frame,
            FRAME_TIME_SECONDS * frame + self.window_size_seconds
        ))

        return self.line


class RollingImage:
    def __init__(self, ax, window_size_seconds=3):
        self.window_size_seconds = window_size_seconds

        t = np.linspace(0, 4, num=10000)
        x = np.linspace(0,1)
        tt, xx = np.meshgrid(t, x)

        self.ax = ax
        self.ax.set_title("Rolling image")
        self.pcolormesh = ax.pcolormesh(tt, xx, np.sin(tt))

    def update(self, frame):
        self.ax.set_xlim((
            FRAME_TIME_SECONDS * frame,
            FRAME_TIME_SECONDS * frame + self.window_size_seconds
        ))

        return self.pcolormesh


if __name__ == '__main__':
    fig, ax = plt.subplots(2,1)

    sensors = [
        RollingLine(ax[0]),
        RollingImage(ax[1])
    ]

    def update(frame):
        return [
            sensor.update(frame)
            for sensor in sensors
        ]

    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False
    )

    plt.tight_layout()
    plt.show()
