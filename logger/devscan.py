import time
import asyncio
import serial
import serial_asyncio
from serial.tools import list_ports
from dataclasses import dataclass


INFO_MESSAGE = b'INFO\r\n'


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

    writer.write(INFO_MESSAGE)
    await writer.drain()

    # il sensore SR250_ESP32 risponde al comando INFO con due linee:
    #   * "I (%d) uwb_session: INFO command received"
    #   * "SR250_ESP32"
    #
    # per includere questa eccezione (non sapendo a priori il device dalla porta)
    # implemento la soluzione sotto
    response = await reader.readline()
    if b'uwb_session: INFO command received' in response:
        response = await reader.readline()

    name = response.decode('ascii', errors='ignore').strip('\n\r')

    return Device(name, port, reader, writer)


# TODO: implementare la logica per killare un task dato un timeout
# un task potrebbe bloccarsi quando un device non implementando il protocollo
# non risponde a INFO_MESSAGE
async def scan_for_devices() -> list[Device]:
    results = await asyncio.gather(
        *(
            perform_handshake(com_port.device)
            for com_port in list_ports.comports()
        )
    )
 
    return [
        device
        for device in results
        if device is not None
    ]
