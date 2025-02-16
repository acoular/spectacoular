import sys
import acoular as ac
import spectacoular as sp
from threading import Event
from functools import partial
from datetime import datetime
from threads import SamplesThread,EventThread
from layout import toggle_labels, plot_colors, button_height
from pathlib import Path
import numpy as np
from time import sleep

from bokeh.models import TabPanel as Panel, CustomJS, ColumnDataSource
from bokeh.layouts import column, Spacer, row
from bokeh.models.widgets import Toggle, TextInput, CheckboxGroup, Select, Button, Div,\
    DataTable, TableColumn, NumberEditor
from bokeh.plotting import figure
from bokeh.models.ranges import Range1d

BUFFERSIZE = 400
# disable_obj_disp = [
#         selectPerCallPeriod,select_micgeom,select_all_channels_button,
#         checkbox_micgeom, *calfiltWidgets.values(), *calWidgets.values(),
#         ]
# disable_obj_rec = [
#         ti_msmtime,checkbox_use_current_time,display_toggle, calib_toggle, 
#         beamf_toggle
#         ]
# disable_obj_calib = [
#         msm_toggle
#         ]
# disable_obj_beamf = [
#         freqSlider,wtimeSlider,dynamicSlider,autolevel_toggle,
#         checkbox_paint_mode
#         ]
# if sinus_enabled: 
#     disable_obj_disp = append_disable_obj(disable_obj_disp)

# widgets_disable =   {'msm': disable_obj_rec,
#                      'display': disable_obj_disp,
#                      'calib' : disable_obj_calib,
#                      'beamf' : disable_obj_beamf}

# widgets_enable =    {'msm': [],
#                      'display': [calib_toggle,msm_toggle,beamf_toggle],
#                      'calib' : [],
#                      'beamf' : [freqSlider,wtimeSlider,dynamicSlider,
#                                 autolevel_toggle,checkbox_paint_mode]}


def current_time():
    return datetime.now().isoformat('_').replace(':', '-').replace('.', '_') # for timestamp filename

def _get_channel_labels(source, ltype='Number'):
    if ltype == 'Index':
        labels = [str(i) for i in range(source.num_channels)]
    elif ltype == 'Number':
        labels = [str(i+1) for i in range(source.num_channels)]
    elif ltype == 'Physical':
        labels = [source.inchannels_[i] for i in range(source.num_channels)]
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
            self.beamf = sp.TimeOutPresenter(source=ac.Average(source=ac.TimePower(source=sp.FiltOctave(source=ac.BeamformerTime(source=sp.MaskedTimeOut(source=self.splitter), steer=steer), band=cfreq)), num_per_average = blocksize))
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

    def get_numsamples(self):
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
            self.msm.numsamples_write = self.get_numsamples()
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

    def __init__(self, 
        h5path=Path(__file__).parent  / "data",
        h5name="two_sources_one_moving_10s.h5", 
        **kwargs):
        if not h5path.exists():
            h5path.mkdir()
        h5f = h5path / h5name
        if not h5f.exists():
            self.create_three_sources_moving(h5f)
        kwargs['source'] = sp.TimeSamplesPhantom(file=h5f)
        super().__init__(**kwargs)
        
    def create_three_sources_moving(self, h5f):
        sfreq = 25600 
        duration = 10
        nsamples = duration*sfreq
        micgeofile = "Measurement_App/micgeom/array_64.xml"
        mg = ac.MicGeom( file=micgeofile )
        n1 = ac.WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=100 )
        n2 = ac.WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=200, rms=0.7 )
        n3 = ac.WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=300, rms=0.5 )
        # trajectory of source
        tr = ac.Trajectory()
        rps = 0.2 # revs pre second
        delta_t = 1./abs(rps)/16.0 # ca. 16 spline nodes per revolution 
        r1 = 0.141
        for t in np.arange(0, duration*1.001, delta_t):
            phi = t * rps * 2 * np.pi #angle
            # define points for trajectory spline
            tr.points[t] = (r1 * np.cos(phi), r1 * np.sin(phi), 0.3)
        # point sources
        p1 = ac.MovingPointSource(signal=n1, mics=mg, trajectory=tr)
        p2 = ac.PointSource(signal=n2, mics=mg, loc=(0.15, 0, 0.3))
        p3 = ac.PointSource(signal=n3, mics=mg, loc=(0, 0.1, 0.3))
        pa = ac.Mixer(source=p1, sources=[p2, p3])
        wh5 = ac.WriteH5(source=pa, name=h5f)
        wh5.save()

