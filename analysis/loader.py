import os
import numpy as np


DATASET_FOLDER = '../datasets'
sensors = ['Infineon', 'SR250Mate']
experiments = ['apnea', 'breathing', 'foreign', 'intensity', 'misc', 'recovery', 'rpm-ladder', 'signal-to-noise']


def get_experiment_names(sensor: str, experiment: str, subject = None, antenna = None, dataset_folder: str = DATASET_FOLDER) -> tuple[str, list[str]]:
    base_folder_path = os.path.join(dataset_folder, sensor, experiment)
    experiment_list = os.listdir(base_folder_path)

    needs_filter = (subject is not None) or (antenna is not None)

    if needs_filter:
        filtered = []

        for name in experiment_list:
            # questa è la convenzione con cui abbiamo salvato i file
            # e.g. 'MillenIAls_M_signal-to-noise_00cm_20250526-150252_sr250_rx2.npy'
            atoms = name.split('_')
            sub = atoms[1]
            ant = atoms[-1].split('.')[0]

            if (sub == subject) and (ant == antenna):
                filtered.append(name)

        experiment_list = filtered

    return base_folder_path, experiment_list


def load_experiment(base_folder_path: str, name: str) -> np.ndarray:
    complete_path = os.path.join(base_folder_path, name)

    return np.load(complete_path)