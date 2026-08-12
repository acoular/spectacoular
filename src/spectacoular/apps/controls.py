"""Audio-stream control extension point and built-in discovery."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points

from bokeh.layouts import column

logger = logging.getLogger(__name__)
ENTRY_POINT_GROUP = 'spectacoular.audio_stream_controls'


class BaseAudioStreamControl:
    """Provide an audio source and configuration UI to an :class:`AudioStreamApp`."""

    id = ''
    label = ''

    def __init__(self, doc, logger=None):
        self.doc = doc
        self.logger = logger or logging.getLogger(type(self).__module__)
        self._source_changed_callbacks = []
        self.source = self.create_source()

    def create_source(self):
        """Create and return the Acoular-compatible stream source."""
        raise NotImplementedError

    def get_widgets(self):
        """Return one Bokeh layout containing backend-specific settings."""
        return column()

    def on_source_changed(self, callback):
        """Register a no-argument callback invoked after ``source`` changes."""
        self._source_changed_callbacks.append(callback)

    def source_changed(self):
        """Notify the app that this stopped control replaced its source."""
        for callback in self._source_changed_callbacks:
            callback()

    def start(self):
        """Start backend acquisition. Default controls need no action."""

    def stop(self):
        """Stop backend acquisition. Default controls need no action."""

    def close(self):
        """Release backend resources. Default controls need no action."""

    def set_config_enabled(self, enabled):
        """Enable or disable source-changing configuration widgets."""


def discover_controls(builtins, eps=None):
    """Return *builtins* extended by valid, non-conflicting control entry points."""
    controls = dict(builtins)
    entries = entry_points(group=ENTRY_POINT_GROUP) if eps is None else eps
    for entry in entries:
        try:
            control = entry.load()
            valid = isinstance(control, type) and issubclass(control, BaseAudioStreamControl)
            unique = valid and entry.name not in controls and control.id == entry.name
            if unique:
                controls[entry.name] = control
            else:
                logger.error('Ignoring invalid or duplicate audio stream control entry point %s', entry.name)
        except Exception:
            logger.exception('Ignoring audio stream control entry point %s', entry.name)
    return controls


# Built-ins are imported after the base type to avoid a circular import.
from .measurement_app.controls import PhantomControl, SoundDeviceControl  # noqa: E402

BUILTIN_CONTROLS = {'phantom': PhantomControl, 'sounddevice': SoundDeviceControl}
available_controls = discover_controls(BUILTIN_CONTROLS)
