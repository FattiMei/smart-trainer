import time
import serial
from serial.tools import list_ports
from threading import Lock

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIntValidator
from vispy import scene
from vispy.app import use_app
from vispy.scene import STTransform

from form import ExperimentParametersForm


class DeviceLayout(QtWidgets.QWidget):
    def __init__(self, serial_lock=None, parent=None):
        super().__init__(parent)
        self.com_table = []
        self.serial_lock = serial_lock
        self._build_layout()

    def _perform_handshake(self, device: str) -> str:
        try:
            ser = serial.Serial(device, timeout=1)
            ser.write(b'INFO\r\n')
            res = ser.readlines()

            if len(res) > 0:
                name = res[-1].decode('utf-8')
                return name

        except:
            return ''

    def _build_com_table(self):
        if self.serial_lock.locked():
            print('Device list scan failed because another operation is occupying the serial bus')
            return
        else:
            self.serial_lock.acquire()

        old_com = self.com_table
        com = []

        for port in list_ports.comports():
            device = port.device
            name = self._perform_handshake(device)

            if name is not None and name != '':
                name = name.strip('\n')
                sensor = {
                    'name': name,
                    'device': device,
                    'enabled': True
                }
                com.append(sensor)

        self.serial_lock.release()

        # Vorremmo visualizzare i device in una lista (scrollable), per farlo questa funzione
        # deve modificare il layout interno detto `self.device_list_layout`, che potrebbe già contenere
        # degli elementi che andrebbero rimossi prima di operare.
        # Non ho capito bene come funziona questa cosa, posso provare a inserire uno snippet prodotto da chatgpt
        #
        # Una feature interessante è la possibilità di selezionare quali sensori leggere durante la misurazione
        # Questo significa che la lista deve contenere delle checkbox (o gli elementi stessi potrebbero essere checkbox)
        # per lasciare all'utente la scelta.
        #
        # Lo stato dei sensori (nome, device e enabled) al momento è memorizzato in una lista.
        # C'è bisogno di associare ogni elemento della lista ad una checkbox differente, e ho pensato a due soluzioni:
        #   1. collegare le checkbox al dato corrispondente: ad ogni toggle cambio il campo enabled del sensore corrispondente
        #   2. fare il mapping solo quando viene richiesto: come i parametri dell'acquisizione sono assemblati e validati solo
        #      nella funzione FormLayout.get_acquisition_info(), si potrebbe fare qui
        #
        # la seconda soluzione mi sembra nello stesso spirito della classe FormLayout, quindi la implementerò così.
        # Sarebbe bello se qualcuno con esperienza di UI mi desse un feedback

        last_enabled_devices = set(dev['name'] for dev in self._get_enabled_devices(old_com))
        while self.checkbox_container.count():
            child = self.checkbox_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.checkboxes.clear()

        for dev in com:
            container = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(container)

            checkbox = QtWidgets.QCheckBox(dev['name'])
            checkbox.setLayoutDirection(Qt.LeftToRight)

            # questa è una cosa un po' sofisticata, ma che migliora l'esperienza utente:
            # se l'utente ha già selezionato un device, il refresh lo fa deselezionare.
            # risolvo la cosa salvandomi prima una struttura di device enabled
            checkbox.setChecked(dev['name'] in last_enabled_devices)

            device_port_label = QtWidgets.QLabel(dev['device'])
            device_port_label.setStyleSheet('''
                color: gray;
                font-weight: lighter;
            ''')

            layout.addWidget(checkbox)
            layout.addStretch()
            layout.addWidget(device_port_label)

            self.checkbox_container.addWidget(container)
            self.checkboxes.append(checkbox)

        self.com_table = com

    def _build_layout(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        title_layout = QtWidgets.QHBoxLayout()

        # Create a container for the checkboxes with scroll capability
        self.checkboxes = []
        self.checkbox_container = QtWidgets.QVBoxLayout()
        checkbox_frame = QtWidgets.QFrame()
        checkbox_frame.setLayout(self.checkbox_container)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(checkbox_frame)

        title = QtWidgets.QLabel('Device list')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(30)
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
        """)

        self.refresh_button = QtWidgets.QPushButton('refresh')
        self.refresh_button.clicked.connect(self._build_com_table)
        self.refresh_button.click()

        title_layout.addWidget(title)
        title_layout.addSpacing(5)
        title_layout.addWidget(self.refresh_button)

        self.main_layout.addItem(title_layout)
        self.main_layout.addWidget(scroll_area)

        self.setLayout(self.main_layout)

    def _get_enabled_devices(self, com_table: list):
        # qui convertiamo le informazioni delle checkbox in una lista di sensori abilitati
        # L'ordine della lista `self.com_table` è lo stesso ordine di inserimento dei widget
        enabled_devices = []
        for i, device in enumerate(com_table):
            if self.checkboxes[i].checkState() == Qt.CheckState.Checked:
                enabled_devices.append(device)

        return enabled_devices

    def get_device_info(self):
        radar_sensors = ['Infineon', 'SR250_ESP32']
        enabled_devices = self._get_enabled_devices(self.com_table)
        has_a_radar_sensor = False

        for device in enabled_devices:
            has_a_radar_sensor = device['name'] in radar_sensors

        if has_a_radar_sensor:
            return enabled_devices
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleziona almeno un sensore radar")
            return None


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_lock = Lock()

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        control_buttons_layout = QtWidgets.QHBoxLayout()

        self.form = ExperimentParametersForm()
        self.device_scanner = DeviceLayout(self.serial_lock)

        self.start_button = QtWidgets.QPushButton('Start Collection')
        self.start_button.clicked.connect(self.start_collection)

        control_buttons_layout.addWidget(self.start_button)

        layout.addWidget(self.form)
        layout.addWidget(self.device_scanner)
        layout.addItem(control_buttons_layout)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_collection(self):
        experiment_parameters = self.form.get_acquisition_info()

        if self.serial_lock.locked():
            QtWidgets.QMessageBox.warning(self, "Error", "Il bus seriale è occupato")
            return

        self.serial_lock.acquire()

        self.start_button.setText('Stop Collection')
        self.start_button.clicked.disconnect(self.start_collection)
        self.start_button.clicked.connect(self.stop_collection)

        # qui c'è la logica di spawn dei thread e la visualizzazione


    def stop_collection(self):
        self.serial_lock.release()
        self.start_button.setText('Start Collection')
        self.start_button.clicked.disconnect(self.stop_collection)
        self.start_button.clicked.connect(self.start_collection)

        # qui c'è la logica del salvataggio file da copiare
        # dal logger originale


if __name__ == '__main__':
    app = use_app("pyqt5")
    app.create()

    win = MyMainWindow()
    win.show()
    app.run()
