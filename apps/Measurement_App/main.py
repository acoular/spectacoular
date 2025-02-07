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
import sys
import argparse
import acoular as ac
import spectacoular as sp
import numpy as np 
from pathlib import Path
from datetime import datetime
from threading import Event
from functools import partial
try:
    import cv2
    cam_enabled=True
    from cam import cameraCDS, camWidgets, set_camera_callback, set_alpha_callback
except:
    cam_enabled=False
    camWidgets = []

# local imports
from log import LogWidget
from acoular_future import CSMInOut, BeamformerFreqTime
from threads import SamplesThread,EventThread
from interfaces import get_interface
from layout import plot_colors, toggle_labels, selectPerCallPeriod, checkbox_use_current_time, bfColorMapper,\
select_all_channels_button, msm_toggle, display_toggle,beamf_toggle,calib_toggle,\
dynamicSlider, checkbox_paint_mode, checkbox_autolevel_mode, ClipSlider,\
  COLOR

# bokeh imports
from bokeh.models.widgets.inputs import NumericInput
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, RadioGroup, Spacer, CustomJS,Div
from bokeh.models.widgets import Select,TextInput,Button,CheckboxGroup,Slider,\
TableColumn,NumberEditor,DataTable
from bokeh.models import TabPanel as Panel, Tabs
from bokeh.layouts import column,row

# logging
log = LogWidget()
logger = log.logger
doc = curdoc()

if cam_enabled: 
    set_camera_callback(doc)

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
BLOCKSIZE = args.blocksize
SYNCORDER = args.syncorder
APPFOLDER = Path(__file__).resolve().parent
MGEOMPATH = APPFOLDER / "micgeom"
TDPATH = APPFOLDER / "td"
if not TDPATH.exists():
    TDPATH.mkdir()
MICSIZE = 25
CLIPVALUE = 120 # value in dB at which CLIP_COLOR is applied
BANDWIDTH = 3
MAXMSG = 20 # maximum number of messages to display in GUI
CFREQ = 4000 
BUFFERSIZE = 400
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
    micGeo = sp.MicGeom(file = '')
    grid = sp.RectGrid()
elif DEVICE == 'phantom':
    micGeo = sp.MicGeom(file = MGEOMPATH / 'array_64.xml')
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.num_channels)]
    grid = sp.RectGrid( x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=.3, increment=0.01)
else: # otherwise it must be sinus
    try:
        import sinus
        sinus_enabled=True
    except ImportError:
        raise NotImplementedError("sinus module cannot be imported!")
    from sinus_dev import get_interface, append_left_column,append_disable_obj,\
        get_callbacks, close_device_callback, get_teds_component, gather_metadata
    micGeo = sp.MicGeom(file = MGEOMPATH / 'tub_vogel64.xml')
    iniManager, devManager, devInputManager,inputSignalGen = get_interface(DEVICE,SYNCORDER)
    ch_names = inputSignalGen.inchannels_
    grid = sp.RectGrid( x_min=-0.75, x_max=0.75, y_min=-0.5, y_max=0.5, z=1.3, increment=0.015)
    
num_channels = inputSignalGen.num_channels
# Splitting of incoming samples
splitter = ac.SampleSplitter(source = inputSignalGen)
# display Mode
timePow = ac.TimePower(source=splitter)
timePowAvg = ac.Average(source=timePow,num_per_average=BLOCKSIZE) 
tioAvg = sp.TimeOutPresenter(source=timePowAvg) # not necessary!
# calib Mode
fo_cal = sp.FiltOctave(source=splitter,band=1000.0)
tp_cal = ac.TimePower(source=fo_cal)
ta_cal = ac.Average(source=tp_cal,num_per_average=BLOCKSIZE)          
ch = sp.CalibHelper(source = ta_cal)
# rec Mode
wh5 = ac.WriteH5(source=splitter)
# beamforming Mode
csm = CSMInOut(source=splitter, block_size=BLOCKSIZE, center_freq= CFREQ, 
             band_width=BANDWIDTH, weight_time=WTIME)
steer = ac.SteeringVector(grid=grid, mics=micGeo, steer_type = 'true location')
beamformer = BeamformerFreqTime(
    source=csm, 
    beamformer = ac.BeamformerBase(steer=steer, r_diag=True, cached = False)
    )
