# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to process data 
"""

from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs,Div,Button, Toggle
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import TimeSamplesPhantom, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerPresenter,TimeSamplesPresenter,\
MicGeomPresenter, TimeAveragePresenter
from acoular import TimeAverage, TimePower
import threading

# build processing chain
ts = TimeSamplesPhantom(time_delay=.3)
tp = TimePower(source=ts)
ta = TimeAverage(source=tp,naverage=256)
tpp = TimeAveragePresenter(source=ta)

# get widgets to control settings
tsWidgets = ts.get_widgets()

def get_data():
    ct = threading.currentThread()
    i = 0
    gen = tpp.result(1)
    while getattr(ct, "do_run", True):
        print("get block: ",i)
        next(gen)

def server_doc(doc):
    bttn = Toggle(label="start") 
    def toggle_handler(arg):
        global periodic_plot_callback,thread # need to be global
        if arg:
            thread = threading.Thread(target=get_data)
            thread.start()
            periodic_plot_callback = doc.add_periodic_callback(tpp.update,300)
        if not arg:
            thread.do_run = False
            doc.remove_periodic_callback(periodic_plot_callback)
    bttn.on_click(toggle_handler) 

    ampPlot = figure(title="Amplitudes")
    ampPlot.vbar(x='x', width=0.5, bottom=0,top='y', source=tpp.cdsource)

    ### CREATE LAYOUT ### 
    # columns    
    tsWidgetsCol = column(Div(text="TimeSamples:"),row(bttn,
            column(*tsWidgets.values())))

    # Tabs
    tsTab = Panel(child=row(ampPlot,tsWidgetsCol),title='Time Signal')
    ControlTabs = Tabs(tabs=[tsTab],width=850)

    # make Document
    doc.add_root(ControlTabs)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': server_doc}, num_procs=1)
server.start()

if __name__ == '__main__':
    print('Opening LiveView application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

