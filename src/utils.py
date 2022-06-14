"""Common utility functions"""

import datetime
import logging
import os
import yaml

from hydra.utils import to_absolute_path


def now():
    return datetime.datetime.now().isoformat().replace(':', '-').split(".")[0]


def setup_logging(step_name):
    logging.basicConfig(level=logging.INFO)
    logging.info(f'Logging set up for step - {step_name}')


def log_job_succeeded():
    logging.info('JOB SUCCEEDED')


def maybe_create_capta_directory(stage):
    if stage not in ['source', 'processed']:
        raise ValueError('Unrecognized stage')
    abs_path = to_absolute_path(f'capta/{stage}')
    os.makedirs(abs_path, exist_ok=True)


with open('config/source_capta/park_types.yaml', 'r') as fi:
    _PARK_TYPES = yaml.safe_load(fi)
with open('config/source_capta/all_parks.yaml', 'r') as fi:
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
    long_park_name, park_type = parse_park_name(park_name)
    long_park_type = get_long_park_type(park_type)
    return f'{long_park_name} {long_park_type}'
