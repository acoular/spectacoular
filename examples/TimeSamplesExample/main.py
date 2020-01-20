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
from bokeh.events import MouseLeave
from bokeh.models.widgets import Toggle, Select, TextInput, Button, PreText
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import MaskedTimeSamples, TimeSamplesPresenter,TimeSamplesPlayback
import sounddevice as sd

doc = curdoc()
# build processing chain
ts = MaskedTimeSamples(name='example_data.h5')
tv = TimeSamplesPresenter(source=ts)
playback = TimeSamplesPlayback(source=ts)

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
tv.set_widgets(**{'channels': msWidget})
playback.set_widgets(**{'channels': msWidget})

def plot(arg):
    if arg:
        applyButton.label = 'Plotting ...'
        tv.update()
        applyButton.active = False
        applyButton.label = 'Plot Time Data'
    if not arg:
        applyButton.label = 'Plot Time Data'
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
tsPlot = figure(title="Time Signals",plot_width=1000, plot_height=800)
tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
#create layout
tsWidgetsCol = widgetbox(applyButton,*tsWidgets.values(),width=400)
pbWidgetCol = widgetbox(playButton,row(inputDevice,outputDevice,width=400),
                        queryButton,queryOutput,width=400)
allWidgetsLayout = column(msWidget,row(tsWidgetsCol,pbWidgetCol))
doc.add_root(row(tsPlot,allWidgetsLayout))

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.

