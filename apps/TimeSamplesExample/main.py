# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to plot TimeData
"""
from bokeh.io import curdoc
from bokeh.layouts import column, row, widgetbox
# from bokeh.events import MouseLeave
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Toggle, Select, TextInput, Button, PreText, Tabs, Panel
from bokeh.plotting import figure
# from bokeh.server.server import Server
from spectacoular import MaskedTimeSamples, TimeSamplesPresenter,TimeSamplesPlayback, \
                         SpectraInOut                       
import sounddevice as sd
# from spectra_example import SpectraInOut
from acoular import L_p
from numpy import mean, conj, real, array



doc = curdoc()
# build processing chain
ts       = MaskedTimeSamples(name='example_data.h5')
tv       = TimeSamplesPresenter(source=ts, _numsubsamples = 1000)
sp       = SpectraInOut(source=ts)
playback = TimeSamplesPlayback(source=ts)
freqdata = ColumnDataSource(data=dict(amp=[0], freqs=[0]))

# create widget to select the channel that should be plotted
msWidget = Select(title="Select Channel:", value="0",
                       options=[str(i) for i in range(ts.numchannels)])
# button widget to playback the selected time data
playButton = Toggle(label="Playback Time Data", button_type="success")
# create Button to trigger plot
applyButton = Toggle(label="Plot Time Data",button_type="success")
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

# get widgets to control settings
tsWidgets = ts.get_widgets()
tvWidgets = tv.get_widgets()
spWidgets = sp.get_widgets()
# blkWidget = Select(title="Block Size", value="256", 
#                    options=["128","256","512","1024","2048","4096","8192"])
tv.set_widgets(**{'channels': msWidget})
playback.set_widgets(**{'channels': msWidget})

def get_spectra():
    freq = sp.fftfreq()  
    result = sp.result() # result is a generator!    
    res = next(result) # yields first spectra Block for all 56 channels 
    # get all spectra blocks  
    r = []
    for res in result:
        r.append(res)
    r_mean = list(mean(real(array(r).transpose((0,2,1)) * 
                       conj(array(r).transpose((0,2,1)))),axis=0))
    r_sel  = L_p(r_mean[int(msWidget.value)])
    freqdata.data.update(amp=r_sel, freqs=freq)

def plot(arg):
    if arg:
        applyButton.label = 'Plotting ...'
        tv.update()
        get_spectra()
        applyButton.active = False
        applyButton.label = 'Plot Data'
    if not arg:
        applyButton.label = 'Plot Data'
applyButton.on_click(plot)

def change_selectable_channels():
    channels = [str(idx) for idx in range(ts.numchannels)]
    channels.insert(0,"") # add no data field
    msWidget.options = channels
ts.on_trait_change( change_selectable_channels, "numchannels")

def playButton_handler(arg):
    if arg: playback.play()
    if not arg: playback.stop()
playButton.on_click(playButton_handler)

# TimeSignalPlot
tsPlot = figure(title="Time Signals",plot_width=1000, plot_height=800,
                x_axis_label="sample index", y_axis_label="p [Pa]")
tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
tsPlot.xaxis.axis_label_text_font_style = "normal"
tsPlot.yaxis.axis_label_text_font_style = "normal"
tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
# FrequencySignalPlot
f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
f_ticks_override = {20: '0.02', 50: '0.05', 100: '0.1', 200: '0.2', 500: '0.5', 1000: '1', 2000: '2', 5000: '5', 10000: '10', 20000: '20'}
freqplot = figure(title="Auto Power Spectra", plot_width=1000, plot_height=800,
                  x_axis_type="log", x_axis_label="f in kHz", y_axis_label="|P(f)|^2 / dB")
freqplot.xaxis.axis_label_text_font_style = "normal"
freqplot.yaxis.axis_label_text_font_style = "normal"
freqplot.xgrid.minor_grid_line_color = 'grey'
freqplot.xgrid.minor_grid_line_alpha = 0.3
freqplot.xaxis.ticker = f_ticks
freqplot.xaxis.major_label_overrides = f_ticks_override
freqplot.line('freqs', 'amp', source=freqdata, line_color="lime")
# Put in Tabs
tsTab = Panel(child=tsPlot, title='Time Data')
fdTab = Panel(child=freqplot, title='Frequency Data')
plotTab = Tabs(tabs=[tsTab, fdTab])
#create layout
tsWidgetsCol = widgetbox(applyButton,*tsWidgets.values(),width=400)
pbWidgetCol = widgetbox(playButton,spWidgets['window'],spWidgets['block_size'],
                        row(inputDevice,outputDevice,width=400),
                        queryButton,queryOutput,width=400)
allWidgetsLayout = column(msWidget,row(tsWidgetsCol,pbWidgetCol))
doc.add_root(row(plotTab,allWidgetsLayout))

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.

