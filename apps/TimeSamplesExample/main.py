# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to plot TimeData
"""
from bokeh.io import curdoc
from bokeh.layouts import row, column
# from bokeh.events import MouseLeave
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Toggle, TextInput, Button, PreText, \
Tabs, Panel, MultiSelect
from bokeh.plotting import figure
from bokeh.palettes import Blues
from bokeh.server.server import Server
from numpy import mean, conj, real, array, log10, logspace,append,sort
from acoular import L_p, MaskedTimeInOut
from spectacoular import MaskedTimeSamples, TimeSamplesPresenter,\
    set_calc_button_callback, PowerSpectra
try:
    import sounddevice as sd
    from spectacoular import TimeSamplesPlayback
    sd_enabled = True
except:
    sd_enabled = False

COLORS = Blues[256][::-3] # for plotting different colors
doc = curdoc()

# build processing chain
ts       = MaskedTimeSamples(name='example_data.h5')
tv       = TimeSamplesPresenter(source=ts, _numsubsamples = 1000)
tio      = MaskedTimeInOut(source=ts,invalid_channels=[])
ps       = PowerSpectra(time_data=tio, cached=False) #SpectraInOut(source=ts)
freqdata = ColumnDataSource(data=dict(amp=[[0]], freqs=[[0]], chn=[[0]],color=[[0]]))

chidx = [str(i) for i in range(ts.numchannels)]

# create widget to select the channel that should be plotted
mselect = MultiSelect(title="Select Channel:", value=["0"],
                               options=[(i,i) for i in chidx])

# create Button to trigger plot
plotButton = Toggle(label="Plot Data",button_type="primary")

# get widgets to control settings
tsWidgets = ts.get_widgets()
tsWidgets.pop('invalid_channels')
tvWidgets = tv.get_widgets()
psWidgets = ps.get_widgets()

# THIS FUNCTION GENERATES THE TICKS (TO MOVE)
def get_logticks(frange=[100, 10000], minor_ticks=[5,2,7], unit='kHz'):
    scales = int(log10(frange[1]))-int(log10(frange[0]))+1
    # start with major ticks
    ticks = logspace(int(log10(frange[0])),int(log10(frange[1])), num=scales)
    for n in minor_ticks:
        ticks = append(ticks, ticks[:scales]*n)
        ticks = ticks[frange[0]<=ticks] # lower bound
        ticks = ticks[ticks<=frange[1]] # upper bound
    ticks = list(sort(ticks))
    if unit =='kHz':
        d = 1000
    else:
        d = 1
    override = dict()
    for tick in ticks:
        override[str(int(tick))] = str(tick/d)
    return ticks, override
        
def get_spectra():
    r_sel, freq, chn, color = [], [], [], []
    for sel in mselect.value:
        sel = int(sel)
        mask_idx = [i for i in range(ts.numchannels) if not i == sel]
        tio.invalid_channels = mask_idx # don't calculate unused spectra
        result = L_p(real(ps.csm[:,0,0]))
        r_sel.append(result) # multiselect ColumnDataSource expects a list of lists
        freq.append(ps.fftfreq())
        chn.append([sel])
        color.append([COLORS[sel]])
    freqdata.data.update(amp=r_sel, freqs=freq, chn=chn,color=color)
    freqplot.x_range.start = freq[0][1]-20
    freqplot.x_range.end   = freq[0][-1]+20

if sd_enabled: # in case of audio support
    playback = TimeSamplesPlayback(source=ts)
    # button widget to playback the selected time data
    playButton = Toggle(label="Playback Time Data", button_type="primary")
    # Input Device Textfield
    inputDevice = TextInput(title="Input Device Index", value=str(playback.device[0]))
    # Output Device Textfield
    outputDevice = TextInput(title="Output Device Index", value=str(playback.device[1]))
    # QueryDevices
    queryButton = Button(label="QueryDevices")
    queryOutput = PreText(width=500, height=400)

    def set_input_device(attr,old,new):
        playback.device = [int(new), playback.device[1]]
    inputDevice.on_change('value',set_input_device) 
        
    def set_output_device(attr,old,new):
        playback.device = [playback.device[0],int(new)]
    outputDevice.on_change('value',set_output_device) 

    def print_devices():
        queryOutput.text = f"{sd.query_devices()}"
    queryButton.on_click(print_devices)

    #playback.set_widgets(**{'channels': tselect})

    def playButton_handler(arg):
        if arg:
            playback.channels = [int(v) for v in mselect.value]
            playback.play()
        if not arg: playback.stop()
    playButton.on_click(playButton_handler)

    pbWidgetCol = column(playButton,row(inputDevice,outputDevice,width=400),
                            queryButton,queryOutput,width=400)

def change_selectable_channels():
    channels = [str(idx) for idx in range(ts.numchannels)]
    mselect.options = [(i,i) for i in channels]
    freqdata.data = dict(amp=[[0]], freqs=[[0]], chn=[[0]],color=[[0]])
ts.on_trait_change( change_selectable_channels, "numchannels")

# TimeSignalPlot
tsPlot = figure(title="Time Signals",plot_width=1000, plot_height=800,
                x_axis_label="sample index", y_axis_label="p [Pa]")
tsPlot.toolbar.logo = None
tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)

# FrequencySignalPlot
freqplottips = [("Channel", "@chn"),("Frequency in Hz", "$x"),("|P(f)|^2 in dB", "$y")]
freqplot = figure(title="Auto Power Spectra", plot_width=1000, plot_height=800,
                  x_axis_type="log", x_axis_label="f in Hz", y_axis_label="|P(f)|^2 / dB",
                  tooltips=freqplottips, x_range=(40,26000))
freqplot.toolbar.logo = None
freqplot.xaxis.ticker, freqplot.xaxis.major_label_overrides = get_logticks([10, 30000], unit="Hz")
freqplot.multi_line(xs='freqs', ys='amp',color='color', source=freqdata)
#create layout
tsWidgetsCol = column(plotButton,mselect,*tsWidgets.values(),width=400)
psWidgetsCol = column(plotButton,mselect,*list(psWidgets.values()),
                         width=400)
if sd_enabled: 
    timeDataLayout = row(tsWidgetsCol,pbWidgetCol)
    freqDataLayout = row(psWidgetsCol,pbWidgetCol)
else:
    allWidgetsLayout = row(tsWidgetsCol)
    freqDataLayout = row(psWidgetsCol)


# Put in Tabs
tsTab = Panel(child=row(tsPlot,timeDataLayout), title='Time Data')
fdTab = Panel(child=row(freqplot,freqDataLayout), title='Frequency Data')
plotTab = Tabs(tabs=[tsTab,fdTab])

def plot():
    if plotTab.active == 0: 
        tv.channels = [int(v) for v in mselect.value]
        tv.update()
    elif plotTab.active == 1:
        get_spectra()
        get_logticks([10, 30000], unit="Hz")
set_calc_button_callback(plot,plotButton,label='Plot Data')

# make Document
def server_doc(doc):
    doc.add_root(plotTab)
    doc.title = "TimeSamplesApp"

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)