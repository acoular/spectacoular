# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
app needs to be started by:
bokeh serve --show Measurement_App --args --argName=argValue

# Processing / Acoular
#
#                                    |-> TimePower -> TimeAverage -> Amplitude Bar
#                                    |-> FiltOctave ->  TimePower -> TimeAverage -> Calibration    
# SamplesGenerator -> SampleSplitter |-> LastInOut -> BeamformerTime -> FiltOctave -> TimePower -> TimeAverage -> Beamforming
#                                    |-> WriteH5   

In case of SINUS Devices:
if sync order of pci cards should be specified use
bokeh serve --show Measurement_App --args --device=typhoon --syncorder SerialNb1 SerialNb2 ...

"""
import os
import numpy as np 
try:
    import cv2
    cam_enabled=True
    from cam import update_camera, cameraCDS
except:
    cam_enabled=False
from datetime import datetime
from time import time
from threading import Event
from functools import partial
from collections import deque
import argparse
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, ColorBar
from bokeh.models.widgets import Div, Select,TextInput,Button,CheckboxGroup,Tabs,Panel,Slider
from bokeh.layouts import column,row
from bokeh.models.ranges import Range1d
# acoular imports
from acoular import TimePower, TimeAverage, L_p, MicGeom, \
FiltOctave, SteeringVector, BeamformerTime,  SampleSplitter, BeamformerBase, WriteH5
from acoular_future import CSMInOut, BeamformerFreqTime
from SamplesProcessor import SamplesThread,EventThread,LastInOut
from spectacoular import RectGrid,CalibHelper,FiltOctaveLive,TimeInOutPresenter
#local imports
from interfaces import get_interface
from layout import MODE_COLORS, micgeom_fig,amp_fig,buffer_bar,\
selectPerCallPeriod, checkbox_use_current_time, \
select_setting, bfColorMapper,ampColorMapper, \
settings_button,select_all_channels_button, msm_toggle, display_toggle,beamf_toggle,\
calib_toggle,text_user_info, dynamicSlider,checkbox_use_camera,  \
checkbox_paint_mode, checkbox_autolevel_mode, ClipSlider

parser = argparse.ArgumentParser()
parser.add_argument(
  '--device',
  type=str,
  default="phantom",
  choices=["uma16","tornado","typhoon","phantom"],
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
APPFOLDER =os.path.dirname(os.path.abspath( __file__ ))
MGEOMPATH = os.path.join(APPFOLDER,"micgeom/")
CONFPATH = os.path.join(APPFOLDER,"config_files/")
TDPATH = os.path.join(APPFOLDER,"td/")
BANDWIDTH = 3
MAXMSG = 20 # maximum number of messages to display in GUI
MICSCALE = 7
CFREQ = 4000 
BUFFERSIZE = 400
NBLOCKS = 5 # number of blocks after which to do beamforming
WTIME = 0.025
XCAM = (-0.5,-0.375,1.,0.75)

# =============================================================================
#
# =============================================================================
if DEVICE == 'uma16':
    mg_file = 'minidsp_uma16.xml'
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.numchannels)]
    grid = RectGrid( x_min=-0.15, x_max=0.15, y_min=-0.15, y_max=0.15, z=0.2, increment=0.01)
    #x_grid = (-0.2,0.2,-0.2,0.2,0.3)
elif DEVICE == 'phantom':
    mg_file = 'array_64.xml'
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.numchannels)]
    grid = RectGrid( x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=.3, increment=0.01)
elif DEVICE == 'tornado' or DEVICE == 'typhoon':
    mg_file = 'tub_vogel64.xml'
    iniManager, devManager, devInputManager,inputSignalGen = get_interface(DEVICE,SYNCORDER)
    ch_names = inputSignalGen.inchannels_
    micGeo = MicGeom(from_file = os.path.join(MGEOMPATH,mg_file)) 
    grid = RectGrid( x_min=-0.75, x_max=0.75, y_min=-0.5, y_max=0.5, z=1.3, increment=0.015)
NUMCHANNELS = inputSignalGen.numchannels

micGeo = MicGeom(from_file = os.path.join(MGEOMPATH,mg_file))
# Spplitting of incoming samples
sampSplit = SampleSplitter(source = inputSignalGen, buffer_size=BUFFERSIZE)
# ProcesampSpliting display Mode
timePow = TimePower(source=sampSplit)
timePowAvg = TimeAverage(source=timePow,naverage=BLOCKSIZE) 
tioAvg = TimeInOutPresenter(source=timePowAvg)
# ProcesampSpliting calib Mode
fo_cal = FiltOctave(source=sampSplit,band=1000.0)
tp_cal = TimePower(source=fo_cal)
ta_cal = TimeAverage(source=tp_cal,naverage=BLOCKSIZE)          
ch = CalibHelper(source = ta_cal)
# procesampSpliting rec Mode
wh5 = WriteH5(source=sampSplit)
# procesampSpliting beamforming Mode
stVec = SteeringVector(grid=grid, mics=micGeo, steer_type = 'true location')
lastOut = LastInOut(source=sampSplit)
#f = CSMInOut(source=lastOut, block_size=BLOCKSIZE)
f = CSMInOut(source=lastOut, block_size=BLOCKSIZE, center_freq= CFREQ, 
             band_width=BANDWIDTH, weight_time=WTIME)
bb = BeamformerBase(steer=stVec, r_diag=True, cached = False)
bfFreq = BeamformerFreqTime(source=f, beamformer = bb)
bfTime = BeamformerTime(source=lastOut, steer=stVec) 
bfFilt = FiltOctaveLive(source=bfTime, band=CFREQ)
bfPow = TimePower(source=bfFilt)
bfAvg = TimeAverage(source=bfPow, naverage = BLOCKSIZE)
bf_used = bfFreq

# =============================================================================
# spectacoular widgets
# =============================================================================

# get widgets of acoular objects
rgWidgets = grid.get_widgets()
zSlider = Slider(start=0.01, end=10.0, value=grid.z, step=.02, title="z",disabled=False)
grid.set_widgets(**{'z':zSlider})
rgWidgets['z'] = zSlider # replace textfield with slider

micgeomfiles = [os.path.join(MGEOMPATH,fname) for fname in os.listdir(MGEOMPATH)]
select_micgeom = Select(title="Select MicGeom:", value=os.path.join(MGEOMPATH,mg_file),
                                options=micgeomfiles+["None"])
micGeo.set_widgets(**{'from_file':select_micgeom})
mgWidgets = micGeo.get_widgets()
mgWidgets['from_file'] = select_micgeom
calWidgets = ch.get_widgets()

# =============================================================================
# bokeh
# =============================================================================
# Text Inputs
ti_msmtime = TextInput(value="10", title="Measurement Time [s]:")
ti_savename = TextInput(value="", title="Filename:",disabled=True)

# save calib button
savecal = Button(label="save calibration",button_type="warning")
savecal.on_click(lambda: ch.save())

# Columndatasources
ChLevelsCDS = ColumnDataSource(data = {'channels':list(np.arange(1,NUMCHANNELS+1)),
                                       'level':np.zeros(NUMCHANNELS)} )
MicGeomCDS = ColumnDataSource(data={'x':micGeo.mpos[0,:],'y':micGeo.mpos[1,:],
                                    'sizes':np.array([MICSCALE]*micGeo.num_mics),
                                    'channels':[str(_) for _ in range(micGeo.num_mics)]}) 
BeamfCDS = ColumnDataSource({'beamformer_data':[]})
BufferBarCDS = ColumnDataSource({'y':['buffer'],'filling':np.zeros(1)}) 

# Widgets     
select_setting.options=["None"]+os.listdir(CONFPATH)
#
freqSlider = Slider(start=50, end=10000, value=CFREQ, 
                    step=1, title="Frequency",disabled=False)
bfFilt.set_widgets(**{'band':freqSlider}) # 
f.set_widgets(**{'center_freq':freqSlider})

wtimeSlider = Slider(start=0.0, end=0.25, value=WTIME, format="0[.]000",
                     step=0.0025, title="Time weighting (FAST: 0.125, SLOW: 1.0)",
                     disabled=True)

# checkboxes # inline=True -> arange horizontally, False-> vertically
checkbox_micgeom = CheckboxGroup(labels=ch_names,
                                 active=[_ for _ in range(NUMCHANNELS)],
                                 width=100,height=100,inline=False)

# Figures 
amp_bar = amp_fig.vbar(x='channels', width=0.5, bottom=0,top='level', 
                   color={'field': 'level', 'transform': ampColorMapper},
                   source=ChLevelsCDS)

micgeom_fig.circle(x='x',y='y', size='sizes',
                   color={'field': 'sizes', 'transform': ampColorMapper},
                   source=MicGeomCDS)

barbuff = buffer_bar.hbar(y='y', height=0.9, left=0, right='filling',
                          source=BufferBarCDS)

# make image
dx = grid.x_max-grid.x_min
dy = grid.y_max-grid.y_min

width = 800
height = int(width * dy/dx+0.5)

beam_fig = figure(plot_width=width, plot_height=height,
                  x_range=[grid.x_min,grid.x_max], 
                  y_range=[grid.y_min,grid.y_max])
beam_fig.image(image='beamformer_data', x=grid.x_min, y=grid.y_min, dw=dx, dh=dy,
                global_alpha=0.45,
                color_mapper=bfColorMapper,
                source=BeamfCDS)
beam_fig.toolbar.logo=None
# color_bar = ColorBar(color_mapper=bfColorMapper,label_standoff=12, 
#                      background_fill_color = '#2F2F2F',
#                      border_line_color=None, location=(0,0))
#beam_fig.add_layout(color_bar, 'right')
if cam_enabled:
    beam_fig.image_rgba(image='image_data',
                        x=XCAM[0], y=XCAM[1], dw=XCAM[2], dh=XCAM[3],
                        source=cameraCDS)


# define bokeh widgets which should be disabled when display, recording or 
# calibration runs

disable_obj_disp = [
        selectPerCallPeriod,settings_button,
        select_micgeom,select_setting,
        select_all_channels_button,checkbox_micgeom
        ]

disable_obj_rec = [
        ti_msmtime,checkbox_use_current_time,
        display_toggle, calib_toggle, beamf_toggle
        ]

disable_obj_calib = [msm_toggle]

disable_obj_beamf = [
        freqSlider,wtimeSlider,dynamicSlider,checkbox_autolevel_mode,
        checkbox_paint_mode
        ]
# =============================================================================
# Basic callbacks
# =============================================================================
# This is important! Save curdoc() to make sure all threads
# see the same document.
doc = curdoc()

# Definitions
log_text_toggles =  {('msm',True): "collecting samples...",
                    ('msm',False): "stopped collecting samples.",
                    ('display',True): "display samples...",
                    ('display',False): "stopped to display samples.",
                    ('calib',True): "calibrating...",
                    ('calib',False): "stopped calibrating.",
                    ('beamf',True): "beamforming...",
                    ('beamf',False): "stopped beamforming."}

toggle_labels =     {('msm',False): "START MEASUREMENT",
                    ('msm',True): "STOP MEASUREMENT",
                    ('display',False): "start display",
                    ('display',True): "stop display",
                    ('calib',True): "stop calibration",
                    ('calib',False): "start calibration",
                    ('beamf',True): "stop beamforming",
                    ('beamf',False): "start beamforming"}

plot_colors =       {('msm',True): [MODE_COLORS['msm'],MODE_COLORS['msm']],
                    ('msm',False): [MODE_COLORS['display'],MODE_COLORS['display']],
                    ('display',True): [MODE_COLORS['display'],MODE_COLORS['display']],
                    ('display',False): [MODE_COLORS['display'],MODE_COLORS['display']],
                    ('calib',True): [MODE_COLORS['calib'],MODE_COLORS['calib']],
                    ('calib',False): [MODE_COLORS['display'],MODE_COLORS['display']],
                    ('beamf',True): [],
                    ('beamf',False): []}

widgets_disable =   {'msm': disable_obj_rec,
                     'display': disable_obj_disp,
                     'calib' : disable_obj_calib,
                     'beamf' : disable_obj_beamf}

widgets_enable =    {'msm': [],
                     'display': [calib_toggle,msm_toggle,beamf_toggle],
                     'calib' : [],
                     'beamf' : [freqSlider,wtimeSlider,dynamicSlider,
                                checkbox_autolevel_mode,checkbox_paint_mode]}

txt_buffer = deque([],maxlen=MAXMSG)

# small functions

current_time = lambda: datetime.now().isoformat('_').replace(':','-').replace('.','_') # for timestamp filename
stamp = lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S')+": " # for timestamp log
to_txt_buffer = lambda text: txt_buffer.appendleft(stamp(time())+text)
convert_table = lambda x: None if x == ' ' or x== '' or x==None else float(x)    

# non bokeh functions

def get_active_channels():
    if DEVICE == 'typhoon' or DEVICE == 'tornado':
        ch = [inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]
    else:
        ch = checkbox_micgeom.active    
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

def wtime_slider_callback(attr,old,new):
    f.weight_time = new

wtimeSlider.on_change('value',wtime_slider_callback)

def checkbox_paint_mode_callback(arg):
    if arg == []:
        f.accumulate = False
    elif arg == [0]:
        f.accumulate = True
checkbox_paint_mode.on_click(checkbox_paint_mode_callback)
  
def select_micgeom_callback(attr, old, new):
    MicGeomCDS.data = {'x':micGeo.mpos[0,:],'y':micGeo.mpos[1,:],
                       'sizes':np.array([MICSCALE]*micGeo.num_mics),
                       'channels':get_active_channels()}
select_micgeom.on_change('value',select_micgeom_callback)

def select_all_channels_callback():
    checkbox_micgeom.active=[_ for _ in range(len(checkbox_micgeom.labels))]
select_all_channels_button.on_click(select_all_channels_callback)

def checkbox_micgeom_callback(attr, old, new):
    if micGeo.num_mics > 0:
        MicGeomCDS.data['channels'] = get_active_channels()
checkbox_micgeom.on_change('active',checkbox_micgeom_callback)    

def checkbox_use_current_time_callback(arg):
    if arg == []:
        disable_obj_rec.append(ti_savename)
        ti_savename.disabled = False
    elif arg == [0]:
        if ti_savename in disable_obj_rec:
            disable_obj_rec.remove(ti_savename)
        ti_savename.disabled = True
checkbox_use_current_time.on_click(checkbox_use_current_time_callback)

def checkbox_autolevel_mode_callback(arg):
    if not arg:
        (bfColorMapper.low, bfColorMapper.high) = dynamicSlider.value
        
def savename_callback(attr,old,new):
    wh5.name = os.path.join(TDPATH,new+'.h5')
ti_savename.on_change("value", savename_callback)

def select_setting_callback(attr, old, new):
    iniManager.from_file = os.path.join(CONFPATH,new)
select_setting.on_change('value',select_setting_callback)

def mode_log_callback(mode,isSet):
    to_txt_buffer(log_text_toggles[(mode,isSet)])

def mode_label_callback(toggle,mode,isSet):
    toggle.label = toggle_labels[(mode,isSet)]
    
def widget_activation_callback(mode,isSet):
    for widget in widgets_disable[mode]: widget.disabled = isSet
    for widget in widgets_enable[mode]: widget.disabled = bool(1-isSet)
    
def color_callback(mode, isSet):
    if plot_colors[(mode,isSet)]:
        ampColorMapper.palette = plot_colors[(mode,isSet)]
        
def change_mode(toggle,mode,isSet):    
    print("change mode",mode, isSet)
    toggle.active = isSet
    mode_log_callback(mode,isSet)
    mode_label_callback(toggle,mode,isSet)
    widget_activation_callback(mode,isSet)   
    color_callback(mode, isSet)

def displaytoggle_handler(arg):
    global periodic_plot_callback, disp_threads # need to be global
    if arg:
        inputSignalGen.collectsamples = True
        dispEvent = Event()
        dispEventThread = EventThread(
                post_callback=partial(change_mode,display_toggle,'display',False),
                pre_callback=partial(change_mode,display_toggle,'display',True),
                doc = doc,
                event=dispEvent)
        amp_thread = SamplesThread(
                    samplesGen=tioAvg.result(1),
                    splitterObj= sampSplit,
                    splitterDestination=timePow,
                    event=dispEvent)
        disp_threads = [amp_thread,dispEventThread]
        [thread.start() for thread in disp_threads]
        periodic_plot_callback = doc.add_periodic_callback(update_app,
                                               int(selectPerCallPeriod.value))
    if not arg:
        inputSignalGen.collectsamples = False
        [thread.join() for thread in disp_threads] # wait maximum 2 seconds until finished 
        doc.remove_periodic_callback(periodic_plot_callback)
    
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
                    splitterObj= sampSplit,
                    splitterDestination=lastOut,
                    event=beamfEvent)        
        bf_thread.start()
        beamfEventThread.start()
    if not arg:
        bf_thread.breakThread = True
        bf_thread.join()
        print("bf thread finished")
        beamfEventThread.join()
        print("bf event thread finished")

beamf_toggle.on_click(beamftoggle_handler)

def msmtoggle_handler(arg):
    global wh5_thread
    if arg: # button is presampSplited
        wh5.numsamples_write = get_numsamples()
        if checkbox_use_current_time.active == [0]: ti_savename.value = current_time()
        wh5_event = Event()
        wh5_consumer = EventThread(
                post_callback=partial(change_mode,msm_toggle,'msm',False),
                pre_callback=partial(change_mode,msm_toggle,'msm',True),
                doc = doc,
                event=wh5_event)
        wh5_thread = SamplesThread(
                samplesGen=wh5.result(BLOCKSIZE),
                splitterObj=sampSplit,
                splitterDestination=wh5,
                event = wh5_event)
        wh5_thread.start()
        wh5_consumer.start()
    if not arg:
        wh5.writeflag = False
        wh5_thread.join()
    
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
                splitterObj= sampSplit,
                splitterDestination=fo_cal,
                event=calibEvent)
        calib_thread.start()
        calibEventThread.start()
    if not arg:
        calib_thread.breakThread = True
        calib_thread.join()
        print("calib thread finished")
        calibEventThread.join()
        print("calib event thread finished")

calib_toggle.on_click(calibtoggle_handler)

# procesampSpliting functions
bfdata = {'data':np.array([])}
def get_bf_data(num):
    for temp in bf_used.result(num):
        bfdata['data'] = L_p(temp)#L_p(synthetic(temp,f.fftfreq(),bfFilt.band,1))
        yield

def update_amp_bar_plot():
    if tioAvg.data.data['data'].size > 0:
        ChLevelsCDS.data['level'] =  L_p(tioAvg.data.data['data'].T)
#                                            'channel': inputSignalGen.inchannels_}
def update_mic_geom_plot():
    if micGeo.num_mics > 0: 
        mg_vals = [L_p(tioAvg.data.data['data'].T[i]) for i in checkbox_micgeom.active] # only take which are active
        MicGeomCDS.data['sizes'] = np.array(mg_vals)/MICSCALE

def update_beamforming_plot():
    if bfdata['data'].size > 0:
        BeamfCDS.data['beamformer_data'] = [((np.reshape(bfdata['data'],(grid.nxsteps,grid.nysteps))).T)[:,::-1]]
        if checkbox_autolevel_mode.active:
            dynamicValue = (dynamicSlider.value[1] - dynamicSlider.value[0])
            maxValue = bfdata['data'].max()
            bfColorMapper.high = max(ClipSlider.value+dynamicValue, maxValue)
            bfColorMapper.low = max(ClipSlider.value, maxValue-dynamicValue)

def update_app():  # only update figure when necesampSplitary
    if figureTabs.active == 0: 
        update_amp_bar_plot()
    if figureTabs.active ==1:
        update_mic_geom_plot()
    if figureTabs.active == 2 and beamf_toggle.active: 
        update_beamforming_plot() 
        if cam_enabled and checkbox_use_camera.active: update_camera()
    if DEVICE == 'tornado' or DEVICE == 'typhoon':
        update_buffer_bar_plot()

def periodic_update_log():
    text_user_info.text = "\n".join(msg for msg in txt_buffer)

if DEVICE == 'tornado' or DEVICE == 'typhoon':
    
    def update_buffer_bar_plot():
        BufferBarCDS.data['filling'] = np.array([inputSignalGen._pdiff_in])

    def settings_callback():
        to_txt_buffer("load settings ...")
        try:
            iniManager.get_data(devManager,devInputManager,inputSignalGen)
            [obj.set_settings() for obj in [devManager,devInputManager]]
        except Exception as e_text: 
            to_txt_buffer("{}".format(e_text))
            return
        to_txt_buffer("set settings ok!")
        single_update_settings()
        
    settings_button.on_click(settings_callback)  

    def single_update_settings():
        ticker = list(np.arange(1,inputSignalGen.numchannels+1))
        ChLevelsCDS.data = {'channels':ticker,'level': np.zeros(inputSignalGen.numchannels)}
        amp_fig.xaxis.ticker = ticker
        amp_fig.xaxis.major_label_overrides = {str(ticker[i]): inputSignalGen.inchannels_[i] for i in range(inputSignalGen.numchannels)}
        checkbox_micgeom.labels = inputSignalGen.inchannels_
        checkbox_micgeom.active = [_ for _ in range(inputSignalGen.numchannels)]
        # CalValsCDS.data = {'channels':[ _ for _ in inputSignalGen.inchannels_],
        #                'calib': ch.calib_value}
        buffer_bar.x_range=Range1d(0,int(devManager.BlockCount[0]))
        if micGeo.num_mics > 0:
            MicGeomCDS.data = {'x':micGeo.mpos[0,:],'y':micGeo.mpos[1,:],
                    'sizes':np.array([7]*micGeo.num_mics),
                    'channels':[inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]} 

# =============================================================================
#  Set Up Bokeh Document Layout
# =============================================================================
emptyspace = Div(text='',width=20, height=1000) # just for horizontal spacing
emptyspace1 = Div(text='',width=30, height=1000) # just for horizontal spacing
emptyspace2 = Div(text='',width=250, height=30) # just for vertical spacing
emptyspace3 = Div(text='',width=250, height=10) # just for vertical spacing

# Columns
calWidgets['calibdata'].height = 750
calCol = row(calWidgets['calibdata'], emptyspace, column(
                    savecal,calWidgets['name'], calWidgets['magnitude'],
                    calWidgets['delta'],width=300,height=400))
mgWidgetCol = column(mgWidgets['from_file'],mgWidgets['invalid_channels'],
                     mgWidgets['num_mics'])
channelsCol = column(mgWidgetCol,select_all_channels_button,checkbox_micgeom,
                                 width=300,height=400)
gridCol = column(*rgWidgets.values())

# Tabs
amplitudesTab = Panel(child=amp_fig,title='Channel Levels')
micgeomTab = Panel(child=column(row(micgeom_fig,emptyspace1,channelsCol)),title='Microphone Geometry')
beamformTab = Panel(child=column(
                        row(beam_fig,emptyspace1,gridCol,emptyspace,
                        column(
                         freqSlider,
                         wtimeSlider,
                         dynamicSlider,
                         ClipSlider,
                         checkbox_autolevel_mode,
                         checkbox_use_camera,
                         checkbox_paint_mode
                         ))
                        ),title='Beamforming')
calibrationTab = Panel(child=calCol, title="Calibration")
figureTabs = Tabs(tabs=[amplitudesTab,micgeomTab,beamformTab,calibrationTab],width=850)

logTab = Tabs(tabs=[Panel(child=text_user_info, title="Log")])

if DEVICE == 'tornado' or DEVICE == 'typhoon':
    left_column = column(emptyspace2,
                         select_setting,
                         settings_button,
                         display_toggle,
                         ti_savename,
                         checkbox_use_current_time,
                         ti_msmtime,
                         msm_toggle,
                         calib_toggle,
                         beamf_toggle,
                         buffer_bar,
                         selectPerCallPeriod,
                         emptyspace3,
                         logTab)
    
elif DEVICE == 'uma16' or DEVICE == 'phantom':
    left_column = column(emptyspace2,
                         display_toggle,
                         ti_savename,
                         checkbox_use_current_time,
                         ti_msmtime,
                         msm_toggle,
                         calib_toggle,
                         beamf_toggle,
                         selectPerCallPeriod,
                         emptyspace3,
                         logTab)    
    
right_column = column(figureTabs)

layout = row(emptyspace,left_column,emptyspace,right_column,)

doc.add_root(layout)
doc.add_periodic_callback(periodic_update_log,500)
doc.title = "Measurement App"
