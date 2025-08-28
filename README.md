# smart-trainer
Exploring UWB radar data for monitoring static physical activities


## `logger.py`
This python script is responsable of data logging. It must handle multiple asynchronous sensor streams coming from:
  * Arduino boards
  * UWB radar boards

### Communication protocol
Each sensor board implements a common serial communication protocol described by the diagram below:
**TODO: make such diagram**

### Original features
The original logger implementation (legacy) was a PyQt5 GUI application. It came with several features like:
  * runtime sensor selection (from a predefined list of radar sensors)
  * form selection of acquisition parameters
  * live visualization of preprocessed radar data
  * GUI controls for starting and stopping the data collection

It is a sophisticated program coming at about 1000 SLOC and I found challenges in understanding the general control flow as it's event based and driven from UI controls.

### Proposed implementation
I propose a simpler implementation that focuses on:
  * robust multithreaded serial communication (robust to disconnection, always maintains a "safe state" in the communication protocol)
  * sliding window visualization of (*any*) preprocessed sensor data
  * extensibility for new sensors to be added

It would also be nice to explore different plotting backends to achieve a 60 FPS visualization. From simple experiments (see `logger/demo_sliding_window.py`) the matplotlib backend struggles to produce smooth visualizations.
There is the possibility of using a relatively new GPU accelerated plotting library called [Vispy](https://vispy.org). It's heavily object oriented and requires a PyQt5 dependency but it's promising for delivering fast plots.
