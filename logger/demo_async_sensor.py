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
        # in questo caso `t` è il wall-time esterno
        deltat = np.clip(
            t - self.start_time - self.window.seconds,
            0.0,
            np.inf
        )
        self.ax.set_xlim((deltat, deltat + self.window.seconds))

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
    sensor.start_collection(time.perf_counter())

    def update(frame):
        # usando il tempo esatto, anziché il tempo ricavato dall'indice di frame
        # rendiamo lo scorrimento della finestra indipendente dal carico di lavoro
        # durante il frame. Questo significa che non avremo delle belle gif della
        # animazione, amen
        return sensor.update_visualization(time.perf_counter())

    # da analisi preliminari sembra che non sia possibile fare a meno della animation
    # per aggiornare in real time un grafico matplotlib
    #
    # questo rende più difficoltosa l'esplorazione della libreria vispy perché bisognerà
    # riscrivere più parti del programma
    ani = animation.FuncAnimation(
        fig=fig,
        func=update,
        interval=FRAME_TIME_SECONDS*1000,
        cache_frame_data=False
    )

    plt.show()
    sensor.stop_collection()
