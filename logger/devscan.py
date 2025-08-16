import time
import serial
from serial.tools import list_ports
from dataclasses import dataclass

import threading


@dataclass
class Device:
    name: str
    port: str
    serial_obj: serial.serialposix.Serial


def perform_handshake(port: str):
    INFO_MESSAGE = b'INFO\r\n'

    try:
        ser = serial.Serial(port)
    except:
        return None

    # questo delay è necessario per i sensori con Arduino
    # l'apertura di una comunicazione seriale con l'oggetto `serial.Serial`
    # triggera il reset dell'Arduino da parte del suo bootloader.
    #
    # Questo rende l'Arduino irrangiungibile per un paio di secondi,
    # quindi non gli arriverebbe `INFO_MESSAGE` anche se l'istruzione
    # non genera eccezioni.
    #
    # Siccome non riesco a discriminare a priori quale device è un Arduino,
    # metto il delay ad ogni handshake.
    # NOTA che se non abbiamo i permessi necessari sulla porta, questa
    # funzione esce prima di fare il delay e aspettare inutilmente.
    time.sleep(3)

    bytes_written = ser.write(INFO_MESSAGE)
    assert(len(INFO_MESSAGE) == bytes_written)

    # sfortunatamente non posso leggere soltanto una riga dalla seriale
    # perché il sensore SR250 risponde con due righe di cui la seconda è il suo nome
    #
    # per gestire tutti i sensori con una unica chiamata la soluzione che ho trovato
    # è leggere tutti i dati disponibili con la chiamata `read_all()`.
    # da esperimenti con tutti i sensori (Arduino e radar) sembra che ci voglia un delay
    # importante prima di leggere.
    #
    # ci va bene che questo avviene soltanto alla device discovery
    # è una brutta soluzione (io sistemerei il firmware del SR250), ma funziona
    time.sleep(3)
    res = ser.read_all()

    if res != b'':
        name = res.decode('ascii', errors='ignore').splitlines()[-1].strip('\n\r')

        # Per le ragioni specificate sopra, restituisco anche l'oggetto seriale
        # così da non riaprire la comunicazione causando ulteriori reset
        return Device(name, port, ser)


def scan_for_devices():
    return filter(
        lambda device: device is not None,
        (
            perform_handshake(com_port.device)
            for com_port in list_ports.comports()
        )
    )


def scan_for_devices_mt():
    ''' multithreaded version of `scan_for_devices`'''
    def perform_handshake_wrapper(results_list: list, port: str):
        # per quanto ne sappia non si possono catturare i valori di ritorno
        # quando si usano i `threading.Thread`s. Per questo li faccio uscire
        # tramite una struttura mutevole come una lista
        device = perform_handshake(port)

        if device is not None:
            # questo potrebbe avere una race condition perché più thread
            # concorrenti vogliono aggiungere tutti un elemento alla lista
            #
            # non dovrebbe essere un problema perché l'interprete esegue sempre
            # un thread alla volta
            results_list.append(device)

    devices = []
    threads = [
        threading.Thread(
            target=perform_handshake_wrapper,
            args=(devices, com_port.device)
        )
        for com_port in list_ports.comports()
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    return devices
