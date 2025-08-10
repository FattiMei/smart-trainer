import time
import serial
from serial.tools import list_ports

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QWidget, 
    QStyle,
    QVBoxLayout, QHBoxLayout, QFormLayout, 
    QFrame,
    QScrollArea,
    QMessageBox,
    QCheckBox,
    QLineEdit, QLabel,
    QPushButton
)

from collections import namedtuple
Device = namedtuple(
    'Device',
    [
        'name',
        'port',
        'serial_obj'
    ]
)


def perform_handshake(port: str):
    INFO_MESSAGE = b'INFO\r\n'

    try:
        ser = serial.Serial(port, timeout=1)
    except:
        return None

    bytes_written = ser.write(INFO_MESSAGE)
    assert(len(INFO_MESSAGE) == bytes_written)

    ser.send_break()
    res = ser.readlines()

    print(res)

    if res != []:
        name = res[-1].strip(b'\n\r').decode('ascii', errors='ignore')
        return Device(name, port, ser)


# this primitive function doesn't concern with the state (possibly busy)
# of the serial bus. Other wrappers may implement more complex logic.
def scan_for_devices():
    devices = []

    for port in list_ports.comports():
        dev = perform_handshake(port.device)

        if dev is not None:
            devices.append(dev)

    return devices


class DeviceSelector(QWidget):
    def __init__(self, serial_bus_lock, parent=None):
        super().__init__(parent)

        self.serial_bus_lock = serial_bus_lock
        self.com = []
        self.device_checkboxes = []
        self._build_layout()

    def _build_layout(self):
        self.main_layout = QVBoxLayout()
        title_layout = QHBoxLayout()

        title = QLabel('Device list')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(30)
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
        """)

        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(
            self.style().standardIcon(
                getattr(QStyle, 'SP_BrowserReload')
            )
        )
        self.refresh_button.clicked.connect(self._build_com_table_layout)

        title_layout.addWidget(title)
        title_layout.addSpacing(5)
        title_layout.addWidget(self.refresh_button)

        # Create a container for the checkboxes with scroll capability
        self.checkbox_container = QVBoxLayout()
        checkbox_frame = QFrame()
        checkbox_frame.setLayout(self.checkbox_container)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(checkbox_frame)

        self.main_layout.addItem(title_layout)
        self.main_layout.addWidget(scroll_area)
        self.setLayout(self.main_layout)

    def _build_com_table_layout(self):
        if self.serial_bus_lock.locked():
            QMessageBox.warning(self, "DeviceScanner error", "Serial bus is busy, try later")
            return None

        self.serial_bus_lock.acquire()
        com = scan_for_devices()
        self.serial_bus_lock.release()

        last_enabled_devices_name = set(
            dev.name
            for dev in self._get_enabled_devices(self.com, self.device_checkboxes)
        )

        while self.checkbox_container.count():
            child = self.checkbox_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.device_checkboxes.clear()

        for dev in com:
            container = QWidget()
            layout = QHBoxLayout(container)

            checkbox = QCheckBox(dev.name)
            checkbox.setLayoutDirection(Qt.LeftToRight)

            # questa è una cosa un po' sofisticata, ma che migliora l'esperienza utente:
            # se l'utente ha già selezionato un device, il refresh lo fa deselezionare.
            # risolvo la cosa salvandomi prima una struttura di device enabled
            checkbox.setChecked(dev.name in last_enabled_devices_name)

            device_port_label = QLabel(dev.port)
            device_port_label.setStyleSheet('''
                color: gray;
                font-weight: lighter;
            ''')

            layout.addWidget(checkbox)
            layout.addStretch()
            layout.addWidget(device_port_label)

            self.checkbox_container.addWidget(container)
            self.device_checkboxes.append(checkbox)

        self.com = com

    def _get_enabled_devices(self, com: list[Device], checkboxes: list) -> list[Device]:
        # qui convertiamo le informazioni delle checkbox in una lista di sensori abilitati
        # L'ordine della lista `self.com_table` è lo stesso ordine di inserimento dei widget
        assert(len(com) == len(checkboxes))

        return [
            dev
            for (dev, box) in zip(com, checkboxes)
            if box.checkState() == Qt.CheckState.Checked
        ]

    def get_enabled_devices(self):
        return self._get_enabled_devices(self.com, self.device_checkboxes)
