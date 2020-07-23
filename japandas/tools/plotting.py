#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import pandas as pd

try:
    from pandas.plotting._matplotlib import LinePlot
except ImportError:
    from pantas.tools.plotting import LinePlot

try:
    from pandas.plotting._core import PlotAccessor as accessor
    from pandas.plotting._matplotlib import PLOT_CLASSES as plot_classes
except ImportError:
    from pandas.plotting._core import plotting as accessor
    from pandas.plotting._core.plotting import _plot_klass as plot_classes

from japandas.io.data import _ohlc_columns_jp, _ohlc_columns_en


class OhlcPlot(LinePlot):
    ohlc_cols = pd.Index(['open', 'high', 'low', 'close'])
    reader_cols_en = pd.Index(_ohlc_columns_en)
    reader_cols_jp = pd.Index(_ohlc_columns_jp)

    def __init__(self, data, **kwargs):
        data = data.copy()
        self.freq = kwargs.pop('freq', 'B')

        if isinstance(data, pd.Series):
            data = data.resample(self.freq).ohlc()
        assert isinstance(data, pd.DataFrame)
        assert isinstance(data.index, pd.DatetimeIndex)

        if data.columns.equals(self.ohlc_cols):
            data.columns = [c.title() for c in data.columns]
        elif data.columns.equals(self.reader_cols_jp):
            data.columns = self.reader_cols_en
        elif data.columns.equals(self.reader_cols_en):
            pass
        else:

            raise ValueError('data is not ohlc-like:')
        data = data[['Open', 'Close', 'High', 'Low']]
        LinePlot.__init__(self, data, **kwargs)

    def _get_plot_function(self):
        try:
            from mplfinance.original_flavor import candlestick_ohlc
        except ImportError as e:
            try:
                from matplotlib.finance import candlestick_ohlc
            except ImportError:
                raise ImportError(e)

        def _plot(data, ax, **kwds):
            candles = candlestick_ohlc(ax, data.values, **kwds)
            return candles

        return _plot

    def _make_plot(self):
        from pandas.plotting._matplotlib.timeseries import _decorate_axes, format_dateaxis
        plotf = self._get_plot_function()
        ax = self._get_ax(0)

        data = self.data
        data.index.name = 'Date'
        data = data.to_period(freq=self.freq)
        index = data.index
        data = data.reset_index(level=0)

        if self._is_ts_plot():
            data['Date'] = data['Date'].apply(lambda x: x.ordinal)
            _decorate_axes(ax, self.freq, self.kwds)
            candles = plotf(data, ax, **self.kwds)
            format_dateaxis(ax, self.freq, index)
        else:
            from matplotlib.dates import date2num, AutoDateFormatter, AutoDateLocator

            data['Date'] = data['Date'].apply(lambda x: date2num(x.to_timestamp()))
            candles = plotf(data, ax, **self.kwds)

            locator = AutoDateLocator()
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(AutoDateFormatter(locator))

        return candles


if 'ohlc' not in accessor._common_kinds:
    accessor._common_kinds = (*accessor._common_kinds, 'ohlc')
    accessor._all_kinds = (*accessor._all_kinds, 'ohlc')
    plot_classes['ohlc'] = OhlcPlot
