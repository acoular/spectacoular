"""Tests for audio stream app controls and lifecycle."""

from bokeh.document import Document
from bokeh.layouts import column

from spectacoular.apps.base import AudioStreamApp
from spectacoular.apps.controls import BaseAudioStreamControl, discover_controls
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
        raise RuntimeError('close failed')


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


def test_measurement_app_document_constructs_and_locks_workflows():
    """Measurement app builds and prevents conflicting workflow starts."""
    app = MeasurementApp(Document())
    app.server_doc()

    assert app.doc.roots
    app._set_workflow(app.display_toggle)
    assert not app.display_toggle.disabled
    assert app.record_toggle.disabled and app.beamform_toggle.disabled
