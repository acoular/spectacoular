import sys
import acoular as ac
import spectacoular as sp
from threading import Event
from functools import partial
from datetime import datetime
from threads import SamplesThread,EventThread
from layout import toggle_labels, plot_colors, button_height
from acoular_future.tprocess import MaskedChannels
from pathlib import Path
import numpy as np
from time import sleep

from bokeh.models import TabPanel as Panel, CustomJS, ColumnDataSource
from bokeh.layouts import column, Spacer, row, layout
from bokeh.models.widgets import Toggle, TextInput, CheckboxGroup, Select, Button, Div,\
    DataTable, TableColumn, NumberEditor, NumericInput, Slider
from bokeh.plotting import figure
from bokeh.models.ranges import Range1d
try:
    import sounddevice as sd
except:
    pass

BUFFERSIZE = 400

def current_time():
    return datetime.now().isoformat('_').replace(':', '-').replace('.', '_') # for timestamp filename

def _get_channel_labels(source, ltype='Number'):
    if ltype == 'Index':
        labels = [str(i) for i in range(source.num_channels)]
    elif ltype == 'Number':
        labels = [str(i+1) for i in range(source.num_channels)]
    elif ltype == 'Physical':
        labels = [ch.name for ch in source._enabled_analog_inputs]
    return labels