bfTime = ac.BeamformerTime(source=splitter, steer=steer) 
bfFilt = sp.FiltOctaveLive(source=bfTime, band=CFREQ)
bfPow = ac.TimePower(source=bfFilt)
bfAvg = ac.Average(source=bfPow, num_per_average = BLOCKSIZE)
bf_used = beamformer


# =============================================================================
# Figures
# =============================================================================

# Amplitude Figure
# Tooltips
amp_fig = figure(
    title='SPL/dB',tooltips=[("Lp/dB", "@level"), ("Channel", "@channels"),], tools="",**{
    'y_range': (0,140),'width':1200, 'height':800}
    )
amp_fig.xgrid.visible = False
amp_fig.xaxis.major_label_orientation = np.pi/2
amp_fig.toolbar.logo=None

# MicGeomFigure
micgeom_fig = figure(
        title='Array Geometry', tooltips=[("Channel Index", "@channels"),("(x,y)", "(@x, @y)"),],
        tools = 'pan,wheel_zoom,reset',**{'width':800,  'height':800}
        )


# =============================================================================
# spectacoular widgets
# =============================================================================

# get widgets of acoular objects
rgWidgets = grid.get_widgets()
zSlider = Slider(start=0.01, end=10.0, value=grid.z, step=.02, title="z",disabled=False)
grid.set_widgets(**{'z':zSlider})
rgWidgets['z'] = zSlider # replace textfield with slider

select_micgeom = Select(title="Select MicGeom:", value=str(micGeo.file),
                                options=["None"]+[str(file) for file in MGEOMPATH.iterdir() if file.is_file()],
                                width=250)
micGeo.set_widgets(**{'file':select_micgeom})
mgWidgets = micGeo.get_widgets()
mgWidgets['file'] = select_micgeom
calWidgets = ch.get_widgets()
calfiltWidgets = fo_cal.get_widgets()

# =============================================================================
# bokeh
# =============================================================================
# Columndatasources
ChLevelsCDS = ColumnDataSource(data = {'channels':list(np.arange(1,num_channels+1)),
                                       'level':np.zeros(num_channels),
                                       'colors':[COLOR[1]]*num_channels} )
if micGeo.num_mics > 0:
    MicGeomCDS = ColumnDataSource(data={'x':micGeo.pos[0],'y':micGeo.pos[1],
                                        'sizes':np.array([MICSIZE]*micGeo.num_mics),
                                        'channels':[str(_) for _ in range(micGeo.num_mics)],
                                        'colors':[COLOR[1]]*micGeo.num_mics}) 
else:
    MicGeomCDS = ColumnDataSource(data={'x': [],'sizes':[], 'channels':[],'colors':[]})                                                                                                        
BeamfCDS = ColumnDataSource({'beamformer_data':[]})
calibCDS = ColumnDataSource(data={"calibvalue":[],"caliblevel":[],"calibfactor":[], "channel":[]})


# Numeric Inputs
cliplevel = NumericInput(value=CLIPVALUE, title="Clip Level/dB",width=100)
def update_cliplevel(attr,old,new):
    global CLIPVALUE
    CLIPVALUE = new
cliplevel.on_change('value',update_cliplevel)

# Text Inputs
ti_msmtime = TextInput(value="10", title="Measurement Time [s]:")
ti_savename = TextInput(value="", title="Filename:",disabled=True)

# RadioGroup
view_labels= ["Back View", "Front View"]
geomview = RadioGroup(labels=view_labels, active=0)
bfview = RadioGroup(labels=view_labels, active=0)
def update_micgeom_view(attr,old,new):
    if new == 0: # BackView
        MicGeomCDS.data['x'] = micGeo.pos[0,:]
    elif new == 1: # FrontView
        MicGeomCDS.data['x'] = micGeo.pos[0,:]*-1
geomview.on_change('active',update_micgeom_view)


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
    calibCDS.data['channel'] = labels
labelSelect.on_change('value',update_channel_labels)
        
# Buttons
reload_micgeom_button = Button(label="↻",disabled=False,width=60,height=60)
def update_micgeom_options_callback():
    select_micgeom.options=["None"]+[str(file) for file in MGEOMPATH.iterdir() if file.is_file()]
