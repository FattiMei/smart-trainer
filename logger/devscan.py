import time
import asyncio
import serial
import serial_asyncio
from serial.tools import list_ports
from dataclasses import dataclass

INFO_MESSAGE = b'INFO'


@dataclass
class Device:
    name: str
    port: str
    reader: asyncio.streams.StreamReader
    writer: asyncio.streams.StreamWriter


async def perform_handshake(port: str) -> Device:
    try:
        reader, writer = await serial_asyncio.open_serial_connection(url=port)
    except:
        return None

    # l'apertura di una comunicazione seriale con i device Arduino
    # causa un reset della scheda che la rende irrangiungibile per
    # un paio di secondi
    await asyncio.sleep(3)

    # questo è il protocollo legacy. Non possiamo modificarlo perché
    # non sappiamo modificare il firmware delle schede ESP32
    writer.write(INFO_MESSAGE)
    await writer.drain()

    # il sensore SR250_ESP32 risponde al comando INFO con due linee:
    #   * "I (%d) uwb_session: INFO command received"
    #   * "SR250_ESP32"
    #
    # per includere questa eccezione (non sapendo distinguere a priori il device dalla porta)
    # implemento la soluzione sotto
    response = await reader.readline()
    if b'uwb_session: INFO command received' in response:
        response = await reader.readline()

    name = response.decode('ascii', errors='ignore').strip('\n\r')

    return Device(name, port, reader, writer)


async def perform_handshake_with_timeout(port: str, timeout_seconds):
    device = None

    try:
        async with asyncio.timeout(timeout_seconds):
            device = await perform_handshake(port)
    except TimeoutError:
        print(f'[WARNING]: unusual wait at port {port}')

    return device


async def scan_for_devices(timeout_seconds: float = 5.0) -> list[Device]:
    results = await asyncio.gather(
        *(
            perform_handshake_with_timeout(com_port.device, timeout_seconds)
            for com_port in list_ports.comports()
        )
    )
 
    return [dev for dev in results if dev is not None]
