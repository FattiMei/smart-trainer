import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# I decided to use PyQt5 because the logger.py already uses it
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import Qt
from pathlib import Path


ALPHA = 0.9
NORMALIZATION = (1 + ALPHA) / 2


# adapted from logger.py `declutter_alt` function
def declutter(cir: np.ndarray, alpha: float = ALPHA, normalization: float = NORMALIZATION) -> np.ndarray:
    decBase = cir[0]
    res = np.empty_like(cir)

    for i in range(cir.shape[0]):
        res[i] = normalization * (cir[i] - decBase)
        decBase = alpha * decBase + (1-alpha) * cir[i]

    return res


# these variables could be modified by UI elements (in the future)
MAX_BINS = 50
MAX_SAMPLES = 300


# This is copied from ChatGPT. It was asked to implement drag and drop functionality
# with an already open python window.
class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__("Drag and drop a file here", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: lightgray; font-size: 16px;")
        self.setAcceptDrops(True)

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
                stem = Path(filepath).stem
                raw = np.load(filepath)
                assert(raw.ndim == 2)
                assert(raw.shape[1] == 120)
                assert(raw.dtype == np.complex64)
                print(f'Successfully loaded {filepath}')

                abs = np.abs(raw)
                out = declutter(abs)

                # voglio mettere l'asse dei tempi in secondi
                # so che ogni sample è 1/fps = 1/20 di secondo
                bins = np.arange(raw.shape[1])
                seconds = np.arange(raw.shape[0]) / 20

                # questo mi serve per plottare i dati come un pcolormesh
                XX, YY = np.meshgrid(seconds, bins)

                fig, ax = plt.subplots(2,1)
                ax[0].pcolormesh(XX[:MAX_BINS], YY[:MAX_BINS], abs.T[:MAX_BINS])
                ax[0].set_title(stem)

                ax[1].pcolormesh(XX[:MAX_BINS], YY[:MAX_BINS], out.T[:MAX_BINS])
                ax[1].set_title('Declutter')
                ax[1].set_xlabel('seconds')

                plt.tight_layout()
                plt.show()

            except Exception as e:
                print(f"Error loading file: {e}")
        else:
            print("Not a valid file")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Declutter drag and drop")
        self.setGeometry(100, 100, 400, 200)

        self.label = DropLabel(self)
        self.setCentralWidget(self.label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())