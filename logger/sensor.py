import serial
import numpy as np
from time import perf_counter
from devscan import Device

from abc import ABC, abstractmethod
from collections import namedtuple

from pyqtgraph.Qt.QtCore import QThread, pyqtSignal
from vispy.scene import visuals


SensorMeasurement = namedtuple(
    'SensorMeasurement',
    [
        'timestamps',
        'frames'
    ]
)


def sensor_factory(name: str):
    if name == 'Infineon_ESP32':
        return InfineonSensor

    elif name == 'SR250_ESP32':
        return SR250Sensor

    else:
        return None


# ho deciso di misurare contemporaneamente i frame e il timestamp
# dei frame così da produrre un dato primitivo compatibile sia
# con le misure radar sia con le misure asincrone degli altri sensori
class SensorReader(QThread):
    def __init__(self, device: Device, view=None):
        super().__init__()
        self.ser = serial.Serial(device.port, timeout=1)
        self.timestamps = []
        self.frames = []
        self.running = True
        self.view = view

        self.responds_after_start = False

    def read_frame(self) -> np.ndarray:
        raw_frame = np.empty(0, dtype=np.uint8)

        line = self.ser.readline()
        assert(line == b'BEGIN\n')

        while True:
            line = self.ser.readline()

            if line == b'END\n':
                break
            else:
                raw_frame = np.concatenate([
                    raw_frame,
                    np.frombuffer(line, dtype=np.uint8)
                ])

        return raw_frame

    @abstractmethod
    def process_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        pass

    def run(self):
        self.ser.write(b'START')

        if self.responds_after_start:
            _ = self.ser.readline()

        while self.running:
            self.timestamps.append(perf_counter())
            raw_frame = self.read_frame()
            processed_frame = self.process_frame(raw_frame)
            self.frames.append(processed_frame)

        self.ser.write(b'STOP')

    # il sensore non decide mai quando terminare l'acquisizione
    def stop(self):
        self.running = False


    def get_measurements(self) -> SensorMeasurement:
        assert(self.running == False)

        return SensorMeasurement(
            timestamps=np.array(self.timestamps),
            frames=np.array(self.frames)
        )


class InfineonSensor(SensorReader):
    def __init__(self, device: Device, view):
        super().__init__(device, view)
        self.num_ant = 3
        self.num_chirps = 4
        self.samples_per_chirp = 128

    def process_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        # probably the last byte is a newline
        view = raw_frame[:-1].view(np.int16)

        return view.reshape(
            self.num_ant,
            self.num_chirps,
            self.samples_per_chirp
        )


class SR250Sensor(SensorReader):
    def __init__(self, device: Device, view):
        super().__init__(device, view)
        self.taps = 128
        self.range_bins = 120
        self.num_ant = 3
        self.bytes_per_cir = self.taps * 4 *self.num_ant
        self.len_antenna = self.taps*2
        self.window_length = 100

        self.image = visuals.Image(
            np.zeros((self.window_length, self.range_bins)),
            texture_format='auto',
            parent = self.view.scene
        )

        self.responds_after_start = True


    def process_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        view = raw_frame[:-1].view(np.int16).reshape(self.num_ant, -1)

        # for every antenna, removes the first 16 bytes
        # this is probably the time stamp of the measurement but I don't know.
        # this info is obtained by reverse engineering the original logger
        cir_casted_int16 = view[:, 16:].reshape(
            self.num_ant,
            -1,
            2 # stands for real and imaginary part
        )

        cir_complex = cir_casted_int16[:,:,0] + 1j*cir_casted_int16[:,:,1]

        return cir_complex.astype(np.complex64)