class MeasurementControl:

    def __init__(self, doc, source, logger, blocksize=1024, steer=None, cfreq=1000):
        self.modecolor = None
        self.clipcolor = None
        self.blocksize = blocksize
        self.doc = doc
        self.source = source
        self.splitter = ac.SampleSplitter(source = self.source)
        self.disp = sp.TimeOutPresenter(source=ac.Average(source=ac.TimePower(source=self.splitter),num_per_average=blocksize)) 
        self.msm = ac.WriteH5(source=self.splitter)
        self.calib = sp.CalibHelper(source = ac.Average(source=ac.TimePower(source=sp.FiltOctave(source=self.splitter,band=1000.0)),num_per_average=blocksize))
        if steer is not None:
            self.beamf = sp.TimeOutPresenter(source=ac.Average(source=ac.TimePower(source=sp.FiltOctave(source=ac.BeamformerTime(source=MaskedChannels(source=self.splitter), steer=steer), band=cfreq)), num_per_average = blocksize))
        self.logger = logger

        # create measurement toggle button
        self.display_toggle = Toggle(label="Display", active=False,button_type="primary", sizing_mode="stretch_width", height=button_height)
        self.msm_toggle = Toggle(label="MEASURE", active=False, disabled=True, button_type="danger", sizing_mode="stretch_width", height=button_height)
        self.calib_toggle = Toggle(label="Calibration", active=False,disabled=True,button_type="warning", sizing_mode="stretch_width", height=button_height)
        self.beamf_toggle = Toggle(label="Beamforming", active=False,disabled=True,button_type="warning", sizing_mode="stretch_width", height=button_height)
        # Others
        self.ti_msmtime = TextInput(value="10", title="Measurement Time [s]:")
        self.ti_savename = TextInput(value="", title="Filename:",disabled=True,
            description=f"Filename for the measurement data. Files are saved to {ac.config.td_dir}")
        self.current_time_checkbox = CheckboxGroup(labels=["use current time"], active=[0])
        self.update_period = Select(title="Select Update Period [ms]", value=str(50), options=["25","50","100", "200", "400","800"])
        self.exit_button = Button(label="Exit", button_type="danger", sizing_mode="stretch_width")

        # threads
        self._disp_threads = []
        self._view_callback_id = None

        # widgets disable / enable lists depending on mode
        self.widgets_disable =   {'msm': [self.ti_msmtime, self.current_time_checkbox, self.ti_savename, self.display_toggle, self.calib_toggle, self.beamf_toggle],
                            'display': [self.update_period], # maybe unfinished!
                            'calib' : [self.msm_toggle],
                            'beamf' : []
                            }

        self.widgets_enable =    {'msm': [],
                                'display': [self.calib_toggle, self.msm_toggle, self.beamf_toggle],
                                'calib': [],
                                'beamf': [],
                                         }
        self.set_callbacks()

    def get_num_samples(self):
        if self.ti_msmtime.value == '-1' or  self.ti_msmtime.value == '':
            return -1
        else:
            return int(float(self.ti_msmtime.value) * self.msm.sample_freq)

    def _change_mode(self, toggle, mode, active):
        # activate / deactivate toggle button    
        toggle.active = active
        toggle.label = toggle_labels[(mode, active)]
        # activate / deactivate associated widgets
        disabled = active
        for widget in self.widgets_disable[mode]: 
            widget.disabled = disabled
        for widget in self.widgets_enable[mode]: 
            widget.disabled = not disabled
        # change colors
        if not mode == "beamf":
            self.modecolor, self.clipcolor = plot_colors[(mode, active)]

    def checkbox_use_current_time_callback(self, attr,old,new):
        if new == []:
            self.widgets_disable['msm'].append(self.ti_savename)
            self.ti_savename.disabled = False
        elif new == [0]:
            if self.ti_savename in self.widgets_disable['msm']:
                self.widgets_disable['msm'].remove(self.ti_savename)
            self.ti_savename.disabled = True

    def savename_callback(self, attr,old,new):
        self.msm.name = Path(ac.config.td_dir) / f"{new}.h5"

    def exit_callback(arg):
        sleep(0.5)
        sys.exit()

    def displaytoggle_handler(self, arg):
        if arg:
            self.source.collectsamples = True
            dispEvent = Event()
            dispEventThread = EventThread(
                    pre_callback=partial(self._change_mode,self.display_toggle,'display',True),
                    post_callback=partial(self._change_mode,self.display_toggle,'display',False),
                    doc = self.doc,
                    event=dispEvent)
            amp_thread = SamplesThread(
                        gen=self.disp.result(1),
                        splitter= self.splitter,
                        register=self.disp.source.source,
                        register_args={
                            'buffer_size':BUFFERSIZE,
                            'buffer_overflow_treatment': 'none'
                        },
                        event=dispEvent
                    )
            self._disp_threads = [amp_thread, dispEventThread]
            for thread in self._disp_threads:
                thread.start() 
            self.logger.info("Display...")
        if not arg:
            self.source.collectsamples = False
            for thread in self._disp_threads:
                thread.join()
            self._disp_threads = []
            self.logger.info("stopped display")

    def msmtoggle_handler(self, arg):
        if arg: # toggle button is pressed
            self.msm.num_samples_write = self.get_num_samples()
            if self.current_time_checkbox.active == [0]: 
                self.ti_savename.value = current_time()
            # if sinus_enabled: # gather important informations from SINUS Messtechnik devices
            #     self.msm.metadata = gather_metadata(devManager,devInputManager,inputSignalGen,iniManager,ch)
            msm_event = Event()
            msm_consumer = EventThread(
                    post_callback=partial(self._change_mode, self.msm_toggle, 'msm', False),
                    pre_callback=partial(self._change_mode, self.msm_toggle, 'msm', True),
                    doc=self.doc,
                    event=msm_event)
            self._msm_thread = SamplesThread(
                    gen=self.msm.result(self.blocksize),
                    splitter=self.splitter,
                    register=self.msm,
                    register_args={
                        'buffer_size': BUFFERSIZE,
                        'buffer_overflow_treatment': 'error'
                    },
                    event=msm_event
                )
            self._msm_thread.start()
            msm_consumer.start()
            self.logger.info("recording...")
        if not arg:
            self.msm.writeflag = False
            self._msm_thread.join()
            self.logger.info("finished recording")
        
    def calibtoggle_handler(self, arg):
        if arg:
            self._calibEvent = Event()
            self._calibEventThread = EventThread(
                    post_callback=partial(self._change_mode,self.calib_toggle,'calib',False),
                    pre_callback=partial(self._change_mode,self.calib_toggle,'calib',True),
                    doc = self.doc,
                    event=self._calibEvent)
            self._calib_thread = SamplesThread(
                    gen= self.calib.result(1),
                    splitter= self.splitter,
                    register=self.calib.source.source.source,
                    register_args={
                        'buffer_size':BUFFERSIZE,
                        'buffer_overflow_treatment':'none'
                    },
                    event=self._calibEvent)
            self._calib_thread.start()
            self._calibEventThread.start()
            self.logger.info("calibrating...")
        if not arg:
            self._calib_thread.breakThread = True
            self._calib_thread.join()
            self._calibEventThread.join()
            self.logger.info("finished calibration...")
    
    def beamftoggle_handler(self, arg):
        if arg:
            self._beamfEvent = Event()
            self._beamfEventThread = EventThread(
                    pre_callback=partial(self._change_mode,self.beamf_toggle,'beamf',True),
                    post_callback=partial(self._change_mode,self.beamf_toggle,'beamf',False),
                    doc = self.doc,
                    event=self._beamfEvent)
            self._bf_thread = SamplesThread(
                        gen=self.beamf.result(1),
                        splitter= self.splitter,
                        register=self.beamf.source.source.source.source.source,
                        register_args={
                            'buffer_size':1,
                            'buffer_overflow_treatment':'none'
                        },
                        event=self._beamfEvent)        
            self._bf_thread.start()
            self._beamfEventThread.start()
            self.logger.info("Beamforming...")
        if not arg:
            self._bf_thread.breakThread = True
            self._bf_thread.join()
            self._beamfEventThread.join()
            self.logger.info("stopped beamforming")

    def get_widgets(self):
        return column([
                self.exit_button,
                Spacer(height=100),
                self.ti_savename,
                self.current_time_checkbox,  
                self.ti_msmtime,
                self.display_toggle,
                self.calib_toggle, 
                self.beamf_toggle, 
                self.msm_toggle, 
                self.update_period,
                ], width=150)

    def set_callbacks(self):
        self.msm_toggle.on_click(self.msmtoggle_handler)
        self.display_toggle.on_click(self.displaytoggle_handler)
        self.calib_toggle.on_click(self.calibtoggle_handler)
        self.beamf_toggle.on_click(self.beamftoggle_handler)
        self.current_time_checkbox.on_change('active', self.checkbox_use_current_time_callback)
        self.ti_savename.on_change("value", self.savename_callback)
        self.exit_button.on_click(self.exit_callback)
        self.exit_button.js_on_click(CustomJS( code='''
            setTimeout(function(){
                window.location.href = "about:blank";
            }, 500);
            '''))



