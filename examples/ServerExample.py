#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example that demonstrates different beamforming algorithms
"""

from os import path
import acoular

from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs,Div, Select, Toggle
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerFunctional,BeamformerCapon,\
BeamformerEig,BeamformerMusic,BeamformerDamas,BeamformerDamasPlus,BeamformerOrth,\
BeamformerCleansc, BeamformerClean, BeamformerPresenter,TimeSamplesPresenter,\
BeamformerCMF,BeamformerGIB,Environment,Calib,config,PointSource,\
MicGeomPresenter, ColorMapperController, SingleChannelController

# build processing chain
micgeofile = path.join( path.split(acoular.__file__)[0],'xml','array_56.xml')
tdfile = 'example_data.h5'
calibfile = 'example_calib.xml'
ts = MaskedTimeSamples(name=tdfile)
cal = Calib(from_file=calibfile)
#ts = MaskedTimeSamples()
#cal = Calib()
ts.start = 0 # first sample, default
ts.stop = 16000 # last valid sample = 15999
invalid = [1,7] # list of invalid channels (unwanted microphones etc.)
ts.invalid_channels = invalid 
ts.calib = cal
#mg = MicGeom()
mg = MicGeom(from_file=micgeofile,invalid_channels = invalid)
ps = PowerSpectra(time_data=ts)
rg = RectGrid(x_min=-0.6, x_max=-0.0, y_min=-0.3, y_max=0.3, z=0.68,increment=0.05)
env = Environment(c = 346.04)
st = SteeringVector( grid = rg, mics=mg, env=env )    

# Beamforming Algorithms
bb = BeamformerBase( freq_data=ps, steer=st )  
bf = BeamformerFunctional( freq_data=ps, steer=st, gamma=4)
bc = BeamformerCapon( freq_data=ps, steer=st )  
be = BeamformerEig( freq_data=ps, steer=st, n=54)
bm = BeamformerMusic( freq_data=ps, steer=st, n=6)   
bd = BeamformerDamas(beamformer=bb, n_iter=100)
bdp = BeamformerDamasPlus(beamformer=bb, n_iter=100)
bo = BeamformerOrth(beamformer=be, eva_list=list(range(38,54)))
bs = BeamformerCleansc(freq_data=ps, steer=st, r_diag=True)
bl = BeamformerClean(beamformer=bb, n_iter=100)
bcmf = BeamformerCMF(freq_data=ps, steer=st, method='LassoLarsBIC')
bgib = BeamformerGIB(freq_data=ps, steer=st, method= 'LassoLars', n=10)

beamformer_dict = {
                    'Conventional Beamforming': bb,
                   'Functional Beamforming': bf,
                   'Capon Beamforming': bc,
                   'Eigenvalue Beamforming': be,
                   'Music Beamforming': bm,
                   'Damas Deconvolution': bd,
                   'DamasPlus Deconvolution' : bdp,
                   'Orthogonal Beamforming' : bo,
                   'CleanSC Deconvolution' : bs,
                   'Clean Deconvolution' : bl,
                   'CMF' : bcmf,
                   'GIB' : bgib
                   }

# use additional classes for data evaluation/view
mv = MicGeomPresenter(source=mg)
bv = BeamformerPresenter(source=bb,grid=rg)
cm = ColorMapperController()

# get widgets to control settings
tsWidgets = ts.get_widgets()
mgWidgets = mg.get_widgets()
envWidgets = env.get_widgets()
calWidgets = cal.get_widgets()
psWidgets = ps.get_widgets()
rgWidgets = rg.get_widgets()
stWidgets = st.get_widgets()
bbWidgets = bb.get_widgets()
bvWidgets = bv.get_widgets()
mvWidgets = mv.get_widgets()
cmWidgets = cm.get_widgets()
confWidgets = config.get_widgets()

def server_doc(doc):
    
    beamformerSelector = Select(title="Select Beamforming Method:",
                            options=list(beamformer_dict.keys()),
                            value=list(beamformer_dict.keys())[0])

    calcButton = Toggle(label="Calculate",button_type="success")
    def calc(arg):
        if arg:
            calcButton.label = 'Calculating ...'
            bv.update()
            calcButton.active = False
            calcButton.label = 'Calculate'
        if not arg:
            calcButton.label = 'Calculate'
    calcButton.on_click(calc)
            
    ### CREATE LAYOUT ### 

    #MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', tools = 'hover,pan,wheel_zoom,reset')
    mgPlot.circle(x='x',y='y',source=mv.cdsource)

    # beamformerPlot
    bfPlot = figure(title='Beamforming Result', tools = 'pan,wheel_zoom,reset')
    bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',
                 color_mapper=cm.colorMapper,source=bv.cdsource)
    bfPlot.add_layout(cm.colorBar, 'right')

    # Plot Tabs
    mgPlotTab = Panel(child=row(mgPlot),title='Microphone Geometry Plot')
    bfPlotTab = Panel(child=row(bfPlot),title='Source Plot')
    plotTabs = Tabs(tabs=[mgPlotTab,bfPlotTab],width=600)

    # Property Tabs
    selectedBfWidgets = column(*bbWidgets)  
    tsTab = Panel(child=column(*tsWidgets),title='Time Data')
    mgTab = Panel(child=column(*mgWidgets),title='MicGeometry')
    calTab = Panel(child=column(*calWidgets),title='Calibration')
    envTab = Panel(child=column(*envWidgets),title='Environment')
    gridTab = Panel(child=column(*rgWidgets),title='Grid')
    stTab = Panel(child=column(*stWidgets),title='Steering')
    psTab = Panel(child=column(*psWidgets),title='FFT')
    bfTab = Panel(child=column(beamformerSelector,selectedBfWidgets),
                  title='Beamforming')
    globalTab = Panel(child=column(*confWidgets),title='Global Settings')

    propertyTabs = Tabs(tabs=[tsTab,mgTab,calTab,envTab,gridTab,stTab,
                              psTab,bfTab,globalTab],width=1000)
    
    calcColumn = column(calcButton,*bvWidgets,*cmWidgets)
    
    def beamformer_handler(attr,old,new):
        bv.source = beamformer_dict[new]
        selectedBfWidgets.children = beamformer_dict[new].get_widgets()
    beamformerSelector.on_change('value',beamformer_handler)
    
    # make Document
    mainlayout = row(plotTabs,calcColumn,propertyTabs)
    doc.add_root(mainlayout)


server = Server({'/': server_doc}, num_procs=1)
server.start()


if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

