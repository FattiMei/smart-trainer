import numpy as np
import matplotlib.pyplot as plt

file = np.load('out.npz')
ev = file['heartbeat']

t_infineon = file['t_infineon']
frame_infineon = file['frame_infineon']

t_sr250 = file['t_sr250']
frame_sr250 = file['frame_sr250']

delta = np.diff(t_sr250)

avg_frame_time = np.mean(np.diff(t_sr250))

window_size = 0.5
num_frames_in_window = int(np.ceil(window_size / avg_frame_time))

print(num_frames_in_window)

first_event_index = 0
second_event_index = 1

middle_points = []
good_windows = []
labels = []

for i in range(t_sr250.shape[0] - num_frames_in_window):
    window = frame_sr250[i:i+num_frames_in_window]

    times = t_sr250[i:i+num_frames_in_window]
    middle_point = np.mean(times)

    t0 = ev[first_event_index]
    t1 = ev[second_event_index]

    if middle_point < t0:
        continue

    if middle_point > t1:
        first_event_index = second_event_index
        second_event_index = second_event_index+1

        if second_event_index == len(ev):
            break

    if abs(middle_point-t0) + abs(middle_point-t1) > 1.5:
        continue

    middle_points.append(middle_point)
    good_windows.append(window)

    if abs(middle_point - t0) < window_size/2 or abs(middle_point-t1) < window_size/2:
        labels.append(True)
    else:
        labels.append(False)


fig, ax = plt.subplots(2,1)

ax[0].eventplot(ev, color='red')
ax[1].plot(middle_points, labels)
plt.show()