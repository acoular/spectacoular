import sys
import acoular as ac
import spectacoular as sp
from threading import Event
from functools import partial
from datetime import datetime
from .threads import SamplesThread, EventThread
from .layout import toggle_labels, plot_colors, button_height
from acoular import MaskedTimeOut
from pathlib import Path
import numpy as np
from time import sleep

from bokeh.models import TabPanel as Panel, CustomJS
from bokeh.layouts import column, Spacer, row
from bokeh.models.widgets import (
    Toggle,
    TextInput,
    CheckboxGroup,
    Select,
    Button,
    Div,
    DataTable,
    TableColumn,
    NumberEditor,
    NumericInput,
)

try:
    import sounddevice as sd
except ModuleNotFoundError:
    pass

BUFFERSIZE = 400


def current_time():
    return (
        datetime.now().isoformat("_").replace(":", "-").replace(".", "_")
    )  # for timestamp filename


def _get_channel_labels(source, ltype="Number"):
    if ltype == "Index":
        labels = [str(i) for i in range(source.num_channels)]
    elif ltype == "Number":
        labels = [str(i + 1) for i in range(source.num_channels)]
    elif ltype == "Physical":
        labels = [ch.name for ch in source._enabled_analog_inputs]
    return labels


class MeasurementControl:
    def __init__(self, doc, source, logger, blocksize=1024, steer=None, cfreq=1000):
        self.modecolor = None
        self.clipcolor = None
        self.blocksize = blocksize
        self.doc = doc
        self.source = source
        self.splitter = ac.SampleSplitter(source=self.source)
        self.disp = sp.TimeOutPresenter(
            source=ac.Average(
                source=ac.TimePower(source=self.splitter), num_per_average=blocksize
            )
        )
        self.msm = ac.WriteH5(source=self.splitter)
        self.calib = sp.CalibHelper(
            source=ac.Average(
                source=ac.TimePower(
                    source=sp.FiltOctave(source=self.splitter, band=1000.0)
                ),
                num_per_average=blocksize,
            )
        )
        if steer is not None:
            self.beamf = sp.TimeOutPresenter(
                source=ac.Average(
                    source=ac.TimePower(
                        source=sp.FiltOctave(
                            source=ac.BeamformerTime(
                                source=MaskedTimeOut(source=self.splitter), steer=steer
                            ),
                            band=cfreq,
                        )
                    ),
                    num_per_average=blocksize,
                )
            )
        self.logger = logger

        # create measurement toggle button
        self.display_toggle = Toggle(
            label="Display",
            active=False,
            button_type="primary",
            sizing_mode="stretch_width",
            height=button_height,
        )
        self.msm_toggle = Toggle(
            label="MEASURE",
            active=False,
            disabled=True,
            button_type="danger",
            sizing_mode="stretch_width",
            height=button_height,
        )
        self.calib_toggle = Toggle(
            label="Calibration",
            active=False,
            disabled=True,
            button_type="warning",
            sizing_mode="stretch_width",
            height=button_height,
        )
        self.beamf_toggle = Toggle(
            label="Beamforming",
            active=False,
            disabled=True,
            button_type="warning",
            sizing_mode="stretch_width",
            height=button_height,
        )
        # Others
        self.ti_msmtime = TextInput(value="10", title="Measurement Time [s]:")
        self.ti_savename = TextInput(
            value="",
            title="Filename:",
            disabled=True,
            description=f"Filename for the measurement data. Files are saved to {ac.config.td_dir}",
        )
        self.current_time_checkbox = CheckboxGroup(
            labels=["use current time"], active=[0]
        )
        self.update_period = Select(
            title="Select Update Period [ms]",
            value=str(50),
            options=["25", "50", "100", "200", "400", "800"],
        )
        self.exit_button = Button(
            label="Exit", button_type="danger", sizing_mode="stretch_width"
        )

        # threads
        self._disp_threads = []
        self._view_callback_id = None

        # widgets disable / enable lists depending on mode
        self.widgets_disable = {
            "msm": [
                self.ti_msmtime,
                self.current_time_checkbox,
                self.ti_savename,
                self.display_toggle,
                self.calib_toggle,
                self.beamf_toggle,
            ],
            "display": [self.update_period],  # maybe unfinished!
            "calib": [self.msm_toggle],
            "beamf": [],
        }

        self.widgets_enable = {
            "msm": [],
            "display": [self.calib_toggle, self.msm_toggle, self.beamf_toggle],
            "calib": [],
            "beamf": [],
        }
        self.set_callbacks()

    def get_num_samples(self):
        if self.ti_msmtime.value == "-1" or self.ti_msmtime.value == "":
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

    def checkbox_use_current_time_callback(self, attr, old, new):
        if new == []:
            self.widgets_disable["msm"].append(self.ti_savename)
            self.ti_savename.disabled = False
        elif new == [0]:
            if self.ti_savename in self.widgets_disable["msm"]:
                self.widgets_disable["msm"].remove(self.ti_savename)
            self.ti_savename.disabled = True

    def savename_callback(self, attr, old, new):
        self.msm.name = Path(ac.config.td_dir) / f"{new}.h5"

    def exit_callback(arg):
        sleep(0.5)
        sys.exit()

    def displaytoggle_handler(self, arg):
        if arg:
            self.source.collect_samples = True
            dispEvent = Event()
            dispEventThread = EventThread(
                pre_callback=partial(
                    self._change_mode, self.display_toggle, "display", True
                ),
                post_callback=partial(
                    self._change_mode, self.display_toggle, "display", False
                ),
                doc=self.doc,
                event=dispEvent,
            )
            amp_thread = SamplesThread(
                gen=self.disp.result(1),
                splitter=self.splitter,
                register=self.disp.source.source,
                register_args={
                    "buffer_size": BUFFERSIZE,
                    "buffer_overflow_treatment": "none",
                },
                event=dispEvent,
            )
            self._disp_threads = [amp_thread, dispEventThread]
            for thread in self._disp_threads:
                thread.start()
            self.logger.info("Display...")
        if not arg:
            self.source.collect_samples = False
            for thread in self._disp_threads:
                thread.join()
            self._disp_threads = []
            self.logger.info("stopped display")

    def msmtoggle_handler(self, arg):
        if arg:  # toggle button is pressed
            self.msm.num_samples_write = self.get_num_samples()
            if self.current_time_checkbox.active == [0]:
                self.ti_savename.value = current_time()
            msm_event = Event()
            msm_consumer = EventThread(
                post_callback=partial(self._change_mode, self.msm_toggle, "msm", False),
                pre_callback=partial(self._change_mode, self.msm_toggle, "msm", True),
                doc=self.doc,
                event=msm_event,
            )
            self._msm_thread = SamplesThread(
                gen=self.msm.result(self.blocksize),
                splitter=self.splitter,
                register=self.msm,
                register_args={
                    "buffer_size": BUFFERSIZE,
                    "buffer_overflow_treatment": "error",
                },
                event=msm_event,
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
                post_callback=partial(
                    self._change_mode, self.calib_toggle, "calib", False
                ),
                pre_callback=partial(
                    self._change_mode, self.calib_toggle, "calib", True
                ),
                doc=self.doc,
                event=self._calibEvent,
            )
            self._calib_thread = SamplesThread(
                gen=self.calib.result(1),
                splitter=self.splitter,
                register=self.calib.source.source.source,
                register_args={
                    "buffer_size": BUFFERSIZE,
                    "buffer_overflow_treatment": "none",
                },
                event=self._calibEvent,
            )
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
                pre_callback=partial(
                    self._change_mode, self.beamf_toggle, "beamf", True
                ),
                post_callback=partial(
                    self._change_mode, self.beamf_toggle, "beamf", False
                ),
                doc=self.doc,
                event=self._beamfEvent,
            )
            self._bf_thread = SamplesThread(
                gen=self.beamf.result(1),
                splitter=self.splitter,
                register=self.beamf.source.source.source.source.source,
                register_args={"buffer_size": 1, "buffer_overflow_treatment": "none"},
                event=self._beamfEvent,
            )
            self._bf_thread.start()
            self._beamfEventThread.start()
            self.logger.info("Beamforming...")
        if not arg:
            self._bf_thread.breakThread = True
            self._bf_thread.join()
            self._beamfEventThread.join()
            self.logger.info("stopped beamforming")

    def get_widgets(self):
        return column(
            [
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
            ],
            width=150,
        )

    def set_callbacks(self):
        self.msm_toggle.on_click(self.msmtoggle_handler)
        self.display_toggle.on_click(self.displaytoggle_handler)
        self.calib_toggle.on_click(self.calibtoggle_handler)
        self.beamf_toggle.on_click(self.beamftoggle_handler)
        self.current_time_checkbox.on_change(
            "active", self.checkbox_use_current_time_callback
        )
        self.ti_savename.on_change("value", self.savename_callback)
        self.exit_button.on_click(self.exit_callback)
        self.exit_button.js_on_click(
            CustomJS(
                code="""
            setTimeout(function(){
                window.location.href = "about:blank";
            }, 500);
            """
            )
        )


