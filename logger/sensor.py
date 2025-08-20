import time
import serial
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
    async def start_collection(self, start_time: float, window_duration_seconds: float):
        self.start_time = start_time

        # per il momento uso il meccanismo delle exceptions
        # per terminare preventivamente la task `self._run()`
        # che altrimenti girerebbe all'infinito
        #
        # quindi la gestione della finestra è delegata ai
        # singoli sensori, anche se sono comuni nel comportamento
        try:
            async with asyncio.timeout(window_duration_seconds):
                await self._run()
        except TimeoutError:
            pass

        await self.stop_collection()

    async def stop_collection(self):
        raise NotImplementedError

    async def _run(self):
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

    async def stop_collection(self):
        self.device.writer.write(SerialSensor.STOP_MESSAGE)
        await self.device.writer.drain()

    # valutare di usare i futures per gestire il valore di ritorno
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
            # la facoltà di killare completamente la task `self._run()` (che ha
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

    # qui mi lascerei la possibilità che una task esterna possa interrompere il ciclo
    # e triggerare il comando di STOP
    async def _run(self):
        state = CollectionState.START

        while state != CollectionState.STOP:
            if state == CollectionState.START:
                self.device.writer.write(SerialSensor.START_MESSAGE)
                await self.device.writer.drain()

                state = CollectionState.READ

            elif state == CollectionState.READ:
                timestamp, raw_frame = await self._read_raw_frame()
                frame = self._interpret_raw_frame(raw_frame)

                self.timestamps.append(timestamp)
                self.frames.append(frame)
