"""Utility functions for IO operations related to capta and configs."""

import os
from typing import Dict

from hydra.utils import to_absolute_path
from omegaconf import DictConfig, ListConfig, OmegaConf
import pandas as pd


def create_model_output_dirs(name, outputs_subdir=None):
    """Helper function to get and create output directories for models and
    plots associated with a single modeling effort.

    Args:
        name (str): the name of the modeling effort
        outputs_subdir (str): an optional subdirectory inside of models/ and
            plots/ in which the other directories should be placed

    Returns:
        Tuple[str, str]: the (absolute) paths of the output directories in
            models/ and plots/, respectively
    """
    if outputs_subdir is not None:
        model_output_path = os.path.join('models', outputs_subdir, name)
        plots_output_path = os.path.join('plots', outputs_subdir, name)
    else:
        model_output_path = os.path.join('models', name)
        plots_output_path = os.path.join('plots', name)
    model_output_path = to_absolute_path(model_output_path)
    plots_output_path = to_absolute_path(plots_output_path)
    for p in (model_output_path, plots_output_path):
        os.makedirs(p, exist_ok=True)
    return model_output_path, plots_output_path


def get_step_inputs(inputs_config):
    """Retrieves and caches input DataFrames.

    Args:
        inputs_config (ListConfig): a list of objects with "name" and "path"
            attributes

    Returns:
        Dict[str, pd.DataFrame]: a structure of the form {name: df} covering
            all input objects
    """
    return {
        item.name: pd.read_csv(to_absolute_path(item.path))
        for item in inputs_config
    }


def maybe_create_capta_directory(stage):
    """Creates a subdirectory under capta/, since dvc deletes any existing
    output directory upon running a stage.
    """
    if stage not in ['source', 'processed']:
        raise ValueError('Unrecognized stage')
    abs_path = to_absolute_path(f'capta/{stage}')
    os.makedirs(abs_path, exist_ok=True)


def read_config_file(path):
    """Helper function to read a YAML configuration file.

    Args:
        path (str): path relative to the national-parks working directory

    Returns:
        DictConfig | ListConfig: a structured object from the indicated file
    """
    abs_path = to_absolute_path(path)
    return OmegaConf.load(abs_path)