class PhantomControl(MeasurementControl):
    def __init__(
        self,
        h5path=Path(__file__).parent / "data",
        initial_file="rotating.h5",
        **kwargs,
    ):
        self.sfreq = 25600
        self.duration = 10
        self.num_samples = self.duration * self.sfreq
        self.mics = ac.MicGeom(
            file=Path(ac.__file__).parent / "xml" / "tub_vogel64.xml"
        )
        if not h5path.exists():
            h5path.mkdir()
        self.h5path = h5path
        kwargs["source"] = sp.TimeSamplesPhantom()
        super().__init__(**kwargs)

        self.select_file = Select(
            title="Select Source Case",
            value=initial_file,
            options=[
                ("rotating.h5", "Rotating Source"),
                ("calib.h5", "Calibration Signal"),
            ],
        )
        self.change_file(None, None, None)
        self.select_file.on_change("value", self.change_file)

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
        n1 = ac.WNoiseGenerator(
            sample_freq=self.sfreq, num_samples=self.num_samples, seed=100
        )
        n2 = ac.WNoiseGenerator(
            sample_freq=self.sfreq, num_samples=self.num_samples, seed=200, rms=0.7
        )
        n3 = ac.WNoiseGenerator(
            sample_freq=self.sfreq, num_samples=self.num_samples, seed=300, rms=0.5
        )
        # trajectory of source
        tr = ac.Trajectory()
        rps = 0.2  # revs pre second
        delta_t = 1.0 / abs(rps) / 16.0  # ca. 16 spline nodes per revolution
        r1 = self.mics.aperture / 2
        for t in np.arange(0, self.duration * 1.001, delta_t):
            phi = t * rps * 2 * np.pi  # angle
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
        n1 = ac.SineGenerator(
            sample_freq=self.sfreq,
            num_samples=self.num_samples,
            freq=1000,
            amplitude=20.0,
        )
        n2 = ac.WNoiseGenerator(
            sample_freq=self.sfreq, num_samples=self.num_samples, seed=1, rms=0.0001
        )
        noise = ac.UncorrelatedNoiseSource(signal=n2, mics=self.mics)
        d = np.zeros((n1.num_samples, self.mics.num_mics))
        d[:, 0] = n1.signal()
        sine = ac.TimeSamples(data=d, sample_freq=self.sfreq)
        mix = ac.SourceMixer(sources=[sine, noise])
        wh5 = ac.WriteH5(source=mix, file=h5f)
        wh5.save()

    def get_widgets(self):
        return column(
            [
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
            ],
            width=150,
        )


