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
from bokeh.palettes import viridis
from numpy import array, nan
import acoular
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerFunctional,BeamformerCapon,\
BeamformerEig,BeamformerMusic,BeamformerDamas,BeamformerDamasPlus,BeamformerOrth,\
BeamformerCleansc, BeamformerClean, BeamformerPresenter,\
BeamformerCMF,BeamformerGIB,Environment,Calib,set_calc_button_callback

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
rg = RectGrid(x_min=-0.6, x_max=-0.0, y_min=-0.3, y_max=0.3, z=0.68,increment=0.01)
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
                    'Conventional Beamforming': (bb,bb.get_widgets()),
                   'Functional Beamforming': (bf,bf.get_widgets()),
                   'Capon Beamforming': (bc,bc.get_widgets()),
                   'Eigenvalue Beamforming': (be,be.get_widgets()),
                   'Music Beamforming': (bm,bm.get_widgets()),
                   'Damas Deconvolution': (bd,bd.get_widgets()),
                   'DamasPlus Deconvolution' : (bdp,bdp.get_widgets()),
                   'Orthogonal Beamforming' : (bo,bo.get_widgets()),
                   'CleanSC Deconvolution' : (bs, bs.get_widgets()),
                   'Clean Deconvolution' : (bl,bl.get_widgets()),
                   'CMF' : (bcmf,bcmf.get_widgets()),
                   'GIB' : (bgib,bgib.get_widgets()),
                   }

# create Select Button to select Beamforming Algorithm
beamformerSelector = Select(title="Beamforming Method:",
                        options=list(beamformer_dict.keys()),
                        value=list(beamformer_dict.keys())[0],
                        height=75)


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
                              low=40, high=50 ,low_color=(1,1,1,0))
dynamicSlider = RangeSlider(start=0, end=120, step=1., value=(40,50),
                            width=220,height=50,
                            title="Dynamic Range")
def dynamicSlider_callback(attr, old, new):
    (colorMapper.low, colorMapper.high) = dynamicSlider.value
dynamicSlider.on_change("value",dynamicSlider_callback)

# create Button to trigger beamforming result calculation
calcButton = Toggle(label="Calculate",button_type="primary", width=175,height=75)
set_calc_button_callback(bv.update,calcButton)

RED = "#961400"
BLUE = "#3288bd"

# beamformerPlot
bfplotwidth = 700
bfPlot = figure(title='Source Map', 
                tools = 'pan,wheel_zoom,reset', 
                width=bfplotwidth,
                height=700)
# bfPlot.grid[0].bounds = (rg.x_min,rg.x_max) 
# bfPlot.grid[1].bounds = (rg.y_min,rg.y_max)
# bfPlot.grid[0].visible = False
# bfPlot.grid[1].visible = False
# ('x', 'y', 'width', 'height', 'angle', 'dilate')
bfPlot.rect(-0.38, 0.0, 0.2, 0.5,alpha=1.,color='gray',fill_alpha=.8,line_width=5,line_color="#1e3246")
bfPlot.rect(-.3, 0.0, 0.6, 0.6,alpha=1.,color='#d2d6da',fill_alpha=0,line_width=1)#line_color="#213447")
bfPlot.toolbar.logo=None
bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',alpha=0.9,
             color_mapper=colorMapper,source=bv.cdsource)
bfPlot.add_layout(ColorBar(color_mapper=colorMapper,location=(0,0),
                           title="dB",
                           title_standoff=10),'right')
# bfPlot.circle(x='x',y='y',color='#961400',size=10,alpha=.7,
#               source=mgWidgets['mpos_tot'].source)

# FrequencySignalPlot
# freqdata = ColumnDataSource(data={'freqs':[list(ps.fftfreq())],
#                                   'amp':[[zeros((ps.fftfreq().shape))]]})
freqdata = ColumnDataSource(data={'freqs':[],
                                  'amp':[]})
f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
f_ticks_override = {20: '0.02', 50: '0.05', 100: '0.1', 200: '0.2', 
                    500: '0.5', 1000: '1', 2000: '2', 5000: '5', 10000: '10', 
                    20000: '20'}
freqplot = figure(title="Sector-Integrated Spectrum", plot_width=bfplotwidth, plot_height=500,
                  x_axis_type="log", x_axis_label="f / kHz", 
                  y_axis_label="SPL / dB")
freqplot.toolbar.logo=None
freqplot.xaxis.axis_label_text_font_style = "normal"
freqplot.yaxis.axis_label_text_font_style = "normal"
freqplot.xgrid.minor_grid_line_color = 'navy'
freqplot.xgrid.minor_grid_line_alpha = 0.05
freqplot.xaxis.ticker = f_ticks
freqplot.xaxis.major_label_overrides = f_ticks_override
freqplot.multi_line('freqs', 'amp',color=RED,alpha=.8,line_width=4, source=freqdata)

#%% Layout Grid Column
from bokeh.layouts import layout
from bokeh.models.widgets import Div

