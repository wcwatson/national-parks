"""Class for managing model training. Note that all "helper" training functions
must take a DataFrame as input, as well as an optional argument named
outputs_subdir, which specifies identically named subdirectories of models/ and
plots/ where relevant artifacts may be written. Additional keyword arguments
may also be required and are passed in with the ** unpacking operator.
"""

import joblib
import logging
import os

from hydra.utils import to_absolute_path
from pmdarima.arima import AutoARIMA
import statsmodels.api as sm

from visualization import plot_differenced_ts, plot_forecast


def _get_output_dirs(name, outputs_subdir=None):
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


def _train_and_evaluate_arima_models(
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

    for ts_col in ts_cols:
        ts = df[ts_col].dropna()
        if len(ts) < 36:
            logging.info(f'Skipping ARIMA for {ts_col} - too few capta')
            continue  # TODO (WW): clarify / config this logic
        logging.info(f'Fitting ARIMA for {ts_col}')

        # Setup output paths and split capta for training and evaluation
        model_output_path, plots_output_path = _get_output_dirs(
            ts_col, outputs_subdir
        )
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
        diff_ts = (
            (train_ts - train_ts.shift(m)).dropna() if m > 1
            else train_ts
        )
        diff_ts, diffs, df_p_value = _detrend_time_series(
            diff_ts, alpha=df_alpha, max_diffs=max_diffs
        )
        plot_differenced_ts(
            diff_ts,
            diffs=diffs,
            m=m,
            df_p_value=df_p_value,
            fp=os.path.join(plots_output_path, f'{ts_col}_analysis.png')
        )

        # Fit and evaluate an ARIMA model, writing both the model object and an
        # analytic summary to the models/ directory
        # NB: this uses the original time series rather than the detrended time
        # series analyzed above, since AutoARIMA will determine an appropriate
        # degree of differencing automatically
        arima_model = AutoARIMA(m=m, max_order=max_order)
        arima_model.fit(train_ts, X=train_exog)
        arima_model_fn = os.path.join(model_output_path, f'{ts_col}_arima.pkl')
        joblib.dump(arima_model, arima_model_fn)
        arima_summary_fn = os.path.join(
            model_output_path, f'{ts_col}_arima_summary.txt'
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
            fp=os.path.join(plots_output_path, f'{ts_col}_forecast.png')
        )


class NationalParkModel(object):
    """Object for managing model training.

    Attributes:
        algorithm_name (str): the name of an ML algorithm to apply
        outputs_subdir (str): identically named subdirectory within models/ and
            plots/ where output artifacts should be written
        params (dict): a dictionary of parameters to be passed to the relevant
            algorithm
    """

    def __init__(self, algorithm_name, outputs_subdir, params=None):
        _allowable_algorithms = {
            'arima': _train_and_evaluate_arima_models
        }
        if algorithm_name not in _allowable_algorithms:
            raise NotImplementedError(
                f'Unimplemented algorithm {algorithm_name}'
            )
        self.algorithm_name = algorithm_name
        self._algorithm = _allowable_algorithms[algorithm_name]
        self.outputs_subdir = outputs_subdir
        self.params = params if params is not None else {}

    def fit_and_evaluate(self, df):
        """Applies the indicated ML training algorithm to a DataFrame and
        evaluates the result, including writing any artifacts to models/ and
        plots/.

        Args:
            df (pd.DataFrame): a DataFrame to be fit

        Returns:
            None
        """
        self._algorithm(df, self.outputs_subdir, **self.params)
