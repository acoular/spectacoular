#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
import os
from numpy import zeros, array, arange
from bokeh.models import ColumnDataSource,Spacer
from bokeh.models.widgets import Button, Select, Div, TableColumn, DataTable,TextInput
from bokeh.plotting import figure
from bokeh.models.ranges import Range1d
from bokeh.layouts import column,row
from sinus import SINUSDeviceManager, SINUSAnalogInputManager, \
SinusSamplesGenerator, ini_import, get_dev_state, change_device_status, SINUS
from datetime import datetime

current_time = lambda: datetime.now().isoformat('_').replace(':','-').replace('.','_') # for timestamp filename

APPFOLDER =os.path.dirname(os.path.abspath( __file__ ))
CONFPATH = os.path.join(APPFOLDER,"config_files/")
BUFFBAR_ARGS = {'width':280,  'height':50}
DEV_SERIAL_NUMBERS = {'tornado': ['10142', '10112', '10125', '10126'],
                        'typhoon': [
                                '10092','10095','10030','10038',
                                '10115','10116','10118','10119',
                                '10120','10123',
                                ],
                        'apollo11283': ['11283']}

BufferBarCDS = ColumnDataSource({'y':['buffer'],'filling':zeros(1)}) 

tedscolumns = [
            TableColumn(field='channel', title='Channel',width=800),
            TableColumn(field='serial', title='SensorSerNo',width=800),
            TableColumn(field='sensitivity', title='SensorSensitivity',width=800),
            #TableColumn(field='wiredata', title='1_Wire_Data',width=800),
            TableColumn(field='calibdate', title='CalibDate',width=800),
            #TableColumn(field='calibperiod', title='CalibPeriod',width=800),
            #TableColumn(field='chipserial', title='ChipSerNo',width=800),
            TableColumn(field='manufacturer', title='Manufacturer',width=1800),
            TableColumn(field='sensorversion', title='SensorVersion',width=800),
            #TableColumn(field='tedstemp', title='TEDS_Template',width=800),
            ]
tedsCDS = ColumnDataSource(data={
            "channel":[],
            "serial":[],
            "sensitivity":[],
            #"wiredata":[],
            "calibdate":[],
            "calibperiod":[],
            "chipserial":[],
            "manufacturer":[],
            "sensorversion":[],
            #"tedstemp":[], 
            })
tedsTable = DataTable(source=tedsCDS,columns=tedscolumns,width=1200)
tedsSavename = TextInput(value="", title="Filename:",disabled=False, width=500)

# Buttons
settings_button = Button(label="Load Setting",disabled=False)

# Open Close Status Section
open_device_button = Button(label="Open Device",disabled=False,button_type="primary",width=175,height=50)
close_device_button = Button(label="Close Device",disabled=False,button_type="danger",width=175,height=50)
reload_device_status_button = Button(label="↻",disabled=False,width=40,height=40)
load_teds_button = Button(label="get TEDS",width=200,height=60,button_type="primary")
save_teds_button = Button(label="save to .csv",width=200,height=60,button_type="warning")

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
                  ChLevelsCDS,checkbox_micgeom,amp_fig,
                  MicGeomCDS,micGeo,logger):
    
    def single_update_settings():
        ticker = list(arange(1,inputSignalGen.num_channels+1))
        ChLevelsCDS.data = {'channels':ticker,'level': zeros(inputSignalGen.num_channels)}
        amp_fig.xaxis.ticker = ticker
        amp_fig.xaxis.major_label_overrides = {str(ticker[i]): inputSignalGen.inchannels_[i] for i in range(inputSignalGen.num_channels)}
        checkbox_micgeom.labels = inputSignalGen.inchannels_
        checkbox_micgeom.active = [_ for _ in range(inputSignalGen.num_channels)]
        buffer_bar.x_range=Range1d(0,int(devManager.BlockCount[0]))
        if micGeo.num_mics > 0:
            MicGeomCDS.data = {'x':micGeo.mpos[0,:],'y':micGeo.mpos[1,:],
                    'sizes':array([7]*micGeo.num_mics),
                    'channels':[inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]} 

    #
    def settings_callback():
        logger.info("load settings ...")
        try:
            iniManager.get_data(devManager,devInputManager,inputSignalGen)
            [obj.set_settings() for obj in [devManager,devInputManager]]
        except Exception as e_text: 
            logger.error("{}".format(e_text))
            return
        logger.info("set settings ok!")
        single_update_settings()
        status_text.text = f"Device Status: {get_dev_state()}"
        
    settings_button.on_click(settings_callback)  
    
    def select_setting_callback(attr, old, new):
        iniManager.from_file = os.path.join(CONFPATH,new)
    select_setting.on_change('value',select_setting_callback)    
    return update_buffer_bar_plot

