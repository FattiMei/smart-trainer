import time
import serial
import numpy as np
import threading

from enum import Enum
from devscan import Device
from window import SlidingWindow


class CollectionState(Enum):
    WAIT  = 0
    START = 1
    READ  = 2
    STOP  = 3


class AbstractSensor:
    def __init__(self):
        self.state = CollectionState.WAIT
        self.backgroud_thread = threading.Thread(target=self._run)

    def start_collection(self, start_time):
        assert(self.state == CollectionState.WAIT)
        self.start_time = start_time
        self.state = CollectionState.START
        self.backgroud_thread.start()

    def stop_collection(self):
        assert(self.state == CollectionState.READ)
        self.state = CollectionState.STOP
        self.backgroud_thread.join()

    def _run(self):
        raise NotImplementedError


class SerialSensor(AbstractSensor):
    START_MESSAGE = b'START'
    STOP_MESSAGE  = b'STOP'
    BEGIN_MESSAGE = b'BEGIN'
    END_MESSAGE   = b'END'

    def __init__(self, device: Device):
        super().__init__()
        self.timestamps = []
        self.frames = []
        self.device = device

    def _read_raw_frame(self) -> tuple[float, np.ndarray]:
        raw_frame_bytes = []
        found_begin_command = False
        found_end_command = True

        # questo per integrare il sensore SR250_ESP32 che al comando 'START'
        # risponde con una linea prima di iniziare con 'BEGIN'
        while not found_begin_command:
            message = self.device.serial_obj.readline().strip(b'\n\r')
            found_begin_command = (message == SerialSensor.BEGIN_MESSAGE)

        timestamp = time.perf_counter() - self.start_time

        while not found_end_command:
            data = self.device.serial_obj.readline()
            possible_end = data.strip(b'\n\r')

            if data.strip(b'\n\r') == SerialSensor.END_MESSAGE:
                found_end_command = True
            else:
                raw_frame_bytes.append(data)

        return timestamp, np.array(b''.join(raw_frame_bytes))

    def _interpret_raw_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def _run(self):
        while self.state != CollectionState.STOP:
            if self.state == CollectionState.WAIT:
                assert(False)

            elif self.state == CollectionState.START:
                self.state = CollectionState.READ
                self.device.serial_obj.write(SerialSensor.START_MESSAGE)

            elif self.state == CollectionState.READ:
                timestamp, raw_frame = self._read_raw_frame()
                frame = self._interpret_raw_frame(raw_frame)

                self.timestamps.append(timestamp)
                self.frames.append(frame)

        assert(self.state == CollectionState.STOP)
        self.device.serial_obj.write(SerialSensor.STOP_MESSAGE)
