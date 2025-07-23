import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# I decided to use PyQt5 because the logger.py already uses it
from PyQt5.QtWidgets import QLabel, QMainWindow
from PyQt5.QtCore import Qt


# This is copied from ChatGPT. It was asked to implement drag and drop functionality
# with an already open python window.
class DropLabel(QLabel):
    def __init__(self, visualization_function, parent=None):
        super().__init__("Drag and drop a file here", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: lightgray; font-size: 16px;")
        self.setAcceptDrops(True)

        # this is a function that takes a filename,
        # does some preprocessing and plot the results
        self.visualization_function = visualization_function

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()

        if urls:
            filepath = urls[0].toLocalFile()
            print(f"Dropped file: {filepath}")
            self.handle_file(filepath)

    def handle_file(self, filepath):
        if os.path.isfile(filepath):
            try:
                self.visualization_function(filepath)

            except Exception as e:
                print(f"Error loading file: {e}")
        else:
            print("Not a valid file")


class MainWindow(QMainWindow):
    def __init__(self, visualization_function):
        super().__init__()
        self.setWindowTitle("Declutter drag and drop")
        self.setGeometry(100, 100, 400, 200)

        self.label = DropLabel(visualization_function, self)
        self.setCentralWidget(self.label)