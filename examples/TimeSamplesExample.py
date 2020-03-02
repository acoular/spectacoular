# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to plot TimeData
"""
from bokeh.layouts import row, widgetbox
from bokeh.models.widgets import Toggle, Select, TextInput, Button, PreText,\
Tabs,Panel
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server
from numpy import mean, conj, real, array
from acoular import L_p
from spectacoular import MaskedTimeSamples, TimeSamplesPresenter, SpectraInOut,\
    set_calc_button_callback
try:
    import sounddevice as sd
    from spectacoular import TimeSamplesPlayback
    sd_enabled = True
except:
    sd_enabled = False

# build processing chain
ts       = MaskedTimeSamples(name='example_data.h5')
tv       = TimeSamplesPresenter(source=ts, _numsubsamples = 1000)
sp       = SpectraInOut(source=ts)
freqdata = ColumnDataSource(data=dict(amp=[0], freqs=[0]))
chidx = [str(i) for i in range(ts.numchannels)]

# create widget to select the channel that should be plotted
tselect = Select(title="Select Channel:", value="0",options=chidx)
# create Button to trigger plot
plotButton = Toggle(label="Calculate",button_type="primary")

# get widgets to control settings
tsWidgets = ts.get_widgets()
tvWidgets = tv.get_widgets()
spWidgets = sp.get_widgets()
tv.set_widgets(**{'channels': tselect})

def get_spectra():
    # sp.block_size = int(blkWidget.value)
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

    playback.set_widgets(**{'channels': tselect})

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

def server_doc(doc):
    # TimeSignalPlot
    tsPlot = figure(title="Time Signals",plot_width=1000, plot_height=800,
                    x_axis_label="sample index", y_axis_label="p [Pa]")
    tsPlot.xaxis.axis_label_text_font_style = "normal"
    tsPlot.yaxis.axis_label_text_font_style = "normal"
    tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
    # FrequencySignalPlot
    f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    f_ticks_override = {20: '0.02', 50: '0.05', 100: '0.1', 200: '0.2', 
                        500: '0.5', 1000: '1', 2000: '2', 5000: '5', 10000: '10', 
                        20000: '20'}
    freqplot = figure(title="Auto Power Spectra", plot_width=1000, plot_height=800,
                      x_axis_type="log", x_axis_label="f in kHz", 
                      y_axis_label="|P(f)|^2 / dB")
    freqplot.xaxis.axis_label_text_font_style = "normal"
    freqplot.yaxis.axis_label_text_font_style = "normal"
    freqplot.xgrid.minor_grid_line_color = 'navy'
    freqplot.xgrid.minor_grid_line_alpha = 0.05
    freqplot.xaxis.ticker = f_ticks
    freqplot.xaxis.major_label_overrides = f_ticks_override
    freqplot.line('freqs', 'amp', source=freqdata)

    #create layout
    tsWidgetsCol = widgetbox(plotButton,tselect,*tsWidgets.values(),width=400)
    if sd_enabled: 
        allWidgetsLayout = row(tsWidgetsCol,pbWidgetCol)
    else:
        allWidgetsLayout = row(tsWidgetsCol)
    spWidgetsCol = widgetbox(plotButton,tselect,spWidgets['window'],
                             spWidgets['block_size'],
                             width=400)

    # Put in Tabs
    tsTab = Panel(child=row(tsPlot,allWidgetsLayout), title='Time Data')
    fdTab = Panel(child=row(freqplot,spWidgetsCol), title='Frequency Data')
    plotTab = Tabs(tabs=[tsTab, fdTab])

    def plot():
        if plotTab.active == 0: 
            tv.update()
        elif plotTab.active == 1:
            get_spectra()
    set_calc_button_callback(plot,plotButton)

    # add to doc
    doc.add_root(plotTab)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': server_doc}, num_procs=1)
server.start()

if __name__ == '__main__':
    print('Opening TimeSamples application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
