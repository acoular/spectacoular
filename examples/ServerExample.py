#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:45:33 2019
@author: kujawski
"""

from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs,Div
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerPresenter,TimeSamplesPresenter,\
MicGeomPresenter, ColorMapperController


# build processing chain
ts = MaskedTimeSamples(name='/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/example_data.h5')
mg = MicGeom(from_file='/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/acoular/xml/array_56.xml')
ps = PowerSpectra(time_data=ts)
rg = RectGrid(x_min=-0.6, x_max=-0.0, y_min=-0.3, y_max=0.3, z=0.68,increment=0.05)
st = SteeringVector( grid = rg, mics=mg )    
bb = BeamformerBase( freq_data=ps, steer=st )  


def server_doc(doc):

    # use additional classes for data evaluation/view
    mv = MicGeomPresenter(source=mg)
    bv = BeamformerPresenter(source=bb)
    tv = TimeSamplesPresenter(source=ts)
    cm = ColorMapperController()

    # get widgets to control settings
    tsWidgets = ts.get_widgets()
    mgWidgets = mg.get_widgets()
    psWidgets = ps.get_widgets()
    rgWidgets = rg.get_widgets()
    stWidgets = st.get_widgets()
    bbWidgets = bb.get_widgets()
    bvWidgets = bv.get_widgets()
    tvWidgets = tv.get_widgets()
    mvWidgets = mv.get_widgets()
    cmWidgets = cm.get_widgets()

#    print(bv.cdsource.data.items())

    # TimeSignalPlot
    tsPlot = figure(title="Time Signals")
    tsPlot.multi_line(xs='xs', ys='ys',color='color',source=tv.cdsource)

    #MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', tools = 'pan,wheel_zoom,reset')
    mgPlot.circle(x='x',y='y',source=mv.cdsource)

    # beamformerPlot
    bfPlot = figure(title='Beamforming Result', tools = 'pan,wheel_zoom,reset')
    bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',
                 color_mapper=cm.colorMapper,source=bv.cdsource)
    bfPlot.add_layout(cm.colorBar, 'right')

    ### CREATE LAYOUT ### 
    
    # columns    
    tsWidgetsCol = column(Div(text="TimeSamples:"),*tvWidgets,*tsWidgets)
    mgWidgetsCol = column(Div(text="MicGeom:"),*mgWidgets)
    psWidgetsCol = column(Div(text="PowerSpectra:"),*psWidgets)
    rgWidgetsCol = column(Div(text="Grid:"),*rgWidgets)
    bfWidgetsCol = column(Div(text="SteeringVector:"),*stWidgets,
                          Div(text="BeamformerBase:"),*bbWidgets,*bvWidgets,*cmWidgets)

    # Tabs
    tsTab = Panel(child=row(tsPlot,tsWidgetsCol,psWidgetsCol),title='Time Signal')
    mgTab = Panel(child=row(mgPlot,mgWidgetsCol,column(*mvWidgets)),title='Microphone Geometry')
    bfTab = Panel(child=row(bfPlot,rgWidgetsCol,bfWidgetsCol),title='Beamforming')
    ControlTabs = Tabs(tabs=[tsTab,mgTab,bfTab],width=850)

    # make Document
    doc.add_root(ControlTabs)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': server_doc}, num_procs=1)
server.start()


if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

