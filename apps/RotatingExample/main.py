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
RectGrid,SteeringVector,SpatialInterpolator,\
SpatialInterpolatorRotation,AngleTracker,Trigger,\
SpatialInterpolatorConstantRotation,\
BeamformerBase, BeamformerFunctional,BeamformerCapon,\
BeamformerEig,BeamformerMusic,BeamformerDamas,BeamformerDamasPlus,BeamformerOrth,\
BeamformerCleansc, BeamformerClean, BeamformerPresenter,\
BeamformerCMF,BeamformerGIB,Environment,Calib,set_calc_button_callback

doc = curdoc() 
# build processing chain
micgeofile = path.join( path.split(acoular.__file__)[0],'xml','array_56.xml')
tdfile = 'rotating_source.h5'
ts = MaskedTimeSamples(name=tdfile)

mg = MicGeom(from_file=micgeofile)

si = SpatialInterpolatorConstantRotation(source = ts,mics = mg,  rotational_speed = 15.0,\
                                         array_dimension = '2D')

ps = PowerSpectra(time_data=si)
rg = RectGrid(x_min=-0.8, x_max=0.8, y_min=-0.8, y_max=0.8, z=1.00,increment=0.05)
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
bv = BeamformerPresenter(source=bb,num=3,freq=4000.)

# get widgets to control settings
tsWidgets = ts.get_widgets()
siWidgets = si.get_widgets()
mgWidgets = mg.get_widgets()
envWidgets = env.get_widgets()
psWidgets = ps.get_widgets()
rgWidgets = rg.get_widgets()
stWidgets = st.get_widgets()
bbWidgets = bb.get_widgets()
bvWidgets = bv.get_widgets()

colorMapper = LogColorMapper(palette=viridis(100), 
                              low=50, high=65 ,low_color=(1,1,1,0))
dynamicSlider = RangeSlider(start=0, end=120, step=1., value=(50,65),
                            title="Dynamic Range")
def dynamicSlider_callback(attr, old, new):
    (colorMapper.low, colorMapper.high) = dynamicSlider.value
dynamicSlider.on_change("value",dynamicSlider_callback)

# create Button to trigger beamforming result calculation
calcButton = Toggle(label="Calculate",button_type="primary")
set_calc_button_callback(bv.update,calcButton)

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
siTab = Panel(child=column(*siWidgets.values()),title='Virtual Rotation')
mgTab = Panel(child=column(*mgWidgets.values()),title='MicGeometry')
envTab = Panel(child=column(*envWidgets.values()),title='Environment')
gridTab = Panel(child=column(*rgWidgets.values()),title='Grid')
stTab = Panel(child=column(*stWidgets.values()),title='Steering')
psTab = Panel(child=column(*psWidgets.values()),title='FFT')
bfTab = Panel(child=column(beamformerSelector,selectedBfWidgets),
              title='Beamforming')
propertyTabs = Tabs(tabs=[tsTab,siTab,mgTab,envTab], sizing_mode="stretch_both")
 
propertyTabs2 = Tabs(tabs=[gridTab,stTab,
                          psTab,bfTab], sizing_mode="stretch_both")


calcColumn = column(calcButton,*bvWidgets.values(),dynamicSlider)

def beamformer_handler(attr,old,new):
    bv.source = beamformer_dict.get(new)
    selectedBfWidgets.children = list(beamformer_dict.get(new).get_widgets().values())
beamformerSelector.on_change('value',beamformer_handler)

# make Document
mainlayout = row(plotTabs,calcColumn,propertyTabs,propertyTabs2)

# make Document
def server_doc(doc):
    doc.add_root(mainlayout)
    doc.title = "RotatingExample"

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)