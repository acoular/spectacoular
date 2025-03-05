#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example that demonstrates different beamforming algorithms
"""
from pathlib import Path
import acoular as ac
import spectacoular as sp
import numpy as np

# bokeh imports
from bokeh.io import curdoc
from bokeh.layouts import column, row, layout
from bokeh.models.tools import BoxEditTool
from bokeh.models import LinearColorMapper,ColorBar,ColumnDataSource, Range1d, HoverTool, Spacer
from bokeh.models.widgets import Select, Toggle, RangeSlider, Div, NumberEditor, TableColumn, NumberFormatter
from bokeh.models.glyphs import Scatter
from bokeh.plotting import figure
from bokeh.palettes import viridis, Spectral11
from bokeh.server.server import Server



COLORS = list(Spectral11)
RED = "#961400"
BLUE = "#3288bd"

doc = curdoc() 

#%% Build processing chain
invalid = [1,7]
ts = sp.MaskedTimeSamples(file=Path(__file__).parent.parent / 'example_data.h5', invalid_channels=invalid, start=0, stop=16000)
cal = sp.Calib(source=ts, file=Path(__file__).parent.parent / 'example_calib.xml', invalid_channels=ts.invalid_channels)
mg = sp.MicGeom(file=Path(ac.__file__).parent / 'xml' / 'array_56.xml',invalid_channels = ts.invalid_channels)
ps = sp.PowerSpectra(source=cal,block_size=1024,overlap="50%")
rg = sp.RectGrid(x_min=-0.6, x_max=-0.1, y_min=-0.3, y_max=0.3, z=0.68,increment=0.01)
env = sp.Environment(c = 346.04)
st = sp.SteeringVector( grid = rg, mics=mg, env=env )    


#%%  Beamforming Algorithms
bb = sp.BeamformerBase( freq_data=ps, steer=st )  
bf = sp.BeamformerFunctional( freq_data=ps, steer=st, gamma=4)
bc = sp.BeamformerCapon( freq_data=ps, steer=st )  
be = sp.BeamformerEig( freq_data=ps, steer=st, n=54)
bm = sp.BeamformerMusic( freq_data=ps, steer=st, n=6)   
bd = sp.BeamformerDamas(freq_data=ps, n_iter=100)
bdp = sp.BeamformerDamasPlus(freq_data=ps, n_iter=100)
bo = sp.BeamformerOrth(freq_data=ps, eva_list=list(range(38,54)))
bs = sp.BeamformerCleansc(freq_data=ps, steer=st, r_diag=True)
bl = sp.BeamformerClean(freq_data=ps, n_iter=100)
bcmf = sp.BeamformerCMF(freq_data=ps, steer=st, method='LassoLarsBIC')
bgib = sp.BeamformerGIB(freq_data=ps, steer=st, method= 'LassoLars', n=10)

bv = sp.BeamformerPresenter(source=bb,num=3,freq=4000.)
mgp = sp.MicGeomPresenter(source=mg, auto_update=True)
mgp.update()

#%% figures

# CDS
grid_data = ColumnDataSource(data={
    # x and y are the centers of the rectangle! 
    'x': [(rg.x_max + rg.x_min)/2], 'y': [(rg.y_max + rg.y_min)/2],
    'width': [rg.x_max-rg.x_min], 'height': [rg.y_max-rg.y_min]
})

f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
freqdata = ColumnDataSource(data={'freqs':[np.array(f_ticks)], # initialize
                                  'amp':[np.array([0]*len(f_ticks))],
                                  'colors':['white']})

sectordata = ColumnDataSource(data={'x':[],'y':[],'width':[], 'height':[]})


# Beamforming Plot
bfPlot = figure(title='Source Map', 
                tools = 'pan,wheel_zoom,reset', 
                width=700,
                match_aspect=True)
# draw airfoil
bfPlot.rect(
    -0.38, 0.0, 0.2, 0.5,alpha=1.,color='gray',fill_alpha=.8,line_width=5,line_color="#1e3246")
bfPlot.rect( # draw rect grid bounds
    alpha=1.,color='#d2d6da',fill_alpha=0,line_width=2, source=grid_data)#line_color="#213447")
bfPlot.toolbar.logo=None
bfPlot.xgrid.visible = False
bfPlot.ygrid.visible = False
colorMapper = LinearColorMapper(palette=viridis(100), low=40, high=50 ,low_color=(1,1,1,0))
bfImage = bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',alpha=0.9,
             color_mapper=colorMapper,source=bv.cdsource, anchor='bottom_left', origin='bottom_left')
bfPlot.add_layout(ColorBar(color_mapper=colorMapper,location=(0,0),
                           title="dB",
                           title_standoff=10),'right')
mic_layout = sp.layouts.MicGeomComponent(
    glyph=Scatter(marker='circle_cross', x='xi', y='yi', size=15, fill_alpha=0.2),
    presenter=mgp,figure=bfPlot)
bfPlot.add_tools(HoverTool(tooltips=[("L_p (dB)", "@bfdata"),('mic', "@channels"),], 
    mode="mouse",renderers=[bfImage, mic_layout._glyph_renderer]))


# set up widgets for Microphone Geometry
editor = NumberEditor()
formatter = NumberFormatter(format="0.00")
mpos_columns = [TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
                TableColumn(field='y', title='x/m', editor=editor, formatter=formatter),
                TableColumn(field='z', title='x/m', editor=editor, formatter=formatter)]
mic_layout.mics_trait_widget_args.update(
    {'pos_total':  {'width' : 280,'editable':True, 'transposed':True, 'columns':mpos_columns,},
    'invalid_channels': {'width': 280, 'options':[str(i) for i in range(mg.pos_total.shape[1])]}}
)

# FrequencySignalPlot
f_ticks_override = {20: '0.02', 50: '0.05', 100: '0.1', 200: '0.2', 
                    500: '0.5', 1000: '1', 2000: '2', 5000: '5', 10000: '10', 
                    20000: '20'}
freqplot = figure(title="Sector-Integrated Spectrum", width=800, match_aspect=True,
                  x_axis_type="log", x_axis_label="f / kHz", 
                  y_axis_label="SPL / dB", )#tooltips=TOOLTIPS)
freqplot.toolbar.logo=None
freqplot.xaxis.axis_label_text_font_style = "normal"
freqplot.yaxis.axis_label_text_font_style = "normal"
freqplot.xgrid.minor_grid_line_color = 'navy'
freqplot.xgrid.minor_grid_line_alpha = 0.05
freqplot.xaxis.ticker = f_ticks
freqplot.x_range=Range1d(20, 20000)
freqplot.y_range=Range1d(0, 120)
freqplot.xaxis.major_label_overrides = f_ticks_override
frLine = freqplot.multi_line('freqs', 'amp',color='colors',alpha=0.0,line_width=3, source=freqdata)


#%% widgets

beamformer_dict = {
    'Conventional Beamforming': (bb, bb.get_widgets()),
    'Functional Beamforming': (bf, bf.get_widgets()),
    'Capon Beamforming': (bc, bc.get_widgets()),
    'Eigenvalue Beamforming': (be, be.get_widgets()),
    'Music Beamforming': (bm, bm.get_widgets()),
    'Damas Deconvolution': (bd, bd.get_widgets()),
    'DamasPlus Deconvolution': (bdp, bdp.get_widgets()),
    'Orthogonal Beamforming': (bo, bo.get_widgets()),
    'CleanSC Deconvolution': (bs, bs.get_widgets()),
    'Clean Deconvolution': (bl, bl.get_widgets()),
    'CMF': (bcmf, bcmf.get_widgets()),
    'GIB': (bgib, bgib.get_widgets()),
}

# create Select Button to select Beamforming Algorithm
beamformerSelector = Select(title="Beamforming Method:",
                        options=list(beamformer_dict.keys()),
                        value=list(beamformer_dict.keys())[0],
                        height=75, sizing_mode='stretch_width')

# use additional classes for data evaluation/view
bv.trait_widget_args.update({'num':{'width':40},'freq':{'width':100}})
# get widgets to control settings
tsWidgets = ts.get_widgets()
mgWidgets = mic_layout.widgets
envWidgets = env.get_widgets()
calWidgets = cal.get_widgets()
psWidgets = ps.get_widgets()
rgWidgets = rg.get_widgets()
stWidgets = st.get_widgets()
bbWidgets = bb.get_widgets()
bvWidgets = bv.get_widgets()
tsWidgets.pop('invalid_channels')

invalid_widget = mgWidgets['invalid_channels']
ts.set_widgets(invalid_channels = invalid_widget)
cal.set_widgets(invalid_channels = invalid_widget)

settings_dict = {
    "Time Data": tsWidgets,
    "Microphone Geometry": mgWidgets,
    "Environment": envWidgets,
    "Calibration": calWidgets,
    "FFT/CSM": psWidgets,
    "Focus Grid": rgWidgets,
    "Steering Vector": stWidgets,
    "Beamforming Method": bbWidgets,
}


#%% Widgets for display

dynamicSlider = RangeSlider(start=0, end=120, step=1., value=(40,50),
                            width=220,height=50,
                            title="Dynamic Range")
splSlider = RangeSlider(start=0, end=140, step=1., value=(10,120),
                            width=350,height=50,
                            title="SPL Range")

freqSlider = RangeSlider(start=20, end=20000, step=1., value=(20,20000),
                            width=350,height=50,
                            title="Frequency Range")

def dynamicSlider_callback(attr, old, new):
    (colorMapper.low, colorMapper.high) = dynamicSlider.value
dynamicSlider.on_change("value",dynamicSlider_callback)

def splSlider_callback(attr, old, new):
    # adjust the y limits of the frequency plot
    freqplot.y_range.start, freqplot.y_range.end = splSlider.value
splSlider.on_change("value",splSlider_callback)

def freqSlider_callback(attr, old, new):
    # adjust the x limits of the frequency plot
    freqplot.x_range.start, freqplot.x_range.end = freqSlider.value
freqSlider.on_change("value",freqSlider_callback)

# create Button to trigger beamforming result calculation
calcButton = Toggle(button_type="primary", width=125,height=50, label="Calculate")
sp.set_calc_button_callback(bv.update,calcButton)

def update_grid(attr,old,new):
    """update grid data source when grid settings change"""
    grid_data.data = {
    # x and y are the centers of the rectangle! 
    'x': [(rg.x_max + rg.x_min)/2], 'y': [(rg.y_max + rg.y_min)/2],
    'width': [rg.x_max-rg.x_min], 'height': [rg.y_max-rg.y_min]
    }
rgWidgets['x_min'].on_change('value',update_grid)
rgWidgets['x_max'].on_change('value',update_grid)
rgWidgets['y_min'].on_change('value',update_grid)
rgWidgets['y_max'].on_change('value',update_grid)


#%% Property Tabs
selectedBfWidgets = column(*bbWidgets.values(),height=1000)  

# create Select Button to select Beamforming Algorithm
settingSelector = Select(title="Select Setting",
                        options=list(settings_dict.keys()),
                        value=list(settings_dict.keys())[0],
                        height=75)

selectedSettingCol = column(list(settings_dict["Time Data"].values()),
                            height=1000)

def select_setting_handler(attr, old, new):
    """changes column layout (changes displayed widgets) 
    according to selected Acoular object
    """
    #print(attr,old,new)
    if not new == "Beamforming Method":
        selectedSettingCol.children = list(settings_dict[new].values())
    else:
        selectedSettingCol.children = selectedBfWidgets.children      
settingSelector.on_change("value",select_setting_handler)

def beamformer_handler(attr,old,new):
    bv.source = beamformer_dict.get(new)[0]
    # if dropdown.value == "bbWidgets"
    selectedBfWidgets.children = list(beamformer_dict.get(new)[1].values())
    if settingSelector.value == "Beamforming Method":
        selectedSettingCol.children = selectedBfWidgets.children 
    #print(selectedBfWidgets.children)
beamformerSelector.on_change('value',beamformer_handler)

#%% Integration sector
def integrate_result(attr,old,new):
    numsectors = len(sectordata.data['x']) 
    if numsectors > 0:
        frLine.glyph.line_alpha=0.8 
        famp = []
        ffreq = []
        colors = []
        for i in range(numsectors):
            sector = np.array([
                sectordata.data['x'][i]-sectordata.data['width'][i]/2, 
                sectordata.data['y'][i]-sectordata.data['height'][i]/2, 
                sectordata.data['x'][i]+sectordata.data['width'][i]/2, 
                sectordata.data['y'][i]+sectordata.data['height'][i]/2
                ])
            print(sector)
            specamp = ac.L_p(bv.source.integrate(sector))
            specamp[specamp<-300] = np.nan
            famp.append(specamp)
            ffreq.append(ps.fftfreq())
            colors.append(COLORS[i])
        freqdata.data.update(amp=famp, freqs=ffreq, colors=colors)
    else:
        frLine.glyph.line_alpha=0.0 # make transparent if no integration sector exist
        freqdata.data = {'freqs':[np.array(f_ticks)],
                        'amp':[np.array([0]*len(f_ticks))],
                        'colors':['white']}

   
isector = bfPlot.rect('x', 'y', 'width', 'height',alpha=1.,fill_alpha=0.2,color='black',
                      line_width=3,source=sectordata)
tool = BoxEditTool(renderers=[isector],num_objects=len(COLORS)) # allow only as many boxes as Colors
bfPlot.add_tools(tool)
sectordata.on_change('data',integrate_result)
bv.cdsource.on_change('data',integrate_result) # also change integration result when source map changes

#%% Instructions

instruction_calculation = Div(text="""<p><b>Calculate Source Map:</b></p> <b>Select a desired beamforming method</b> via the "Beamforming Method" widget and <b>press the Calculate Button</b>.
Depending on the method, this may take some time. You may also want to change the desired frequency and bandwith of interest with the "freq" and "num" Textfield widget.
""")

instruction_sector_integration = Div(text="""<p><b>Integrate over Source Map Region:</b></p> <b>Select the "Box Edit Tool"</b> in the upper right corner of the source map figure after calculating the source map.
<b>Hold down the shift key to draw an integration sector</b> in the Source Map. A sector-integrated spectrum should appear. One can <b>remove the sector by pressing the Backspace key</b>.
""")


#%% Document layout

left_layout=layout([
        [Spacer(width=40),calcButton,*bvWidgets.values(),dynamicSlider],
        [bfPlot],
        ])

center_layout = layout([
    [Spacer(width=40),splSlider, Spacer(width=20),freqSlider],
    [freqplot],
    ])

right_layout = column(beamformerSelector,settingSelector,Spacer(height=20),selectedSettingCol,sizing_mode='stretch_width')
instructionsCol = column(instruction_calculation, instruction_sector_integration)
layout = column(
    instructionsCol, Spacer(height=50),row(left_layout,Spacer(width=10),center_layout,Spacer(width=20),right_layout),
)

# make Document
def server_doc(doc):
    doc.add_root(layout)
    doc.title = "FreqBeamformingExample"

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)

