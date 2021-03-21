# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
app can be started with:
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
    from cam import cameraCDS, camWidgets, set_camera_callback, set_alpha_callback
except:
    cam_enabled=False
    camWidgets = []
from datetime import datetime
from time import time
from threading import Event
from functools import partial
from collections import deque
import argparse
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, ColorBar, LinearColorMapper
from bokeh.models.widgets import Div, Select,TextInput,Button,CheckboxGroup,Tabs,Panel,Slider
from bokeh.layouts import column,row
from acoular import TimePower, TimeAverage, L_p, MicGeom, FiltOctave, \
SteeringVector, BeamformerTime,  SampleSplitter, BeamformerBase, WriteH5
from acoular_future import CSMInOut, BeamformerFreqTime
from SamplesProcessor import SamplesThread,EventThread,LastInOut
from spectacoular import RectGrid,CalibHelper,FiltOctaveLive,TimeInOutPresenter
from interfaces import get_interface
from layout import log_text_toggles, plot_colors, toggle_labels,micgeom_fig, \
amp_fig, selectPerCallPeriod, checkbox_use_current_time, bfColorMapper,ampColorMapper, \
select_all_channels_button, msm_toggle, display_toggle,beamf_toggle,calib_toggle,\
text_user_info, dynamicSlider, checkbox_paint_mode, checkbox_autolevel_mode, ClipSlider,\
  COLOR,CLIPVALUE

doc = curdoc()
if cam_enabled: set_camera_callback(doc)
parser = argparse.ArgumentParser()
parser.add_argument(
  '--device',
  type=str,
  default="phantom",
  choices=["uma16","tornado","typhoon","phantom","apollo"],
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
TDPATH = os.path.join(APPFOLDER,"td/")
if not os.path.exists(TDPATH): 
    os.mkdir(TDPATH)
BANDWIDTH = 3
MAXMSG = 20 # maximum number of messages to display in GUI
MICSCALE = 7
CFREQ = 4000 
BUFFERSIZE = 400
NBLOCKS = 5 # number of blocks after which to do beamforming
WTIME = 0.025
XCAM = (-0.5,-0.375,1.,0.75)

# =============================================================================
# load device
# =============================================================================
sinus_enabled=False
if DEVICE == 'uma16':
    mg_file = 'minidsp_uma16.xml'
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.numchannels)]
    grid = RectGrid( x_min=-0.15, x_max=0.15, y_min=-0.15, y_max=0.15, z=0.2, increment=0.01)
elif DEVICE == 'phantom':
    mg_file = 'array_64.xml'
    inputSignalGen = get_interface(DEVICE)
    ch_names = [str(_) for _ in range(inputSignalGen.numchannels)]
    grid = RectGrid( x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=.3, increment=0.01)
else: # otherwise it must be sinus
    try:
        import sinus
        sinus_enabled=True
    except:
        raise NotImplementedError("sinus module can not be imported")
    from sinus_dev import get_interface, append_left_column,append_disable_obj,\
        get_callbacks
    mg_file = 'tub_vogel64.xml'
    iniManager, devManager, devInputManager,inputSignalGen = get_interface(DEVICE,SYNCORDER)
    ch_names = inputSignalGen.inchannels_
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

# DataTable
from bokeh.models.widgets import TableColumn,NumberEditor,DataTable
columns = [TableColumn(field='calibvalue', title='calibvalue', editor=NumberEditor()),
           TableColumn(field='caliblevel', title='caliblevel', editor=NumberEditor())]
calibCDS = ColumnDataSource(data={"calibvalue":[],"caliblevel":[]})
calibTable = DataTable(source=calibCDS,columns=columns)

def _calibtable_callback():
    calibCDS.data = {"calibvalue":ch.calibdata[:,0],
                     "caliblevel":ch.calibdata[:,1]}
calibtable_callback = lambda: doc.add_next_tick_callback(_calibtable_callback)
ch.on_trait_change(calibtable_callback,"calibdata")

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


#
freqSlider = Slider(start=50, end=10000, value=CFREQ, 
                    step=1, title="Frequency",disabled=False)
bfFilt.set_widgets(**{'band':freqSlider}) # 
f.set_widgets(**{'center_freq':freqSlider})

wtimeSlider = Slider(start=0.0, end=0.25, value=WTIME, format="0[.]000",
                     step=0.0025, title="Time weighting (FAST: 0.125, SLOW: 1.0)",
                     disabled=False)
f.set_widgets(**{'weight_time':wtimeSlider})

# checkboxes # inline=True -> arange horizontally, False-> vertically
checkbox_micgeom = CheckboxGroup(labels=ch_names,
                                 active=[_ for _ in range(NUMCHANNELS)],
                                 width=100,height=100,inline=False)

# Figures 
amp_bar = amp_fig.vbar(x='channels', width=0.5, bottom=0,top='level', 
                   color={'field': 'level', 'transform': ampColorMapper},
                   source=ChLevelsCDS)

mgColorMapper = LinearColorMapper(palette=[COLOR[0],COLOR[10]], low=0.,high=CLIPVALUE*2/MICSCALE)
micgeom_fig.circle(x='x',y='y', size='sizes',
                   color={'field': 'sizes', 'transform': mgColorMapper},
                   source=MicGeomCDS)