reload_micgeom_button.on_click(update_micgeom_options_callback)

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

# DataTable
columns = [TableColumn(field='channel', title='channel'),
            TableColumn(field='calibvalue', title='calibvalue', editor=NumberEditor()),
           TableColumn(field='caliblevel', title='caliblevel', editor=NumberEditor()),
           TableColumn(field='calibfactor', title='calibfactor', editor=NumberEditor()),]
calibTable = DataTable(source=calibCDS,columns=columns,width=600)

def _calibtable_callback():
    calibCDS.data = {"calibvalue":ch.calibdata[:,0],
                     "caliblevel":ch.calibdata[:,1],
                     "calibfactor":ch.calibfactor[:],
                     "channel":_get_channel_labels(labelSelect.value)}
def calibtable_callback():
    return doc.add_next_tick_callback(_calibtable_callback)
ch.on_trait_change(calibtable_callback,"calibdata")

# save calib button
savecal = Button(label="save to .xml",button_type="warning",width=200, height=60)
def save_calib_callback():
    if not calWidgets['name'].value:
        fname = Path("Measurement_App") / "metadata" / f"calibdata_{current_time()}.xml"
        calWidgets['name'].value = fname
    else:
        fname = calWidgets['name'].value
    ch.save()
savecal.on_click(save_calib_callback)

freqSlider = Slider(start=50, end=10000, value=CFREQ, 
                    step=1, title="Frequency",disabled=False)
#bfFilt.set_widgets(**{'band':freqSlider}) # 
csm.set_widgets(**{'center_freq':freqSlider})

wtimeSlider = Slider(start=0.0, end=0.25, value=WTIME, format="0[.]000",
                     step=0.0025, title="Time weighting (FAST: 0.125, SLOW: 1.0)",
                     disabled=False)
csm.set_widgets(**{'weight_time':wtimeSlider})

micsizeSlider = Slider(start=1, end=50, value=MICSIZE, 
                    step=0.5, title="Circle Size",disabled=False)
def update_micsizes(attr,old,new):
    global MICSIZE 
    MICSIZE = new
    MicGeomCDS.data['sizes'] = np.array([MICSIZE]*micGeo.num_mics)
micsizeSlider.on_change('value', update_micsizes)

# checkboxes # inline=True -> arange horizontally, False-> vertically
checkbox_micgeom = CheckboxGroup(labels=ch_names,
                                 active=[_ for _ in range(num_channels)],
                                 width=100,height=100,inline=False)

# Figures and Glyphs
amp_bar = amp_fig.vbar(x='channels', width=0.5, bottom=0,top='level', color='colors', source=ChLevelsCDS)
micgeom_fig.scatter(marker='circle', x='x',y='y', size='sizes', color='colors', source=MicGeomCDS)

# make image
dx = grid.x_max-grid.x_min
dy = grid.y_max-grid.y_min
width = 800
height = int(width * dy/dx+0.5)

beam_fig = figure(width=width, height=height,
                   tools = 'pan,wheel_zoom,save,reset')
if cam_enabled:
    beam_fig.image_rgba(image='image_data',
                        x=XCAM[0], y=XCAM[1], dw=XCAM[2], dh=XCAM[3],
                        source=cameraCDS)
bfImage = beam_fig.image(image='beamformer_data', x=grid.x_min, y=grid.y_min, dw=dx, dh=dy,
                #global_alpha=0.45,
                color_mapper=bfColorMapper,
                source=BeamfCDS)
beam_fig.toolbar.logo=None
if cam_enabled: 
    set_alpha_callback(bfImage)
# color_bar = ColorBar(color_mapper=bfColorMapper,label_standoff=12, 
#                      background_fill_color = '#f6f6f6',
#                      border_line_color=None, location=(0,0))
#beam_fig.add_layout(color_bar, 'right')


# =============================================================================
# # define bokeh widgets which should be disabled when display, recording or 
# # calibration runs
# =============================================================================
disable_obj_disp = [
        selectPerCallPeriod,select_micgeom,select_all_channels_button,
        checkbox_micgeom, *calfiltWidgets.values(), *calWidgets.values(),
        ]
disable_obj_rec = [
        ti_msmtime,checkbox_use_current_time,display_toggle, calib_toggle, 
        beamf_toggle
        ]
