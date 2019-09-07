#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:45:33 2019

@author: kujawski
"""

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider
from bokeh.models.widgets import Panel,Tabs
from bokeh.plotting import figure
from bokeh.server.server import Server
#from bokeh.themes import Theme

import numpy as np
from spectacoular import TimeSamples, MicGeom


def modify_doc(doc):
    
    # instanciate Acoular classes
    ts = TimeSamples()
    mg = MicGeom()

    # create widgets
    tsWidgets = column(ts.create_widgets_from_traits())
    mgWidgets = column(mg.create_widgets_from_traits())
    
    # TimeSignalPlot
    tsPlot = figure(title="Time Signals")
    tsPlot.line(x='sample', y='values',source=ts.cdsource)

    #MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', tools = 'pan,wheel_zoom,reset')
    mgPlot.toolbar.logo=None
    mgPlot.circle(x='x',y='y',source=mg.cdsource)

    # make Panels
    tsTab = Panel(child=row(tsPlot,tsWidgets),title='Time Signal')
    mgTab = Panel(child=row(mgPlot,mgWidgets),title='Microphone Geometry')
    ControlTabs = Tabs(tabs=[tsTab,mgTab],width=850)

    # make Document
    doc.add_root(ControlTabs)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': modify_doc}, num_procs=1)
server.start()

if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

#    
    
