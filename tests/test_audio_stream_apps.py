"""Tests for audio stream app controls and lifecycle."""

from time import sleep
from types import SimpleNamespace

from spectacoular.apps.base import AudioStreamApp
from spectacoular.apps.controls import (
    PHANTOM_ROTATIONAL_SPEED,
    PHANTOM_SAMPLE_FREQ,
    BaseAudioStreamControl,
    PhantomControl,
    SoundDeviceControl,
    discover_controls,
)
from spectacoular.apps.measurement_app.main import MeasurementApp

import numpy as np
import pytest
from bokeh.core.validation import check_integrity
from bokeh.document import Document
from bokeh.layouts import Row, Spacer, column
from bokeh.models import Div, Tabs


class _TestControl(BaseAudioStreamControl):
    """Small in-memory control used by lifecycle tests."""

    id = 'test'
    label = 'Test'

    def __init__(self, *args, **kwargs):
        self.started = self.stopped = self.closed = False
        self.config_enabled = None
        super().__init__(*args, **kwargs)

    def create_source(self):
        """Provide an object sufficient for this app test."""
        return object()

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True

    def set_config_enabled(self, enabled):
        self.config_enabled = enabled


class _FailingCloseControl(_TestControl):
    """Control that cannot cleanly release its backend."""

    def close(self):
        message = 'close failed'
        raise RuntimeError(message)


class _FailingStopControl(_TestControl):
    """Control that fails to stop but still records close."""

    def stop(self):
        self.stopped = True
        message = 'stop failed'
        raise RuntimeError(message)


class _TestApp(AudioStreamApp):
    """Minimal app that records source rebuilds."""

    def __init__(self, *args, **kwargs):
        self.sources = []
        self.consumers_stopped = 0
        super().__init__(*args, **kwargs)
        for callback in tuple(self.doc.session_callbacks):
            callback.callback()

    def _initialize_control(self, control):
        control.initialize_source()
        self._finish_source(control)

    def build_stream_content(self, source):
        self.sources.append(source)
        return column()

    def stop_consumers(self):
        self.consumers_stopped += 1


def _run_next_ticks(doc):
    for _ in range(50):
        callbacks = tuple(doc.session_callbacks)
        for callback in callbacks:
            callback.callback()
        if not doc.session_callbacks:
            sleep(0.01)
        else:
            return


def _select_test_stream(app, value='test'):
    app.control_select.value = value
    _run_next_ticks(app.doc)
    return app.control


def _select_measurement_stream(app, value='phantom'):
    app.control_select.value = value
    for _ in range(100):
        for callback in tuple(app.doc.session_callbacks):
            callback.callback()
        if app.control is not None and not app.control_select.disabled and list(app.doc.select({'type': Tabs})):
            return app.control
        sleep(0.02)
    message = 'measurement stream did not initialize'
    raise AssertionError(message)


class _EntryPoint:
    """Minimal importlib.metadata entry point fake."""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def load(self):
        return self.value


def test_phantom_control_generates_single_rotation_in_memory():
    """The default phantom stream is one generated rotation, not a bundled file."""
    control = PhantomControl(Document())
    control.initialize_source()

    assert control.source.data is not None
    assert control.source.file is None
    assert control.source.sample_freq == PHANTOM_SAMPLE_FREQ
    assert control.source.data.shape == (int(PHANTOM_SAMPLE_FREQ / abs(PHANTOM_ROTATIONAL_SPEED)), 64)
    assert control.source.data.shape[0] / control.source.sample_freq == 1.0 / abs(PHANTOM_ROTATIONAL_SPEED)
    assert not np.all(control.source.data == 0)


def test_phantom_control_repeats_generated_example_data():
    """The measurement Phantom source should behave like a continuous stream."""
    control = PhantomControl(Document())
    control.initialize_source()

    assert control.source.repeat


def test_discover_controls_adds_valid_controls_and_rejects_duplicates():
    """Entry point discovery admits only non-conflicting controls."""

    class Plugin(_TestControl):
        id = 'plugin'

    controls = discover_controls({'test': _TestControl}, [_EntryPoint('plugin', Plugin), _EntryPoint('test', Plugin)])

    assert controls == {'test': _TestControl, 'plugin': Plugin}


def test_audio_stream_app_starts_without_active_control():
    """Apps wait for explicit audio-stream selection before creating controls."""
    app = _TestApp(Document(), controls={'test': _TestControl})

    assert app.control is None
    assert app.control_select.value == ''
    assert all(isinstance(child, Spacer) for child in app._control_content.children)
    assert all(isinstance(child, Spacer) for child in app._stream_content.children)
    assert app.sources == []