disable_obj_calib = [
        msm_toggle
        ]
disable_obj_beamf = [
        freqSlider,wtimeSlider,dynamicSlider,checkbox_autolevel_mode,
        checkbox_paint_mode
        ]
if sinus_enabled: 
    disable_obj_disp = append_disable_obj(disable_obj_disp)

widgets_disable =   {'msm': disable_obj_rec,
                     'display': disable_obj_disp,
                     'calib' : disable_obj_calib,
                     'beamf' : disable_obj_beamf}

widgets_enable =    {'msm': [],
                     'display': [calib_toggle,msm_toggle,beamf_toggle],
                     'calib' : [],
                     'beamf' : [freqSlider,wtimeSlider,dynamicSlider,
                                checkbox_autolevel_mode,checkbox_paint_mode]}
# =============================================================================
# Callbacks
# =============================================================================
# small functions
def current_time():
    return datetime.now().isoformat('_').replace(':', '-').replace('.', '_') # for timestamp filename

# non bokeh functions
def get_active_channels():
    if DEVICE == 'typhoon' or DEVICE == 'tornado':
        ch = [inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]
    else:
        ch = checkbox_micgeom.active   
    ch.sort() 
    return ch

def get_numsamples():
    if ti_msmtime.value == '-1' or  ti_msmtime.value == '':
        return -1
    else:
        return int(float(ti_msmtime.value)*inputSignalGen.sample_freq)

# callback functions
def dynamic_slider_callback(attr, old, new):
    if not checkbox_autolevel_mode.active:
        (bfColorMapper.low, bfColorMapper.high) = new
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
  
def select_micgeom_callback(attr, old, new):
    MicGeomCDS.data = {'x':micGeo.pos[0,:],'y':micGeo.pos[1,:],
                       'sizes':np.array([MICSIZE]*micGeo.num_mics),
                       'channels':get_active_channels(),
                       'colors': [COLOR[1]]*micGeo.num_mics}
select_micgeom.on_change('value',select_micgeom_callback)

def select_all_channels_callback():
    checkbox_micgeom.active=[_ for _ in range(len(checkbox_micgeom.labels))]
select_all_channels_button.on_click(select_all_channels_callback)

def checkbox_micgeom_callback(attr, old, new):
    if micGeo.num_mics > 0:
        MicGeomCDS.data['channels'] = get_active_channels()
checkbox_micgeom.on_change('active',checkbox_micgeom_callback)    

def checkbox_use_current_time_callback(attr,old,new):
    if new == []:
        disable_obj_rec.append(ti_savename)
        ti_savename.disabled = False
    elif new == [0]:
        if ti_savename in disable_obj_rec:
            disable_obj_rec.remove(ti_savename)
        ti_savename.disabled = True
checkbox_use_current_time.on_change('active', checkbox_use_current_time_callback)

def checkbox_autolevel_mode_callback(arg):
    if not arg:
        (bfColorMapper.low, bfColorMapper.high) = dynamicSlider.value
        
def savename_callback(attr,old,new):
    wh5.name = TDPATH / f"{new}.h5"
ti_savename.on_change("value", savename_callback)

def widget_activation_callback(mode,isSet):
    for widget in widgets_disable[mode]: widget.disabled = isSet
    for widget in widgets_enable[mode]: widget.disabled = bool(1-isSet)
    
def change_mode(toggle,mode,isSet):    
    global MODECOLOR, CLIPCOLOR
    toggle.active = isSet
    toggle.label = toggle_labels[(mode,isSet)]
    widget_activation_callback(mode,isSet) 
    if not mode == "beamf":
        MODECOLOR, CLIPCOLOR = plot_colors[(mode,isSet)]

def displaytoggle_handler(arg):
    global periodic_plot_callback, disp_threads # need to be global
    if arg:
        logger.info("start display...")
        inputSignalGen.collectsamples = True
        dispEvent = Event()
        dispEventThread = EventThread(
                post_callback=partial(change_mode,display_toggle,'display',False),
                pre_callback=partial(change_mode,display_toggle,'display',True),
                doc = doc,
                event=dispEvent)
        amp_thread = SamplesThread(
                    samplesGen=tioAvg.result(1),
                    splitterObj= splitter,
                    splitterDestination=timePow,
                    event=dispEvent,
                    buffer_size=BUFFERSIZE)
        disp_threads = [amp_thread,dispEventThread]
        [thread.start() for thread in disp_threads]
        periodic_plot_callback = doc.add_periodic_callback(update_app,
                                               int(selectPerCallPeriod.value))
    if not arg:
        inputSignalGen.collectsamples = False
        [thread.join() for thread in disp_threads] # wait maximum 2 seconds until finished 
        doc.remove_periodic_callback(periodic_plot_callback)
        logger.info("stopped display")
    