class PhantomControl(MeasurementControl):

    def __init__(self, h5path=Path(__file__).parent  / "data", **kwargs):
        self.sfreq = 25600
        self.duration = 10
        self.num_samples=self.duration*self.sfreq
        self.mics = ac.MicGeom(file=Path(ac.__file__).parent / 'xml' / 'tub_vogel64.xml')
        if not h5path.exists():
            h5path.mkdir()
        self.h5path = h5path
        kwargs['source'] = sp.TimeSamplesPhantom()
        super().__init__(**kwargs)

        self.select_file = Select(
            title="Select Source Case", value="rotating.h5", options=[
                ("rotating.h5","Rotating Source"), ("calib.h5", "Calibration Signal")]
        )
        self.change_file(None, None, None)
        self.select_file.on_change('value', self.change_file)

    def change_file(self, attr, old, new):
        h5f = self.h5path / self.select_file.value
        if not h5f.exists():
            self.logger.info("file does not exist. Create file...")
            if self.select_file.value == "rotating.h5":
                self.create_three_sources_moving(h5f)
            elif self.select_file.value == "calib.h5":
                self.create_calibration_signal(h5f)
        self.source.file = Path(h5f)

    def create_three_sources_moving(self, h5f):
        n1 = ac.WNoiseGenerator( sample_freq=self.sfreq, num_samples=self.num_samples, seed=100 )
        n2 = ac.WNoiseGenerator( sample_freq=self.sfreq, num_samples=self.num_samples, seed=200, rms=0.7 )
        n3 = ac.WNoiseGenerator( sample_freq=self.sfreq, num_samples=self.num_samples, seed=300, rms=0.5 )
        # trajectory of source
        tr = ac.Trajectory()
        rps = 0.2 # revs pre second
        delta_t = 1./abs(rps)/16.0 # ca. 16 spline nodes per revolution 
        r1 = self.mics.aperture/2
        for t in np.arange(0, self.duration*1.001, delta_t):
            phi = t * rps * 2 * np.pi #angle
            # define points for trajectory spline
            tr.points[t] = (r1 * np.cos(phi), r1 * np.sin(phi), r1)
        # point sources
        p1 = ac.MovingPointSource(signal=n1, mics=self.mics, trajectory=tr)
        p2 = ac.PointSource(signal=n2, mics=self.mics, loc=(0.15, 0, r1))
        p3 = ac.PointSource(signal=n3, mics=self.mics, loc=(0, 0.1, r1))
        pa = ac.Mixer(source=p1, sources=[p2, p3])
        wh5 = ac.WriteH5(source=pa, file=h5f)
        wh5.save()

    def create_calibration_signal(self, h5f):
        n1 = ac.SineGenerator( sample_freq=self.sfreq, num_samples=self.num_samples, freq=1000,amplitude=20.0 )
        n2 = ac.WNoiseGenerator( sample_freq=self.sfreq, num_samples=self.num_samples, seed=1, rms=.0001 )
        noise = ac.UncorrelatedNoiseSource(signal=n2,mics=self.mics)
        d = np.zeros((n1.num_samples, self.mics.num_mics))
        d[:,0] = n1.signal()
        sine = ac.TimeSamples(data=d, sample_freq=self.sfreq)
        mix = ac.SourceMixer(sources=[sine, noise])
        wh5 = ac.WriteH5( source=mix, file=h5f )
        wh5.save()

    def get_widgets(self):
        return column([
                self.exit_button,
                Spacer(height=100),
                self.select_file,
                self.ti_savename,
                self.current_time_checkbox,  
                self.ti_msmtime,
                self.display_toggle,
                self.calib_toggle, 
                self.beamf_toggle, 
                self.msm_toggle, 
                self.update_period,
                ], width=150)
        

