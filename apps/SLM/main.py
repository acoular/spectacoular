#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
app can be started with:
bokeh serve --show SLM 
"""
import threading
import sys
import acoular as ac
import spectacoular as sp
import numpy as np
import sounddevice as sd

from itertools import cycle

# bokeh imports
from bokeh.layouts import column, row
from bokeh.models import TabPanel as Panel, Tabs
from bokeh.models.widgets import Button, Toggle, Select, RadioGroup,\
    TableColumn, DataTable, Div, NumericInput
from bokeh.models import CDSView, CustomJSFilter, CustomJSTransform, HoverTool,\
     CustomJSHover, CustomJS, Spacer, WheelPanTool, Range1d, DataRange1d, Slider,\
         Slope, ColumnDataSource, NumberFormatter
from bokeh.transform import transform
from bokeh.plotting import figure, curdoc
from bokeh.server.server import Server
from bokeh.palettes import Category10_10



palette = cycle(Category10_10)

# spectacoular related definitions
trait_widget_mapper = {'device': NumericInput,
                       'sample_freq': NumericInput,
                       'num_channels' : NumericInput
                       }
trait_widget_args = {'device': {'disabled':False,'mode':'int'},
                     'sample_freq':  {'disabled':True,'mode':'float'},
                     'num_channels': {'disabled':True,'mode':'int'},
                     }
sp.add_bokeh_attr(ac.SoundDeviceSamplesGenerator,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'band': NumericInput}
trait_widget_args = {'band': {'disabled':False,'mode':'float'},
                     }
sp.add_bokeh_attr(ac.FiltOctave,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'weight': Select}
trait_widget_args = {'weight': {'disabled':False},
                     }
sp.add_bokeh_attr(ac.TimeExpAverage,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'weight': Select}
trait_widget_args = {'weight': {'disabled':False},
                     }
sp.add_bokeh_attr(ac.FiltFreqWeight,trait_widget_mapper,trait_widget_args)

trait_widget_mapper = {'elapsed': NumericInput}
trait_widget_args = {'elapsed': {'disabled':True,'mode':'float'},
                     }
sp.add_bokeh_attr(sp.TimeBandsConsumer,trait_widget_mapper,trait_widget_args)

all_iso_bands = np.array([1,1.25,1.6,2,2.5,3.15,4,5,6.3,8,10,12.5,16,20,31.5,40,50,63,80,100,
125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,
12500,16000,20000,25000])

def iso_bands(bands):
    return all_iso_bands[np.searchsorted(all_iso_bands,np.array(bands)/1.01)]

def bands_label(bands):
    return ["{:.0f}".format(x) for x in iso_bands(bands)]

# build processing chains
ts = ac.SoundDeviceSamplesGenerator(numsamples=-1,num_channels=1)

# slm chain
fw = ac.FiltFreqWeight(source=ts)
tp = ac.TimePower(source=fw)
te = ac.TimeExpAverage(source=tp, weight='F')
tca = ac.TimeCumAverage(source=tp)
tic = sp.TimeConsumer(source=te,down=1024,channels=[0,],
    num=8192,rollover=16*2*96)

# spectrum chain
fob = ac.OctaveFilterBank(source=ts, fraction='Third octave')
tbc = sp.TimeBandsConsumer(source=te,channels=[0,],num=8192, lfunc=bands_label)

# band slm chain
fob2 = ac.OctaveFilterBank(source=ts, fraction='Octave')
tp2 = ac.TimePower(source=fob2)
ta = sp.Average(source=tp2, num_per_average=512) # hack for *about* 50~ms average
tic3 = sp.TimeConsumer(source=ta,down=1,channels=list(range(ta.num_channels)),
    num=32,rollover=16*2*96)

# oscilloscope chain
tic2 = sp.TimeConsumer(source=ts,down=32,channels=[0,],
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
def exit_callback(arg):
    from time import sleep
    sleep(1)
    sys.exit()

exit_button.on_click(lambda : sys.exit())
exit_button.js_on_click(CustomJS( code='''
    setTimeout(function(){
        window.location.href = "about:blank";
    }, 500);
    '''))

# button to start / stop measurement
def toggle_handler(arg):
    if arg:
        device_select.disabled = True
        lin_or_exp.disabled = True
        exit_button.disabled = True
        active_consumer = (tic,tbc,tic2,tic3)[layout.active]
        print(active_consumer.num_channels)
        active_consumer.thread = threading.Thread(target=active_consumer.consume,args=[curdoc(),])
        active_consumer.thread.start()
        play_button.label = "⏹︎"
    if not arg:
        for consumer in (tic,tbc,tic2,tic3):
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
view = CDSView(filter=custom_filter)

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
levelhistory = figure(output_backend="webgl",width=800, height=600,
                    y_range=Range1d(start=10,end=90,bounds='auto',min_interval=40))
levelhistory.xaxis.axis_label = 'time / s'
levelhistory.yaxis.axis_label = 'sound pressure level / dB'
levelhistory.text(x='t', y=60, text=transform(ch,tofixed), 
            text_font_size={'value': '32px'}, text_align='right',
            source=tic.ds, view = view, color='orange')
levelhistory.line(x='t', y=transform(ch,todB), source=tic.ds, color='orange')
levelhistory.add_tools(WheelPanTool(dimension="height"))
levelhistory.x_range = DataRange1d(follow='end', follow_interval=10, range_padding=0)

# plot for band level time history
levelhistory2 = figure(output_backend='webgl', tools='pan,wheel_zoom,xbox_select,reset,xbox_zoom',
                    active_drag="xbox_select",width=800, height=600,
                    y_range=Range1d(start=10,end=90,bounds='auto',min_interval=40))
levelhistory2.xaxis.axis_label = 'time / s'
levelhistory2.yaxis.axis_label = 'sound pressure level / dB'
#litems = []
slopes = {}
for ch,color,band in zip(tic3.ch_names(), palette, tbc.lfunc(fob2.bands)):
    levelhistory2.circle(x='t', y=transform(ch,todB), source=tic3.ds, color=None, \
        selection_color=color)
    levelhistory2.line(x='t', y=transform(ch,todB), source=tic3.ds, color=color, \
        legend_label=band)
    slopes[ch] = Slope(gradient=0, y_intercept=0,
                line_color=color, line_dash='dashed', line_width=2)
    levelhistory2.add_layout(slopes[ch])  
levelhistory2.x_range = DataRange1d(follow='end', follow_interval=10, range_padding=0)

# bar graph plot for 3rd octave average
barplot = figure(x_range=tbc.lfunc(fob.bands), y_range=(0,80),
                 width=800, height=600, output_backend="webgl")
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
scope = figure(output_backend="webgl",width=800, height=600)
scope.xaxis.axis_label = 'time / s'
scope.yaxis.axis_label = 'sound pressure / Pa'
scope.line(x='t', y=ch, source=tic2.ds, color='orange')
scope.add_tools(WheelPanTool(dimension="height"))
scope.x_range = DataRange1d(follow='end', follow_interval=10, range_padding=0)

# xzoom for scope
xzoom_widget = Slider(start=1, end=10, step=1, value=10, title='time range')
xzoom_widget.js_link('value', scope.x_range, 'follow_interval')

# xzoom for levelhistory
xzoom_widget2 = Slider(start=5, end=60, step=5, value=10, title='time range')
xzoom_widget2.js_link('value', levelhistory.x_range, 'follow_interval')

T60ds = ColumnDataSource(data={'f':[],'T60a':[],'T60b':[]}) 

# select callback for reverberation time
def selection_change(attrname, old, new):
    t = tic3.ds.data['t'][new]
    bands = []
    T60a = []
    T60b = []
    # iterate over bands
    for ch,color,band in zip(tic3.ch_names(), palette, tbc.lfunc(fob2.bands)):
        levels = ac.L_p(tic3.ds.data[ch][new])
        # dynamic range should be at least 20 dB
        if len(new)>2 and levels.ptp() > 20:
            levels1 = levels[levels>levels.min()+10]
            # do not consider the lowest 10 dB
            t1 = t[levels>levels.min()+10]
            if len(levels1)>2:
                # fit line for interrupted noise
                gradient, y_intercept = np.polyfit(t1,levels1,1)
                # backward integration (impulse response)
                levels2 = (tic3.ds.data[ch][new][np.argsort(t)])
                # fit on backward integrated imp. response squared
                gradient2, _ = np.polyfit(t,10*np.log10(levels2[::-1].cumsum()[::-1]),1)
                # reverberation time
                bands.append(band)
                T60a.append(-60/gradient)
                T60b.append(-60/gradient2)
        else:
            gradient, y_intercept = 0,0
        slopes[ch].gradient=gradient
        slopes[ch].y_intercept=y_intercept     
    T60ds.data = {'f':bands,'T60a':T60a,'T60b':T60b}

tic3.ds.selected.on_change('indices', selection_change)

# data table widget
Tcolumns = [
    TableColumn(field="f", title="band / Hz", width=100),
    TableColumn(field="T60a", title="T60 noise / s", formatter=NumberFormatter(format="0.00"), width=100),
    TableColumn(field="T60b", title="T60 impulse / s", formatter=NumberFormatter(format="0.00"), width=100)
]

data_table = DataTable(source=T60ds, columns=Tcolumns, width=300,#autosize_mode="force_fit", 
    sizing_mode="stretch_both", width_policy="min",index_position=None)

instruction_T60 = Div(text='''To estimate reverberation time T, make recording and use 
the select tool to carefully select the decay part of the time history. Make sure not to select 
parts of the time history before and after decay. T is then automatically computed for both the 
case of interrupted noise and impulse excitation.
''', width=400, height=100)

# data save buttons
save_spectrum = Button(label="Download data", button_type="warning")
save_spectrum.js_on_click(CustomJS(args={'source' :tbc.ds},
        code=
        '''
        var length = source.get_length();
        var data = source.data;
        var out = "frequency / Hz, mean square sound pressure / Pa^2\\n";
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
        var out = "time / s, mean square sound pressure / Pa^2\\n";
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

save_reverberation_time = Button(label="Download data", button_type="warning")
save_reverberation_time.js_on_click(CustomJS(args={'source' :T60ds},
        code=
        '''
        var length = source.get_length();
        var data = source.data;
        var out = "band / Hz, T /s (interrupted noise), T /s (impulse excitation)\\n";
        for (var i = 0; i < length; i++) {
            out += data['f'][i] + "," + data['T60a'][i] + "," + data['T60b'][i] + "\\n";
        }
        var file = new Blob([out], {type: 'text/plain'});
        var elem = window.document.createElement('a');
        elem.href = window.URL.createObjectURL(file);
        elem.download = 'reverberation_time.txt';
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

average_controls = column(lin_or_exp,time_weight_widget)

# weight control
freq_weight_widget = fw.get_widgets()['weight']

# widgets on every tab
every = column( row(play_button,exit_button),device_select)

# tabs
spectrum_tab = Panel(child=row(
                        column(every,save_spectrum,
                        Spacer(height_policy='max'),average_controls,elapsed_widget),
                        barplot
                        ),
                    title="Third octave band average")

level_tab = Panel(child=row(
                        column(every,save_levelhistory,
                        Spacer(height_policy='max'),freq_weight_widget,average_controls,xzoom_widget2),
                        levelhistory
                        ),
                    title="Sound level meter")

band_level_tab = Panel(child=row(
                        column(every,
                        instruction_T60,
                        data_table,
                        save_reverberation_time,
                        #xzoom_widget2,
                        height=600),
                        levelhistory2
                        ),
                    title="Band sound level meter")

scope_tab = Panel(child=row(
                        column(every, 
                        Spacer(height_policy='max'),xzoom_widget),
                        scope
                        ),
                    title="Oscilloscope")

# overall layout 
layout = Tabs(tabs=[level_tab,spectrum_tab,scope_tab,band_level_tab],active=0)

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
