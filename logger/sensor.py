import time
import serial
import numpy as np
import threading

from enum import Enum
from devscan import Device
from window import SlidingWindow


class CollectionState(Enum):
    WAIT = 0
    START = 1
    READ = 2
    STOP = 3


class AbstractSensor:
    def __init__(self, sliding_window_seconds: float, ax):
        self.window = SlidingWindow(sliding_window_seconds)
        self.ax = ax
        self.timestamps = []
        self.frames = []

        self.state = CollectionState.WAIT
        self.backgroud_thread = threading.Thread(target=self._run)

    # è necessario dare una reference di tempo esterna perché nel caso
    # in cui si facciano partire più sensori i sistemi di riferimento
    # devono essere allineati.
    #
    # nel caso in cui ogni sensore usi il proprio sistema di riferimento
    # i dati potrebbero essere sfasati di qualche millisecondo, giusto
    # il tempo di eseguire la funzione `start_collection`. Stiamo parlando
    # di millisecondi, è assolutamente irrilevante ai nostri scopi, però
    # è importante fare questo ragionamento
    def start_collection(self, start_time):
        assert(self.state == CollectionState.WAIT)
        self.start_time = start_time
        self.state = CollectionState.START
        self.backgroud_thread.start()

    def stop_collection(self):
        assert(self.state == CollectionState.READ)
        self.state = CollectionState.STOP
        self.backgroud_thread.join(timeout=2)

    def update_visualization(self, t: float):
        raise NotImplemented

    def _run(self):
        raise NotImplemented
