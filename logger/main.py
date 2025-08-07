import time
import serial
from serial.tools import list_ports
from threading import Lock

from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIntValidator
from vispy import scene
from vispy.app import use_app
from vispy.scene import STTransform

from form import ExperimentParametersForm
from sensor import sensor_factory
from devscan import DeviceSelector


class CanvasWrapper:
    def __init__(self, enabled_sensors: list):
        self.canvas = scene.SceneCanvas()
        self.grid = self.canvas.central_widget.add_grid()

        for i, sensor in enumerate(enabled_sensors):
            sensor.set_view(
                self.grid.add_view(i,0)
            )


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_lock = Lock()
        self.form = ExperimentParametersForm()
        self.device_selector = DeviceSelector(self.serial_lock)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        control_buttons_layout = QtWidgets.QHBoxLayout()

        self.start_button = QtWidgets.QPushButton('Start Collection')
        self.start_button.clicked.connect(self.start_collection)

        control_buttons_layout.addWidget(self.start_button)

        layout.addWidget(self.form)
        layout.addWidget(self.device_selector)
        layout.addItem(control_buttons_layout)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_collection(self):
        self.experiment_parameters = self.form.get_acquisition_info()
        self.selected_devices = self.device_selector.get_enabled_devices()

        if self.experiment_parameters is None:
            return

        if len(self.selected_devices) == 0:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleziona almeno un device di input")
            return

        if self.serial_lock.locked():
            QtWidgets.QMessageBox.warning(self, "Error", "Il bus seriale è occupato")
            return


        self.start_button.setText('Stop Collection')
        self.start_button.clicked.disconnect(self.start_collection)
        self.start_button.clicked.connect(self.stop_collection)

        # qui c'è la logica di spawn dei thread e la visualizzazione
        self.canvas = scene.SceneCanvas()
        self.grid = self.canvas.central_widget.add_grid()

        self.sensors = [
            sensor_factory(dev.name)(dev, self.grid.add_view(i,0))
            for i, dev in enumerate(self.selected_devices)
        ]

        # bisogna far partire tutti i thread dei singoli sensori
        for sensor in self.sensors:
            sensor.start()

        # qui ci va un bel timer per la lunghezza della finestra
        self.timer = QTimer()
        self.timer.timeout.connect(self.stop_collection)
        self.timer.start(1000 * self.experiment_parameters.window_size)

        self.serial_lock.acquire()



    def stop_collection(self):
        print('stop collection')
        self.timer.timeout.disconnect(self.stop_collection)

        if self.serial_lock.locked():
            self.serial_lock.release()

        self.start_button.setText('Start Collection')
        self.start_button.clicked.disconnect(self.stop_collection)
        self.start_button.clicked.connect(self.start_collection)

        # qui c'è la logica del salvataggio file da copiare
        # dal logger originale
        for sensor in self.sensors:
            sensor.stop()


if __name__ == '__main__':
    app = use_app("pyqt5")
    app.create()

    win = MyMainWindow()
    win.show()
    app.run()
