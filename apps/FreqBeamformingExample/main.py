# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example that demonstrates different beamforming algorithms
"""
from os import path
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import LogColorMapper,ColorBar
from bokeh.models.widgets import Panel,Tabs,Select, Toggle, RangeSlider
from bokeh.plotting import figure
from bokeh.palettes import viridis, plasma, inferno, magma
from bokeh.server.server import Server
import acoular
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerFunctional,BeamformerCapon,\
BeamformerEig,BeamformerMusic,BeamformerDamas,BeamformerDamasPlus,BeamformerOrth,\
BeamformerCleansc, BeamformerClean, BeamformerPresenter,\
BeamformerCMF,BeamformerGIB,Environment,Calib

doc = curdoc() 
# build processing chain
micgeofile = path.join( path.split(acoular.__file__)[0],'xml','array_56.xml')
tdfile = 'example_data.h5'
calibfile = 'example_calib.xml'
ts = MaskedTimeSamples(name=tdfile)
cal = Calib(from_file=calibfile)
ts.start = 0 # first sample, default
ts.stop = 16000 # last valid sample = 15999
invalid = [1,7] # list of invalid channels (unwanted microphones etc.)
ts.invalid_channels = invalid 
ts.calib = cal
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

# create Select Button to select Beamforming Algorithm
beamformerSelector = Select(title="Select Beamforming Method:",
                        options=list(beamformer_dict.keys()),
                        value=list(beamformer_dict.keys())[0])


# use additional classes for data evaluation/view
bv = BeamformerPresenter(source=bb,steer=st)

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
bvWidgets['freq'].value = "4000.0"
bvWidgets['num'].value = "3"


colorMapper = LogColorMapper(palette=viridis(100), 
                              low=30, high=50 ,low_color=(1,1,1,0))
dynamicSlider = RangeSlider(start=0, end=120, step=1., value=(30,50),
                            title="Dynamic Range")
def dynamicSlider_callback(attr, old, new):
    (colorMapper.low, colorMapper.high) = dynamicSlider.value
dynamicSlider.on_change("value",dynamicSlider_callback)

# create Button to trigger beamforming result calculation
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


#MicGeomPlot
mgPlot = figure(title='Microphone Geometry', tools = 'hover,pan,wheel_zoom,reset')
mgPlot.circle(x='x',y='y',source=mgWidgets['mpos_tot'].source)

# beamformerPlot
bfPlot = figure(title='Beamforming Result', tools = 'pan,wheel_zoom,reset')
bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',
             color_mapper=colorMapper,source=bv.cdsource)
bfPlot.add_layout(ColorBar(color_mapper=colorMapper,location=(0,0),
                           title="Level [dB]",
                            title_standoff=10),'right')

# Plot Tabs
mgPlotTab = Panel(child=row(mgPlot),title='Microphone Geometry Plot')
bfPlotTab = Panel(child=row(bfPlot),title='Source Plot')
plotTabs = Tabs(tabs=[mgPlotTab,bfPlotTab],width=600)

# Property Tabs
selectedBfWidgets = column(*bbWidgets.values())  
tsTab = Panel(child=column(*tsWidgets.values()),title='Time Data')
mgTab = Panel(child=column(*mgWidgets.values()),title='MicGeometry')
calTab = Panel(child=column(*calWidgets.values()),title='Calibration')
envTab = Panel(child=column(*envWidgets.values()),title='Environment')
gridTab = Panel(child=column(*rgWidgets.values()),title='Grid')
stTab = Panel(child=column(*stWidgets.values()),title='Steering')
psTab = Panel(child=column(*psWidgets.values()),title='FFT')
bfTab = Panel(child=column(beamformerSelector,selectedBfWidgets),
              title='Beamforming')
propertyTabs = Tabs(tabs=[tsTab,mgTab,calTab,envTab,gridTab,stTab,
                          psTab,bfTab],width=1000)

calcColumn = column(calcButton,*bvWidgets.values(),dynamicSlider)

def beamformer_handler(attr,old,new):
    bv.source = beamformer_dict.get(new)
    selectedBfWidgets.children = list(beamformer_dict.get(new).get_widgets().values())
beamformerSelector.on_change('value',beamformer_handler)

# make Document
mainlayout = row(plotTabs,calcColumn,propertyTabs)
doc.add_root(mainlayout)


