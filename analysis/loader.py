import os
import numpy as np


DATASET_FOLDER = '../datasets'
sensors = ['Infineon', 'SR250Mate']
experiments = ['apnea', 'breathing', 'foreign', 'intensity', 'misc', 'recovery', 'rpm-ladder', 'signal-to-noise']


def get_experiment_names(sensor: str, experiment: str, dataset_folder: str = DATASET_FOLDER) -> tuple[str, list[str]]:
    base_folder_path = os.path.join(dataset_folder, sensor, experiment)
    experiment_list = os.listdir(base_folder_path)

    return base_folder_path, experiment_list


def load_experiment(base_folder_path: str, name: str) -> np.ndarray:
    complete_path = os.path.join(base_folder_path, name)

    return np.load(complete_path)