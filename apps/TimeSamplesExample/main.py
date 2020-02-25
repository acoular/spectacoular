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
from bokeh.models.widgets import Toggle, Select, TextInput, Button, PreText
from bokeh.plotting import figure
from spectacoular import MaskedTimeSamples, TimeSamplesPresenter
try:
    import sounddevice as sd
    from spectacoular import TimeSamplesPlayback
    sd_enabled = True
except:
    sd_enabled = False



doc = curdoc()
# build processing chain
ts       = MaskedTimeSamples(name='example_data.h5')
tv       = TimeSamplesPresenter(source=ts, _numsubsamples = 1000)
sp       = SpectraInOut(source=ts)
playback = TimeSamplesPlayback(source=ts)
freqdata = ColumnDataSource(data=dict(amp=[0], freqs=[0]))

chidx = [str(i) for i in range(ts.numchannels)]

# create widget to select the channel that should be plotted
msWidget = Select(title="Select Channel:", value="0",
                       options=[str(i) for i in range(ts.numchannels)])
# button widget to playback the selected time data
playButton = Toggle(label="Playback Time Data", button_type="success")
# create Button to trigger plot
applyButton = Toggle(label="Plot Time Data",button_type="success")

# get widgets to control settings
tsWidgets = ts.get_widgets()
tvWidgets = tv.get_widgets()
spWidgets = sp.get_widgets()
tv.set_widgets(**{'channels': tselect})

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
    freq = sp.fftfreq()  
    result = sp.result() # result is a generator!    
    # get all spectra blocks  
    r = []
    for res in result:
        r.append(res)
    r_mean = list(mean(real(array(r).transpose((0,2,1)) * 
                       conj(array(r).transpose((0,2,1)))),axis=0))
    r_sel  = L_p(r_mean[int(tselect.value)])
    freqdata.data.update(amp=r_sel, freqs=freq)
if sd_enabled: # in case of audio support
    playback = TimeSamplesPlayback(source=ts)
    # button widget to playback the selected time data
    playButton = Toggle(label="Playback Time Data", button_type="success")
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

    playback.set_widgets(**{'channels': msWidget})

    def playButton_handler(arg):
        if arg: playback.play()
        if not arg: playback.stop()
    playButton.on_click(playButton_handler)

    pbWidgetCol = widgetbox(playButton,row(inputDevice,outputDevice,width=400),
                            queryButton,queryOutput,width=400)

def change_selectable_channels():
    channels = [str(idx) for idx in range(ts.numchannels)]
    channels.insert(0,"") # add no data field
    tselect.options = channels
ts.on_trait_change( change_selectable_channels, "numchannels")

# TimeSignalPlot
tsPlot = figure(title="Time Signals",plot_width=1000, plot_height=800,
                x_axis_label="sample index", y_axis_label="p [Pa]")
tsPlot.toolbar.logo = None
tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
# FrequencySignalPlot
freqplot = figure(title="Auto Power Spectra", plot_width=1000, plot_height=800,
                  x_axis_type="log", x_axis_label="f in Hz", y_axis_label="|P(f)|^2 / dB")
freqplot.toolbar.logo = None
freqplot.xaxis.ticker, freqplot.xaxis.major_label_overrides = get_logticks([10, 30000], unit="Hz")
freqplot.line('freqs', 'amp', source=freqdata)
#create layout
tsWidgetsCol = widgetbox(applyButton,*tsWidgets.values(),width=400)
if sd_enabled: 
    allWidgetsLayout = column(msWidget,row(tsWidgetsCol,pbWidgetCol))
else:
    allWidgetsLayout = column(msWidget,row(tsWidgetsCol))
doc.add_root(row(tsPlot,allWidgetsLayout))

def plot(arg):
    if arg:
        applyButton.label = 'Plotting ...'
        if plotTab.active == 0: 
            tv.update()
        if plotTab.active == 1: 
            get_spectra()
            get_logticks()
        applyButton.active = False
        applyButton.label = 'Plot Data'
    if not arg:
        applyButton.label = 'Plot Data'
applyButton.on_click(plot)

