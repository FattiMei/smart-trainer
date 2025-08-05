import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, QHBoxLayout, QFormLayout, 
    QMessageBox,
    QLineEdit, QLabel
)

from collections import namedtuple
ExperimentParameters = namedtuple(
    'ExperimentParameters',
    [
        'base_name',
        'destination_folder',
        'window_size'
    ]
)


class ExperimentParametersForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_layout()

    def _build_layout(self):
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.group_id_textbox = QLineEdit()
        self.subject_textbox = QLineEdit()
        self.activity_textbox = QLineEdit()
        self.additional_info_textbox = QLineEdit()

        self.window_size_textbox = QLineEdit()
        self.window_size_textbox.setValidator(QIntValidator())
        self.window_size_textbox.setText('15')

        self.acquisition_delay_textbox = QLineEdit()
        self.acquisition_delay_textbox.setValidator(QIntValidator())
        self.acquisition_delay_textbox.setText('1')

        self.required_fields = [self.group_id_textbox, self.activity_textbox]
        for field in self.required_fields:
            field.setPlaceholderText('required')

        form_layout.addRow(QLabel('Group ID: '),              self.group_id_textbox)
        form_layout.addRow(QLabel('Subject: '),               self.subject_textbox)
        form_layout.addRow(QLabel('Activity: '),              self.activity_textbox)
        form_layout.addRow(QLabel('Parameters: '),            self.additional_info_textbox)
        form_layout.addRow(QLabel('Window size (s): '),       self.window_size_textbox)
        form_layout.addRow(QLabel('Acquisition delay (s): '), self.acquisition_delay_textbox)

        title = QLabel('Acquisition parameters')
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
        missing_fields = [field for field in self.required_fields if field.text() == '']

        if len(missing_fields) > 0:
            QMessageBox.warning(self, "Error", 'Fill required fields')
            return None

        group_id_text = self.group_id_textbox.text()
        subject_text = self.subject_textbox.text()
        activity_text = self.activity_textbox.text()
        additional_info_text = self.additional_info_textbox.text()
        timestamp_text = time.strftime("%Y%m%d-%H%M%S")

        elements = (
            group_id_text,
            subject_text,
            activity_text,
            additional_info_text,
            timestamp_text
        )

        base_name = '_'.join(txt for txt in elements if txt != '')
        window_size = int(self.window_size_textbox.text())

        return ExperimentParameters(
            base_name=base_name,
            destination_folder=activity_text,
            window_size=window_size
        )