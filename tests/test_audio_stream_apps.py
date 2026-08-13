"""Tests for audio stream app controls and lifecycle."""

from types import SimpleNamespace

import pytest
from bokeh.document import Document
from bokeh.layouts import column
from bokeh.models import Tabs

from spectacoular.apps.base import AudioStreamApp
from spectacoular.apps.controls import BaseAudioStreamControl, SoundDeviceControl, discover_controls
from spectacoular.apps.measurement_app.main import MeasurementApp


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

    def build_stream_content(self, source):
        self.sources.append(source)
        return column()

    def stop_consumers(self):
        self.consumers_stopped += 1


class _EntryPoint:
    """Minimal importlib.metadata entry point fake."""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def load(self):
        return self.value


def test_discover_controls_adds_valid_controls_and_rejects_duplicates():
    """Entry point discovery admits only non-conflicting controls."""

    class Plugin(_TestControl):
        id = 'plugin'

    controls = discover_controls({'test': _TestControl}, [_EntryPoint('plugin', Plugin), _EntryPoint('test', Plugin)])

    assert controls == {'test': _TestControl, 'plugin': Plugin}


def test_audio_stream_app_switches_controls_after_closing_old_control():
    """A backend switch stops and closes its predecessor before activation."""

    class OtherControl(_TestControl):
        id = 'other'
        label = 'Other'

    app = _TestApp(Document(), controls={'test': _TestControl, 'other': OtherControl})
    first = app.control
    app.start()
    app.stop()
    app.control_select.value = 'other'

    assert first.stopped and first.closed
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
    app.control_select.value = 'other'

    assert app.control is None
    assert app.control_select.value == ''
    assert 'Unable to close audio stream control' in app._error.text


def test_stop_failure_still_closes_old_control():
    """A stop failure does not skip the required close attempt."""

    class FailingControl(_FailingStopControl):
        id = 'test'

    app = _TestApp(Document(), controls={'test': FailingControl, 'other': _TestControl})
    control = app.control
    app._running = True

    with pytest.raises(RuntimeError, match='stop failed'):
        app._stop_and_close(control)

    assert control.stopped
    assert control.closed


def test_failed_initial_control_construction_stays_blank():
    """Initial construction failure resets the selector without retrying."""

    class FailingControl(_TestControl):
        id = 'test'

        def __init__(self, *args, **kwargs):
            message = 'construction failed'
            raise RuntimeError(message)

    app = _TestApp(Document(), controls={'test': FailingControl})

    assert app.control is None
    assert app.control_select.value == ''
    assert 'Unable to create audio stream control' in app._error.text


def test_session_destroy_closes_control_once():
    """Session teardown follows the idempotent close path."""
    app = _TestApp(Document(), controls={'test': _TestControl})
    control = app.control

    app._session_destroyed(None)
    app._session_destroyed(None)

    assert control.closed
    assert app.consumers_stopped == 1


def test_source_changed_rebuilds_while_stopped():
    """A stopped control source change rebuilds stream content."""
    app = _TestApp(Document(), controls={'test': _TestControl})

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


def test_measurement_app_document_constructs_and_locks_workflows():
    """Measurement app builds and prevents conflicting workflow starts."""
    app = MeasurementApp(Document())
    app.server_doc()

    assert app.doc.roots
    tabs = next(iter(app.doc.select({'type': Tabs})))
    assert [tab.title for tab in tabs.tabs] == ['Channel Levels', 'Microphone Geometry / Beamforming']
    app._set_workflow(app.display_toggle)
    assert not app.display_toggle.disabled
    assert app.record_toggle.disabled and app.beamform_toggle.disabled


def test_measurement_app_beamforming_starts_plot_updates(monkeypatch):
    """Beamforming must schedule the callback that renders its result."""
    app = MeasurementApp(Document())
    app.server_doc()
    monkeypatch.setattr(app, 'start', lambda: None)
    calls = []
    monkeypatch.setattr(app, '_start_consumer', lambda *_args: calls.append(_args))

    app._beamform_toggled(True)

    assert calls[0][1] is app.beamforming_input
    assert app._periodic_callback is not None
    app.stop_consumers()
