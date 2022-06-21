"""Plotting functionality associated with the analysis of time series
themselves, independent of any modeling efforts.
"""

import pandas as pd
import statsmodels.api as sm

from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import plotnine as p9

from .utils import get_full_series_name, ordinal


def plot_time_series(ts, rolling_window=None, figure_size=(12, 8), fp=None):
    """Plots a time series.

    Args:
        ts (pd.Series): a time series
        rolling_window (int): the size of the window over which to apply
            and plot a rolling average, if None then no rolling average is
            plotted
        figure_size (tuple): the figure size
        fp (str): a path where the plot should be saved, if None then the plot
            is drawn in stdout

    Returns:
        None
    """

    # Coerce input to series if not already
    if not isinstance(ts, pd.Series):
        ts = pd.Series(ts, name='Time Series')
    ts_name = ts.name
    full_name = get_full_series_name(ts_name)
    ts_df = pd.DataFrame(ts)
    plot_title = full_name + '\nMonthly Visitors'

    # These objects have to be created before the ggplot object to be used
    if rolling_window is not None:
        rolling_avg_df = (
            ts_df.rolling(window=rolling_window, center=True).mean().dropna()
        )
        plot_title += f' and {rolling_window}-Month Rolling Average'

    # Plot of the actual time series
    ts_plot = (
        p9.ggplot(data=ts_df, mapping=p9.aes(x='ts_df.index', y=ts_name))
        + p9.geom_line(color='#a6cee3')
        + p9.labs(
            x='Time',
            y='Monthly Visitors',
            title=plot_title
        )
        + p9.theme_538()
        + p9.theme(
            figure_size=figure_size,
            axis_text_x=p9.element_text(rotation=90)
        )
    )

    # If indicated, add a plot of a rolling average
    if rolling_window is not None:
        ts_plot += p9.geom_line(
            data=rolling_avg_df,
            mapping=p9.aes(x='rolling_avg_df.index', y=ts_name),
            inherit_aes=False,
            color='#1f78b4'
        )

    # Save or draw, as indicated
    if fp is None:
        ts_plot.draw()
    else:
        ts_plot.save(fp, verbose=False)


def plot_differenced_time_series(
        ts,
        lags=None,
        diffs=0,
        m=1,
        df_p_value=None,
        figure_size=(12, 8),
        fp=None
):
    """Produces a collection of artifacts for evaluating a time series. Adapted
    from https://towardsdatascience.com/multi-step-time-series-forecasting...
    ...-with-arima-lightgbm-and-prophet-cc9e3f95dfb0.

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
    ts_name = ts.name
    full_name = get_full_series_name(ts_name)

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
        + f'{ordinal(diffs)}-Order Differenced Series for\n'
        + f'{full_name}\n'
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
