import sys
import numpy as np
import scipy.fft
import scipy.signal
import matplotlib.pyplot as plt

from pathlib import Path


def process_file(filepath: str):
    stem = Path(filepath).stem
    raw = np.load(filepath)
    assert(raw.ndim == 2)
    assert(raw.shape[1] == 120)
    assert(raw.dtype == np.complex64)
    print(f'Successfully loaded {filepath}')

    mag = np.abs(raw)
    normalized = mag - np.mean(mag, axis=0)
    merged = np.mean(normalized[:,:20], axis=1)

    fhat = scipy.fft.fft(merged)
    power = np.abs(fhat)[:(fhat.size//2)]

    samples_per_window = raw.shape[0]
    samples_per_second = 20 # hardcoded from logger.py
    seconds_per_window = samples_per_window / samples_per_second

    base_frequency = 1.0 / seconds_per_window
    frequency_range_hz = np.arange(power.shape[0]) * base_frequency
    frequency_range_bpm = 60 * frequency_range_hz

    peaks = scipy.signal.find_peaks(power, distance=10, threshold=1)[0]

    plt.figure()
    plt.title(stem)
    plt.plot(frequency_range_bpm, power)

    for peak in peaks:
        if frequency_range_bpm[peak] < 200:
            plt.scatter(frequency_range_bpm[peak], power[peak], c='r')
            plt.text(frequency_range_bpm[peak], power[peak], f'{frequency_range_bpm[peak]: .0f}')

    plt.xlabel('BPM')
    plt.show()



if __name__ == "__main__":
    import dragdrop
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = dragdrop.MainWindow(process_file)
    window.show()
    sys.exit(app.exec_())
