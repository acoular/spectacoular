# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
import os
from numpy import zeros, array, arange
from bokeh.models import ColumnDataSource,Spacer
from bokeh.models.widgets import Button, Select, Div
from bokeh.plotting import figure
from bokeh.models.ranges import Range1d
from bokeh.layouts import column,row
from sinus import SINUSDeviceManager, SINUSAnalogInputManager, \
SINUSSamplesGenerator, ini_import, get_dev_state, change_device_status

APPFOLDER =os.path.dirname(os.path.abspath( __file__ ))
CONFPATH = os.path.join(APPFOLDER,"config_files/")
BUFFBAR_ARGS = {'plot_width':280,  'plot_height':50}
DEV_SERIAL_NUMBERS = {'tornado': ['10142', '10112', '10125', '10126'],
                        'typhoon': [
                                '10092','10095','10030','10038',
                                '10115','10116','10118','10119',
                                '10120','10123',
                                ],
                        'apollo11283': ['11283']}

BufferBarCDS = ColumnDataSource({'y':['buffer'],'filling':zeros(1)}) 

# Buttons
settings_button = Button(label="Load Setting",disabled=False)

# Open Close Status Section
open_device_button = Button(label="Open Device",disabled=False,button_type="primary",width=175,height=50)
close_device_button = Button(label="Close Device",disabled=False,button_type="danger",width=175,height=50)
reload_device_status_button = Button(label="↻",disabled=False,width=40,height=40)
status_text = Div(text="Device Status: ")
sinus_open_close = column(
    row(open_device_button, close_device_button),
    row(reload_device_status_button,status_text))

def get_device_mode_callback():
    dev_mode = get_dev_state()
    status_text.text = f"Device Status: {dev_mode}"
reload_device_status_button.on_click(get_device_mode_callback)

def open_device_callback():
    change_device_status('Open')
    dev_mode = get_dev_state()
    status_text.text = f"Device Status: {dev_mode}"
    
open_device_button.on_click(open_device_callback)

def close_device_callback():
    change_device_status('Config')
    dev_mode = get_dev_state()
    status_text.text = f"Device Status: {dev_mode}"
    
close_device_button.on_click(close_device_callback)

# Select Settings    
select_setting = Select(title="Select Settings:", value="None")
reload_settings_options = Button(label="↻",disabled=False,width=40)
select_setting.options=["None"]+os.listdir(CONFPATH)
def update_select_settings_options_callback():
    select_setting.options=["None"]+os.listdir(CONFPATH)
reload_settings_options.on_click(update_select_settings_options_callback)
select_settings_row = row(column(Spacer(height=15),reload_settings_options),select_setting)

# Buffer Bar
buffer_bar = figure(title="Buffer",y_range=['buffer'],x_range=(0,400),**BUFFBAR_ARGS)
buffer_bar.xgrid.visible = False
buffer_bar.ygrid.visible = False
buffer_bar.toolbar.logo = None
buffer_bar.toolbar_location = None
buffer_bar.axis.visible = False
buffer_bar.grid.visible = False
barbuff = buffer_bar.hbar(y='y', height=0.9, left=0, right='filling',
                          source=BufferBarCDS)

def get_callbacks(inputSignalGen,iniManager,devManager,devInputManager,
                  to_txt_buffer,ChLevelsCDS,checkbox_micgeom,amp_fig,
                  MicGeomCDS,micGeo):
    
    def single_update_settings():
        ticker = list(arange(1,inputSignalGen.numchannels+1))
        ChLevelsCDS.data = {'channels':ticker,'level': zeros(inputSignalGen.numchannels)}
        amp_fig.xaxis.ticker = ticker
        amp_fig.xaxis.major_label_overrides = {str(ticker[i]): inputSignalGen.inchannels_[i] for i in range(inputSignalGen.numchannels)}
        checkbox_micgeom.labels = inputSignalGen.inchannels_
        checkbox_micgeom.active = [_ for _ in range(inputSignalGen.numchannels)]
        buffer_bar.x_range=Range1d(0,int(devManager.BlockCount[0]))
        if micGeo.num_mics > 0:
            MicGeomCDS.data = {'x':micGeo.mpos[0,:],'y':micGeo.mpos[1,:],
                    'sizes':array([7]*micGeo.num_mics),
                    'channels':[inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]} 

    def update_buffer_bar_plot():
        BufferBarCDS.data['filling'] = array([inputSignalGen._pdiff_in])
    #
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
        dev_mode = get_dev_state()
        status_text.text = f"Device Status: {dev_mode}"
        
    settings_button.on_click(settings_callback)  
    
    def select_setting_callback(attr, old, new):
        iniManager.from_file = os.path.join(CONFPATH,new)
    select_setting.on_change('value',select_setting_callback)    
    return update_buffer_bar_plot

def get_interface(device,syncorder=[]):
    if syncorder: 
        DevManager = SINUSDeviceManager(orderdevices = syncorder)
    elif not syncorder:
        DevManager = SINUSDeviceManager(orderdevices = DEV_SERIAL_NUMBERS[device])
        
    DevInputManager = SINUSAnalogInputManager()
    InputSignalGen = SINUSSamplesGenerator(manager=DevInputManager,
                                           inchannels=DevInputManager.namechannels)
    IniManager = ini_import()
    return IniManager, DevManager,DevInputManager,InputSignalGen

def append_left_column(left_column):
    left_column.children.insert(1,sinus_open_close)
    left_column.children.insert(2,select_settings_row)
    left_column.children.insert(3, settings_button)
    left_column.children.insert(4,Spacer(height=20))
    left_column.children.insert(12, buffer_bar)
    
def append_disable_obj(disable_obj_disp):
    disable_obj_disp.append(select_setting)
    disable_obj_disp.append(settings_button)
    return disable_obj_disp