"""Functionality for training, evaluating, and analyzing an ARIMA model."""

import joblib
import logging
import os

import pandas as pd
from pmdarima.arima import AutoARIMA
import statsmodels.api as sm

from ..utils.io import create_model_output_dirs
from ..visualization.model_evaluation import plot_forecast
from ..visualization.time_series import (
    plot_differenced_time_series, plot_time_series
)


# TODO (WW): consider moving elsewhere long-term, depending on plans
def _detrend_time_series(ts, alpha=0.05, max_diffs=3):
    """Helper function to sequester logic for detrending a time series.

    Args:
        ts (pd.Series): a time series
        alpha (float): the desired significance level of the Dickey-Fuller
            test statistic before differencing halts
        max_diffs (int): the maximum number of differences to take before
            abandoning the search for Dickey-Fuller significance

    Returns:
        Tuple[pd.Series, int, float]: the detrended series, the degree of
            differencing applied to detrend the series, and the p-value of the
            DF test statistic attained
    """
    diffs = 0
    p_value = sm.tsa.adfuller(ts)[1]
    while p_value > alpha and diffs < max_diffs:
        ts = (ts - ts.shift(1)).dropna()
        p_value = sm.tsa.adfuller(ts)[1]
        diffs += 1
    return ts, diffs, p_value


def _train_and_evaluate_arima_model(
        ts,
        outputs_subdir=None,
        exog=None,
        test_size=0.2,
        m=1,
        df_alpha=0.05,
        max_diffs=3,
        max_order=8,
        arima_ci_alpha=0.05,
        plot_train_limit=2,
):
    """Trains and evaluates an ARIMA model for a single time series.

    Args:
        ts (pd.Series): a single time series
        outputs_subdir (str): optional subdirectory within models/ and plots/
            where output artifacts should be written, if None then all
            artifacts will be written at the top level of the relevant
            directory
        exog (pd.DataFrame): an optional DataFrame of exogenous variables
        test_size (float | int): if <1 the proportion of each time series to be
            held out as a test set; if an integer the number of steps to be
            held out as a test set
        m (int): the period for seasonal differencing (see the pmdarima
            documentation for more details) - note that this seasonality will
            be removed from the time series prior to performing the DF test and
            plotting (P)ACF curves
        df_alpha (float): the desired significance level of the Dickey-Fuller
            test statistic before differencing halts
        max_diffs (int): the maximum number of differences to take before
            abandoning the search for Dickey-Fuller significance
        max_order (int): the maximum value of p+q+P+Q in the ARIMA model
        arima_ci_alpha (float): the significance level to which a confidence
            interval should be estimated for the ARIMA model's predictions
        plot_train_limit (int): the number of test-set-length portions of
            the training set to include in the forecast plot

    Returns:
        None
    """
    # Setup output paths and plot the entire time series alongside a rolling
    # average for post hoc analysis
    model_output_path, plots_output_path = create_model_output_dirs(
        name=ts.name, outputs_subdir=outputs_subdir
    )
    plot_time_series(
        ts,
        rolling_window=12,
        fp=os.path.join(plots_output_path, f'{ts.name}.png')
    )

    # Split capta for training and evaluation
    test_cutoff = int(test_size * len(ts)) if test_size < 1 else test_size
    train_ts, test_ts = ts[:-test_cutoff], ts[-test_cutoff:]
    if exog is not None:
        train_exog = exog.iloc[:, :-test_cutoff]
        test_exog = exog.iloc[:, -test_cutoff:]
    else:
        train_exog = test_exog = None

    # Remove any indicated seasonality and iteratively evaluate the
    # Dickey-Fuller test statistic on increasingly differenced training
    # series until significance is achieved
    diff_ts = (train_ts - train_ts.shift(m)).dropna() if m > 1 else train_ts
    diff_ts, diffs, df_p_value = _detrend_time_series(
        diff_ts, alpha=df_alpha, max_diffs=max_diffs
    )
    plot_differenced_time_series(
        diff_ts,
        diffs=diffs,
        m=m,
        df_p_value=df_p_value,
        fp=os.path.join(plots_output_path, f'{ts.name}_analysis.png')
    )

    # Fit and evaluate an ARIMA model, writing both the model object and an
    # analytic summary to the models/ directory
    # NB: this uses the original time series rather than the detrended time
    # series analyzed above, since AutoARIMA will determine an appropriate
    # degree of differencing automatically
    arima_model = AutoARIMA(m=m, max_order=max_order)
    arima_model.fit(train_ts, X=train_exog)
    arima_model_fn = os.path.join(model_output_path, f'{ts.name}_arima.pkl')
    joblib.dump(arima_model, arima_model_fn)
    arima_summary_fn = os.path.join(
        model_output_path, f'{ts.name}_arima_summary.txt'
    )
    with open(arima_summary_fn, 'w') as fo:
        fo.write(arima_model.summary().as_text())
    forecast, forecast_ci = arima_model.predict(
        n_periods=len(test_ts),
        X=test_exog,
        return_conf_int=True,
        alpha=arima_ci_alpha
    )
    plot_forecast(
        train_ts,
        test_ts,
        forecast,
        forecast_ci,
        train_limit=plot_train_limit,
        fp=os.path.join(plots_output_path, f'{ts.name}_forecast.png')
    )