def get_interface(device, syncorder=[]):
    if syncorder: 
        devManager = SINUSDeviceManager(orderdevices = syncorder)
    elif not syncorder:
        devManager = SINUSDeviceManager(orderdevices = DEV_SERIAL_NUMBERS[device])
        
    devInputManager = SINUSAnalogInputManager()
    inputSignalGen = SinusSamplesGenerator(manager=devInputManager,
                                           inchannels=devInputManager.namechannels)
    iniManager = ini_import()
    return iniManager, devManager,devInputManager,inputSignalGen

def get_teds_component(devInputManager, logger):
    """Returns the button and table widget that provides the TEDS data.
    Necessary callbacks will be set up and implemented by this function.

    Parameters
    ----------
    inputSignalGen : instance
        class instance from sinus python module
    """
    # activate the detectTEDS functionality
    def load_teds_callback():
        logger.info("detect TEDS ...")
        if not 'None' in devInputManager.DetectTEDS: # force reload of TEDS data if it was already loaded
            devInputManager.DetectTEDS = ['None']  
            devInputManager.set_settings()     
        devInputManager.DetectTEDS = ['DetectTEDS']
        devInputManager.set_settings()    
        tedsCDS.data = { # update DataTable ColumnDataSource
            'channel' : [c for c in devInputManager.namechannels],  
            'serial' : [SINUS.Get(str(c),'TEDSData','SensorSerNo') for c in devInputManager.namechannels],
            'sensitivity' : [SINUS.Get(str(c),'TEDSData','SensorSensitivity') for c in devInputManager.namechannels],
            #'wiredata' : [SINUS.Get(str(c),'TEDSData','1_Wire_Data') for c in devInputManager.namechannels],
            'calibdate' : [SINUS.Get(str(c),'TEDSData','CalibDate') for c in devInputManager.namechannels],
            'calibperiod' : [SINUS.Get(str(c),'TEDSData','CalibPeriod') for c in devInputManager.namechannels],
            'chipserial' : [SINUS.Get(str(c),'TEDSData','ChipSerNo') for c in devInputManager.namechannels],
            'manufacturer' : [SINUS.Get(str(c),'TEDSData','Manufacturer') for c in devInputManager.namechannels],
            'sensorversion' : [SINUS.Get(str(c),'TEDSData','SensorVersion') for c in devInputManager.namechannels],
            #'tedstemp' : [SINUS.Get(str(c),'TEDSData','TEDS_Template') for c in devInputManager.namechannels],
        }
        print(tedsCDS.data)
        logger.info("detect TEDS finished")

    def save_csv_callback():
        import csv
        if not tedsSavename.value:
            fname = os.path.join("Measurement_App","metadata",f"TEDSdata_{current_time()}.csv")
            tedsSavename.value = fname
        else:
            fname = tedsSavename.value
        with open(fname, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile,  dialect='excel')
            csvwriter.writerow(tedsCDS.data.keys())
            rows = [[list(v)[i] for v in tedsCDS.data.values()] for i in range(len(list(tedsCDS.data.values())[0]))]
            for values in rows:
               csvwriter.writerow(values)
    # set up callback
    load_teds_button.on_click(load_teds_callback)
    save_teds_button.on_click(save_csv_callback)
    ur = row(load_teds_button,save_teds_button,tedsSavename)
    return column(Spacer(height=15),ur,Spacer(height=15),tedsTable)


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

def gather_metadata(devManager,devInputManager,inputSignalGen,iniManager,calibHelper):
    meta = {
        'config_file' : [iniManager.from_file],
        'pci_synchronization' : devManager.orderdevices,
        'generic_sensitivity' : inputSignalGen.sensval_,
        'input_channel_names' : inputSignalGen.inchannels_,
    }
    for key,value in tedsCDS.data.items(): # add TEDS information
        meta['TEDS_'+key] = value
    for property in devInputManager.properties['settable']:
        meta['AnalogInput_'+property] = eval(f"devInputManager.{property}")
    if calibHelper.calibdata.size > 0:
        meta['calib_value'] = calibHelper.calibdata[0,:]
        meta['calib_level'] = calibHelper.calibdata[1,:]
        meta['calib_factor'] = calibHelper.calibfactor[:]
    return meta
