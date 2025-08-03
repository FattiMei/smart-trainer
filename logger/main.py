import time
import serial
from serial.tools import list_ports

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIntValidator
from vispy import scene
from vispy.app import use_app
from vispy.scene import STTransform


class FormLayout(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_layout()

    def _build_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()

        self.group_id_textbox = QtWidgets.QLineEdit()
        self.subject_textbox = QtWidgets.QLineEdit()
        self.activity_textbox = QtWidgets.QLineEdit()
        self.additional_info_textbox = QtWidgets.QLineEdit()

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

        atoms.append(time.strftime("%Y%m%d-%H%M%S"))

        name = '_'.join(atoms)
        window_size = int(self.window_size_textbox.text())

        return name, window_size


class DeviceLayout(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.com_table = self._build_com_table()
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
        com = []

        for port in list_ports.comports():
            device = port.device
            name = self._perform_handshake(device)

            if name != '':
                sensor = {
                    'name': name,
                    'device': device,
                    'enabled': True
                }
                com.append(sensor)

        self.com_table = com
        print(com)

    def _build_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        title_layout = QtWidgets.QHBoxLayout()
        self.device_list_layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel('Device list')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(30)
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
        """)

        self.refresh_button = QtWidgets.QPushButton('refresh')
        self.refresh_button.clicked.connect(self._build_com_table)

        title_layout.addWidget(title)
        title_layout.addSpacing(5)
        title_layout.addWidget(self.refresh_button)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addItem(title_layout)
        main_layout.addItem(self.device_list_layout)

        self.setLayout(main_layout)


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.form = FormLayout()
        self.device_scanner = DeviceLayout()

        layout.addWidget(self.form)
        layout.addWidget(self.device_scanner)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


if __name__ == '__main__':
    app = use_app("pyqt5")
    app.create()

    win = MyMainWindow()
    win.show()
    app.run()
