import time
import serial
import serial_asyncio
import asyncio
import numpy as np

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
        pass

    async def collect(self, start_time: float, duration_seconds: float):
        raise NotImplementedError


class SerialSensor(AbstractSensor):
    START_MESSAGE = b'START'
    STOP_MESSAGE  = b'STOP'
    BEGIN_MESSAGE = b'BEGIN'
    END_MESSAGE   = b'END'

    def __init__(self, device: Device, sliding_window_duration_seconds: float = 3.0):
        super().__init__()
        self.timestamps = []
        self.frames = []
        self.device = device
        self.window = SlidingWindow(sliding_window_duration_seconds)

        self.start_time = None

    async def collect(self, start_time: float, duration_seconds: float):
        self.start_time = start_time
        state = CollectionState.START

        try:
            async with asyncio.timeout(duration_seconds):
                while True:
                    if state == CollectionState.START:
                        self.device.writer.write(SerialSensor.START_MESSAGE)
                        await self.device.writer.drain()

                        state = CollectionState.READ

                    elif state == CollectionState.READ:
                        timestamp, raw_frame = await self._read_raw_frame()
                        frame = self._interpret_raw_frame(raw_frame)

                        self.timestamps.append(timestamp)
                        self.frames.append(frame)

                        self.window.push(timestamp, frame)
                        self.update_visualization_data((
                            self.window.timeq,
                            self.window.dataq
                        ))

                    elif state == CollectionState.STOP:
                        break

        except (TimeoutError, asyncio.CancelledError):
            self.device.writer.write(SerialSensor.STOP_MESSAGE)
            await self.device.writer.drain()
            print(f'Sensor collection terminated for {self.device.name}')

    async def _read_raw_frame(self) -> tuple[float, np.ndarray]:
        raw_frame_bytes = []
        found_begin_command = False
        found_end_command = True

        # questo per integrare il sensore SR250_ESP32 che al comando 'START'
        # risponde con una linea prima di iniziare con 'BEGIN'
        while not found_begin_command:
            raw_message = await self.device.reader.readline()
            message = raw_message.strip(b'\n\r')

            # questo ciclo potrebbe non terminare mai: in caso di mancata lettura
            # il flusso di questa corutine è bloccato in un `await`.
            # questo significa che restituisco il controllo all'event loop che ha
            # la facoltà di killare completamente la task `self.collect()` (che ha
            # a sua volta chiamato questa coroutine)
            found_begin_command = (message == SerialSensor.BEGIN_MESSAGE)

        timestamp = time.perf_counter() - self.start_time

        while not found_end_command:
            data = await self.device.reader.readline()
            possible_end = data.strip(b'\n\r')

            if data.strip(b'\n\r') == SerialSensor.END_MESSAGE:
                found_end_command = True
            else:
                raw_frame_bytes.append(data)

        return timestamp, np.array(b''.join(raw_frame_bytes))

    def _interpret_raw_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def init_visualization(self, ax):
        raise NotImplementedError

    def update_visualization(self, t: float):
        raise NotImplementedError

    def update_visualization_data(self, data):
        raise NotImplementedError


class ArduinoAnalogSensor(SerialSensor):
    def __init__(self, device: Device, sliding_window_duration_seconds: float = 3.0, maxval: float = 1024.0):
        self.maxval = maxval
        super().__init__(device, sliding_window_duration_seconds)

    def _interpret_raw_frame(self, raw_frame: np.ndarray) -> np.ndarray:
        # interpreta i byte come se fossero stringhe
        return np.array([100])

    def init_visualization(self, ax):
        ax.set_title('Arduino analog sensor')
        ax.set_xlim((0.0, self.window.seconds))
        ax.set_ylim((0, self.maxval))

        self.line = ax.plot([], [], marker='o')[0]
        self.ax = ax

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
