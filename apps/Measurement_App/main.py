#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
app can be started with:
bokeh serve --show Measurement_App --args --argName=argValue

# Processing / Acoular
#
#                                    |-> TimePower -> Average -> Amplitude Bar
#                                    |-> FiltOctave ->  TimePower -> Average -> Calibration    
# SamplesGenerator -> SampleSplitter |-> BeamformerTime -> FiltOctave -> TimePower -> Average -> Beamforming
#                                    |-> WriteH5   

In case of SINUS Devices:
if sync order of pci cards should be specified use
bokeh serve --show Measurement_App --args --device=typhoon --syncorder SerialNb1 SerialNb2 ...
"""
import argparse
import sys
from pathlib import Path

import acoular as ac
import numpy as np

import spectacoular as sp

try:
    import cv2
    cam_enabled=True
    from cam import cameraCDS, camWidgets, set_alpha_callback, set_camera_callback
except:
    cam_enabled=False
    camWidgets = []

# local imports
from app import MeasurementControl, current_time
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    Div,
    LogColorMapper,
    Spacer,
    Tabs,
)
from bokeh.models import TabPanel as Panel
from bokeh.models.glyphs import Scatter
from bokeh.models.widgets import (
    Button,
    DataTable,
    NumberEditor,
    NumberFormatter,
    RangeSlider,
    Select,
    Slider,
    TableColumn,
)

# bokeh imports
from bokeh.models.widgets.inputs import NumericInput
from bokeh.palettes import Viridis256
from bokeh.plotting import curdoc, figure
from interfaces import get_interface
from layout import (
    COLOR,
    ClipSlider,
    autolevel_toggle,
)
from log import LogWidget

parser = argparse.ArgumentParser()
parser.add_argument(
  '--device',
  type=str,
  default="phantom",
  choices=["sounddevice","tornado","typhoon","phantom","apollo"],
  help='Connected device.')
parser.add_argument(
  '--blocksize',
  type=int,
  default=4096,
  help='Size of data blocks to be processed')
parser.add_argument(
  '--syncorder',
  default=[],
  nargs='+', # accepts more than one argument   
  help='Synchronization order of PCI cards')

args = parser.parse_args()
DEVICE = args.device
SYNCORDER = args.syncorder
MGEOMPATH = Path(__file__).resolve().parent / "micgeom"
MICSIZE = 10
BANDWIDTH = 3
CFREQ = 4000 
NBLOCKS = 5 # number of blocks after which to do beamforming
WTIME = 0.025
XCAM = (-0.5,-0.375,1.,0.75)



# =============================================================================
# load device
# =============================================================================
sinus_enabled=False
if DEVICE == 'sounddevice':
    import sounddevice as sd
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.num_channels)]
    mics = sp.MicGeom()
    grid = sp.RectGrid()
elif DEVICE == 'phantom':
    mics = sp.MicGeom(file = MGEOMPATH / 'array_64.xml')
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.num_channels)]
    grid = sp.RectGrid( x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=.3, increment=0.01)
else: # otherwise it must be sinus
    try:
        import sinus
        sinus_enabled=True
    except ImportError:
        raise NotImplementedError("sinus module cannot be imported!")
    from sinus_dev import (
        append_left_column,
        close_device_callback,
        get_callbacks,
        get_interface,
        get_teds_component,
    )
    mics = sp.MicGeom(file = MGEOMPATH / 'tub_vogel64.xml')
    iniManager, devManager, devInputManager,inputSignalGen = get_interface(DEVICE,SYNCORDER)
    ch_names = inputSignalGen.inchannels_
    grid = sp.RectGrid( x_min=-0.75, x_max=0.75, y_min=-0.5, y_max=0.5, z=1.3, increment=0.015)
num_channels = inputSignalGen.num_channels

doc = curdoc()
log = LogWidget(doc=doc)
if cam_enabled: 
    set_camera_callback(doc)

control = MeasurementControl(
    doc=doc,
    source=inputSignalGen,
    logger=log.logger,
    blocksize=args.blocksize,
    steer=ac.SteeringVector(grid=grid, mics=mics, ref=[0,0,0]),
)

mic_presenter = sp.MicGeomPresenter(source=mics, auto_update=True)
mic_presenter.update(**{
     'sizes':np.array([MICSIZE]*mics.num_mics),'colors':[COLOR[1]]*mics.num_mics})

# =============================================================================
# DEFINE FIGURES
# =============================================================================

fig_height = 750
fig_width = 1000

# Amplitude Figure
amp_fig = figure(
    title='SPL/dB',tooltips=[("Lp/dB", "@level"), ("Channel", "@channels"),], tools="",
    y_range=(105,110), width=1500, height=fig_height)
amp_fig.xgrid.visible = False
amp_fig.xaxis.major_label_orientation = np.pi/2
amp_fig.toolbar.logo=None

# MicGeom / Sourcemap Figure
dx = grid.x_max-grid.x_min
dy = grid.y_max-grid.y_min
height = int(fig_width * dy/dx+0.5)
mics_beamf_fig = figure(
        title='Array Geometry', tooltips=[("Lp/dB", "@level"), ("Channel Index", "@channels"),("(x,y)", "(@x, @y)"),],
        tools = 'pan,wheel_zoom,reset',
         match_aspect=True, aspect_ratio=1, frame_width=fig_width, frame_height=height,
        **{'width':fig_width,  'height':height}
        )

# =============================================================================
# DEFINE COLUMN DATA SOURCES
# =============================================================================

amp_cds = ColumnDataSource({'channels':list(np.arange(1,num_channels+1)), 'level':np.zeros(num_channels),'colors':[COLOR[1]]*num_channels} )
beamf_cds = ColumnDataSource({'level':[]})
calib_cds = ColumnDataSource({"calibvalue":[],"caliblevel":[],"calibfactor":[], "channel":[]})
grid_data = ColumnDataSource(data={# x and y are the centers of the rectangle!
    'x': [(grid.x_max + grid.x_min)/2], 'y': [(grid.y_max + grid.y_min)/2],
    'width': [grid.x_max-grid.x_min], 'height': [grid.y_max-grid.y_min]
})

# =============================================================================
# DEFINE GLYPHS
# =============================================================================

# Amplitude Bar Plot
amp_bar = amp_fig.vbar(x='channels', width=0.5, bottom=0,top='level', color='colors', source=amp_cds)

if cam_enabled:
    mics_beamf_fig.image_rgba(image='image_data',
                        x=XCAM[0], y=XCAM[1], dw=XCAM[2], dh=XCAM[3],
                        source=cameraCDS)
beamf_color_mapper = LogColorMapper(palette=Viridis256, low=70, high=90,low_color=(1,1,1,0))
bfImage = mics_beamf_fig.image(image='level', x=grid.x_min, y=grid.y_min, dw=dx, dh=dy,
                color_mapper=beamf_color_mapper,
                source=beamf_cds)
if cam_enabled: 
    set_alpha_callback(bfImage)

# Microphone Geometry Plot
mic_layout = sp.layouts.MicGeomComponent(
    glyph=Scatter(marker='circle_cross', x='xi', y='yi', fill_color='colors', size='sizes', fill_alpha=0.2),
    figure=mics_beamf_fig, presenter=mic_presenter, allow_point_draw=True,
    )
mics_beamf_fig.rect( # draw rect grid bounds (dotted)
    alpha=1.,color='black',fill_alpha=0,line_width=2, source=grid_data)#line_color="#213447")


# =============================================================================
# DEFINE WIDGETS
# =============================================================================

# set up widgets for Microphone Geometry
editor = NumberEditor()
formatter = NumberFormatter(format="0.00")
mpos_columns = [TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
                TableColumn(field='y', title='x/m', editor=editor, formatter=formatter),
                TableColumn(field='z', title='x/m', editor=editor, formatter=formatter)]
mic_layout.mics_trait_widget_args.update(
    {'pos_total':  {'height' : 280, 'editable':True, 'transposed':True, 'columns':mpos_columns,}})
mics_widgets = mic_layout.widgets

# set up widgets for Beamforming
dynamicSlider = RangeSlider(start=30, end=110, 
                            value=(beamf_color_mapper.low,beamf_color_mapper.high), 
                            step=.5, title="Level",disabled=True)

rgWidgets = grid.get_widgets()
zSlider = Slider(start=0.01, end=10.0, value=grid.z, step=.02, title="z",disabled=False)
grid.set_widgets(**{'z':zSlider})
rgWidgets['z'] = zSlider # replace textfield with slider

# set up widgets for Calibration
calWidgets = control.calib.get_widgets()
calfiltWidgets = control.calib.source.source.source.get_widgets()

#Others:
cliplevel = NumericInput(value=120, title="Clip Level/dB",width=100)

# Select
if sinus_enabled:
    label_options = ["Index","Number","Physical"]
else:
    label_options = ["Index","Number"]

labelSelect = Select(title="Select Channel Labeling:", value="Index",
                                options=label_options,
                                width=200)

def _get_channel_labels(ltype):
    if ltype == 'Index':
        labels = [str(i) for i in range(inputSignalGen.num_channels)]
    elif ltype == 'Number':
        labels = [str(i+1) for i in range(inputSignalGen.num_channels)]
    elif ltype == 'Physical':
        labels = [inputSignalGen.inchannels_[i] for i in range(inputSignalGen.num_channels)]
    return labels

def update_channel_labels(attr,old,new):
    ticker = list(range(1,inputSignalGen.num_channels+1))
    labels = _get_channel_labels(new)
    amp_fig.xaxis.ticker = ticker
    amp_fig.xaxis.major_label_overrides = {str(ticker[i]): label for i,label in enumerate(labels)}
    calib_cds.data['channel'] = labels
labelSelect.on_change('value',update_channel_labels)
        

# DataTable
columns = [TableColumn(field='channel', title='channel'),
            TableColumn(field='calibvalue', title='calibvalue', editor=NumberEditor()),
           TableColumn(field='caliblevel', title='caliblevel', editor=NumberEditor()),
           TableColumn(field='calibfactor', title='calibfactor', editor=NumberEditor()),]
calibTable = DataTable(source=calib_cds,columns=columns,width=600)

def _calibtable_callback():
    calib_cds.data = {"calibvalue":control.calib.calibdata[:,0],
                     "caliblevel":control.calib.calibdata[:,1],
                     "calibfactor":control.calib.calibfactor[:],
                     "channel":_get_channel_labels(labelSelect.value)}
def calibtable_callback():
    return doc.add_next_tick_callback(_calibtable_callback)
control.calib.on_trait_change(calibtable_callback,"calibdata")

# save calib button
savecal = Button(label="save to .xml",button_type="warning",width=200, height=60)
def save_calib_callback():
    if not calWidgets['name'].value:
        fname = Path("Measurement_App") / "metadata" / f"calibdata_{current_time()}.xml"
        calWidgets['name'].value = fname
    else:
        fname = calWidgets['name'].value
    control.calib.save()
savecal.on_click(save_calib_callback)

freqSlider = Slider(start=50, end=10000, value=CFREQ, 
                    step=1, title="Frequency",disabled=False)
control.beamf.source.source.source.set_widgets(**{'band':freqSlider}) # 
#csm.set_widgets(**{'center_freq':freqSlider})

# wtimeSlider = Slider(start=0.0, end=0.25, value=WTIME, format="0[.]000",
#                      step=0.0025, title="Time weighting (FAST: 0.125, SLOW: 1.0)",
#                      disabled=False)
# csm.set_widgets(**{'weight_time':wtimeSlider})


# color_bar = ColorBar(color_mapper=beamf_color_mapper,label_standoff=12, 
#                      background_fill_color = '#f6f6f6',
#                      border_line_color=None, location=(0,0))
#mics_beamf_fig.add_layout(color_bar, 'right')


def update_grid(attr,old,new):
    """update grid data source when grid settings change"""
    grid_data.data = {
    # x and y are the centers of the rectangle! 
    'x': [(grid.x_max + grid.x_min)/2], 'y': [(grid.y_max + grid.y_min)/2],
    'width': [grid.x_max-grid.x_min], 'height': [grid.y_max-grid.y_min]
    }
rgWidgets['x_min'].on_change('value',update_grid)
rgWidgets['x_max'].on_change('value',update_grid)
rgWidgets['y_min'].on_change('value',update_grid)
rgWidgets['y_max'].on_change('value',update_grid)


# button to stop the server
exit_button = Button(label="Exit", button_type="danger",sizing_mode="stretch_width",width=100)
def exit_callback(arg):
    from time import sleep
    sleep(1)
    if sinus_enabled:
        close_device_callback()
    sys.exit()
exit_button.on_click(exit_callback)
exit_button.js_on_click(CustomJS( code='''
    setTimeout(function(){
        window.location.href = "about:blank";
    }, 500);
    '''))
# =============================================================================
# DEFINE CALLBACKS
# =============================================================================

def update_app():  # only update figure when tab is active
    if figureTabs.active == 0: 
        update_amp_bar_plot()
    if figureTabs.active == 1:
        if control.beamf_toggle.active:
            update_beamforming_plot()
        else:
            update_mic_geom_plot()
    if sinus_enabled:
        pass #TODO fix!
        #update_buffer_bar_plot()

def update_amp_bar_plot():
    if control.disp.cdsource.data['data'].size > 0:
        levels = ac.L_p(control.disp.cdsource.data['data'][0])
        amp_cds.data['level'] =  levels
        amp_cds.data['colors'] = np.where(levels < cliplevel.value, control.modecolor, control.clipcolor)

def update_mic_geom_plot():
    log.logger.debug("update_mic_geom_plot")
    if mics.num_mics > 0: 
        p2 = control.disp.cdsource.data['data'][0]
        levels = ac.L_p(p2)
        if mics_widgets['mic_size'].value > 0:
            mic_presenter.cdsource.data['sizes'] = 20*p2/p2.max() + mics_widgets['mic_size'].value
        else:
            mic_presenter.cdsource.data['sizes'] = np.zeros(p2.shape[0])
        mic_presenter.cdsource.data['colors'] = np.where(levels < cliplevel.value, control.modecolor, control.clipcolor)

def update_beamforming_plot():
    if control.beamf.cdsource.data['data'].size > 0:
        beamf_cds.data['level'] = [
            ac.L_p(control.beamf.cdsource.data['data'].reshape(grid.shape)).T]
        if autolevel_toggle.active:
            dynamicValue = (dynamicSlider.value[1] - dynamicSlider.value[0])
            maxValue = beamf_cds.data['level'][0].max()
            beamf_color_mapper.high = max(ClipSlider.value+dynamicValue, maxValue)
            beamf_color_mapper.low = max(ClipSlider.value, maxValue-dynamicValue)

def update_view(arg):
    if arg:
        control._view_callback_id = doc.add_periodic_callback(
            update_app, int(control.update_period.value))
    if not arg:
        [thread.join() for thread in control._disp_threads]
        doc.remove_periodic_callback(control._view_callback_id)
control.display_toggle.on_click(update_view)

# =============================================================================

# callback functions
def dynamic_slider_callback(attr, old, new):
    if not autolevel_toggle.active:
        (beamf_color_mapper.low, beamf_color_mapper.high) = new
dynamicSlider.on_change('value', dynamic_slider_callback)    

def update_bfImage_axis(attr,old,new):
    dx = grid.x_max-grid.x_min
    dy = grid.y_max-grid.y_min
    bfImage.glyph.x = grid.x_min
    bfImage.glyph.y = grid.y_min
    bfImage.glyph.dw = dx
    bfImage.glyph.dh = dy
    bfImage.glyph.update()

rgWidgets['x_min'].on_change('value',update_bfImage_axis)
rgWidgets['x_max'].on_change('value',update_bfImage_axis)
rgWidgets['y_min'].on_change('value',update_bfImage_axis)
rgWidgets['y_max'].on_change('value',update_bfImage_axis)
  

# # non bokeh functions
# def get_active_channels():
#     if DEVICE == 'typhoon' or DEVICE == 'tornado':
#         ch = [inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]
#     else:
#         ch = checkbox_micgeom.active   
#     ch.sort() 
#     return ch

# def select_micgeom_callback(attr, old, new):
#     mic_presenter.cdsource.data = {'x':mics.pos[0,:],'y':mics.pos[1,:],
#                        'sizes':np.array([MICSIZE]*mics.num_mics),
#                        'channels':get_active_channels(),
#                        'colors': [COLOR[1]]*mics.num_mics}
# select_micgeom.on_change('value',select_micgeom_callback)


# def checkbox_micgeom_callback(attr, old, new):
#     if mics.num_mics > 0:
#         mic_presenter.cdsource.data['channels'] = get_active_channels()
# checkbox_micgeom.on_change('active',checkbox_micgeom_callback)    


def autolevel_toggle_callback(arg):
    if not arg:
        (beamf_color_mapper.low, beamf_color_mapper.high) = dynamicSlider.value
      
# functions

if sinus_enabled:
    pass #TODO fix!
    # update_buffer_bar_plot = get_callbacks(inputSignalGen,iniManager,devManager,devInputManager,
    #               amp_cds,checkbox_micgeom,amp_fig,mic_presenter.cdsource,mics,log.logger)

# =============================================================================
#  Set Up Bokeh Document Layout
# =============================================================================

# Calibration Panel
calWidgets['name'].width=500
caldiv1 = Div(text=r"""<b>Calibration Filter Settings<b\>""")
caldiv2 = Div(text=r"""<b>Basic Calibration Settings<b\>""")
calCol = column(Spacer(height=15),
                row(labelSelect,savecal,calWidgets['name']),
                Spacer(height=15),
                row(calibTable,
                column(
                caldiv1,
                *calfiltWidgets.values(),
                caldiv2,
                calWidgets['magnitude'],
                calWidgets['delta'],
                width=150)))

mgWidgetCol = column(
                mics_widgets['file'],
                mics_widgets['num_mics'],
                mics_widgets['invalid_channels'],
                mics_widgets['pos_total'],
                width=250,
                )

gridCol = column(*rgWidgets.values(),width=200)

# Tabs
amplitudesTab = Panel(child=column(row(Spacer(width=25),cliplevel,Spacer(width=25),labelSelect),row(amp_fig, log.log_text)),title='Channel Levels')
micgeomTab = Panel(child=column(
    row(column(
        row(Spacer(width=25),cliplevel,Spacer(width=15),mics_widgets['mic_size'], mics_widgets['mirror_view'], Spacer(width=15)),
        mics_beamf_fig
        ),
        Spacer(width=30, height=1000),mgWidgetCol)),title='Microphone Geometry')
beamformTab = Panel(child=column(
                        row(Spacer(width=30, height=1000),gridCol,Spacer(width=20, height=1000),
                        column(
                            freqSlider, dynamicSlider, #wtimeSlider, 
                            ClipSlider,autolevel_toggle,*camWidgets,
                         width=200)
                         #checkbox_paint_mode
                         ),
                        ),title='Beamforming')
calibrationTab = Panel(child=calCol, title="Calibration")
figureTabs = Tabs(tabs=[
    amplitudesTab,
    micgeomTab,
    calibrationTab
    ],width=850)

left_column = control.get_widgets()

if sinus_enabled:
    # Additional Panel when SINUS Messtechnik API is used
    teds_component = get_teds_component(devInputManager,log.logger)
    sinusTab = Panel(child=teds_component,title='SINUS Messtechnik')
    figureTabs.tabs.append(sinusTab)
    # add buttons
    append_left_column(left_column)
if DEVICE == 'sounddevice':
    # set up devices choice
    devices = {}
    for i,dev in enumerate(sd.query_devices()):
        if dev['max_input_channels']>0:
            devices["{}".format(i)] = "{name} {max_input_channels}".format(**dev)
    device_select = Select(title="Choose input device:", 
        value="{}".format(list(devices.keys())[0]), options=list(devices.items()))
    inputSignalGen.device=int(device_select.value)
    inputSignalGen.set_widgets(device=device_select)
    left_column.children.insert(1,device_select)
    sdwidgets = list(inputSignalGen.get_widgets().values())
    left_column.children.insert(2,sdwidgets[2]) # num_channels

    def device_update(attr,old,new):
        inputSignalGen.num_channels = sd.query_devices(inputSignalGen.device)['max_input_channels']
        ticker = list(np.arange(1,inputSignalGen.num_channels+1))
        amp_cds.data = {'channels':ticker,'level': np.zeros(inputSignalGen.num_channels)}
        amp_fig.xaxis.ticker = ticker
        # checkbox_micgeom.labels = [str(_) for _ in range(inputSignalGen.num_channels)]
        # checkbox_micgeom.active = [_ for _ in range(inputSignalGen.num_channels)]
        # if mics.num_mics > 0:
            # mic_presenter.cdsource.data = {'x':mics.pos[0,:],'y':mics.pos[1,:],
            #         'sizes':np.array([7]*mics.num_mics),
            #         'channels':[str(_) for _ in checkbox_micgeom.active]} 
    device_select.on_change('value',device_update)

right_column = column(figureTabs, width=1000, sizing_mode='inherit')

layout = column(row(Spacer(width=1400),exit_button),row(Spacer(width=20),
    left_column,
    Spacer(width=20),
    right_column,
    ),
)
doc.add_root(layout)
doc.title = "Measurement App"