class SoundDeviceControl(MeasurementControl):
    def __init__(self, **kwargs):
        devices, default_index, num_channels = self._get_devices()
        kwargs["source"] = sp.SoundDeviceSamplesGenerator(
            device=int(default_index), num_channels=num_channels
        )
        widgets = kwargs["source"].get_widgets(
            trait_widget_mapper={"device": Select, "num_channels": NumericInput},
            trait_widget_args={
                "device": {"value": default_index, "options": devices},
                "num_channels": {
                    "title": "Number of Input Channels",
                    "value": num_channels,
                },
            },
        )
        self.device_select = widgets["device"]
        self.num_channels_text = widgets["num_channels"]
        self.device_select.on_change("value", self.device_update)
        for dev in devices:
            if "nanoSHARC" in dev[1] and "16" in dev[1]:
                kwargs["steer"].mics.file = (
                    Path(ac.__file__).parent / "xml" / "minidsp_uma-16.xml"
                )
        super().__init__(**kwargs)

    def _get_devices(self):
        devices = []
        default_index = None
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append((f"{i}", "{name} {max_input_channels}".format(**dev)))
            if "nanoSHARC" in dev["name"]:
                default_index = f"{i}"
        if default_index is None:
            default_index = f"{devices[0][0]}"
        num_channels = sd.query_devices(int(default_index))["max_input_channels"]
        return devices, default_index, num_channels

    def device_update(self, attr, old, new):
        self.source.num_channels = sd.query_devices(self.source.device)[
            "max_input_channels"
        ]

    def get_widgets(self):
        return column(
            [
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
            ],
            width=150,
        )


