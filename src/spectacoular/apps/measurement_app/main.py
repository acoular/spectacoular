"""Measurement Bokeh application."""

from __future__ import annotations

from pathlib import Path
from threading import Event

import acoular as ac
import spectacoular as sp
from acoular import MaskedTimeOut
from spectacoular.apps.base import AudioStreamApp

from .log import LogHandler
from .threads import SamplesThread

import numpy as np
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, FactorRange, Select, Toggle
from bokeh.plotting import figure


class MeasurementApp(AudioStreamApp):
    """Backend-independent measurement display and recording application."""

    title = 'Measurement App'

    def __init__(self, doc, logger=None):
        self.blocksize = 512
        self.mics = sp.MicGeom(file=Path(__file__).parent / 'micgeom' / 'tub_vogel64.xml')
        self.grid = sp.RectGrid(x_min=-0.75, x_max=0.75, y_min=-0.75, y_max=0.75, z=0.75, increment=0.05)
        self._workers = []
        self._periodic_callback = None
        self._active_workflow = None
        super().__init__(doc, logger)

    def _labels(self, source):
        return [str(index + 1) for index in range(source.num_channels)]

    def build_stream_content(self, source):
        """Build the measurement pipeline and source-dependent display."""
        self.splitter = ac.SampleSplitter(source=source)
        self.disp = sp.TimeOutPresenter(
            source=ac.Average(source=ac.TimePower(source=self.splitter), num_per_average=self.blocksize)
        )
        self.msm = ac.WriteH5(source=self.splitter)
        self.beamf = sp.TimeOutPresenter(
            source=ac.Average(
                source=ac.TimePower(
                    source=sp.FiltOctave(
                        source=ac.BeamformerTime(
                            source=MaskedTimeOut(source=self.splitter),
                            steer=ac.SteeringVector(grid=self.grid, mics=self.mics),
                        ),
                        band=4000,
                    )
                ),
                num_per_average=self.blocksize,
            )
        )
        labels = self._labels(source)
        self.amp_data = ColumnDataSource({'channels': labels, 'level': np.zeros(len(labels))})
        self.amp_fig = figure(
            title='SPL/dB', x_range=FactorRange(*labels), y_range=(0, 120), height=600, sizing_mode='stretch_width'
        )
        self.amp_fig.vbar(x='channels', top='level', width=0.5, source=self.amp_data)
        self.display_toggle = Toggle(label='Display', button_type='primary')
        self.record_toggle = Toggle(label='Measure', button_type='danger')
        self.beamform_toggle = Toggle(label='Beamforming', button_type='warning')
        self.label_select = Select(title='Channel labels', value='Number', options=['Number'])
        self.display_toggle.on_click(self._display_toggled)
        self.record_toggle.on_click(self._record_toggled)
        self.beamform_toggle.on_click(self._beamform_toggled)
        controls = row(self.display_toggle, self.record_toggle, self.beamform_toggle, self.label_select)
        return column(controls, self.amp_fig)

    def _set_workflow(self, workflow):
        self._active_workflow = workflow
        toggles = (self.display_toggle, self.record_toggle, self.beamform_toggle)
        for toggle in toggles:
            toggle.disabled = workflow is not None and toggle is not workflow

    def _start_consumer(self, generator, register, args):
        event = Event()
        worker = SamplesThread(generator, self.splitter, register, args, event)
        worker.start()
        self._workers.append(worker)

    def _display_toggled(self, active):
        if active:
            self._set_workflow(self.display_toggle)
            self.start()
            self._start_consumer(
                self.disp.result(1),
                self.disp.source.source,
                {'buffer_size': 400, 'buffer_overflow_treatment': 'none'},
            )
            self._periodic_callback = self.doc.add_periodic_callback(self._update_display, 50)
        else:
            self.stop()

    def _record_toggled(self, active):
        if active:
            self._set_workflow(self.record_toggle)
            self.start()
            self.msm.num_samples_write = -1
            self._start_consumer(
                self.msm.result(self.blocksize),
                self.msm,
                {'buffer_size': 400, 'buffer_overflow_treatment': 'error'},
            )
        else:
            self.msm.writeflag = False
            self.stop()

    def _beamform_toggled(self, active):
        if active:
            self._set_workflow(self.beamform_toggle)
            self.start()
            self._start_consumer(
                self.beamf.result(1),
                self.beamf.source.source.source.source.source,
                {'buffer_size': 1, 'buffer_overflow_treatment': 'none'},
            )
        else:
            self.stop()

    def _update_display(self):
        data = self.disp.cdsource.data['data']
        if data.size:
            self.amp_data.data['level'] = ac.L_p(data[0])

    def stop_consumers(self):
        """Stop and join app-owned pipeline consumers."""
        for worker in self._workers:
            worker.breakThread = True
        for worker in self._workers:
            worker.join()
        self._workers = []
        if self._periodic_callback is not None:
            self.doc.remove_periodic_callback(self._periodic_callback)
            self._periodic_callback = None
        self._active_workflow = None
        for toggle in (
            getattr(self, 'display_toggle', None),
            getattr(self, 'record_toggle', None),
            getattr(self, 'beamform_toggle', None),
        ):
            if toggle is not None:
                toggle.active = False
                toggle.disabled = False


def server_doc(doc):
    """Populate a Bokeh document for the measurement app."""
    log = LogHandler(doc=doc)
    td = Path(__file__).parent / 'td'
    td.mkdir(exist_ok=True)
    ac.config.td_dir = td
    app = MeasurementApp(doc, log.logger)
    app.server_doc()


if __name__ == '__main__':
    from bokeh.server.server import Server

    server = Server({'/': server_doc})
    server.start()
    server.io_loop.add_callback(server.show, '/')
    server.io_loop.start()