def test_control_shows_status_before_source_initialization():
    """Controllers render before their source initializes on the next Bokeh tick."""

    class LoadingControl(BaseAudioStreamControl):
        id = 'loading'
        label = 'Loading'

        def create_source(self):
            return object()

        def set_config_enabled(self, _enabled):
            pass

        def build_loading_widget(self):
            return Div(text='Connecting…')

    app = _TestApp(Document(), controls={'test': _TestControl, 'loading': LoadingControl})
    app.control_select.value = 'loading'

    assert isinstance(app.control, LoadingControl)
    assert app._control_content.children
    assert all(isinstance(child, Spacer) for child in app._stream_content.children[0].children)
    assert app.control._loading_widget.text == 'Connecting…'
    assert app.control_select.disabled

    next(iter(app.doc.session_callbacks)).callback()

    assert isinstance(app.control, LoadingControl)
    assert not app.control._loading_widget.visible
    assert not app.control_select.disabled


def test_audio_stream_app_switches_controls_after_closing_old_control():
    """A backend switch stops and closes its predecessor before activation."""

    class OtherControl(_TestControl):
        id = 'other'
        label = 'Other'

    app = _TestApp(Document(), controls={'test': _TestControl, 'other': OtherControl})
    first = _select_test_stream(app)
    app.start()
    app.stop()
    app.control_select.value = 'other'
    _run_next_ticks(app.doc)

    assert first.stopped
    assert first.closed
    assert isinstance(app.control, OtherControl)
    assert len(app.sources) == 2


def test_failed_old_cleanup_leaves_no_active_control():
    """A failed old cleanup prevents construction of the requested backend."""

    class OtherControl(_TestControl):
        id = 'other'
        label = 'Other'

    class FailingControl(_FailingCloseControl):
        id = 'test'

    app = _TestApp(Document(), controls={'test': FailingControl, 'other': OtherControl})
    _select_test_stream(app)
    app.control_select.value = 'other'

    assert app.control is None
    assert app.control_select.value == ''
    assert 'Unable to close audio stream control' in app._error.text


def test_stop_failure_still_closes_old_control():
    """A stop failure does not skip the required close attempt."""

    class FailingControl(_FailingStopControl):
        id = 'test'

    app = _TestApp(Document(), controls={'test': FailingControl, 'other': _TestControl})
    control = _select_test_stream(app)
    app._running = True

    with pytest.raises(RuntimeError, match='stop failed'):
        app._stop_and_close(control)

    assert control.stopped
    assert control.closed


def test_failed_selected_control_construction_stays_blank():
    """Selected-control construction failure resets the selector without retrying."""

    class FailingControl(_TestControl):
        id = 'test'

        def __init__(self, *_args, **_kwargs):
            message = 'construction failed'
            raise RuntimeError(message)

    app = _TestApp(Document(), controls={'test': FailingControl})
    app.control_select.value = 'test'

    assert app.control is None
    assert app.control_select.value == ''
    assert 'Unable to create audio stream control' in app._error.text


def test_session_destroy_closes_control_once():
    """Session teardown follows the idempotent close path."""
    app = _TestApp(Document(), controls={'test': _TestControl})
    control = _select_test_stream(app)

    app._session_destroyed(None)
    app._session_destroyed(None)

    assert control.closed
    assert app.consumers_stopped == 1


def test_source_changed_rebuilds_while_stopped():
    """A stopped control source change rebuilds stream content."""
    app = _TestApp(Document(), controls={'test': _TestControl})
    _select_test_stream(app)

    app.control.source = object()
    app.control.source_changed()

    assert len(app.sources) == 2


def test_channel_count_edit_notifies_source_change():
    """Direct channel-count edits update the stream and notify the app."""
    source = SimpleNamespace(num_channels=2)
    changes = []
    control = SimpleNamespace(source=source, source_changed=lambda: changes.append(True))

    SoundDeviceControl._num_channels_changed(control, 'value', 2, 4)

    assert source.num_channels == 4
    assert changes == [True]


def test_measurement_app_starts_without_selected_audio_stream():
    """Measurement app waits for explicit audio-stream selection before building controls."""
    app = MeasurementApp(Document())
    app.server_doc()

    assert app.doc.roots
    assert app.control is None
    assert app.control_select.value == ''
    assert not list(app.doc.select({'type': Tabs}))
    assert not [issue for issue in check_integrity(app.doc.models).warning if issue.code == 1002]


