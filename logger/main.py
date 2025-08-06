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
from devscan import DeviceSelector


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_lock = Lock()

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        control_buttons_layout = QtWidgets.QHBoxLayout()

        self.form = ExperimentParametersForm()
        self.device_scanner = DeviceSelector(self.serial_lock)

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
        if experiment_parameters is None:
            return

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