class Calibration:
    def __init__(self, doc, control):
        self.doc = doc
        self.control = control
        self.cal_widgets = control.calib.get_widgets()
        self.cal_filter_widgets = self.control.calib.source.source.source.get_widgets()
        # save button
        self.savecal = Button(
            label="save to .xml", button_type="warning", height=button_height
        )
        self.savecal.on_click(self._save_calib_callback)
        # calibration table
        columns = [
            TableColumn(field="channel", title="channel"),
            TableColumn(field="calibvalue", title="calibvalue", editor=NumberEditor()),
            TableColumn(field="caliblevel", title="caliblevel", editor=NumberEditor()),
            TableColumn(
                field="calibfactor", title="calibfactor", editor=NumberEditor()
            ),
        ]
        self.cal_table = DataTable(columns=columns, sizing_mode="stretch_both")
        self._calibtable_callback()
        self.control.calib.on_trait_change(self.calibtable_callback, "calibdata")

    def _calibtable_callback(self):
        cal_fac = self.control.calib.calibfactor
        if cal_fac.size == 0:
            cal_fac = np.ones(self.control.calib.calibdata.shape[0])
        self.cal_table.source.data = {
            "calibvalue": self.control.calib.calibdata[:, 0],
            "caliblevel": self.control.calib.calibdata[:, 1],
            "calibfactor": cal_fac,
            "channel": np.arange(1, self.control.calib.calibdata.shape[0] + 1),
        }

    def calibtable_callback(self):
        return self.doc.add_next_tick_callback(self._calibtable_callback)

    def _save_calib_callback(self):
        if not self.cal_widgets["file"].value:
            fname = (
                Path("Measurement_App") / "metadata" / f"calibdata_{current_time()}.xml"
            )
            self.cal_widgets["file"].value = fname
        else:
            fname = self.cal_widgets["file"].value
        self.control.calib.save()

    def get_widgets(self):
        return column(
            Div(text=r"""<b style="font-size:15px;">Save Calibration Data</b>"""),
            row(
                self.cal_table,
                column(
                    row(self.savecal, self.cal_widgets["file"]),
                    Spacer(height=50),
                    Div(
                        text=r"""<b style="font-size:15px;">Calibration Filter Settings</b>"""
                    ),
                    *self.cal_filter_widgets.values(),
                    Spacer(height=50),
                    Div(
                        text=r"""<b style="font-size:15px;">Basic Calibration Settings</b>"""
                    ),
                    *self.cal_widgets.values(),
                ),
                sizing_mode="stretch_both",
            ),
            sizing_mode="stretch_both",
        )

    def get_tab(self):
        return Panel(child=self.get_widgets(), title="Calibration")
