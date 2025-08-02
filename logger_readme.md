# Instructions for working with the `logger.py` script.
It is highly suggested to start a python virtual environment. If you instead want to break your python installation look at the packages in `requirements.txt`

## `venv` install
```bash
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

I have found a quirk: `pyqtgraph` needs the module `PyQt5` to be installed, not `PyQt6` because it lacks some imports.

## System libraries
  * `pyqtgraph` needs Qt support from a system package perspective. For Ubuntu the package I found it works is `qt5dxcb-plugin`.
  * for enabling the sounddevice functionality one would need PortAudio library


## Device file permissions
When you connect the ESP32 board to your PC, the logger script tries to open some device files. On linux machines (although it may depend on the specific machine) the files are
```
/dev/ttyACM0
/dev/ttyACM1
```

Those files need to have read and write permissions that can be enabled by running the following command:
```bash
sudo chmod +rw /dev/ttyACM0
sudo chmod +rw /dev/ttyACM1
```