class SoundDeviceControl(MeasurementControl):

    def __init__(self, **kwargs):
        devices, default_index, num_channels = self._get_devices()
        kwargs['source'] = sp.SoundDeviceSamplesGenerator(device=int(default_index), num_channels=num_channels)
        widgets = kwargs['source'].get_widgets(
            trait_widget_mapper={'device': Select, 'num_channels': NumericInput},
            trait_widget_args={
                'device': {'value': default_index, 'options' : devices},
                'num_channels' : {'title' : 'Number of Input Channels', 'value': num_channels},
            })
        self.device_select = widgets['device']
        self.num_channels_text = widgets['num_channels']
        self.device_select.on_change('value', self.device_update)
        for dev in devices:
            if 'nanoSHARC' in dev[1] and '16' in dev[1]:
                kwargs['steer'].mics.file = Path(ac.__file__).parent / 'xml' / 'minidsp_uma-16.xml'
        super().__init__(**kwargs)

    def _get_devices(self):
        devices = []
        default_index = None
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels']>0:
                devices.append(
                    (f"{i}", "{name} {max_input_channels}".format(**dev)))
            if 'nanoSHARC' in dev['name']:
                default_index = f"{i}"
        if default_index is None:
            default_index = f"{devices[0][0]}"
        num_channels = sd.query_devices(int(default_index))['max_input_channels']
        return devices, default_index, num_channels

    def device_update(self, attr, old, new):
        self.source.num_channels = sd.query_devices(self.source.device)['max_input_channels']

    def get_widgets(self):
        return column([
                self.exit_button,
                Spacer(height=100),
                self.device_select,
                self.num_channels_text,
                self.ti_savename,
                self.current_time_checkbox,  
                self.ti_msmtime,
                self.display_toggle,
                self.calib_toggle, 
                self.beamf_toggle, 
                self.msm_toggle, 
                self.update_period,
                ], width=150)