display_toggle.on_click(displaytoggle_handler)
    
def beamftoggle_handler(arg):
    global bf_thread,beamfEventThread # need to be global
    if arg:
        figureTabs.active = 2 # jump to beamformer window
        beamfEvent = Event()
        beamfEventThread = EventThread(
                post_callback=partial(change_mode,beamf_toggle,'beamf',False),
                pre_callback=partial(change_mode,beamf_toggle,'beamf',True),
                doc = doc,
                event=beamfEvent)
        bf_thread = SamplesThread(
                    samplesGen=get_bf_data(NBLOCKS),
                    splitterObj= splitter,
                    splitterDestination=csm,
                    buffer_size=1,
                    event=beamfEvent)        
        bf_thread.start()
        beamfEventThread.start()
        logger.info("start beamforming...")
    if not arg:
        bf_thread.breakThread = True
        bf_thread.join()
        beamfEventThread.join()
        logger.info("stopped beamforming")

beamf_toggle.on_click(beamftoggle_handler)

def msmtoggle_handler(arg):
    global wh5_thread
    if arg: # toggle button is pressed
        wh5.numsamples_write = get_numsamples()
        if checkbox_use_current_time.active == [0]: ti_savename.value = current_time()
        if sinus_enabled: # gather important informations from SINUS Messtechnik devices
            wh5.metadata = gather_metadata(devManager,devInputManager,inputSignalGen,iniManager,ch)
        wh5_event = Event()
        wh5_consumer = EventThread(
                post_callback=partial(change_mode,msm_toggle,'msm',False),
                pre_callback=partial(change_mode,msm_toggle,'msm',True),
                doc = doc,
                event=wh5_event)
        wh5_thread = SamplesThread(
                samplesGen=wh5.result(BLOCKSIZE),
                splitterObj=splitter,
                splitterDestination=wh5,
                buffer_size=BUFFERSIZE,
                event = wh5_event)
        wh5_thread.start()
        wh5_consumer.start()
        logger.info("recording...")
    if not arg:
        wh5.writeflag = False
        wh5_thread.join()
        logger.info("finished recording")
    
msm_toggle.on_click(msmtoggle_handler)

def calibtoggle_handler(arg):
    global calib_thread,calibEventThread # need to be global
    if arg:
        calibEvent = Event()
        calibEventThread = EventThread(
                post_callback=partial(change_mode,calib_toggle,'calib',False),
                pre_callback=partial(change_mode,calib_toggle,'calib',True),
                doc = doc,
                event=calibEvent)
        calib_thread = SamplesThread(
                samplesGen= ch.result(1),
                splitterObj= splitter,
                splitterDestination=fo_cal,
                buffer_size=BUFFERSIZE,
                event=calibEvent)
        calib_thread.start()
        calibEventThread.start()
        logger.info("calibrating...")
    if not arg:
        calib_thread.breakThread = True
        calib_thread.join()
        calibEventThread.join()
        logger.info("finished calibration...")

calib_toggle.on_click(calibtoggle_handler)

# functions
bfdata = {'data':np.array([])}
def get_bf_data(num):
    for temp in bf_used.result(num):
        bfdata['data'] = ac.L_p(temp.reshape(grid.shape)).T
        if bfview.active == 1:
            bfdata['data'] = bfdata['data'][::-1]
        yield

def update_amp_bar_plot():
    if tioAvg.data.data['data'].size > 0:
        levels = ac.L_p(tioAvg.data.data['data'].T)
        ChLevelsCDS.data['level'] =  levels
        ChLevelsCDS.data['colors'] = [MODECOLOR if val<CLIPVALUE else CLIPCOLOR for val in levels]
