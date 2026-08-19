"""Reusable audio-stream controls and their extension-point discovery."""

from __future__ import annotations

import contextlib
import importlib
import logging
from functools import lru_cache
from importlib.metadata import entry_points
from pathlib import Path

import acoular as ac
import spectacoular as sp

import numpy as np
from bokeh.layouts import column
from bokeh.models import Div, Select
from bokeh.models.widgets.inputs import NumericInput

logger = logging.getLogger(__name__)
ENTRY_POINT_GROUP = 'spectacoular.audio_stream_controls'
CONTROL_WIDTH = 300
CONTROL_STYLES = {
    'border': '1px solid #b8b8b8',
    'border-radius': '4px',
    'padding': '10px',
}
PHANTOM_SAMPLE_FREQ = 25600.0
PHANTOM_ROTATIONAL_SPEED = 1.0
PHANTOM_MICGEOM_FILE = Path(__file__).parent / 'measurement_app' / 'micgeom' / 'tub_vogel64.xml'
PHANTOM_TRAJECTORY_NODES_PER_ROTATION = 16
PHANTOM_NOISE_SEED = 100


@lru_cache(maxsize=1)
def _cached_phantom_rotation_data(sample_freq, rotational_speed, seed):
    return create_phantom_rotation_data(
        sample_freq=sample_freq,
        rotational_speed=rotational_speed,
        mics=ac.MicGeom(file=PHANTOM_MICGEOM_FILE),
        seed=seed,
    )


def create_phantom_rotation_data(
    sample_freq=PHANTOM_SAMPLE_FREQ,
    rotational_speed=PHANTOM_ROTATIONAL_SPEED,
    mics=None,
    seed=PHANTOM_NOISE_SEED,
):
    """Return one full rotation of deterministic Acoular-generated phantom data."""
    if mics is None:
        return _cached_phantom_rotation_data(sample_freq, rotational_speed, seed).copy()
    num_samples = int(sample_freq / abs(rotational_speed))
    duration = num_samples / sample_freq
    signal = ac.WNoiseGenerator(sample_freq=sample_freq, num_samples=num_samples, seed=seed)
    trajectory = ac.Trajectory()
    node_interval = 1.0 / abs(rotational_speed) / PHANTOM_TRAJECTORY_NODES_PER_ROTATION
    radius = mics.aperture / 2
    for timestamp in np.arange(0.0, duration * 1.001, node_interval):
        angle = timestamp * rotational_speed * 2.0 * np.pi
        trajectory.points[float(timestamp)] = (radius * np.cos(angle), radius * np.sin(angle), radius)
    source = ac.MovingPointSource(signal=signal, mics=mics, trajectory=trajectory)
    return ac.tools.return_result(source)


class BaseAudioStreamControl:
    """Provide an audio source and consistently styled configuration UI."""

    id = ''
    label = ''

    def __init__(self, doc, logger=None):
        self.doc = doc
        self.logger = logger or logging.getLogger(type(self).__module__)
        self._source_changed_callbacks = []
        self.source = None
        self._loading_widget = self.build_loading_widget()

    def create_source(self):
        """Create and return the Acoular-compatible stream source."""
        raise NotImplementedError

    def initialize_source(self):
        """Create the source after the control widget renders."""
        self.source = self.create_source()

    def source_initialized(self):
        """Finish UI setup after the source is created."""

    def build_loading_widget(self):
        """Return a widget displayed while this control's source initializes."""
        return Div(text=f'⏳ Initializing {self.label}…', styles={'font-style': 'italic'})

    def loading_finished(self):
        """Hide the source-initialization widget."""
        self._loading_widget.visible = False

    def widget_panel(self, *widgets):
        """Return a labelled, bounded panel shared by every audio control."""
        return column(
            Div(text='<b>Audio stream control</b>'),
            Div(text=self.label),
            self._loading_widget,
            *widgets,
            width=CONTROL_WIDTH,
            styles=CONTROL_STYLES,
        )

    def get_widgets(self):
        """Return one Bokeh layout containing backend-specific settings."""
        return self.widget_panel()

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


