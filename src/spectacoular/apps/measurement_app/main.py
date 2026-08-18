"""Measurement Bokeh application."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Event

import acoular as ac
import spectacoular as sp
from acoular import MaskedTimeOut
from spectacoular.apps.base import AudioStreamApp

from .cam import CameraComponent
from .log import LogHandler
from .threads import SamplesThread, StreamDrain

import numpy as np
from bokeh.layouts import Spacer, column, layout, row
from bokeh.models import ColorBar, ColumnDataSource, CustomJS, FactorRange, LinearColorMapper, Select, Tabs, Toggle
from bokeh.models import TabPanel as Panel
from bokeh.models.glyphs import Scatter
from bokeh.models.widgets import (
    Button,
    CheckboxGroup,
    Div,
    MultiSelect,
    NumberEditor,
    NumberFormatter,
    NumericInput,
    Slider,
    TableColumn,
    TextInput,
)
from bokeh.palettes import Spectral11, Viridis256
from bokeh.plotting import figure

COLOR = Spectral11
BUTTON_HEIGHT = 80
ACTION_BUTTON_HEIGHT = 40
ACTION_BUTTON_WIDTH = 100


class MeasurementApp(AudioStreamApp):
    """Measurement display and recording application."""

    title = 'Measurement App'

    def __init__(self, doc, logger=None):
        self.blocksize = 512
        self.mics = sp.MicGeom(file=Path(__file__).parent / 'micgeom' / 'tub_vogel64.xml')
        self.grid = sp.RectGrid(x_min=-0.75, x_max=0.75, y_min=-0.75, y_max=0.75, z=0.75, increment=0.05)
        self._stream_worker = None
        self._display_worker = None
        self._record_worker = None
        self._beamform_worker = None
        self._periodic_callback = None
        self._stream_active = False
        self._updating_toggles = False
        self.stream_toggle = Toggle(
            label='Stream', button_type='success', sizing_mode='stretch_width', height=BUTTON_HEIGHT, disabled=True
        )
        self.filename = TextInput(value='', title='Filename:', disabled=True)
        self.current_time_checkbox = CheckboxGroup(labels=['use current time'], active=[0])
        self.measurement_time = TextInput(value='10', title='Measurement Time [s]:')
        self.update_period = Select(
            title='Select Update Period [ms]', value='50', options=['25', '50', '100', '200', '400', '800']
        )
        self.exit_button = Button(label='Exit', button_type='danger', sizing_mode='stretch_width')
        self._measurement_controls = column(width=300)
        self.current_time_checkbox.on_change('active', self._toggle_filename)
        self.filename.on_change('value', self._set_filename)
        self.exit_button.js_on_click(CustomJS(code='window.location.href = "about:blank";'))
        self.stream_toggle.on_click(self._stream_toggled)
        super().__init__(doc, logger)

    @staticmethod
    def _labels(source, label_type='Number'):
        start = 0 if label_type == 'Index' else 1
        return [str(index) for index in range(start, source.num_channels + start)]

    def build_stream_content(self, source):  # noqa: PLR0915
        """Build the legacy measurement layout for the selected source."""
        self.splitter = ac.SampleSplitter(source=source)
        self.stream_drain = StreamDrain(source=self.splitter)
        self.disp = sp.TimeOutPresenter(
            source=ac.Average(source=ac.TimePower(source=self.splitter), num_per_average=self.blocksize)
        )
        self.msm = ac.WriteH5(source=self.splitter)
        self.beamforming_input = MaskedTimeOut(source=self.splitter)
        self.beamf = sp.TimeOutPresenter(
            source=ac.Average(
                source=ac.TimePower(
                    source=sp.FiltOctave(
                        source=ac.BeamformerTime(
                            source=self.beamforming_input,
                            steer=ac.SteeringVector(grid=self.grid, mics=self.mics),
                        ),
                        band=4000,
                    )
                ),
                num_per_average=self.blocksize,
            )
        )

        labels = self._labels(source)
        self.amp_data = ColumnDataSource(
            {'channels': labels, 'level': np.zeros(len(labels)), 'colors': [COLOR[1]] * len(labels)}
        )
        self.beamf_data = ColumnDataSource({'level': []})
        self.grid_data = ColumnDataSource(
            {
                'x': [(self.grid.x_max + self.grid.x_min) / 2],
                'y': [(self.grid.y_max + self.grid.y_min) / 2],
                'width': [self.grid.x_max - self.grid.x_min],
                'height': [self.grid.y_max - self.grid.y_min],
            }
        )

        self.amp_fig = figure(
            title='SPL/dB',
            tooltips=[('Lp/dB', '@level'), ('Channel', '@channels')],
            tools='',
            x_range=FactorRange(*labels),
            y_range=(0, 120),
            height=750,
            sizing_mode='stretch_width',
        )
        self.amp_fig.xgrid.visible = False
        self.amp_fig.xaxis.major_label_orientation = np.pi / 2
        self.amp_fig.toolbar.logo = None
        self.amp_fig.vbar(x='channels', width=0.5, bottom=0, top='level', color='colors', source=self.amp_data)

        self.mics_beamf_fig = figure(
            tooltips=[('Lp/dB', '@level'), ('Channel Index', '@channels'), ('(x,y)', '(@x, @y)')],
            tools='pan,wheel_zoom,reset',
            match_aspect=True,
            aspect_ratio=1,
            width=1400,
        )
        mapper = LinearColorMapper(palette=Viridis256, low=70, high=90, low_color=(1, 1, 1, 0))
        self.bf_image = self.mics_beamf_fig.image(
            image='level',
            x=self.grid.x_min,
            y=self.grid.y_min,
            dw=self.grid.x_max - self.grid.x_min,
            dh=self.grid.y_max - self.grid.y_min,
            color_mapper=mapper,
            source=self.beamf_data,
        )
        self.mics_beamf_fig.add_layout(
            ColorBar(color_mapper=mapper, location=(0, 0), title='dB', title_standoff=10), 'right'
        )

        mic_presenter = sp.MicGeomPresenter(source=self.mics, auto_update=True)
        self.camera = CameraComponent(doc=self.doc, figure=self.mics_beamf_fig)
        mic_layout = sp.layouts.MicGeomComponent(
            mic_alpha=0.4,
            glyph=Scatter(
                marker='circle_cross',
                x='x',
                y='y',
                fill_color='colors',
                size='sizes',
                fill_alpha='alpha',
                line_alpha='alpha',
            ),
            figure=self.mics_beamf_fig,
            presenter=mic_presenter,
            allow_point_draw=True,
        )
        mic_presenter.update(
            sizes=np.full(self.mics.pos_total.shape[1], 20), colors=[COLOR[1]] * self.mics.pos_total.shape[1]
        )
        self.mics_beamf_fig.rect(alpha=1.0, color='black', fill_alpha=0, line_width=2, source=self.grid_data)

        editor, formatter = NumberEditor(), NumberFormatter(format='0.00')
        mic_layout.mics_trait_widget_args.update(
            {
                'pos_total': {
                    'height': 200,
                    'editable': True,
                    'transposed': True,
                    'columns': [
                        TableColumn(field=axis, title=f'{axis}/m', editor=editor, formatter=formatter) for axis in 'xyz'
                    ],
                }
            }
        )
        self.mics_widgets = mic_layout.widgets
        self.all_mics_valid = Button(label='All Valid', button_type='success', sizing_mode='stretch_width')
        self.all_mics_valid.on_click(lambda: setattr(self.mics, 'invalid_channels', []))

        self.invalid_input_channels = MultiSelect(title='Not-Array Channels', height=150, value=[])
        self.invalid_input_channels.description = 'Select which input channels should not be used for beamforming'
        self.beamforming_input.set_widgets(invalid_channels=self.invalid_input_channels)
        self.all_bf_valid = Button(label='All Valid', button_type='success', sizing_mode='stretch_width')
        self.all_bf_valid.on_click(lambda: setattr(self.beamforming_input, 'invalid_channels', []))
        self.auto_level_toggle = Toggle(label='Auto Level', button_type='success', active=True)
        self.dynamic_range = NumericInput(value=10, title='Dynamic Range/dB')
        self.snapshot_avg = NumericInput(value=1, title='Snapshots to Average')
        self.bf_max_level = Slider(start=0, end=140, value=100, step=1, title='Peak Level/dB')
        self.bf_alpha = Slider(start=0, end=1, step=0.05, value=1, title='Sourcemap Alpha')
        grid_widgets = self.grid.get_widgets()
        z_slider = Slider(start=0.01, end=10.0, value=self.grid.z, step=0.02, title='z')
        self.grid.set_widgets(z=z_slider)
        grid_widgets['z'] = z_slider
        freq_slider = Slider(start=50, end=10000, value=4000, step=1, title='Frequency')
        self.beamf.source.source.source.set_widgets(band=freq_slider)
        self.clip_level = NumericInput(value=120, title='Clip Level/dB', width=100)
        self.label_select = Select(title='Select Channel Labeling:', value='Number', options=['Number', 'Index'])

        self.display_toggle = Toggle(
            label='Display',
            button_type='primary',
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            disabled=True,
        )
        self.record_toggle = Toggle(
            label='Measure',
            button_type='danger',
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            disabled=True,
        )
        self.beamform_toggle = Toggle(
            label='Beamforming',
            button_type='warning',
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            disabled=True,
        )
        self.display_toggle.on_click(self._display_toggled)
        self.record_toggle.on_click(self._record_toggled)
        self.beamform_toggle.on_click(self._beamform_toggled)
        self.stream_toggle.disabled = False
        self.stream_toggle.active = False
        self._set_child_actions_enabled(enabled=False)
        action_buttons = row(
            self.display_toggle,
            self.beamform_toggle,
            self.record_toggle,
            width=ACTION_BUTTON_WIDTH * 3,
            spacing=0,
        )
        self._measurement_controls.children = [
            self.filename,
            self.current_time_checkbox,
            self.measurement_time,
            action_buttons,
            self.update_period,
        ]

        def update_channel_labels(_attr, _old, _new):
            channel_labels = self._labels(source, self.label_select.value)
            self.amp_data.data = {
                'channels': channel_labels,
                'level': np.zeros(len(channel_labels)),
                'colors': [COLOR[1]] * len(channel_labels),
            }
            self.amp_fig.x_range.factors = channel_labels
            self.invalid_input_channels.options = [(str(index), label) for index, label in enumerate(channel_labels)]

        def update_grid(_attr, _old, _new):
            self.grid_data.data = {
                'x': [(self.grid.x_max + self.grid.x_min) / 2],
                'y': [(self.grid.y_max + self.grid.y_min) / 2],
                'width': [self.grid.x_max - self.grid.x_min],
                'height': [self.grid.y_max - self.grid.y_min],
            }
            self.bf_image.glyph.update(
                x=self.grid.x_min,
                y=self.grid.y_min,
                dw=self.grid.x_max - self.grid.x_min,
                dh=self.grid.y_max - self.grid.y_min,
            )

        def update_levels():
            if self.disp.cdsource.data['data'].size:
                levels = ac.L_p(self.disp.cdsource.data['data'][0])
                self.amp_data.data['level'] = levels
                self.amp_data.data['colors'] = np.where(levels < self.clip_level.value, COLOR[1], COLOR[8])
            if self.beamform_toggle.active and self.beamf.cdsource.data['data'].size:
                image = ac.L_p(self.beamf.cdsource.data['data'].reshape(self.grid.shape)).T
                self.beamf_data.data = {'level': [image]}
                if self.auto_level_toggle.active:
                    mapper.high, mapper.low = image.max(), image.max() - self.dynamic_range.value

        self.label_select.on_change('value', update_channel_labels)
        source.on_trait_change(lambda: update_channel_labels(None, None, None), 'num_channels')
        self.dynamic_range.on_change('value', lambda _attr, _old, _new: self._set_bf_levels(mapper))
        self.bf_max_level.on_change('value', lambda _attr, _old, _new: self._set_bf_levels(mapper))
        self.snapshot_avg.on_change(
            'value', lambda _a, _o, new: setattr(self.beamf.source, 'num_per_average', self.blocksize * new)
        )
        self.bf_alpha.on_change('value', lambda _a, _o, new: setattr(self.bf_image.glyph, 'global_alpha', new))
        for name in ('x_min', 'x_max', 'y_min', 'y_max'):
            grid_widgets[name].on_change('value', update_grid)

        amplitudes_tab = Panel(
            child=column(
                row(Spacer(width=25), self.clip_level, Spacer(width=25), self.label_select),
                self.amp_fig,
                sizing_mode='stretch_both',
            ),
            title='Channel Levels',
        )
        self.mics_widgets['invalid_channels'].title = 'Invalid Mics'
        self.mics_widgets['invalid_channels'].height = 150
        mic_control = layout(
            [
                [Div(text='<b style="font-size:15px;">Microphone Setup</b>')],
                [self.mics_widgets['file'], self.mics_widgets['mic_size'], self.mics_widgets['num_mics']],
                [
                    column(self.all_mics_valid, self.mics_widgets['invalid_channels']),
                    column(self.all_bf_valid, self.invalid_input_channels),
                ],
                [self.mics_widgets['pos_total']],
            ],
            sizing_mode='stretch_width',
        )
        bf_control = layout(
            [
                [Div(text='<b style="font-size:15px;">Beamforming Setup</b>')],
                [freq_slider],
                [self.bf_alpha, self.snapshot_avg],
                [self.auto_level_toggle, self.dynamic_range, self.bf_max_level],
                [grid_widgets['x_min'], grid_widgets['x_max'], grid_widgets['y_min'], grid_widgets['y_max']],
                [grid_widgets['increment'], grid_widgets['z']],
                [grid_widgets['size']],
            ],
            sizing_mode='stretch_width',
        )
        camera_widgets = list(self.camera.widgets.values())
        camera_control = layout(
            [
                [Div(text='<b style="font-size:15px;">Camera Setup</b>')],
                [Spacer(width=10), *camera_widgets[:6], Spacer(width=10)],
                [Spacer(width=10), *camera_widgets[6:], Spacer(width=10)],
            ],
            sizing_mode='stretch_width',
        )
        mics_tab = Panel(
            child=row(
                column(camera_control, self.mics_beamf_fig),
                column(mic_control, Spacer(height=25), bf_control, sizing_mode='stretch_width'),
            ),
            title='Microphone Geometry / Beamforming',
        )
        self._update_levels = update_levels
        return Tabs(tabs=[amplitudes_tab, mics_tab], sizing_mode='inherit', width=1700, height=800)

    def _set_bf_levels(self, mapper):
        if not self.auto_level_toggle.active:
            mapper.high = self.bf_max_level.value
            mapper.low = mapper.high - self.dynamic_range.value

    def build_root(self):
        """Keep the original sidebar-and-tabs arrangement around stream controls."""
        sidebar = column(
            self.exit_button,
            self.stream_toggle,
            Spacer(height=100),
            self.control_select,
            self._error,
            self._control_content,
            self._measurement_controls,
            width=300,
        )
        return column(row(Spacer(width=10), sidebar, Spacer(width=20), self._stream_content))

    def _toggle_filename(self, _attr, _old, active):
        self.filename.disabled = active == [0]

    def _set_filename(self, _attr, _old, value):
        if hasattr(self, 'msm'):
            self.msm.file = Path(ac.config.td_dir) / f'{value}.h5'

    def _num_samples(self):
        if self.measurement_time.value in {'', '-1'}:
            return -1
        return int(float(self.measurement_time.value) * self.msm.sample_freq)

    def _set_child_actions_enabled(self, *, enabled):
        for toggle in (
            getattr(self, 'display_toggle', None),
            getattr(self, 'record_toggle', None),
            getattr(self, 'beamform_toggle', None),
        ):
            if toggle is not None:
                toggle.disabled = not enabled

    def _start_consumer(self, generator, register, args):
        worker = SamplesThread(generator, self.splitter, register, args, Event())
        worker.start()
        return worker

    def _stop_worker(self, worker_name):
        worker = getattr(self, worker_name)
        if worker is not None:
            worker.breakThread = True
            worker.join()
            setattr(self, worker_name, None)

    def _set_toggle_active(self, toggle, *, active):
        if toggle.active != active:
            self._updating_toggles = True
            try:
                toggle.active = active
            finally:
                self._updating_toggles = False

    def _start_updates(self):
        if self._periodic_callback is None:
            self._periodic_callback = self.doc.add_periodic_callback(self._update_levels, int(self.update_period.value))

    def _stop_updates_if_idle(self):
        display_active = getattr(self, 'display_toggle', None) is not None and self.display_toggle.active
        beamform_active = getattr(self, 'beamform_toggle', None) is not None and self.beamform_toggle.active
        if self._periodic_callback is not None and not display_active and not beamform_active:
            self.doc.remove_periodic_callback(self._periodic_callback)
            self._periodic_callback = None

    def _stream_toggled(self, active):
        if self._updating_toggles:
            return
        if active:
            self.start()
            if self._stream_worker is None:
                self._stream_worker = self._start_consumer(
                    self.stream_drain.result(self.blocksize),
                    self.stream_drain,
                    {'buffer_size': 1, 'buffer_overflow_treatment': 'none'},
                )
            self._stream_active = True
            self._set_toggle_active(self.stream_toggle, active=True)
            self._set_child_actions_enabled(enabled=True)
        else:
            self.stop_consumers()
            if self._running and self.control is not None:
                try:
                    self.control.stop()
                finally:
                    self.control.set_config_enabled(True)
                    self.control_select.disabled = False
                    self._running = False

    def _require_stream(self, toggle):
        if not self._stream_active:
            self._set_toggle_active(toggle, active=False)
            return False
        return True

    def _display_toggled(self, active):
        if self._updating_toggles:
            return
        if active:
            if not self._require_stream(self.display_toggle):
                return
            if self._display_worker is None:
                self._display_worker = self._start_consumer(
                    self.disp.result(1),
                    self.disp.source.source,
                    {'buffer_size': 400, 'buffer_overflow_treatment': 'none'},
                )
            self._set_toggle_active(self.display_toggle, active=True)
            self._start_updates()
        else:
            self._set_toggle_active(self.display_toggle, active=False)
            self._stop_worker('_display_worker')
            self._stop_updates_if_idle()

    def _record_toggled(self, active):
        if self._updating_toggles:
            return
        if active:
            if not self._require_stream(self.record_toggle):
                return
            if self.current_time_checkbox.active == [0]:
                self.filename.value = datetime.now(tz=UTC).isoformat('_').replace(':', '-').replace('.', '_')
            self.msm.num_samples_write = self._num_samples()
            if self._record_worker is None:
                self._record_worker = self._start_consumer(
                    self.msm.result(self.blocksize),
                    self.msm,
                    {'buffer_size': 400, 'buffer_overflow_treatment': 'error'},
                )
            self._set_toggle_active(self.record_toggle, active=True)
        else:
            self.msm.write_flag = False
            self._set_toggle_active(self.record_toggle, active=False)
            self._stop_worker('_record_worker')

    def _beamform_toggled(self, active):
        if self._updating_toggles:
            return
        if active:
            if not self._require_stream(self.beamform_toggle):
                return
            if self._beamform_worker is None:
                self._beamform_worker = self._start_consumer(
                    self.beamf.result(1),
                    self.beamforming_input,
                    {'buffer_size': 1, 'buffer_overflow_treatment': 'none'},
                )
            self._set_toggle_active(self.beamform_toggle, active=True)
            self._start_updates()
        else:
            self._set_toggle_active(self.beamform_toggle, active=False)
            self.beamf_data.data = {'level': []}
            self._stop_worker('_beamform_worker')
            self._stop_updates_if_idle()

    def stop_consumers(self):
        """Stop and join app-owned pipeline consumers."""
        if getattr(self, 'record_toggle', None) is not None:
            self.msm.write_flag = False
            self._set_toggle_active(self.record_toggle, active=False)
        if getattr(self, 'display_toggle', None) is not None:
            self._set_toggle_active(self.display_toggle, active=False)
        if getattr(self, 'beamform_toggle', None) is not None:
            self._set_toggle_active(self.beamform_toggle, active=False)
            self.beamf_data.data = {'level': []}
        for worker_name in ('_display_worker', '_beamform_worker', '_record_worker', '_stream_worker'):
            self._stop_worker(worker_name)
        if self._periodic_callback is not None:
            self.doc.remove_periodic_callback(self._periodic_callback)
            self._periodic_callback = None
        self._stream_active = False
        self._set_toggle_active(self.stream_toggle, active=False)
        self._set_child_actions_enabled(enabled=False)


def server_doc(doc):
    """Populate a Bokeh document for the measurement app."""
    log = LogHandler(doc=doc)
    td = Path(__file__).parent / 'td'
    td.mkdir(exist_ok=True)
    ac.config.td_dir = td
    MeasurementApp(doc, log.logger).server_doc()


if __name__ == '__main__':
    from bokeh.server.server import Server

    server = Server({'/': server_doc})
    server.start()
    server.io_loop.add_callback(server.show, '/')
    server.io_loop.start()