def train_and_evaluate_arima_models(
        df,
        outputs_subdir=None,
        ts_cols=None,
        exog_vars=None,
        test_size=0.2,
        m=1,
        df_alpha=0.05,
        max_diffs=3,
        max_order=8,
        arima_ci_alpha=0.05,
        plot_train_limit=2,
):
    """Trains and evaluates an ARIMA model for all indicated time series in a
    DataFrame.

    Args:
        df (pd.DataFrame): a DataFrame with one or more time series and
            (optionally) exogenous variables
        outputs_subdir (str): optional subdirectory within models/ and plots/
            where output artifacts should be written, if None then all
            artifacts will be written at the top level of the relevant
            directory
        ts_cols (list): a list of columns to be modeled as the values of a time
            series, defaults to all columns in df that are not included in
            exog_vars
        exog_vars (list): an optional list of columns to be treated as
            exogenous variables in each model
        test_size (float | int): if <1 the proportion of each time series to be
            held out as a test set; if an integer the number of steps to be
            held out as a test set
        m (int): the period for seasonal differencing (see the pmdarima
            documentation for more details) - note that this seasonality will
            be removed from the time series prior to performing the DF test and
            plotting (P)ACF curves
        df_alpha (float): the desired significance level of the Dickey-Fuller
            test statistic before differencing halts
        max_diffs (int): the maximum number of differences to take before
            abandoning the search for Dickey-Fuller significance
        max_order (int): the maximum value of p+q+P+Q in the ARIMA model
        arima_ci_alpha (float): the significance level to which a confidence
            interval should be estimated for the ARIMA model's predictions
        plot_train_limit (int): the number of test-set-length portions of
            the training set to include in the forecast plot

    Returns:
        None
    """
    # Checks and one-time operations before execution
    if not (0 < test_size < 1 or test_size // 1 == test_size):
        raise ValueError('Improper value of test_size')
    if ts_cols is None:
        if exog_vars is not None:
            ts_cols = [c for c in df.columns if c not in exog_vars]
        else:
            ts_cols = df.columns.to_list()
    exog = df[exog_vars] if exog_vars is not None else None

    # Build ARIMAs for all indicated time series, provided there are adequate
    # capta (five years is the threshold here, to allow for at least one year
    # of test data under the default settings)
    # TODO (WW): make this configurable in the long term
    for ts_col in ts_cols:
        ts = df[ts_col].dropna()
        ts_exog = exog[~pd.isna(df[ts_col])] if exog is not None else None
        if len(ts) < 60:
            logging.info(f'Skipping ARIMA for {ts_col} - too few capta')
            continue
        logging.info(f'Fitting ARIMA for {ts_col}')
        _train_and_evaluate_arima_model(
            ts,
            outputs_subdir=outputs_subdir,
            exog=ts_exog,
            test_size=test_size,
            m=m,
            df_alpha=df_alpha,
            max_diffs=max_diffs,
            max_order=max_order,
            arima_ci_alpha=arima_ci_alpha,
            plot_train_limit=plot_train_limit
        )
