# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example how to plot TimeData
"""

from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs,Div
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerPresenter,TimeSamplesPresenter,\
MicGeomPresenter, SingleChannelController,MultiChannelController,\
TimeSignalPlayback

# build processing chain
ts = MaskedTimeSamples()
#mc = SingleChannelController()
mc = MultiChannelController()
tv = TimeSamplesPresenter(source=ts,controller=mc)
playback = TimeSignalPlayback(source=ts,controller=mc)

# get widgets to control settings
tsWidgets = ts.get_widgets()
tvWidgets = tv.get_widgets()
scWidgets = mc.get_widgets()
plWidgets = playback.get_widgets()

def server_doc(doc):

    # TimeSignalPlot
    tsPlot = figure(title="Time Signals")
    tsPlot.multi_line(xs='xs', ys='ys',color='color',source=tv.cdsource)

    ### CREATE LAYOUT ### 
    
    # columns    
    tsWidgetsCol = column(Div(text="TimeSamples:"),row(
            column(*tsWidgets.values()),column(
                *tvWidgets.values(),*scWidgets.values(),*plWidgets.values())))

    # Tabs
    tsTab = Panel(child=row(tsPlot,tsWidgetsCol),title='Time Signal')
    ControlTabs = Tabs(tabs=[tsTab],width=850)

    # make Document
    doc.add_root(ControlTabs)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': server_doc}, num_procs=1)
server.start()


if __name__ == '__main__':
    print('Opening TimeSamples application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

