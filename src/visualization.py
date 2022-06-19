"""Visualization functionality"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import statsmodels.api as sm

from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import plotnine as p9

from utils import get_full_park_name, get_long_park_type, ordinal


def plot_differenced_ts(
        ts,
        lags=None,
        diffs=0,
        m=1,
        df_p_value=None,
        figure_size=(12, 8),
        fp=None
):
    """Produce a collection of artifacts for evaluating a time series. Adapted
    from https://towardsdatascience.com/multi-step-time-series-forecasting-with-arima-lightgbm-and-prophet-cc9e3f95dfb0.

    Args:
        ts (pd.Series): a time series
        lags (int): the number of lag steps to be included in the ACF and PACF
            plots, if None this will be inferred automatically
        diffs (int): the number of times that differencing was applied before
            a Dickey-Fuller test was significant (used only for titling the
            plot)
        m (int): the period of applied seasonal differencing, if any
        df_p_value (float): the pre-computed result of a Dickey-Fuller test, if
            None this will be calculated anew in the function
        figure_size (tuple): the figure size
        fp (str): a path where the plot should be saved, if None then the plot
            is drawn in stdout

    Returns:
        None
    """

    # Coerce input to series if not already
    if not isinstance(ts, pd.Series):
        ts = pd.Series(ts, name='Time Series')

    # Create subpanels for subplots by creating a gridspec on top of an empty
    # plotnine figure (junk data is needed for backend "copy" reasons)
    fig = (
        p9.ggplot()
        + p9.geom_blank(data=pd.DataFrame(ts))
        + p9.theme_void()
        + p9.theme(figure_size=figure_size)
    ).draw()
    gs = GridSpec(2, 2)
    ts_ax = fig.add_subplot(gs[0, 0:2])
    acf_ax = fig.add_subplot(gs[1, 0])
    pacf_ax = fig.add_subplot(gs[1, 1])

    # Plot of the time series itself
    if df_p_value is None:
        df_p_value = sm.tsa.stattools.adfuller(ts)[1]
    ts_plot = (
        p9.ggplot(
            data=pd.DataFrame(ts), mapping=p9.aes(x='ts.index', y=f'{ts.name}')
        )
        + p9.geom_line()
        + p9.labs(x='Time', y='Monthly Visitors')
        + p9.theme_538()
        + p9.theme(axis_text_x=p9.element_text(rotation=90))
    )
    # A hack using a protected method is necessary to make plotnine work with
    # matplotlib's subplot functionality
    _ = ts_plot._draw_using_figure(figure=fig, axs=[ts_ax])
    ts_ax.set_title(
        'Time Series Analysis Plots for '
        + f'{str(m) + "-Step Deseasoned, " if m > 1 else ""}'
        + f'{ordinal(diffs)}-Order Differenced {ts.name}\n'
        + f'Dickey-Fuller $p$-value: {df_p_value:.5}'
    )

    # The other plots are created by statsmodels and fully compatible with the
    # matplotlib API
    sm.tsa.graphics.plot_acf(ts, ax=acf_ax, lags=lags)
    sm.tsa.graphics.plot_pacf(ts, ax=pacf_ax, lags=lags)

    plt.tight_layout()

    # Save or draw, as indicated
    if fp is None:
        fig.show()
    else:
        plt.savefig(fp)
        plt.close(fig)


def plot_forecast(
        train_ts,
        test_ts,
        forecast,
        forecast_ci,
        train_limit=None,
        figure_size=(12, 4),
        fp=None
):
    """Plots a forecast against the training capta and a holdout test set.

    Args:
        train_ts (pd.Series): the time series used to train the model
        test_ts (pd.Series): the holdout test portion of the time series
        forecast (array-like): the forecasts produced by an ARIMA model
        forecast_ci (array-like): the confidence interval for the forecasts
            produced by an ARIMA model
        train_limit (numeric): if present, the product of this number and the
            length of the test set will determine the maximum number of points
            in the training set to plot
        figure_size (tuple): the figure size
        fp (str): a path where the plot should be saved, if None then the plot
            is drawn in stdout

    Returns:
        None
    """

    # All series and forecasts should refer to the same phenomenon, and should
    # thus have the same name
    ts_name = train_ts.name
    # TODO (WW): make the below less hacky
    try:
        full_name = get_full_park_name(ts_name)
    except AttributeError:
        full_name = get_long_park_type(ts_name)
    mae = mean_absolute_error(test_ts, forecast)
    mape = mean_absolute_percentage_error(test_ts, forecast)

    # Subsample the training set for plotting if so indicated
    if train_limit is not None:
        train_limit = int(np.ceil(train_limit * len(test_ts)))
        # Ensure that there are sufficient capta to be plotted
        if not 0 < train_limit <= len(train_ts):
            raise ValueError('train_limit outside of acceptable bounds')
        train_ts = train_ts[-train_limit:]

    # Arrange all the capta into tidy objects for plotting - resetting all of
    # the indexes is necessary since the test and forecast time ranges coincide
    train_ts_df = pd.DataFrame(
        {ts_name: train_ts, 'forecast': False, 'split': 'train'}
    ).reset_index()
    test_ts_df = pd.DataFrame(
        {ts_name: test_ts, 'forecast': False, 'split': 'test'}
    ).reset_index()
    forecast_df = pd.DataFrame(
        {
            ts_name: forecast,
            'forecast': True,
            'split': 'forecast',
            'lower_bound': forecast_ci[:, 0],
            'upper_bound': forecast_ci[:, 1]
        },
        index=test_ts.index
    ).reset_index()
    plot_df = pd.concat(
        [train_ts_df, test_ts_df, forecast_df],
        ignore_index=True
    )

    # Filling NaNs is necessary so that plotnine doesn't drop the entire geom
    plot_df['lower_bound'] = plot_df['lower_bound'].fillna(plot_df[ts_name])
    plot_df['upper_bound'] = plot_df['upper_bound'].fillna(plot_df[ts_name])

    # Solid plot of the true values, dashed line plot of the forecast, and
    # ribbon plot of the forecase confidence interval
    forecast_plot = (
        p9.ggplot(
            data=plot_df,
            mapping=p9.aes(
                x='dt_pk',
                y=ts_name,
                color='split',
                linetype='forecast'
            )
        )
        + p9.geom_line()
        + p9.geom_ribbon(
            mapping=p9.aes(x='dt_pk', ymin='lower_bound', ymax='upper_bound'),
            fill='grey',
            alpha=0.5,
            inherit_aes=False
        )
        + p9.scale_color_brewer(type='qual', palette='Paired')
        + p9.labs(
            x='Time',
            y='Monthly Visitors',
            title=f'Forecast for {full_name}\nMAE = {mae:.5}, MAPE = {mape:.5}'
        )
        + p9.theme_538()
        + p9.theme(
            figure_size=figure_size,
            axis_text_x=p9.element_text(rotation=90)
        )
    )

    # Save or draw, as indicated
    if fp is None:
        forecast_plot.draw();
    else:
        forecast_plot.save(fp, verbose=False)