# rgLayout = layout([ 
#                     [Div(text='',width=100, height=25)],
#                     [rgWidgets['x_min'],rgWidgets['x_max']],
#                     [rgWidgets['y_min'],rgWidgets['y_max']],
#                     [rgWidgets['z'],rgWidgets['increment']],
#                     [rgWidgets['nxsteps'],rgWidgets['nysteps']],
#                     [rgWidgets['size'],rgWidgets['shape']],
#                     ])



#%% Property Tabs
selectedBfWidgets = column(*bbWidgets.values(),height=1000)  

# bfcol = column(beamformerSelector,selectedBfWidgets)
# tsTab = Panel(child=column(*tsWidgets.values()),title='Time Data')
# mgTab = Panel(child=column(*mgWidgets.values()),title='MicGeometry')
# calTab = Panel(child=column(*calWidgets.values()),title='Calibration')
# envTab = Panel(child=column(*envWidgets.values()),title='Environment')
# gridTab = Panel(child=rgLayout,title='Grid')
# stTab = Panel(child=column(*stWidgets.values()),title='Steering')
# psTab = Panel(child=column(*psWidgets.values()),title='FFT')
# bfTab = Panel(child=column(beamformerSelector,selectedBfWidgets),
#               title='Beamforming')
# propertyTabs = Tabs(tabs=[tsTab,mgTab,calTab,envTab,gridTab,stTab,
#                           psTab,bfTab],width=1100)

#%%  

# tsWidgets = ts.get_widgets()
# mgWidgets = mg.get_widgets()
# envWidgets = env.get_widgets()
# calWidgets = cal.get_widgets()
# psWidgets = ps.get_widgets()
# rgWidgets = rg.get_widgets()
# stWidgets = st.get_widgets()
# bbWidgets = bb.get_widgets()

from bokeh.models.widgets import Dropdown, Select

menu = [("Time Data", "tsWidgets"), ("Microphone Geometry","mgWidgets"),
        ("Environment","envWidgets"),("Calibration","calWidgets"),
        ("FFT/CSM","psWidgets"),("Focus Grid","rgWidgets"),
        ("Steering Vector","stWidgets"),("Beamforming Method","bbWidgets"),
        ]
dropdown = Dropdown(label="Selcet Setting", button_type="primary", menu=menu,
                     width=175,height=75)

#%% 
selectedSettingCol = column(height=1000)  
def select_setting_handler(attr,old,new):
    print(attr,old,new)
    if not new == "bbWidgets":
        selectedSettingCol.children = list(eval(new).values())
    else:
        # selmethod = beamformerSelector.value
        selectedSettingCol.children = selectedBfWidgets.children 
        # selectedSettingCol.children = list(beamformer_dict[selmethod][1].values())
        
dropdown.on_change("value",select_setting_handler)
    

def beamformer_handler(attr,old,new):
    bv.source = beamformer_dict.get(new)[0]
    # if dropdown.value == "bbWidgets"
    selectedBfWidgets.children = list(beamformer_dict.get(new)[1].values())
    if dropdown.value == "bbWidgets":
        selectedSettingCol.children = selectedBfWidgets.children 
    print(selectedBfWidgets.children)
beamformerSelector.on_change('value',beamformer_handler)

#%% Integration sector

sectordata = ColumnDataSource(data={'x':[],'y':[],'width':[], 'height':[]})
                                    
def integrate_result(attr,old,new):
    famp = []
    ffreq = []
    for i in range(len(sectordata.data['x'])):
        sector = array([
            sectordata.data['x'][i]-sectordata.data['width'][i]/2, 
            sectordata.data['y'][i]-sectordata.data['height'][i]/2, 
            sectordata.data['x'][i]+sectordata.data['width'][i]/2, 
            sectordata.data['y'][i]+sectordata.data['height'][i]/2
            ])
        print(sector)
        specamp = acoular.L_p(bv.source.integrate(sector))
        specamp[specamp<-300] = nan
        famp.append(specamp)
        ffreq.append(ps.fftfreq())
    freqdata.data.update(amp=famp, freqs=ffreq)


isector = bfPlot.rect('x', 'y', 'width', 'height',alpha=1.,fill_alpha=0.0,color=RED,
                      line_width=4,source=sectordata)
tool = BoxEditTool(renderers=[isector])
bfPlot.add_tools(tool)
sectordata.on_change('data',integrate_result)
bv.cdsource.on_change('data',integrate_result)
#%% Document layout

vspace = Div(text='',width=10, height=1000) # just for vertical spacing
vspace2 = Div(text='',width=50, height=20) # just for vertical spacing
hspace = Div(text='',width=100, height=20) # just for horizontal spacing

midlayout = layout([ 
         [Div(text='',width=80, height=10),calcButton,beamformerSelector],
         ])

calcRow = column(
    midlayout,
    freqplot,
    )

settingsCol = column(dropdown,vspace2,selectedSettingCol)

leftlayout=layout([ 
        [ Div(text='',width=100, height=0),*bvWidgets.values(),dynamicSlider],
        [bfPlot],
        ])

layout = row(leftlayout,vspace,calcRow,Div(text='',width=20),settingsCol)
# make Document
doc.add_root(layout)
