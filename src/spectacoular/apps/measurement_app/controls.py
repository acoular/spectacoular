"""Built-in audio stream controls for the measurement app."""

from __future__ import annotations

import contextlib
import importlib
from pathlib import Path

import spectacoular as sp
from spectacoular.apps.controls import BaseAudioStreamControl

from bokeh.layouts import column
from bokeh.models import Select
from bokeh.models.widgets.inputs import NumericInput

sd = None
with contextlib.suppress(ModuleNotFoundError):
    sd = importlib.import_module('sounddevice')


class PhantomControl(BaseAudioStreamControl):
    """Select one of the bundled phantom audio streams."""

    id = 'phantom'
    label = 'Phantom'

    def __init__(self, doc, logger=None, h5path=Path(__file__).parent / 'data'):
        self.h5path = h5path
        super().__init__(doc, logger)
        self.select_file = Select(title='Select source case', value='rotating.h5', options=['rotating.h5'])
        self.select_file.on_change('value', self._change_file)
        self._change_file(None, None, self.select_file.value)

    def create_source(self):
        """Create the selected phantom source."""
        return sp.TimeSamplesPhantom()

    def _change_file(self, _attr, _old, value):
        self.source.file = self.h5path / value

    def get_widgets(self):
        """Return the phantom source selector."""
        return column(self.select_file, width=150)

    def set_config_enabled(self, enabled):
        """Enable or disable phantom source selection."""
        self.select_file.disabled = not enabled


class SoundDeviceControl(BaseAudioStreamControl):
    """Configure a live sounddevice input source."""

    id = 'sounddevice'
    label = 'Sound device'

    def __init__(self, doc, logger=None):
        if sd is None:
            message = 'sounddevice is not installed'
            raise RuntimeError(message)
        self.devices, self.default_index, self.num_channels = self._get_devices()
        super().__init__(doc, logger)
        widgets = self.source.get_widgets(
            trait_widget_mapper={'device': Select, 'num_channels': NumericInput},
            trait_widget_args={
                'device': {'value': self.default_index, 'options': self.devices},
                'num_channels': {'title': 'Number of Input Channels', 'value': self.num_channels},
            },
        )
        self.device_select = widgets['device']
        self.num_channels_input = widgets['num_channels']
        self.device_select.on_change('value', self._device_changed)
        self.num_channels_input.on_change('value', self._num_channels_changed)

    def create_source(self):
        """Create the live sounddevice source."""
        return sp.SoundDeviceSamplesGenerator(device=int(self.default_index), num_channels=self.num_channels)

    def _get_devices(self):
        devices = [
            (str(i), '{name} {max_input_channels}'.format(**device))
            for i, device in enumerate(sd.query_devices())
            if device['max_input_channels'] > 0
        ]
        if not devices:
            message = 'no audio input devices found'
            raise RuntimeError(message)
        default = next((index for index, label in devices if 'nanoSHARC' in label), devices[0][0])
        return devices, default, sd.query_devices(int(default))['max_input_channels']

    def _device_changed(self, _attr, _old, _new):
        self.source.num_channels = sd.query_devices(self.source.device)['max_input_channels']
        self.source_changed()

    def _num_channels_changed(self, _attr, old, new):
        """Notify the app after an editable channel-count change."""
        if new != old:
            self.source.num_channels = new
            self.source_changed()

    def get_widgets(self):
        """Return live-device configuration widgets."""
        return column(self.device_select, self.num_channels_input, width=150)

    def set_config_enabled(self, enabled):
        """Enable or disable live-device configuration."""
        self.device_select.disabled = not enabled
        self.num_channels_input.disabled = not enabled
