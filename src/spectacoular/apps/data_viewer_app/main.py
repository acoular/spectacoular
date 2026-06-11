# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""
Time-signal data viewer application.

Start from an installed package with:

    data_viewer_app --show
"""

from pathlib import Path

import acoular as ac
import spectacoular as sp

import numpy as np

# bokeh imports
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Tabs
from bokeh.models import TabPanel as Panel
from bokeh.models.widgets import (
    Button,
    MultiSelect,
    PreText,
    RangeSlider,
    Slider,
    TextInput,
    Toggle,
)
from bokeh.palettes import Turbo256
from bokeh.plotting import figure
from bokeh.server.server import Server

rng = np.random.default_rng()
colors = np.array(Turbo256)  # for plotting different colors
rng.shuffle(colors)
doc = curdoc()

line_opts = {
    'line_color': 'color',
    'line_alpha': 0.6,
    'hover_line_color': 'color',
    'hover_line_alpha': 1.0,
}

# build processing chain
ts = sp.MaskedTimeSamples(file=Path(__file__).parent.parent / "example_data.h5")
tv = sp.TimeSamplesPresenter(
    source=ts,
    _numsubsamples=1000,
    cdsource=ColumnDataSource(
        data={"xs": [], "ys": [], "ch": [], "color": [], "sizes": []}
    ),
)
tio = ac.MaskedTimeOut(source=ts, invalid_channels=[])
ps = sp.PowerSpectra(source=tio, cached=False)
freqdata = ColumnDataSource(data={'amp': [[0]], 'freqs': [[0]], 'chn': [[0]], 'color': [[0]]})

# create widget to select the channel that should be plotted
mselect = MultiSelect(
    title="Select Channel:",
    value=[],
    height=250,
    options=[(str(i), str(i)) for i in range(ts.num_channels)],
)

# create Button to trigger plot
plot_button = Toggle(label='Plot Data', button_type='primary')
time_range = RangeSlider(
    start=ts.start,
    end=ts.num_samples,
    value=(0, ts.num_samples),
    step=1000,
    title='Time Range',
)
linesize_slider = Slider(
    start=0.0, end=5, value=2.0, step=0.05, title='Line Size', disabled=False
)


def update_linesize(_attr, _old, _new):
    """Update the line widths in the time-series plot."""
    tv.cdsource.data['sizes'] = np.array([linesize_slider.value] * len(tv.channels))


linesize_slider.on_change('value', update_linesize)

# get widgets to control settings
ts_widgets = ts.get_widgets()
ts_widgets.pop('invalid_channels')
ps_widgets = ps.get_widgets()


def file_change_callback(_attr, _old, _new):
    """Update the time-range widget after the source file changes."""
    time_range.start = ts.start
    if ts.stop:
        time_range.end = ts.stop
    else:
        time_range.end = ts.numsamples
    time_range.value = (time_range.start, time_range.end)


ts_widgets['file'].on_change('value', file_change_callback)


def get_logticks(frange=None, minor_ticks=None, unit='kHz'):
    """Return logarithmic ticks and matching labels for a frequency axis."""
    if frange is None:
        frange = [100, 10000]
    if minor_ticks is None:
        minor_ticks = [5, 2, 7]
    scales = int(np.log10(frange[1])) - int(np.log10(frange[0])) + 1
    ticks = np.logspace(int(np.log10(frange[0])), int(np.log10(frange[1])), num=scales)
    for factor in minor_ticks:
        ticks = np.append(ticks, ticks[:scales] * factor)
        ticks = ticks[frange[0] <= ticks]
        ticks = ticks[ticks <= frange[1]]
    ticks = list(np.sort(ticks))
    divisor = 1000 if unit == 'kHz' else 1
    override = {}
    for tick in ticks:
        override[str(int(tick))] = str(tick / divisor)
    return ticks, override


def get_spectra():
    """Calculate and display spectra for the selected channels."""
    selected_results, freqs, channels, plot_colors = [], [], [], []
    for selected_channel_value in mselect.value:
        selected_channel = int(selected_channel_value)
        mask_idx = [i for i in range(ts.num_channels) if i != selected_channel]
        tio.invalid_channels = mask_idx
        result = ac.L_p(np.real(ps.csm[:, 0, 0]))
        selected_results.append(result)
        freqs.append(ps.fftfreq())
        channels.append([selected_channel])
        plot_colors.append(colors[selected_channel])
    freqdata.data.update(amp=selected_results, freqs=freqs, chn=channels, color=plot_colors)
    freqplot.x_range.start = freqs[0][1] - 20
    freqplot.x_range.end = freqs[0][-1] + 20


if ac.config.have_sounddevice:  # in case of audio support
    import sounddevice as sd

    playback = sp.TimeSamplesPlayback(source=ts)
    play_button = Toggle(label='Playback Time Data', button_type='primary')
    input_device = TextInput(title='Input Index', value=str(playback.device[0]))
    output_device = TextInput(title='Output Index', value=str(playback.device[1]))
    query_button = Button(label='QueryDevices')
    query_output = PreText(width=500, height=400)

    def set_input_device(_attr, _old, new):
        """Update the selected audio input device."""
        playback.device = [int(new), playback.device[1]]

    input_device.on_change('value', set_input_device)

    def set_output_device(_attr, _old, new):
        """Update the selected audio output device."""
        playback.device = [playback.device[0], int(new)]

    output_device.on_change('value', set_output_device)

    def print_devices():
        """Show the available audio devices."""
        query_output.text = f'{sd.query_devices()}'

    query_button.on_click(print_devices)

    def play_button_handler(active):
        """Start or stop playback of the selected channels."""
        if active:
            playback.channels = [int(v) for v in mselect.value]
            playback.play()
        else:
            playback.stop()

    play_button.on_click(play_button_handler)

    pb_widget_col = column(
        play_button,
        row(input_device, output_device, width=200),
        query_button,
        query_output,
        width=200,
    )


def change_selectable_channels():
    """Refresh the list of selectable channels and reset spectral data."""
    channels = [str(idx) for idx in range(ts.num_channels)]
    mselect.options = [(i, i) for i in channels]
    freqdata.data = {'amp': [[0]], 'freqs': [[0]], 'chn': [[0]], 'color': [0]}


ts.on_trait_change(change_selectable_channels, "num_channels")

# TimeSignalPlot
timeplottips = [('Channel Index', '@ch'), ('Sample', '$x'), ('p', '$y')]
ts_plot = figure(
    title='Time Signals',
    width=1500,
    height=800,
    x_axis_label='sample index',
    y_axis_label='p [Pa]',
    tooltips=timeplottips,
)
ts_plot.toolbar.logo = None
ts_plot.multi_line(xs='xs', ys='ys', line_width='sizes', source=tv.cdsource, **line_opts)

# FrequencySignalPlot
freqplottips = [
    ("Channel", "@chn"),
    ("Frequency in Hz", "$x"),
    ("|P(f)|^2 in dB", "$y"),
]
freqplot = figure(
    title="Auto Power Spectra",
    width=1500,
    height=800,
    x_axis_type="log",
    x_axis_label="f in Hz",
    y_axis_label="|P(f)|^2 / dB",
    tooltips=freqplottips,
    x_range=(40, 26000),
)
freqplot.toolbar.logo = None
freqplot.xaxis.ticker, freqplot.xaxis.major_label_overrides = get_logticks(
    [10, 30000], unit="Hz"
)
freqplot.multi_line(xs="freqs", ys="amp", line_width=3, source=freqdata, **line_opts)
# create layout
ts_widgets_col = column(plot_button, mselect, *ts_widgets.values(), width=200)
ps_widgets_col = column(plot_button, mselect, *list(ps_widgets.values()), width=200)
if ac.config.have_sounddevice:
    time_data_layout = row(ts_widgets_col, pb_widget_col, width=200)
    freq_data_layout = row(ps_widgets_col, pb_widget_col, width=200)
else:
    time_data_layout = row(ts_widgets_col, width=100)
    freq_data_layout = row(ps_widgets_col, width=100)


# Put in Tabs
ts_tab = Panel(
    child=row(column(linesize_slider, time_range, ts_plot), time_data_layout),
    title='Time Data',
)
fd_tab = Panel(child=row(freqplot, freq_data_layout), title='Frequency Data')
plot_tab = Tabs(tabs=[ts_tab, fd_tab])


def plot():
    """Plot either the selected time signals or the selected spectra."""
    if plot_tab.active == 0:
        tv.channels = [int(v) for v in mselect.value]
        tv.update(color=[colors[int(v)] for v in mselect.value])
    elif plot_tab.active == 1:
        get_spectra()
        get_logticks([10, 30000], unit='Hz')


sp.set_calc_button_callback(plot, plot_button, label='Plot Data')


def time_range_callback(_attr, _old, _new):
    """Update the selected time window and refresh the plot."""
    ts.start = time_range.value[0]
    ts.stop = time_range.value[1]
    plot()


time_range.on_change('value_throttled', time_range_callback)


# make Document
def server_doc(doc):
    """Add the data viewer layout to a Bokeh document."""
    doc.add_root(plot_tab)
    doc.title = 'Time Signal Exploration App'


if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    server.io_loop.add_callback(server.show, '/')
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)
