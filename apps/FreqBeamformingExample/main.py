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
from bokeh.models.tools import BoxEditTool
from bokeh.models import LinearColorMapper,ColorBar,ColumnDataSource
from bokeh.models.widgets import Panel,Tabs,Select, Toggle, RangeSlider
from bokeh.plotting import figure
from bokeh.palettes import viridis, plasma, inferno, magma
from numpy import array, zeros, nan
import acoular
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerFunctional,BeamformerCapon,\
BeamformerEig,BeamformerMusic,BeamformerDamas,BeamformerDamasPlus,BeamformerOrth,\
BeamformerCleansc, BeamformerClean, BeamformerPresenter,\
BeamformerCMF,BeamformerGIB,Environment,Calib

doc = curdoc() 

#%% Build processing chain
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

#%%  Beamforming Algorithms
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

#%% Beamformer selector

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


#%% Widgets for bf settings

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
bvWidgets['num'].value = "3"
bvWidgets['num'].width = 40
bvWidgets['freq'].value = "4000.0"
bvWidgets['freq'].width = 100


#%% Widgets for display

colorMapper = LinearColorMapper(palette=viridis(100), 
                              low=30, high=50 ,low_color=(1,1,1,0))
dynamicSlider = RangeSlider(start=0, end=120, step=1., value=(30,50),
                            width=220,
                            title="Dynamic Range")
def dynamicSlider_callback(attr, old, new):
    (colorMapper.low, colorMapper.high) = dynamicSlider.value
dynamicSlider.on_change("value",dynamicSlider_callback)

# create Button to trigger beamforming result calculation
calcButton = Toggle(label="Calculate",button_type="primary", width=150, height=50)
def calc(arg):
    if arg:
        calcButton.label = 'Calculating ...'
        bv.update()
        calcButton.active = False
        calcButton.label = 'Calculate'
    else:
        calcButton.label = 'Calculate'
calcButton.on_click(calc)

#%% Plots setup

#MicGeomPlot
mgPlot = figure(title='Microphone Geometry', 
                tools = 'hover,pan,wheel_zoom,reset')
mgPlot.toolbar.logo=None
mgPlot.circle(x='x',y='y',source=mgWidgets['mpos_tot'].source)

# beamformerPlot

bfplotwidth = 600
bfPlot = figure(title='Beamforming Result', 
                tools = 'pan,wheel_zoom,reset', 
                width=bfplotwidth,
                height=500)
bfPlot.toolbar.logo=None
bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',
             color_mapper=colorMapper,source=bv.cdsource)
bfPlot.add_layout(ColorBar(color_mapper=colorMapper,location=(0,0),
                           title="SPL / dB",
                           title_standoff=10),'right')

# FrequencySignalPlot
freqdata = ColumnDataSource(data={'freqs':ps.fftfreq(),
                                  'amp':zeros((ps.fftfreq().shape))})
f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
f_ticks_override = {20: '0.02', 50: '0.05', 100: '0.1', 200: '0.2', 
                    500: '0.5', 1000: '1', 2000: '2', 5000: '5', 10000: '10', 
                    20000: '20'}
freqplot = figure(title="Sector-Integrated Spectrum", plot_width=bfplotwidth, plot_height=300,
                  x_axis_type="log", x_axis_label="f / kHz", 
                  y_axis_label="SPL / dB")
freqplot.toolbar.logo=None
freqplot.xaxis.axis_label_text_font_style = "normal"
freqplot.yaxis.axis_label_text_font_style = "normal"
freqplot.xgrid.minor_grid_line_color = 'navy'
freqplot.xgrid.minor_grid_line_alpha = 0.05
freqplot.xaxis.ticker = f_ticks
freqplot.xaxis.major_label_overrides = f_ticks_override
freqplot.line('freqs', 'amp', source=freqdata)



#%% Property Tabs
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
                          psTab,bfTab],width=1100)

#%% 

def beamformer_handler(attr,old,new):
    bv.source = beamformer_dict.get(new)
    selectedBfWidgets.children = list(beamformer_dict.get(new).get_widgets().values())
beamformerSelector.on_change('value',beamformer_handler)

#%% Integration sector

sectordata = ColumnDataSource(data={'x':[],'y':[],'width':[], 'height':[]})
def integrate_result(attr,old,new):
    for i in range(len(sectordata.data['x'])):
        sector = array([
            sectordata.data['x'][i]-sectordata.data['width'][i]/2, 
            sectordata.data['y'][i]-sectordata.data['height'][i]/2, 
            sectordata.data['x'][i]+sectordata.data['width'][i]/2, 
            sectordata.data['y'][i]+sectordata.data['height'][i]/2
            ])
        print(sector)
        #print(bv.source.integrate(sector))
        specamp = acoular.L_p(bv.source.integrate(sector))
        specamp[specamp<-300] = nan
        freqdata.data['amp'] = specamp
        freqdata.data['freqs'] = ps.fftfreq()
        # print(acoular.L_p(acoular.integrate(array(bv.cdsource.data['pdata']), rg, sector)))


isector = bfPlot.rect('x', 'y', 'width', 'height',alpha=.3,color='red', source=sectordata)
tool = BoxEditTool(renderers=[isector],num_objects=1)
bfPlot.add_tools(tool)
sectordata.on_change('data',integrate_result)

#%% Document layout

calcRow = row(calcButton,*bvWidgets.values(),dynamicSlider)

# Plot Tabs
mgPlotTab = Panel(child=mgPlot,title='Microphone Geometry Plot')

bfPlotTab = Panel(child=column(calcRow, bfPlot,freqplot),title='Source Plot')
plotTabs = Tabs(tabs=[mgPlotTab,bfPlotTab], active=1, width=bfplotwidth)

# make Document
mainlayout = row(plotTabs,propertyTabs)
doc.add_root(mainlayout)