class SinusControl(MeasurementControl):

    def __init__(self, device, config_dir, config_name, sinus_channel_control, inventory_no='TA132', **kwargs):
        try:
            from tapy.devices.sinus import Tornado, Typhoon, Apollo
            from tapy.bindings.acoular import SinusSamplesGenerator
            from tapy.drivers.sinus import SINUS_STREAM
        except ImportError:
            raise ImportError("tapy is not installed. Please install it first.")
        self.sinus_channel_control = sinus_channel_control
        self.stream = SINUS_STREAM
        self.config_dir = Path(config_dir)
        config = None
        if config_name is not None:
            config = Path(self.config_dir) / config_name
        if device == 'tornado':
            self.device = Tornado(config=config)
        elif device == 'typhoon':
            self.device = Typhoon(config=config)
        elif device == 'apollo':
            self.device = Apollo(inventory_no=inventory_no, config=config)
        kwargs['source'] = SinusSamplesGenerator(device=self.device)
        super().__init__(**kwargs)

        # cds
        self.teds_cds = ColumnDataSource(data={})
        # Widgets
        value = "None"
        if config_name is not None:
            value = config_name
        config_options = ["None"] + [f.name for f in Path(config_dir).iterdir() if f.is_file()]

        self.select_setting = Select(title="Select Settings:", value=value, options=config_options, width=100)
        self.reload_settings_options = Button(label="↻", disabled=False, width=30)
        self.settings_button = Button(label="Load Setting", disabled=False, button_type="warning")
        self.level_select = Select(title="Select Level to load:", value="AnalogInput", options=[
            (None, "All"), ("AnalogInput", "AnalogInput"), ("Device", "Device")])
        self.buffer_cds = ColumnDataSource(data=dict(filling=[0], y=['buffer']))
        self.set_sinus_callbacks()
        self.buffer_bar = self.create_buffer_bar()

    def create_buffer_bar(self):
        block_count = int(self.device.pci[0].BlockCount)
        self.buffer_bar = figure(
            title="Buffer", y_range=['buffer'], height=50, x_range=(0, block_count))
        self.buffer_bar.xgrid.visible = False
        self.buffer_bar.ygrid.visible = False
        self.buffer_bar.toolbar.logo = None
        self.buffer_bar.toolbar_location = None
        self.buffer_bar.axis.visible = False
        self.buffer_bar.grid.visible = False
        self.buffer_bar.hbar(y='y', height=0.9, left=0, right='filling',
                                source=self.buffer_cds)
        return self.buffer_bar

    def update_buffer_bar(self):
        self.buffer_cds.data['filling'] = np.array([self.stream._pdiff_in])

    def update_select_settings_options_callback(self):
        self.select_setting.options=["None"]+ [
            f.name for f in Path(self.config_dir).iterdir() if f.is_file()]

    def settings_callback(self):
        self.logger.info("load settings ...")
        try:
            self.device.ini_import(self.config_dir/self.select_setting.value,
                    level=self.level_select.value)
            self.device.set_config_settings()
        except Exception as e_text: 
            self.logger.error("{}".format(e_text))
            return
        self.logger.info("set settings ok!")
        self.source._enabled_analog_inputs # trigger update of fs and num_channels  
        self.update_widgets_and_glyphs(None)

    def update_widgets_and_glyphs(self, event):
        block_count = int(self.device.pci[0].BlockCount)
        self.logger.debug(f"update buffer bar, new block count: {block_count}")
        self.buffer_bar.x_range=Range1d(0,int(block_count))

    def get_widgets(self):
        return column([
                self.exit_button,
                Spacer(height=100),
                row(column(Spacer(height=15),self.reload_settings_options),self.select_setting),
                self.level_select,
                self.settings_button,
                self.ti_savename,
                self.current_time_checkbox,  
                self.ti_msmtime,
                self.display_toggle,
                self.calib_toggle, 
                self.beamf_toggle, 
                self.msm_toggle, 
                self.buffer_bar,
                self.update_period,
                ], width=150)

    def set_sinus_callbacks(self):
        self.reload_settings_options.on_click(self.update_select_settings_options_callback)
        self.settings_button.on_click(self.settings_callback)  

    def get_analog_input_tab(self):
        set_settings_button = Button(label="Set Analog Input Settings", button_type="warning")
        def _callback(event):
            for aio in self.device.analog_inputs:
                aio.set_settings()
            self.source._enabled_analog_inputs # trigger update of fs and num_channels
        set_settings_button.on_click(_callback)
        set_settings_button.on_click(self._update_teds_data)
        # create widgets
        analog_input_widgets = []
        for aio in self.device.analog_inputs:
            trait_widget_mapper = {'name': TextInput, 'sensitivity': NumericInput}
            trait_widget_mapper.update({k: Select for k in aio._settable_attr})
            trait_widget_args = {'sensitivity': {'mode': 'float'}, 'name': {'disabled': True}}
            analog_input_widgets.append(
                list(sp.get_widgets(aio, trait_widget_mapper=trait_widget_mapper, trait_widget_args=trait_widget_args)
                .values()))
        return Panel(child=layout([[set_settings_button],[analog_input_widgets]]), title="Analog Input Settings")

    def get_analog_output_tab(self):
        set_settings_button = Button(label="Set Analog Output Settings", button_type="warning")
        def _callback(event):
            for aio in self.device.analog_outputs:
                aio.set_settings()
        set_settings_button.on_click(_callback)
        # create widgets
        analog_output_widgets = []
        for aio in self.device.analog_outputs:
            trait_widget_mapper = {'name': TextInput}
            trait_widget_mapper.update({k: Select for k in aio._settable_attr})
            trait_widget_args = {'name': {'disabled': True}}
            analog_output_widgets.append(
                list(sp.get_widgets(aio, trait_widget_mapper=trait_widget_mapper, trait_widget_args=trait_widget_args)
                .values()))
        return Panel(child=layout([[set_settings_button],[analog_output_widgets]]), title="Analog Output Settings")

    def get_device_tab(self):
        set_settings_button = Button(label="Set PCI Device Settings", button_type="warning")
        def _callback(event):
            for pci in self.device.pci:
                pci.set_settings()
        set_settings_button.on_click(_callback)
        set_settings_button.on_click(self.update_widgets_and_glyphs)
        # create widgets
        devices_widgets = []
        for pci in self.device.pci:
            trait_widget_mapper = {'serial': TextInput, 'BlockCount': Slider}
            trait_widget_mapper.update({k: Select for k in pci._settable_attr if k not in ['BlockCount','SyncWithDevices']})
            mics_trait_widget_args = {'serial': {'disabled': True}}
            devices_widgets.append(
                list(sp.get_widgets(pci, trait_widget_mapper=trait_widget_mapper, trait_widget_args=mics_trait_widget_args)
            .values()))
        return Panel(child=layout([[set_settings_button],[devices_widgets]]), title="PCI Device Settings")

    def get_adc_to_dac_tab(self):
        set_settings_button = Button(label="Set ADC to DAC Settings", button_type="warning")
        def _callback(event):
            for adc in self.device.adc_to_dac:
                adc.set_settings()
        set_settings_button.on_click(_callback)
        # create widgets
        adc_to_dac_widgets = []
        for adc in self.device.adc_to_dac:
            trait_widget_mapper = {'name': TextInput}
            trait_widget_mapper.update({k: Select for k in adc._settable_attr})
            trait_widget_args = {'name': {'disabled': True}}
            adc_to_dac_widgets.append(
                list(sp.get_widgets(adc, trait_widget_mapper=trait_widget_mapper, trait_widget_args=trait_widget_args)
                .values()))
        return Panel(child=layout([[set_settings_button],[adc_to_dac_widgets]]), title="ADC to DAC Settings")

    def _update_teds_data(self, event):
        self.teds_cds.data = {
            'channel' : [c.name for c in self.device.analog_inputs],
            'serial' : [c.TEDSData.get('SensorSerNo', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'sensitivity': [c.TEDSData.get('SensorSensitivity', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'wiredata': [c.TEDSData.get('1_Wire_Data', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'calibdate': [c.TEDSData.get('CalibDate', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'calibperiod': [c.TEDSData.get('CalibPeriod', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'chipserial': [c.TEDSData.get('ChipSerNo', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'manufacturer': [c.TEDSData.get('Manufacturer', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'sensorversion': [c.TEDSData.get('SensorVersion', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
            'tedstemp': [c.TEDSData.get('TEDS_Template', "") if hasattr(c, 'TEDSData') else "" for c in self.device.analog_inputs],
        }

    def get_teds_tab(self):
        tedscolumns = [
            TableColumn(field='channel', title='Channel'),
            TableColumn(field='serial', title='SensorSerNo'),
            TableColumn(field='sensitivity', title='SensorSensitivity'),
            TableColumn(field='wiredata', title='1_Wire_Data'),
            TableColumn(field='calibdate', title='CalibDate'),
            TableColumn(field='calibperiod', title='CalibPeriod'),
            TableColumn(field='chipserial', title='ChipSerNo'),
            TableColumn(field='manufacturer', title='Manufacturer'),
            TableColumn(field='sensorversion', title='SensorVersion'),
            TableColumn(field='tedstemp', title='TEDS_Template'),
            ]
        self._update_teds_data(None)
        teds_table = DataTable(source=self.teds_cds, columns=tedscolumns, sizing_mode='stretch_width')  
        download_button = Button(label="📥", button_type="warning", sizing_mode='fixed', width=30, height=30)
        download_js = CustomJS(args=dict(source=self.teds_cds), code="""
            var data = source.data;
            var filetext = '';
            var columns = Object.keys(data);
            
            // Add header row
            filetext += columns.join(',') + '\\n';
            
            // Add rows
            var nrows = data[columns[0]].length;
            for (var i = 0; i < nrows; i++) {
                var row = columns.map(col => data[col][i]);
                filetext += row.join(',') + '\\n';
            }
            
            // Create a Blob and trigger download
            var blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'teds_data.csv';
            link.click();
        """)
        
        download_button.js_on_click(download_js)
        return Panel(child=layout([[download_button, teds_table]], sizing_mode='stretch_both'), title="TEDS Data")

    def get_tab(self):
        tabs = []
        if 'Device' in self.sinus_channel_control:
            tabs.append(self.get_device_tab())
        if 'AnalogInput' in self.sinus_channel_control:
            tabs.append(self.get_analog_input_tab())
        if 'AnalogOutput' in self.sinus_channel_control:
            tabs.append(self.get_analog_output_tab())
        if 'ADCToDAC' in self.sinus_channel_control:
            tabs.append(self.get_adc_to_dac_tab())
        if 'TEDS' in self.sinus_channel_control:
            tabs.append(self.get_teds_tab())
        return tabs


class Calibration:

    def __init__(self, doc, control):
        self.doc = doc
        self.control = control
        self.cal_widgets = control.calib.get_widgets()
        self.cal_filter_widgets = self.control.calib.source.source.source.get_widgets()
        # save button
        self.savecal = Button(label="save to .xml",button_type="warning", height=button_height)
        self.savecal.on_click(self._save_calib_callback)
        # calibration table
        columns = [
            TableColumn(field='channel', title='channel'),
            TableColumn(field='calibvalue', title='calibvalue', editor=NumberEditor()),
            TableColumn(field='caliblevel', title='caliblevel', editor=NumberEditor()),
            TableColumn(field='calibfactor', title='calibfactor', editor=NumberEditor()),]
        self.cal_table = DataTable(columns=columns, sizing_mode='stretch_both')
        self._calibtable_callback()
        self.control.calib.on_trait_change(self.calibtable_callback,"calibdata")

    def _calibtable_callback(self):
        cal_fac = self.control.calib.calibfactor
        if cal_fac.size == 0:
            cal_fac = np.ones(self.control.calib.calibdata.shape[0])
        self.cal_table.source.data = {"calibvalue":self.control.calib.calibdata[:,0],
                        "caliblevel":self.control.calib.calibdata[:,1],
                        "calibfactor":cal_fac,
                        "channel": np.arange(1, self.control.calib.calibdata.shape[0]+1)}

    def calibtable_callback(self):
        return self.doc.add_next_tick_callback(self._calibtable_callback)

    def _save_calib_callback(self):
        if not self.cal_widgets['file'].value:
            fname = Path("Measurement_App") / "metadata" / f"calibdata_{current_time()}.xml"
            self.cal_widgets['file'].value = fname
        else:
            fname = self.cal_widgets['file'].value
        self.control.calib.save()

    def get_widgets(self):
        return column(
                Div(text=r"""<b style="font-size:15px;">Save Calibration Data</b>"""),
                row(self.cal_table,
                column(
                row(self.savecal, self.cal_widgets['file']),
                Spacer(height=50),
                Div(text=r"""<b style="font-size:15px;">Calibration Filter Settings</b>"""),
                *self.cal_filter_widgets.values(),
                Spacer(height=50),
                Div(text=r"""<b style="font-size:15px;">Basic Calibration Settings</b>"""),
                *self.cal_widgets.values(),
                ), sizing_mode='stretch_both'), sizing_mode='stretch_both')
                        

    def get_tab(self):
        return Panel(child=self.get_widgets(), title="Calibration")