#                                            'channel': inputSignalGen.inchannels_}
def update_mic_geom_plot():
    global MICSIZE, CLIPVALUE
    if micGeo.num_mics > 0: 
        levels = np.array([ac.L_p(tioAvg.data.data['data'].T[i]) for i in sorted(checkbox_micgeom.active)]) # only take which are active
        MicGeomCDS.data['sizes'] = levels/levels.max()*MICSIZE
        MicGeomCDS.data['colors'] = [MODECOLOR if val<CLIPVALUE else CLIPCOLOR for val in levels]

def update_beamforming_plot():
    if bfdata['data'].size > 0:
        BeamfCDS.data['beamformer_data'] = [bfdata['data']]
        if checkbox_autolevel_mode.active:
            dynamicValue = (dynamicSlider.value[1] - dynamicSlider.value[0])
            maxValue = bfdata['data'].max()
            bfColorMapper.high = max(ClipSlider.value+dynamicValue, maxValue)
            bfColorMapper.low = max(ClipSlider.value, maxValue-dynamicValue)

if sinus_enabled:
    update_buffer_bar_plot = get_callbacks(inputSignalGen,iniManager,devManager,devInputManager,
                  ChLevelsCDS,checkbox_micgeom,amp_fig,
                  MicGeomCDS,micGeo,logger)

def update_app():  # only update figure when tab is active
    if figureTabs.active == 0: 
        update_amp_bar_plot()
    if figureTabs.active ==1:
        update_mic_geom_plot()
    if figureTabs.active == 2 and beamf_toggle.active: 
        update_beamforming_plot() 
    if sinus_enabled:
         update_buffer_bar_plot()


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
                row(reload_micgeom_button,mgWidgets['file']),
                mgWidgets['num_mics'],
                select_all_channels_button,
                checkbox_micgeom,
                width=250,
                )

gridCol = column(*rgWidgets.values(),width=200)

# Tabs
amplitudesTab = Panel(child=column(row(Spacer(width=25),cliplevel,Spacer(width=25),labelSelect),row(amp_fig, log.log_text)),title='Channel Levels')
micgeomTab = Panel(child=column(
    row(column(row(Spacer(width=25),cliplevel,Spacer(width=15),micsizeSlider,Spacer(width=15),geomview),micgeom_fig),Spacer(width=30, height=1000),mgWidgetCol)),title='Microphone Geometry')
beamformTab = Panel(child=column(
                        row(beam_fig,Spacer(width=30, height=1000),gridCol,Spacer(width=20, height=1000),
                        column(bfview, freqSlider, wtimeSlider, dynamicSlider,
                         ClipSlider,checkbox_autolevel_mode,*camWidgets,
                         width=200)
                         #checkbox_paint_mode
                         ),
                        ),title='Beamforming')
calibrationTab = Panel(child=calCol, title="Calibration")
figureTabs = Tabs(tabs=[
    amplitudesTab,
    micgeomTab,
    beamformTab,
    calibrationTab
    ],width=850)

left_column = column(display_toggle,
                     ti_savename,checkbox_use_current_time,
                     ti_msmtime,msm_toggle,calib_toggle,
                     beamf_toggle,selectPerCallPeriod,
                     Spacer(width=250, height=10))

if sinus_enabled:
    # Additional Panel when SINUS Messtechnik API is used
    teds_component = get_teds_component(devInputManager,logger)
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
        ChLevelsCDS.data = {'channels':ticker,'level': np.zeros(inputSignalGen.num_channels)}
        amp_fig.xaxis.ticker = ticker
        checkbox_micgeom.labels = [str(_) for _ in range(inputSignalGen.num_channels)]
        checkbox_micgeom.active = [_ for _ in range(inputSignalGen.num_channels)]
        if micGeo.num_mics > 0:
            MicGeomCDS.data = {'x':micGeo.pos[0,:],'y':micGeo.pos[1,:],
                    'sizes':np.array([7]*micGeo.num_mics),
                    'channels':[str(_) for _ in checkbox_micgeom.active]} 
    device_select.on_change('value',device_update)

right_column = column(figureTabs)

layout = column(row(Spacer(width=1400),exit_button),row(Spacer(width=20, height=1000),
    left_column,
    Spacer(width=20, height=1000),
    right_column,
    ),
)
doc.add_root(layout)
doc.title = "Measurement App"
