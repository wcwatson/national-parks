"""Class for managing transformations to source capta. Note that all "helper
functions" must take a DataFrame as their first argument and return a
transformed copy of that DataFrame.
"""

import pandas as pd

from ._functions import columns_to_lowercase, create_dt_pk, identity, sum_by


class Transformation(object):
    """Object for managing transformations in a configurable manner.

    Attributes:
        name (str): the name of the transformation
        params (dict): keyword arguments to be passed to the transformation
    """

    def __init__(self, name, params=None):
        _allowable_transformations = {
            'columns_to_lowercase': columns_to_lowercase,
            'create_dt_pk': create_dt_pk,
            'identity': identity,
            'melt': pd.melt,
            'pivot': pd.pivot,
            'sum_by': sum_by
        }
        if name not in _allowable_transformations:
            raise NotImplementedError(f'Unimplemented transformation {name}')
        self.name = name
        self._func = _allowable_transformations[name]
        self.params = params

    def transform(self, df):
        """Transforms a DataFrame.

        Args:
            df (pd.DataFrame): a DataFrame

        Returns:
            pd.DataFrame: a transformed copy of df
        """
        if self.params is not None:
            return self._func(df, **self.params)
        return self._func(df)
