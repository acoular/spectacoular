# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
app can be started with:
bokeh serve --show SLM 
"""
import threading
import sys

from numpy import array, searchsorted

from bokeh.layouts import column, row
from bokeh.models.widgets import Panel, Tabs, Button, Toggle, Select, TextInput, RadioGroup
from bokeh.models import CDSView, CustomJSFilter, CustomJSTransform, HoverTool,\
    CustomJSHover, CustomJS, Spacer, WheelPanTool, Range1d, DataRange1d, Slider
from bokeh.transform import transform
from bokeh.plotting import figure, curdoc
from bokeh.server.server import Server
from spectacoular import TimeAverage, add_bokeh_attr, TimeBandsConsumer, TimeConsumer
from acoular import TimePower, FiltOctave, TimeExpAverage, FiltFreqWeight,\
    TimeCumAverage, OctaveFilterBank, SoundDeviceSamplesGenerator

import sounddevice as sd


# spectacoular related definitions
trait_widget_mapper = {'device': TextInput,
                       'sample_freq': TextInput,
                       'numchannels' : TextInput
                       }
trait_widget_args = {'device': {'disabled':False},
                     'sample_freq':  {'disabled':True},
                     'numchannels': {'disabled':True},
                     }
add_bokeh_attr(SoundDeviceSamplesGenerator,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'band': TextInput}
trait_widget_args = {'band': {'disabled':False},
                     }
add_bokeh_attr(FiltOctave,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'weight': Select}
trait_widget_args = {'weight': {'disabled':False},
                     }
add_bokeh_attr(TimeExpAverage,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'weight': Select}
trait_widget_args = {'weight': {'disabled':False},
                     }
add_bokeh_attr(FiltFreqWeight,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'elapsed': TextInput}
trait_widget_args = {'elapsed': {'disabled':True},
                     }
add_bokeh_attr(TimeBandsConsumer,trait_widget_mapper,trait_widget_args)

all_iso_bands = array([1,1.25,1.6,2,2.5,3.15,4,5,6.3,8,10,12.5,16,20,31.5,40,50,63,80,100,
125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,
12500,16000,20000,25000])

def iso_bands(bands):
    return all_iso_bands[searchsorted(all_iso_bands,array(bands)/1.01)]

def bands_label(bands):
    return ["{:.0f}".format(x) for x in iso_bands(bands)]

# build processing chains
ts = SoundDeviceSamplesGenerator(numsamples=-1,numchannels=1)

# slm chain
fw = FiltFreqWeight(source=ts)
tp = TimePower(source=fw)
te = TimeExpAverage(source=tp, weight='F')
tca = TimeCumAverage(source=tp)
tic = TimeConsumer(source=te,down=1024,channels=[0,],
    num=8192,rollover=2*96)

# spectrum chain
fob = OctaveFilterBank(source=ts, fraction='Third octave')
tbc = TimeBandsConsumer(source=te,channels=[0,],num=8192, lfunc=bands_label)

# oscilloscope chain
tic2 = TimeConsumer(source=ts,down=32,channels=[0,],
    num=8192,rollover=32*4*96)


# set up devices choice
devices = {}
for i,dev in enumerate(sd.query_devices()):
    if dev['max_input_channels']>0:
        devices["{}".format(i)] = "{name} {max_input_channels}".format(**dev)
device_select = Select(title="Choose input device:", 
    value="{}".format(list(devices.keys())[0]), options=list(devices.items()))
ts.device=int(device_select.value)
ts.set_widgets(device=device_select)

# button to stop the server
exit_button = Button(label="Exit", button_type="danger",sizing_mode="stretch_width",width=100)
exit_button.on_click(lambda : sys.exit())

# button to start / stop measurement
def toggle_handler(arg):
    if arg:
        device_select.disabled = True
        lin_or_exp.disabled = True
        exit_button.disabled = True
        active_consumer = (tic,tbc,tic2)[layout.active]
        active_consumer.thread = threading.Thread(target=active_consumer.consume,args=[curdoc(),])
        active_consumer.thread.start()
        play_button.label = "⏹︎"
    if not arg:
        for consumer in (tic,tbc,tic2):
            if consumer.thread:
                consumer.thread.do_run = False
        device_select.disabled = False
        lin_or_exp.disabled = False
        exit_button.disabled = False
        play_button.label = "▶"

play_button = Toggle(label="▶",button_type="success",sizing_mode="stretch_width",width=100)
play_button.on_click(toggle_handler) 

# JS routines
custom_filter = CustomJSFilter(code=
    '''
    const size = source.get_length();
    var indices = new Array(size);
    indices.fill(false,0,size)
    indices[size-1]=true
    return indices;
    ''')
view = CDSView(source=tic.ds, filters=[custom_filter])

tofixed = CustomJSTransform(v_func=
    '''
    var out = new Array(xs.length);
    for (let i = 0; i < xs.length; i++) {
        out[i] = Number.parseFloat(10*Math.log10(xs[i]/4e-10)).toFixed(1) + " dB";
    }
    return out
    ''')

custom_hover = CustomJSHover(code=
    '''
    return Number.parseFloat(10*Math.log10(value/4e-10)).toFixed(1) + " dB"
    '''
)

todB = CustomJSTransform(v_func=
    '''
    var out = new Array(xs.length);
    for (let i = 0; i < xs.length; i++) {
        out[i] = 10*Math.log10(xs[i]/4e-10);
    }
    return out
    '''
)

# plot for level time history
ch = list(tic.ch_names())[0]
levelhistory = figure(output_backend="webgl",plot_width=800, plot_height=600,
                    y_range=Range1d(start=10,end=90,bounds='auto',min_interval=40))
levelhistory.xaxis.axis_label = 'time / s'
levelhistory.yaxis.axis_label = 'sound pressure level / dB'
levelhistory.text(x='t', y=60, text=transform(ch,tofixed), 
            text_font_size={'value': '32px'}, text_align='right',
            source=tic.ds, view = view, color='orange')
levelhistory.line(x='t', y=transform(ch,todB), source=tic.ds, color='orange')
levelhistory.add_tools(WheelPanTool(dimension="height"))


# bar graph plot for 3rd octave average
barplot = figure(x_range=tbc.lfunc(fob.bands), y_range=(0,80),
                 plot_width=800, plot_height=600, output_backend="webgl")
barplot.xaxis.axis_label = 'band center frequency / Hz'
barplot.yaxis.axis_label = 'sound pressure level / dB'
barplot.add_tools(HoverTool(tooltips = [("val","@timedata0{custom}")], 
                            formatters={"@timedata0":custom_hover}))
barplot.add_tools(WheelPanTool(dimension="height"))
barplot.toolbar.logo=None
ch = 'timedata0'
barplot.vbar(x='t', top=transform(ch,todB), source=tbc.ds, 
    fill_alpha=0.5, width=0.5, name=ch, color='orange')

# plot for scope
ch = list(tic2.ch_names())[0]
scope = figure(output_backend="webgl",plot_width=800, plot_height=600)
scope.xaxis.axis_label = 'time / s'
scope.yaxis.axis_label = 'sound pressure / Pa'
scope.line(x='t', y=ch, source=tic2.ds, color='orange')
scope.add_tools(WheelPanTool(dimension="height"))
scope.x_range = DataRange1d(follow='end', follow_interval=10, range_padding=0)

# xzoom for scope
xzoom_widget = Slider(start=1, end=10, step=1, value=10, title='time range')
xzoom_widget.js_link('value', scope.x_range, 'follow_interval')

# data save buttons
save_spectrum = Button(label="Download data", button_type="warning")
save_spectrum.js_on_click(CustomJS(args={'source' :tbc.ds},
        code=
        '''
        var length = source.get_length();
        var data = source.data;
        var out = "frequency [Hz], mean square sound pressure [Pa^2]\\n";
        for (var i = 0; i < length; i++) {
            out += data['t'][i] + "," + data['timedata0'][i] + "\\n";
        }
        var file = new Blob([out], {type: 'text/plain'});
        var elem = window.document.createElement('a');
        elem.href = window.URL.createObjectURL(file);
        elem.download = 'spectrum.txt';
        document.body.appendChild(elem);
        elem.click();
        document.body.removeChild(elem);
        '''
        )
    )

save_levelhistory = Button(label="Download data", button_type="warning")
save_levelhistory.js_on_click(CustomJS(args={'source' :tic.ds},
        code=
        '''
        var length = source.get_length();
        var data = source.data;
        var out = "time [s], mean square sound pressure [Pa^2]\\n";
        for (var i = 0; i < length; i++) {
            out += data['t'][i] + "," + data['timedata0'][i] + "\\n";
        }
        var file = new Blob([out], {type: 'text/plain'});
        var elem = window.document.createElement('a');
        elem.href = window.URL.createObjectURL(file);
        elem.download = 'timehistory.txt';
        document.body.appendChild(elem);
        elem.click();
        document.body.removeChild(elem);
        '''
        )
    )

# average controls
def le_callback(a,old,new):
    if new==0:
        time_weight_widget.disabled = False
        tbc.source = te
        tic.source = te
    elif new==1:
        time_weight_widget.disabled = True
        tbc.source = tca
        tic.source = tca


lin_or_exp = RadioGroup(labels=['exponential averaging','linear averaging'],active=0)
lin_or_exp.on_change('active',le_callback)

time_weight_widget = te.get_widgets()['weight']
time_weight_widget.title = 'exponential weighting scheme'

elapsed_widget = tbc.get_widgets()['elapsed']
elapsed_widget.title = 'elapsed time / s'

average_controls = column(lin_or_exp,time_weight_widget,elapsed_widget)

# weight control
freq_weight_widget = fw.get_widgets()['weight']

# widgets on every tab
every = column( row(play_button,exit_button),device_select)

# tabs
spectrum_tab = Panel(child=row(
                        column(every,save_spectrum,
                        Spacer(height_policy='max'),average_controls),
                        barplot
                        ),
                    title="Third octave band average")

level_tab = Panel(child=row(
                        column(every,save_levelhistory,
                        Spacer(height_policy='max'),freq_weight_widget,average_controls),
                        levelhistory
                        ),
                    title="Sound level meter")

scope_tab = Panel(child=row(
                        column(every,
                        Spacer(height_policy='max'),xzoom_widget),
                        scope
                        ),
                    title="Oscilloscope")

# overall layout 
layout = Tabs(tabs=[level_tab,spectrum_tab,scope_tab],active=0)

# rearrange processing chain
def layout_callback(a,old,new):
    play_button.active = False #stop if tab is switched
    if new==0: # level tab
        tp.source = fw
    elif new==1: # spectrum tab
        tp.source = fob  
    elif new==2: # scope tab
        pass


layout.on_change('active',layout_callback)

def server_doc(doc):
    doc.add_root(row(Spacer(width_policy='max'),layout,Spacer(width_policy='max')))
    doc.title = "SLM / Sound Analyzer"

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)