class PhantomControl(BaseAudioStreamControl):
    """Provide a generated repeating phantom audio stream."""

    id = 'phantom'
    label = 'Phantom input'

    def create_source(self):
        """Create a repeating one-rotation phantom source in memory."""
        return sp.TimeSamplesPhantom(
            data=create_phantom_rotation_data(),
            sample_freq=PHANTOM_SAMPLE_FREQ,
            repeat=True,
        )

    def get_widgets(self):
        """Return phantom-source information."""
        return self.widget_panel(
            Div(text=f'Generated rotating source: {PHANTOM_ROTATIONAL_SPEED:g} rps, {PHANTOM_SAMPLE_FREQ:g} Hz')
        )


class SoundDeviceControl(BaseAudioStreamControl):
    """Configure a live sounddevice input source."""

    id = 'sounddevice'
    label = 'Sound device input'

    def initialize_source(self):
        """Discover an input device and create its source."""
        with contextlib.suppress(ModuleNotFoundError):
            self.sd = importlib.import_module('sounddevice')
        if not hasattr(self, 'sd'):
            message = 'sounddevice is not installed'
            raise RuntimeError(message)
        self.devices, self.default_index, self.num_channels = self._get_devices()
        super().initialize_source()

    def source_initialized(self):
        """Build the device settings widgets on Bokeh's event loop."""
        widgets = self.source.get_widgets(
            trait_widget_mapper={
                'device': Select,
                'num_channels': NumericInput,
                'sample_freq': NumericInput,
                'precision': Select,
            },
            trait_widget_args={
                'device': {'value': self.default_index, 'options': self.devices},
                'num_channels': {'title': 'Number of Input Channels', 'value': self.num_channels},
                'sample_freq': {'title': 'Sampling frequency [Hz]', 'mode': 'float'},
                'precision': {'title': 'Sample format'},
            },
        )
        self.device_select = widgets['device']
        self.num_channels_input = widgets['num_channels']
        self.sample_freq_input = widgets['sample_freq']
        self.precision_select = widgets['precision']
        self.device_select.on_change('value', self._device_changed)
        self.num_channels_input.on_change('value', self._num_channels_changed)
        self.sample_freq_input.on_change('value', self._source_setting_changed)
        self.precision_select.on_change('value', self._source_setting_changed)

    def create_source(self):
        """Create the live sounddevice source."""
        return sp.SoundDeviceSamplesGenerator(device=int(self.default_index), num_channels=self.num_channels)

    def _get_devices(self):
        devices = [
            (str(i), '{name} {max_input_channels}'.format(**device))
            for i, device in enumerate(self.sd.query_devices())
            if device['max_input_channels'] > 0
        ]
        if not devices:
            message = 'no audio input devices found'
            raise RuntimeError(message)
        default = next((index for index, label in devices if 'nanoSHARC' in label), devices[0][0])
        return devices, default, self.sd.query_devices(int(default))['max_input_channels']

    def _device_changed(self, _attr, _old, _new):
        properties = self.sd.query_devices(self.source.device)
        self.source.num_channels = properties['max_input_channels']
        self.source.sample_freq = properties['default_samplerate']
        self.sample_freq_input.value = self.source.sample_freq
        self.source_changed()

    def _source_setting_changed(self, _attr, _old, _new):
        """Rebuild consumers after a stream setting changes."""
        self.source_changed()

    def _num_channels_changed(self, _attr, old, new):
        """Notify the app after an editable channel-count change."""
        if new != old:
            self.source.num_channels = new
            self.source_changed()

    def get_widgets(self):
        """Return live-device settings once the source is ready."""
        if self.source is None:
            return self.widget_panel()
        return self.widget_panel(
            self.device_select,
            self.num_channels_input,
            self.sample_freq_input,
            self.precision_select,
        )

    def set_config_enabled(self, enabled):
        """Enable or disable live-device selection."""
        if self.source is not None:
            self.device_select.disabled = not enabled
            self.num_channels_input.disabled = not enabled
            self.sample_freq_input.disabled = not enabled
            self.precision_select.disabled = not enabled


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


BUILTIN_CONTROLS = {'phantom': PhantomControl, 'sounddevice': SoundDeviceControl}
available_controls = discover_controls(BUILTIN_CONTROLS)
