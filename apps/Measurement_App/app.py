import acoular as ac
import spectacoular as sp
from threading import Event
from functools import partial
from datetime import datetime
from threads import SamplesThread,EventThread
from layout import toggle_labels, plot_colors
from pathlib import Path

from bokeh.layouts import column, Spacer, row
from bokeh.models.widgets import Toggle, TextInput, CheckboxGroup, Select
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


class MeasurementControl:

    def __init__(self, doc, source, logger, blocksize=1024, steer=None, cfreq=1000):

        toggle_height = 50
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
            self.beamf = sp.TimeOutPresenter(source=ac.Average(source=ac.TimePower(source=sp.FiltOctave(source=ac.BeamformerTime(source=ac.MaskedTimeOut(source=self.splitter), steer=steer), band=cfreq)), num_per_average = blocksize))
        self.logger = logger

        # create measurement toggle button
        self.display_toggle = Toggle(label="Start Display", active=False,button_type="primary", sizing_mode="stretch_width", height=toggle_height)
        self.msm_toggle = Toggle(label="START MEASUREMENT", active=False, disabled=True, button_type="danger", sizing_mode="stretch_width", height=toggle_height)
        self.calib_toggle = Toggle(label="Start Calibration", active=False,disabled=True,button_type="warning", sizing_mode="stretch_width", height=toggle_height)
        self.beamf_toggle = Toggle(label="Start Beamforming", active=False,disabled=True,button_type="warning", sizing_mode="stretch_width", height=toggle_height)

        # Text Inputs
        self.ti_msmtime = TextInput(value="10", title="Measurement Time [s]:")
        self.ti_savename = TextInput(value="", title="Filename:",disabled=True)
        self.current_time_checkbox = CheckboxGroup(labels=["use current time"], active=[0])

        # Select Widgets
        self.update_period = Select(title="Select Update Period [ms]", value=str(50), options=["25","50","100", "200", "400","800"])

        # threads
        self._disp_threads = []
        self._view_callback_id = None

        # callbacks
        self.msm_toggle.on_click(self.msmtoggle_handler)
        self.display_toggle.on_click(self.displaytoggle_handler)
        self.calib_toggle.on_click(self.calibtoggle_handler)
        self.beamf_toggle.on_click(self.beamftoggle_handler)
        self.current_time_checkbox.on_change('active', self.checkbox_use_current_time_callback)
        self.ti_savename.on_change("value", self.savename_callback)

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
        td = Path(__file__).resolve().parent / "td"
        if not td.exists():
            td.mkdir()
        self.msm.name = td / f"{new}.h5"

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
            self.logger.info("start display...")
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
            self.logger.info("start beamforming...")
        if not arg:
            self._bf_thread.breakThread = True
            self._bf_thread.join()
            self._beamfEventThread.join()
            self.logger.info("stopped beamforming")

    def get_widgets(self):
        return row(column([
                Spacer(height=100),
                self.ti_savename,
                self.current_time_checkbox,  
                self.ti_msmtime,
                self.display_toggle,
                self.calib_toggle, 
                self.beamf_toggle, 
                self.msm_toggle, 
                self.update_period,
                #Spacer(width=250, height=10)
                ], sizing_mode="inherit", width=200), Spacer(width=50))



# class Calibration:

#     def get_widgets(self):
#         calCol = column(Spacer(height=15),
#                         row(savecal,calWidgets['name']),
#                         Spacer(height=15),
#                         row(calibTable,
#                         column(
#                         caldiv1,
#                         *calfiltWidgets.values(),
#                         caldiv2,
#                         calWidgets['magnitude'],
#                         calWidgets['delta'],
#                         width=150)))        
