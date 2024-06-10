#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to plot TimeData
"""
from bokeh.io import curdoc
from bokeh.layouts import row, column
# from bokeh.events import MouseLeave
from bokeh.models import ColumnDataSource
# bokeh > 3.0
from bokeh.models import Tabs, TabPanel as Panel
# bokeh < 3.0
# from bokeh.models.widgets import Panel, Tabs
from bokeh.models.widgets import Toggle, TextInput, Button, PreText, \
MultiSelect, RangeSlider, Slider
from bokeh.plotting import figure
from bokeh.palettes import Turbo256
from bokeh.server.server import Server
from numpy import real, array, log10, logspace,append,sort
from numpy.random import shuffle
from acoular import L_p, MaskedTimeInOut
from spectacoular import MaskedTimeSamples, TimeSamplesPresenter,\
    set_calc_button_callback, PowerSpectra
try:
    import sounddevice as sd
    from spectacoular import TimeSamplesPlayback
    sd_enabled = True
except:
    sd_enabled = False

COLORS=array(Turbo256) # for plotting different colors
shuffle(COLORS)
doc = curdoc()

line_opts = dict(
    line_color='color', line_alpha=0.6,
    hover_line_color='color', hover_line_alpha=1.0,
)

# build processing chain
ts       = MaskedTimeSamples(name='/home/kujawski/Documents/Code/spectacoular_dev/spectacoular/apps/example_data.h5')
tv       = TimeSamplesPresenter(source=ts, _numsubsamples = 1000)
tio      = MaskedTimeInOut(source=ts,invalid_channels=[])
ps       = PowerSpectra(time_data=tio, cached=False) #SpectraInOut(source=ts)
freqdata = ColumnDataSource(data=dict(amp=[[0]], freqs=[[0]], chn=[[0]],color=[[0]]))

# set up callbacks
ts.on_trait_change(tv.update,'digest')

chidx = [str(i) for i in range(ts.numchannels)]

# create widget to select the channel that should be plotted
mselect = MultiSelect(title="Select Channel:", value=["0"],
                               options=[(i,i) for i in chidx])
tv.cdsource.data['color'] = [COLORS[int(v)] for v in mselect.value]

# create Button to trigger plot
plotButton = Toggle(label="Plot Data",button_type="primary")
timeRange = RangeSlider(start=ts.start,end=ts.numsamples,value=(0,ts.numsamples), step=1000, title="Time Range")
linesizeSlider = Slider(start=0.0, end=5, value=2., 
                    step=0.05, title="Line Size",disabled=False)
def update_linesize(attr,old,new):
    tv.cdsource.data['sizes'] = array([linesizeSlider.value]*len(tv.channels))
    #freqdata.data['sizes'] = array([linesizeSlider.value]*len(tv.channels))
linesizeSlider.on_change('value', update_linesize)
update_linesize(None,None,None) 


# get widgets to control settings
tsWidgets = ts.get_widgets()
tsWidgets.pop('invalid_channels')
psWidgets = ps.get_widgets()

def file_change_callback(attr,old,new):
    timeRange.start = ts.start 
    if ts.stop:
        timeRange.end = ts.stop 
    else:
        timeRange.end = ts.numsamples  
    timeRange.value=(timeRange.start,timeRange.end)

tsWidgets['name'].on_change('value',file_change_callback)

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
        color.append(COLORS[sel])
    freqdata.data.update(amp=r_sel, freqs=freq, chn=chn,color=color)
    freqplot.x_range.start = freq[0][1]-20
    freqplot.x_range.end   = freq[0][-1]+20

if sd_enabled: # in case of audio support
    playback = TimeSamplesPlayback(source=ts)
    # button widget to playback the selected time data
    playButton = Toggle(label="Playback Time Data", button_type="primary")
    # Input Device Textfield
    inputDevice = TextInput(title="Input Index", value=str(playback.device[0]))
    # Output Device Textfield
    outputDevice = TextInput(title="Output Index", value=str(playback.device[1]))
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
        elif not arg: 
            playback.stop()
    playButton.on_click(playButton_handler)

    pbWidgetCol = column(playButton,row(inputDevice,outputDevice,width=200),
                            queryButton,queryOutput,width=200)

def change_selectable_channels():
    channels = [str(idx) for idx in range(ts.numchannels)]
    mselect.options = [(i,i) for i in channels]
    freqdata.data = dict(amp=[[0]], freqs=[[0]], chn=[[0]],color=[0])
ts.on_trait_change( change_selectable_channels, "numchannels")

# TimeSignalPlot
timeplottips = [("Channel Index", "@ch"),("Sample", "$x"),("p", "$y")]
tsPlot = figure(title="Time Signals",width=1500, height=800,
                x_axis_label="sample index", y_axis_label="p [Pa]",
                tooltips=timeplottips,)
tsPlot.toolbar.logo = None
tsPlot.multi_line(xs='xs', ys='ys',
                    line_width='sizes',
                    source=tv.cdsource, **line_opts)

# FrequencySignalPlot
freqplottips = [("Channel", "@chn"),("Frequency in Hz", "$x"),("|P(f)|^2 in dB", "$y")]
freqplot = figure(title="Auto Power Spectra", width=1500, height=800,
                  x_axis_type="log", x_axis_label="f in Hz", y_axis_label="|P(f)|^2 / dB",
                  tooltips=freqplottips, x_range=(40,26000))
freqplot.toolbar.logo = None
freqplot.xaxis.ticker, freqplot.xaxis.major_label_overrides = get_logticks([10, 30000], unit="Hz")
freqplot.multi_line(xs='freqs', ys='amp',line_width=3, source=freqdata, **line_opts)
#create layout
tsWidgetsCol = column(plotButton,mselect,*tsWidgets.values(),width=200)
psWidgetsCol = column(plotButton,mselect,*list(psWidgets.values()),
                         width=200)
if sd_enabled: 
    timeDataLayout = row(tsWidgetsCol,pbWidgetCol,width=200)
    freqDataLayout = row(psWidgetsCol,pbWidgetCol,width=200)
else:
    timeDataLayout = row(tsWidgetsCol,width=100)
    freqDataLayout = row(psWidgetsCol,width=100)


# Put in Tabs
tsTab = Panel(child=row(column(linesizeSlider,timeRange,tsPlot),timeDataLayout), title='Time Data')
fdTab = Panel(child=row(freqplot,freqDataLayout), title='Frequency Data')
plotTab = Tabs(tabs=[tsTab,fdTab])

def plot():
    if plotTab.active == 0: 
        tv.channels = [int(v) for v in mselect.value]
        tv.update() #TODO: add argument to update function that handles aditional data that should be added to the ColumnDataSource
        tv.cdsource.data['color'] = [COLORS[int(v)] for v in mselect.value] 
    elif plotTab.active == 1:
        get_spectra()
        get_logticks([10, 30000], unit="Hz")
set_calc_button_callback(plot,plotButton,label='Plot Data')

def time_range_callback(attr,old,new):
    ts.start = timeRange.value[0]
    ts.stop = timeRange.value[1]
    plot()
timeRange.on_change('value_throttled',time_range_callback)

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