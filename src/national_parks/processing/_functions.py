"""Helper module for managing the user-defined functions associated with the
Transformation class.
"""

import pandas as pd


def columns_to_lowercase(df):
    """Changes all column names in a DataFrame to lowercase.

    Args:
        df (pd.DataFrame): a DataFrame

    Returns:
        pd.DataFrame: a transformed copy of df
    """
    return df.rename(columns={c: c.lower() for c in df.columns})


def create_dt_pk(df, year_col, month_col, day_col=None):
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
    # If no day column is given then create a dummy column set to the beginning
    # of the month
    if day_col is None:
        day_col = 'dummy_day'
        df[day_col] = 1
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


def identity(df):
    """Identity transformation to call if nothing else is needed."""
    return df


def sum_by(df, by, summands):
    """Wrapper function for summing columns via pandas groupby.

    Args:
        df (pd.DataFrame): a DataFrame
        by (list): a list of column by which to group df
        summands (list): a list of columns that should be aggregated by
            summation

    Returns:
        pd.DataFrame: a transformed copy of df
    """
    list_by = [b for b in by]
    list_summands = [s for s in summands]
    return df.groupby(by=list_by, as_index=False)[list_summands].sum()
