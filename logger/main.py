import time
import json
import serial
from serial.tools import list_ports

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIntValidator
from vispy import scene
from vispy.app import use_app
from vispy.scene import STTransform


def scan_com_ports(blacklist=[]):
    com = {}

    for port in list_ports.comports():
        device = port.device

        if device not in blacklist:
            try:
                # ser = serial.Serial(device, baudrate=1500000, timeout=1)
                ser = serial.Serial(device, timeout=1)
                ser.write(b'INFO\r\n')
                res = ser.readlines()

                if len(res) > 0:
                    name = res[-1].decode('utf-8')
                    com[name] = device

            except:
                pass

    return com


class FormLayout(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Acquisition parameters')
        self._build_layout()

    def _build_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()

        self.group_id_textbox = QtWidgets.QLineEdit(placeholderText='Group ID')
        self.subject_textbox = QtWidgets.QLineEdit(placeholderText='Subject name')
        self.activity_textbox = QtWidgets.QLineEdit(placeholderText='Nome esperimento')
        self.additional_info_textbox = QtWidgets.QLineEdit(placeholderText='Parametri esperimento')

        self.window_size_textbox = QtWidgets.QLineEdit()
        self.window_size_textbox.setText('15')
        self.window_size_textbox.setValidator(QIntValidator())

        self.acquisition_delay_textbox = QtWidgets.QLineEdit()
        self.acquisition_delay_textbox.setText('1')
        self.acquisition_delay_textbox.setValidator(QIntValidator())

        form_layout.addRow(QtWidgets.QLabel('Group ID: '), self.group_id_textbox)
        form_layout.addRow(QtWidgets.QLabel('Subject: '), self.subject_textbox)
        form_layout.addRow(QtWidgets.QLabel('Activity: '), self.activity_textbox)
        form_layout.addRow(QtWidgets.QLabel('Parameters: '), self.additional_info_textbox)
        form_layout.addRow(QtWidgets.QLabel('Window size (s): '), self.window_size_textbox)
        form_layout.addRow(QtWidgets.QLabel('Acquisition delay (s): '), self.acquisition_delay_textbox)

        title = QtWidgets.QLabel('Acquisition parameters')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(30)
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
        """)

        main_layout.addWidget(title)
        main_layout.addSpacing(5)
        main_layout.addItem(form_layout)

        self.setLayout(main_layout)

    def get_acquisition_info(self):
        atoms = []

        group_id_text = self.group_id_textbox.text()
        subject_text = self.subject_textbox.text()
        activity_text = self.activity_textbox.text()
        additional_info_text = self.additional_info_textbox.text()

        # manual input validation
        #
        # Non sono riuscito a trovare una soluzione dichiarativa, quindi ci teniamo
        # questo spaghetti code. Validare anche il campo soggetto e info mi serve
        # perchè nell'unire gli atomi con '_' non voglio che si presenti la situazione
        # 'foo__baz' solo perché il campo `bar` è ''

        if group_id_text != '':
            atoms.append(group_id_text)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleziona nome gruppo")

        if subject_text != '':
            atoms.append(subject_text)

        if activity_text != '':
            atoms.append(activity_text)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleziona nome attività")

        if additional_info_text != '':
            atoms.append(additional_info_text)

        name = '_'.join(atoms)
        window_size = int(self.window_size_textbox.text())

        return name, window_size


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.form = FormLayout()
        layout.addWidget(self.form)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


if __name__ == '__main__':
    app = use_app("pyqt5")
    app.create()

    win = MyMainWindow()
    win.show()
    app.run()