def test_measurement_app_document_constructs_with_stream_gate_after_selection():
    """Measurement app builds stream-gated controls after audio-stream selection."""
    app = MeasurementApp(Document())
    app.server_doc()
    _select_measurement_stream(app)

    tabs = next(iter(app.doc.select({'type': Tabs})))
    assert [tab.title for tab in tabs.tabs] == ['Channel Levels', 'Microphone Geometry / Beamforming']
    assert app.stream_toggle.label == 'Stream'
    assert not app.stream_toggle.disabled
    assert app.display_toggle.disabled
    assert app.record_toggle.disabled
    assert app.beamform_toggle.disabled


def test_measurement_app_action_buttons_share_one_row_with_bold_labels():
    """Display, Beamforming, and Measure stay grouped in one bold action row."""
    app = MeasurementApp(Document())
    app.server_doc()
    _select_measurement_stream(app)

    action_row = app._measurement_controls.children[4]

    assert isinstance(action_row, Row)
    assert list(action_row.children) == [app.display_toggle, app.beamform_toggle, app.record_toggle]
    assert [button.label for button in action_row.children] == ['Display', 'Beamforming', 'Measure']
    assert all('.bk-btn' in ''.join(button.stylesheets) for button in action_row.children)
    assert all('font-weight: 700' in ''.join(button.stylesheets) for button in action_row.children)
    assert [button.width for button in action_row.children] == [100, 100, 100]
    assert [button.height for button in action_row.children] == [40, 40, 40]


def test_measurement_app_stream_starts_drain_and_enables_child_actions(monkeypatch):
    """Stream mode starts one lossy drain consumer and enables independent actions."""
    app = MeasurementApp(Document())
    app.server_doc()
    _select_measurement_stream(app)
    monkeypatch.setattr(app, 'start', lambda: None)
    calls = []
    monkeypatch.setattr(app, '_start_consumer', lambda *args: calls.append(args) or object())

    app._stream_toggled(True)

    assert len(calls) == 1
    generator, register, args = calls[0]
    assert hasattr(generator, '__next__')
    assert register is app.stream_drain
    assert args == {'buffer_size': 1, 'buffer_overflow_treatment': 'none'}
    assert app._stream_worker is not None
    assert not app.display_toggle.disabled
    assert not app.record_toggle.disabled
    assert not app.beamform_toggle.disabled


def test_measurement_app_stream_stop_turns_off_children_and_stops_all_workers(monkeypatch):
    """Stopping Stream disables child actions and joins every active consumer."""

    class Worker:
        def __init__(self):
            self.breakThread = False
            self.joined = False

        def join(self):
            self.joined = True

    app = MeasurementApp(Document())
    app.server_doc()
    _select_measurement_stream(app)
    monkeypatch.setattr(app, 'start', lambda: None)
    monkeypatch.setattr(app.control, 'stop', lambda: None)
    monkeypatch.setattr(app.control, 'set_config_enabled', lambda _enabled: None)
    workers = [Worker(), Worker(), Worker(), Worker()]
    monkeypatch.setattr(app, '_start_consumer', lambda *_args, **_kwargs: workers.pop(0))
    monkeypatch.setattr(app, '_start_updates', lambda: None)

    app._stream_toggled(True)
    app._display_toggled(True)
    app._beamform_toggled(True)
    app._record_toggled(True)
    app.stream_toggle.active = True
    app.display_toggle.active = True
    app.beamform_toggle.active = True
    app.record_toggle.active = True

    started_workers = [app._stream_worker, app._display_worker, app._beamform_worker, app._record_worker]
    app._stream_toggled(False)

    assert all(worker.breakThread and worker.joined for worker in started_workers)
    assert not app.stream_toggle.active
    assert app.display_toggle.disabled
    assert app.record_toggle.disabled
    assert app.beamform_toggle.disabled
    assert not app.display_toggle.active
    assert not app.record_toggle.active
    assert not app.beamform_toggle.active


def test_measurement_app_record_stop_clears_write_flag():
    """Stopping measurement must ask the Acoular writer to finish cleanly."""
    app = MeasurementApp(Document())
    app.server_doc()
    _select_measurement_stream(app)
    app.msm.write_flag = True

    app._record_toggled(False)

    assert not app.msm.write_flag


def test_measurement_app_beamforming_starts_plot_updates_when_streaming(monkeypatch):
    """Beamforming must schedule result rendering once Stream is active."""
    app = MeasurementApp(Document())
    app.server_doc()
    _select_measurement_stream(app)
    app._stream_active = True
    calls = []
    monkeypatch.setattr(app, '_start_consumer', lambda *_args: calls.append(_args))

    app._beamform_toggled(True)

    assert calls[0][1] is app.beamforming_input
    assert app._periodic_callback is not None
    app.stop_consumers()