# make image
dx = grid.x_max-grid.x_min
dy = grid.y_max-grid.y_min
width = 800
height = int(width * dy/dx+0.5)

beam_fig = figure(plot_width=width, plot_height=height,
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
if cam_enabled: set_alpha_callback(bfImage)
# color_bar = ColorBar(color_mapper=bfColorMapper,label_standoff=12, 
#                      background_fill_color = '#2F2F2F',
#                      border_line_color=None, location=(0,0))
#beam_fig.add_layout(color_bar, 'right')




# =============================================================================
# # define bokeh widgets which should be disabled when display, recording or 
# # calibration runs
# =============================================================================
disable_obj_disp = [
        selectPerCallPeriod,select_micgeom,select_all_channels_button,
        checkbox_micgeom
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
txt_buffer = deque([],maxlen=MAXMSG)

# small functions
current_time = lambda: datetime.now().isoformat('_').replace(':','-').replace('.','_') # for timestamp filename
stamp = lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S')+": " # for timestamp log
to_txt_buffer = lambda text: txt_buffer.appendleft(stamp(time())+text)

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

# def checkbox_paint_mode_callback(arg):
#     if arg == []:
#         f.accumulate = False
#     elif arg == [0]:
#         f.accumulate = True
# checkbox_paint_mode.on_click(checkbox_paint_mode_callback)

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

def widget_activation_callback(mode,isSet):
    for widget in widgets_disable[mode]: widget.disabled = isSet
    for widget in widgets_enable[mode]: widget.disabled = bool(1-isSet)
    
def change_mode(toggle,mode,isSet):    
    print("change mode",mode, isSet)
    toggle.active = isSet
    to_txt_buffer(log_text_toggles[(mode,isSet)])
    toggle.label = toggle_labels[(mode,isSet)]
    widget_activation_callback(mode,isSet)   
    if plot_colors[(mode,isSet)]:
        ampColorMapper.palette = plot_colors[(mode,isSet)]
        mgColorMapper.palette = plot_colors[(mode,isSet)]

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
        beamfEventThread.join()

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
        calibEventThread.join()

calib_toggle.on_click(calibtoggle_handler)

# procesampSpliting functions
bfdata = {'data':np.array([])}
def get_bf_data(num):
    for temp in bf_used.result(num):
        bfdata['data'] = L_p(temp.reshape(grid.shape)).T #L_p(synthetic(temp,f.fftfreq(),bfFilt.band,1))
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
        BeamfCDS.data['beamformer_data'] = [bfdata['data'][:,::-1]]
        if checkbox_autolevel_mode.active:
            dynamicValue = (dynamicSlider.value[1] - dynamicSlider.value[0])
            maxValue = bfdata['data'].max()
            bfColorMapper.high = max(ClipSlider.value+dynamicValue, maxValue)
            bfColorMapper.low = max(ClipSlider.value, maxValue-dynamicValue)

if sinus_enabled:
    update_buffer_bar_plot = get_callbacks(inputSignalGen,iniManager,devManager,devInputManager,
                  to_txt_buffer,ChLevelsCDS,checkbox_micgeom,amp_fig,
                  MicGeomCDS,micGeo)

def update_app():  # only update figure when tab is active
    if figureTabs.active == 0: 
        update_amp_bar_plot()
    if figureTabs.active ==1:
        update_mic_geom_plot()
    if figureTabs.active == 2 and beamf_toggle.active: 
        update_beamforming_plot() 
    if sinus_enabled:
         update_buffer_bar_plot()

def periodic_update_log():
    text_user_info.text = "\n".join(msg for msg in txt_buffer)


# =============================================================================
#  Set Up Bokeh Document Layout
# =============================================================================
emptyspace = Div(text='',width=20, height=1000) # just for horizontal spacing
emptyspace1 = Div(text='',width=30, height=1000) # just for horizontal spacing
emptyspace2 = Div(text='',width=250, height=30) # just for vertical spacing
emptyspace3 = Div(text='',width=250, height=10) # just for vertical spacing

# Columns
# calWidgets['calibdata'].height = 750
calCol = row(calibTable, emptyspace, column(
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
                        column(freqSlider,wtimeSlider,dynamicSlider,
                         ClipSlider,checkbox_autolevel_mode,*camWidgets)
                         #checkbox_paint_mode
                         )
                        ),title='Beamforming')
calibrationTab = Panel(child=calCol, title="Calibration")
figureTabs = Tabs(tabs=[amplitudesTab,micgeomTab,beamformTab,calibrationTab],width=850)
logTab = Tabs(tabs=[Panel(child=text_user_info, title="Log")],width=250)

left_column = column(emptyspace2, display_toggle,
                     ti_savename,checkbox_use_current_time,
                     ti_msmtime,msm_toggle,calib_toggle,
                     beamf_toggle,selectPerCallPeriod,
                     emptyspace3,logTab)
if sinus_enabled: append_left_column(left_column)
right_column = column(figureTabs)

layout = row(emptyspace,left_column,emptyspace,right_column,)
doc.add_root(layout)
doc.add_periodic_callback(periodic_update_log,500)
doc.title = "Measurement App"
