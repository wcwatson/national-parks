"""Class for managing transformations to source capta. Note that all "helper
functions" must take a DataFrame as their first argument and return a
transformed copy of that DataFrame.
"""

import pandas as pd


def _columns_to_lowercase(df):
    """Changes all column names in a DataFrame to lowercase.

    Args:
        df (pd.DataFrame): a DataFrame

    Returns:
        pd.DataFrame: a transformed copy of df
    """
    return df.rename(columns={c: c.lower() for c in df.columns})


def _create_dt_pk(df, year_col, month_col, day_col=None):
    """Consolidates component time columns into a single pandas datetime column
    and drops the original columns. The new column will be called "dt_pk",
    indicating a "primary key" datetime column for time series modeling, though
    it may not be a primary key in the strict sense.

    Args:
        df (pd.DataFrame): a DataFrame
        year_col (str): the name of a column containing years
        month_col (str): the name of a column containing months - can be either
            numeric (1-12) or three-letter strings
        day_col (str): the name of a column containing days

    Returns:
        pd.DataFrame: a transformed copy of df
    """
    # If no day column is given then create a dummy column set to the middle of
    # the month
    if day_col is None:
        day_col = 'dummy_day'
        df[day_col] = 15
    df = df.rename(
        columns={year_col: 'year', month_col: 'month', day_col: 'day'}
    )
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    df['month'] = df['month'].replace(month_map)
    df['dt_pk'] = pd.to_datetime(df[['year', 'month', 'day']])
    return df.drop(columns=['year', 'month', 'day'])


def _identity(df):
    """Identity transformation to call if nothing else is needed."""
    return df


def _sum_by(df, by, summands):
    """

    Args:
        df (pd.DataFrame):
        by (list):
        summands (list):

    Returns:

    """
    list_by = [b for b in by]
    list_summands = [s for s in summands]
    return df.groupby(by=list_by, as_index=False)[list_summands].sum()


_ALLOWABLE_TRANSFORMATIONS = {
    'columns_to_lowercase': _columns_to_lowercase,
    'create_dt_pk': _create_dt_pk,
    'identity': _identity,
    'melt': pd.melt,
    'pivot': pd.pivot,
    'sum_by': _sum_by
}


class Transformation(object):
    """Object for managing transformations in a configurable manner.

    Attributes:
        name (str): the name of the transformation
        params (dict): keyword arguments to be passed to the transformation
    """

    def __init__(self, name, params=None):
        # print(name, params, type(params))  # TODO (WW): delete
        if name not in _ALLOWABLE_TRANSFORMATIONS:
            raise NotImplementedError(f'Unimplemented transformation {name}')
        self.name = name
        self._func = _ALLOWABLE_TRANSFORMATIONS[name]
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
