"""Utility functions for creating plots."""

import pandas as pd

from ..utils.park_names import get_full_park_name, get_long_park_type


def get_full_series_name(series_name):
    """Searches for the full name of a series, checking each likely object type
    in order (individual parks, then aggregated park types).

    Args:
        series_name (str): the name of a time series, expected to be a code or
            abbreviation (e.g., "ACAD", "NP")

    Returns:
        str: the series's human-legible name, to be used for titling and
            labeling plots
    """
    try:
        full_name = get_full_park_name(series_name)
    # If the series name is not a park code, a KeyError will be raised by the
    # utility function
    except KeyError:
        full_name = get_long_park_type(series_name)
    return full_name


def ordinal(n):
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    return str(n) + suffixes.get(4 if 11 <= n % 100 < 14 else n % 10, 'th')