class SoundDeviceControl(MeasurementControl):

    def __init__(self, **kwargs):
        kwargs['source'] = sp.SoundDeviceSamplesGenerator()
        super().__init__(**kwargs)



class SinusControl(MeasurementControl):

    def __init__(self, device, config_dir, config_name, inventory_no='TA132', **kwargs):
        try:
            from tapy.devices.sinus import Tornado, Typhoon, Apollo
            from tapy.bindings.acoular import SINUSSamplesGenerator
        except ImportError:
            raise ImportError("tapy is not installed. Please install it first.")

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
        kwargs['source'] = SINUSSamplesGenerator(device=self.device)
        super().__init__(**kwargs)

        # Widgets
        value = "None"
        if config_name is not None:
            value = config_name
        config_options = ["None"] + [f.name for f in Path(config_dir).iterdir() if f.is_file()]

        self.select_setting = Select(title="Select Settings:", value=value, options=config_options)
        self.reload_settings_options = Button(label="↻",disabled=False,width=40)
        self.settings_button = Button(label="Load Setting",disabled=False)
        self.level_select = Select(title="Select which level to load:", value="AnalogInput", options=[
            (None, "All"), ("AnalogInput", "AnalogInput"), ("Device", "Device")])
        self.buffer_cds = ColumnDataSource(data=dict(filling=[0]))

    def create_buffer_bar(self):
        block_count = self.device.BlockCount[0]
        buffer_bar = figure(
            title="Buffer",y_range=['buffer'], height=50, x_range=(0,block_count))
        buffer_bar.xgrid.visible = False
        buffer_bar.ygrid.visible = False
        buffer_bar.toolbar.logo = None
        buffer_bar.toolbar_location = None
        buffer_bar.axis.visible = False
        buffer_bar.grid.visible = False
        return buffer_bar.hbar(y='y', height=0.9, left=0, right='filling',
                                source=self.buffer_cds)

    def update_buffer_bar(self):
        self.buffer_cds.data['filling'] = np.array([self.source._pdiff_in])

    def update_select_settings_options_callback(self):
        self.select_setting.options=["None"]+ [
            f.name for f in Path(self.config_dir).iterdir() if f.is_file()]

    def settings_callback(self):
        self.logger.info("load settings ...")
        try:
            self.device.ini_import(self.config_dir/self.select_setting.value,
                    level=self.level_select.value)
        except Exception as e_text: 
            self.logger.error("{}".format(e_text))
            return
        self.logger.info("set settings ok!")
        self.update_widgets_and_glyphs()
        #status_text.text = f"Device Status: {get_dev_state()}"        

    def update_widgets_and_glyphs(self):
        # ticker = list(arange(1,inputSignalGen.num_channels+1))
        # ChLevelsCDS.data = {'channels':ticker,'level': zeros(inputSignalGen.num_channels)}
        # amp_fig.xaxis.ticker = ticker
        # amp_fig.xaxis.major_label_overrides = {str(ticker[i]): inputSignalGen.inchannels_[i] for i in range(inputSignalGen.num_channels)}
        # checkbox_micgeom.labels = inputSignalGen.inchannels_
        # checkbox_micgeom.active = [_ for _ in range(inputSignalGen.num_channels)]
        block_count = self.device.BlockCount[0]
        self.buffer_bar.x_range=Range1d(0,int(block_count))
        # if micGeo.num_mics > 0:
        #     MicGeomCDS.data = {'x':micGeo.mpos[0,:],'y':micGeo.mpos[1,:],
        #             'sizes':array([7]*micGeo.num_mics),
        #             'channels':[inputSignalGen.inchannels_[i] for i in checkbox_micgeom.active]} 


    def get_widgets(self):
        return column([
                self.exit_button,
                Spacer(height=100),
                row(column(Spacer(height=15),self.reload_settings_options),self.select_setting),
                row(self.settings_button, self.level_select),
                self.ti_savename,
                self.current_time_checkbox,  
                self.ti_msmtime,
                self.display_toggle,
                self.calib_toggle, 
                self.beamf_toggle, 
                self.msm_toggle, 
                self.update_period,
                ], width=150)


    def set_sinus_callbacks(self):
        self.reload_settings_options.on_click(self.update_select_settings_options_callback)
        self.settings_button.on_click(self.settings_callback)  



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