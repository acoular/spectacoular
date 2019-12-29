#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:45:33 2019
@author: kujawski
"""
import os
from os import path
import acoular
from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs,Div, Select
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import MicGeom,  MicGeomPresenter

# build processing chain
mg = MicGeom()
mg.trait_widget_mapper['from_file'] = Select # Replace TextInput with Select Widget
mv = MicGeomPresenter(source=mg)

# get widgets to control settings
mgWidgets = mg.get_widgets()
mvWidgets = mv.get_widgets()

# add options to Select File Widget
micgeofiles = path.join( path.split(acoular.__file__)[0],'xml')
options = [path.join(micgeofiles,name) for name in os.listdir(micgeofiles)]
options.append('')
mgWidgets[0].options = options

def server_doc(doc):

    #MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', tools = 'pan,wheel_zoom,reset')
    mgPlot.circle(x='x',y='y',source=mv.cdsource)

    ### CREATE LAYOUT ### 
    
    # columns    
    mgWidgetsCol = column(Div(text="MicGeom:"),*mgWidgets)

    # Tabs
    mgTab = Panel(child=row(mgPlot,mgWidgetsCol,column(*mvWidgets)),title='Microphone Geometry')
    ControlTabs = Tabs(tabs=[mgTab],width=850)

    # make Document
    doc.add_root(ControlTabs)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': server_doc}, num_procs=1,port=5101)
server.start()


if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

