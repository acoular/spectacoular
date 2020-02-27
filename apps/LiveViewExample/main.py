# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to process data 
"""

import os
from os import path
from bokeh.io import curdoc
from bokeh.layouts import column, row, widgetbox
from bokeh.models.widgets import Panel,Tabs,Div,Button, Toggle, Select
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import TimeSamplesPhantom, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerPresenter,TimeSamplesPresenter,\
MicGeomPresenter, TimeInOutPresenter,TimeAverage
import acoular
from acoular import TimePower, L_p
import threading

doc = curdoc()
AMPFIG_ARGS = {'y_range': (0,140),'plot_width':500, 'plot_height':500} 
MGEOMFIG_ARGS = {'plot_width':500,  'plot_height':500}

# define selectable microphone geometries
micgeofiles = path.join( path.split(acoular.__file__)[0],'xml')
options = [path.join(micgeofiles,name) for name in os.listdir(micgeofiles)]
options.append('')

# build processing chain
mg = MicGeom(from_file=options[15])
ts = TimeSamplesPhantom(name='example_data.h5',time_delay=.3)
tp = TimePower(source=ts)
ta = TimeAverage(source=tp,naverage=256)
tio = TimeInOutPresenter(source=ta)

micGeomSelect = Select(title='Geometry',value=options[15],options=options) 
mgWidgets = mg.get_widgets()
mg.set_widgets(**{'from_file':micGeomSelect}) # set from file attribute with select widget
mgWidgets['from_file'] = micGeomSelect

# get widgets to control settings
tsWidgets = list(ts.get_widgets().values()) + list(ta.get_widgets().values())

# ColumnDataSource for data processing
cdsource = ColumnDataSource(data={'ch':[],'top':[],'x':[],'y':[],'size':[]})

def get_data():
    ct = threading.currentThread()
    gen = tio.result(1)
    while getattr(ct, "do_run", True):
        next(gen)

def update():
    numchannels = tio.numchannels
    if tio.data.data['data'].shape[0] > 0:
        newData = {'ch':list(range(0,numchannels)),
                   'top':L_p(tio.data.data['data'][0]),
                   'x' : mg.mpos[0,:],
                   'y' : mg.mpos[1,:],
                   'size' : L_p(tio.data.data['data'][0])/5}  
        cdsource.stream(newData,rollover=numchannels)

bttn = Toggle(label="start") 
def toggle_handler(arg):
    global periodic_plot_callback,thread # need to be global
    if arg:
        thread = threading.Thread(target=get_data)
        thread.start()
        periodic_plot_callback = doc.add_periodic_callback(update,80)
    if not arg:
        thread.do_run = False
        doc.remove_periodic_callback(periodic_plot_callback)
bttn.on_click(toggle_handler) 

# amp bar
ampPlot = figure(title='SPL/dB',tools="",**AMPFIG_ARGS)
ampPlot.toolbar.logo = None
ampPlot.vbar(
    x='ch', width=0.5, bottom=0,top='top', source=cdsource)
# ampPlot.xgrid.visible = False
# ampPlot.toolbar.logo=None

#MicGeomPlot
mgPlot = figure(title='Microphone Geometry',**MGEOMFIG_ARGS)
mgPlot.toolbar.logo = None
mgPlot.circle_cross(x='x',y='y',size='size',fill_alpha=0.2,source=cdsource)
                                  
### CREATE LAYOUT ### 
# columns    
plotCol = column(ampPlot,mgPlot)
tsWidgetsCol = widgetbox(bttn,*tsWidgets,width=250)
mgWidgetCol = widgetbox(*mgWidgets.values(),width=250)

# make Document
doc.add_root(row(plotCol,tsWidgetsCol,mgWidgetCol))

