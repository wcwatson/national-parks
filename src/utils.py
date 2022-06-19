"""Common utility functions"""

import logging
import os
import yaml

from hydra.utils import to_absolute_path
from omegaconf import OmegaConf
import pandas as pd


def setup_logging(step_name):
    logging.basicConfig(level=logging.INFO)
    logging.info(f'Logging set up for step - {step_name}')


def log_job_succeeded():
    logging.info('JOB SUCCEEDED')


def read_config_file(path):
    """Helper function to read a YAML configuration file.

    Args:
        path (str): path relative to the national-parks working directory

    Returns:
        DictConfig | ListConfig: a structured object from the indicated file
    """
    abs_path = to_absolute_path(path)
    return OmegaConf.load(abs_path)


def ordinal(n):
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    return str(n) + suffixes.get(4 if 11 <= n % 100 < 14 else n % 10, 'th')


def maybe_create_capta_directory(stage):
    """Creates a subdirectory under capta/, since dvc deletes any existing
    output directory upon running a stage.
    """
    if stage not in ['source', 'processed']:
        raise ValueError('Unrecognized stage')
    abs_path = to_absolute_path(f'capta/{stage}')
    os.makedirs(abs_path, exist_ok=True)


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


# It ends up being more efficient to keep these in memory rather than read them
# each time their contents are required
with open('config/refresh_source_capta/park_types.yaml', 'r') as fi:
    _PARK_TYPES = yaml.safe_load(fi)
with open('config/refresh_source_capta/all_parks.yaml', 'r') as fi:
    _PARK_NAMES = yaml.safe_load(fi)


def parse_park_name(park_name):
    """Helper function to parse a park name.

    Args:
        park_name (str): a park name as found in the configuration files

    Returns:
        str, str: the long park name and the (abbreviated) park type
    """
    park_name_split = park_name.split(' ')
    return ' '.join(park_name_split[:-1]), park_name_split[-1]


def get_long_park_type(park_type):
    """Simple helper function to streamline class methods."""
    return _PARK_TYPES.get(park_type)


def get_full_park_name(park_name):
    """Returns a human-legible full name for a park (e.g., "Acadia
    National Park").

    Args:
        park_name (str): an abbreviated park name (e.g., "ACAD")

    Returns:
        str: the park's full name
    """
    long_park_name, park_type = parse_park_name(_PARK_NAMES.get(park_name))
    long_park_type = get_long_park_type(park_type)
    return f'{long_park_name} {long_park_type}'
