import time
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from sensor import CollectionState, AbstractSensor


class SimulatedLineSensor(AbstractSensor):
    def __init__(self, sliding_window_seconds: float, ax):
        super().__init__(sliding_window_seconds, ax)

        self.ax.set_title('Async line sensor')
        self.ax.set_ylim((-1.2, 1.2))
        self.line = ax.plot([], [], marker='o')[0]

    def update_visualization(self, t: float):
        # TODO: cambiare questa logica, non mi piace.
        t = t - self.window.seconds

        if t < 0:
            t = 0

        self.ax.set_xlim((t, t + self.window.seconds))

        return self.line

    def _run(self):
        while self.state != CollectionState.STOP:
            if self.state == CollectionState.WAIT:
                assert(False)

            elif self.state == CollectionState.START:
                self.state = CollectionState.READ

            elif self.state == CollectionState.READ:
                time.sleep(np.random.uniform())
                timestamp = time.perf_counter() - self.start_time
                data = np.sin(timestamp) + 0.1*np.random.uniform()

                self.window.push(timestamp, data)
                self.line.set_xdata(self.window.timeq)
                self.line.set_ydata(self.window.dataq)


FPS = 30
FRAME_TIME_SECONDS = 1 / FPS


if __name__ == '__main__':
    fig, ax = plt.subplots(1)

    sensor = SimulatedLineSensor(3.0, ax)
    sensor.start_collection()

    def update(frame):
        t = frame * FRAME_TIME_SECONDS
        return sensor.update_visualization(t)

    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False
    )

    plt.show()
    sensor.stop_collection()
