# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------
"""Implement classes for use in live processing applications.

Some of these classes might move to the Acoular module in the future.

.. autosummary::
    :toctree: generated/

    TimeSamplesPhantom
    TimeOutPresenter
    CalibHelper
    TimeSamplesPlayback
"""

from datetime import UTC, datetime
from pathlib import Path
from time import sleep, time
from typing import ClassVar

import acoular as ac
from acoular.deprecation import deprecated_alias

from .dprocess import BasePresenter
from .factory import BaseSpectacoular

import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import (
    DataTable,
    NumberEditor,
    NumericInput,
    TableColumn,
    TextInput,
)
from traits.api import (
    Bool,
    CArray,
    File,
    Float,
    Instance,
    Int,
    List,
    Property,
    cached_property,
    on_trait_change,
)

invch_columns = [
    TableColumn(field='invalid_channels', title='invalid_channels', editor=NumberEditor()),
]


class TimeSamplesPhantom(ac.MaskedTimeSamples, BaseSpectacoular):
    """Propagate signal-processing blocks with a user-defined time delay.

    This class delivers existing blocks of data at a configurable time
    interval. It can be used to simulate a measurement while reading the data
    from file.
    """

    #: Defines the delay with which the individual data blocks are propagated.
    #: Defaults to 1/sample_freq
    time_delay = Float(desc='Time interval between individual blocks of data')

    #: Indicates if samples are collected, helper trait to break result loop
    collect_samples = Bool(default_value=True, desc='Indicates if result function is running')

    trait_widget_mapper: ClassVar[dict[str, type]] = {
        'file': TextInput,
        'basename': TextInput,
        'start': NumericInput,
        'stop': NumericInput,
        'num_samples': NumericInput,
        'sample_freq': NumericInput,
        'invalid_channels': DataTable,
        'num_channels': NumericInput,
        'time_delay': NumericInput,
    }
    trait_widget_args: ClassVar[dict[str, dict[str, object]]] = {
        'file': {'disabled': False},
        'basename': {'disabled': True},
        'start': {'disabled': False, 'mode': 'int'},
        'stop': {'disabled': False, 'mode': 'int'},
        'num_samples': {'disabled': True, 'mode': 'int'},
        'sample_freq': {'disabled': True, 'mode': 'float'},
        'invalid_channels': {
            'disabled': False,
            'editable': True,
            'columns': invch_columns,
        },
        'num_channels': {'disabled': True, 'mode': 'int'},
        'time_delay': {'disabled': False, 'mode': 'float'},
    }

    def result(self, num=128):
        """
        Python generator that yields the output block-wise.

        Parameters
        ----------
        num : integer, defaults to 128
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .

        Returns
        -------
        Samples in blocks of shape (num, num_channels).
            The last block may be shorter than num.
        """
        slp_time = self.time_delay or (1 / self.sample_freq) * num

        if self.num_samples == 0:
            msg = 'no samples available'
            raise OSError(msg)
        i = 0
        while i < self.num_samples and self.collect_samples:
            yield self.data[i : i + num]
            sleep(slp_time)
            i += num


class TimeOutPresenter(ac.TimeOut, BasePresenter):
    """Present live Acoular output through a Bokeh ``ColumnDataSource``.

    This :class:`TimeOut`-derived class updates the ``ColumnDataSource`` from
    its ``result`` method and can be used for automatic presentation of live
    data.
    """

    #: Bokeh's ColumnDataSource, updated from result loop
    cdsource = Instance(ColumnDataSource, kw={'data': {'data': np.array([])}})

    def result(self, num):
        """
        Python generator that yields the output block-wise.

        Parameters
        ----------
        num : integer, defaults to 128
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .

        Returns
        -------
        Samples in blocks of shape (num, num_channels).
            The last block may be shorter than num.
        """
        for temp in self.source.result(num):
            self.cdsource.data['data'] = temp
            yield temp


@deprecated_alias({'name': 'file'})
class CalibHelper(ac.TimeOut, BaseSpectacoular):
    """Calibrate individual source channels."""

    #: Data source; :class:`~acoular.sources.Average` or derived object.
    source = Instance(ac.Average)

    #: Name of the file to be saved. If none is given, the name will be
    #: automatically generated from a time stamp.
    file = File(filter=['*.xml'], desc='name of data file')

    #: calibration level (e. g. dB or Pa) of calibration device
    magnitude = Float(114, desc='calibration level of calibration device')

    #: calibration values determined during evaluation of :meth:`result`.
    #: array of floats with dimension (num_channels, 2)
    calibdata = CArray(dtype=float, desc='determined calibration values')

    #: calibration factor determined during evaluation of :meth:`save`.
    #: array of floats with dimension (num_channels)
    calibfactor = CArray(dtype=float, desc='determined calibration factor')

    #: max elements/averaged blocks to calculate calibration value.
    buffer_size = Int(100, desc='number of blocks considered to determine calibration value')

    #: channel-wise allowed standard deviation of calibration values in buffer
    calibstd = Float(0.5, desc='allowed standard deviation of calibration values in buffer')

    #: minimum allowed difference in magnitude between the channel to be
    #: calibrated and remaining channels.
    delta = Float(
        10,
        desc='magnitude difference between calibrating channel and remaining channels',
    )

    # internal identifier
    digest = Property(depends_on=['source.digest', '__class__'])

    trait_widget_mapper: ClassVar[dict[str, type]] = {
        'file': TextInput,
        'magnitude': NumericInput,
        'buffer_size': NumericInput,
        'calibstd': NumericInput,
        'delta': NumericInput,
    }

    trait_widget_args: ClassVar[dict[str, dict[str, object]]] = {
        'file': {'disabled': False},
        'magnitude': {'disabled': False, 'mode': 'float'},
        'buffer_size': {'disabled': False, 'mode': 'int'},
        'calibstd': {'disabled': False, 'mode': 'float'},
        'delta': {'disabled': False, 'mode': 'float'},
    }

    def to_pa(self, level):
        """Convert a sound level to pressure in pascal."""
        return (10 ** (level / 10)) * (4e-10)

    @cached_property
    def _get_digest(self):
        return ac.internal.digest(self)

    @on_trait_change('source, source.num_channels')
    def adjust_calib_values(self):
        """Resize calibration arrays to match the number of source channels."""
        diff = self.num_channels - self.calibdata.shape[0]
        if self.calibdata.size == 0 or diff != 0:
            self.calibdata = np.zeros((self.num_channels, 2))

    def create_filename(self):
        """Create a default filename for calibration output if none is set."""
        if self.name == '':
            stamp = datetime.fromtimestamp(time(), tz=UTC).strftime('%H:%M:%S')
            self.name = 'calib_file_' + stamp.replace(':', '') + '.xml'

    def save(self):
        """Save the current calibration factors as an XML file."""
        self.create_filename()

        with Path(self.name).open('w') as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n<Calib name="{self.name}">\n')
            for i in range(self.num_channels):
                channel_string = str(i + 1)
                fac = self.calibfactor[i]
                f.write(f'	<pos Name="Point {channel_string}" factor="{fac}"/>\n')
            f.write('</Calib>')
        # savetxt(self.name,self.calibdata,'%f')

    def result(self, num):
        """
        Python generator that yields the output block-wise.

        Parameters
        ----------
        num : integer, defaults to 128
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .

        Returns
        -------
        Samples in blocks of shape (num, num_channels).
            The last block may be shorter than num.
        """
        self.adjust_calib_values()
        nc = self.num_channels
        self.calibfactor = np.zeros(self.num_channels)
        buffer = np.zeros((self.buffer_size, nc))
        for temp in self.source.result(num):
            ns = temp.shape[0]
            bufferidx = self.buffer_size - ns
            buffer[0:bufferidx] = buffer[-bufferidx:]  # copy remaining samples in front of next block
            buffer[-ns:, :] = ac.L_p(temp)
            calibmask = np.logical_and(
                buffer > (self.magnitude - self.delta),
                buffer < (self.magnitude + self.delta),
            ).sum(0)
            # print(calibmask)
            if (calibmask.max() == self.buffer_size) and (calibmask.sum() == self.buffer_size):
                idx = calibmask.argmax()
                # print(buffer[:,idx].std())
                if buffer[:, idx].std() < self.calibstd:
                    calibdata = self.calibdata.copy()
                    calibdata[idx, :] = [np.mean(buffer[:, idx]), self.magnitude]
                    # self.calibdata[idx,:] = [mean(L_p(buffer[:,idx])), self.magnitude]
                    self.calibdata = calibdata

            for i in np.arange(self.num_channels):
                self.calibfactor[i] = self.to_pa(self.magnitude) / self.to_pa(float(self.calibdata[i, 0]))
            yield temp


if ac.config.have_sounddevice:
    import sounddevice as sd

    columns = [
        TableColumn(field='channels', title='channels', editor=NumberEditor()),
    ]

    class TimeSamplesPlayback(ac.TimeOut, BaseSpectacoular):
        """
        Naive class implementation to allow audio playback of .h5 file contents.

        The class uses the devices available to the sounddevice library for
        audio playback. Input and output devices can be listed by

        >>> import sounddevice
        >>> sounddevice.query_devices()  # doctest: +SKIP

        In the future, this class should work in buffer mode and
        also write the current frame that is played to a class attribute.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if ac.config.have_sounddevice is False:
                msg = f'SoundDevice library not found but is required for using {self.__class__}.'
                raise ImportError(msg)

        # internal identifier
        digest = Property(depends_on=['source.digest', '__class__'])

        #: list containing indices of the channels to be played back.
        channels = List(int, desc='channel indices to be played back')

        #: two-element list containing indices of input and output device to
        #: be used for audio playback.
        device = Property()

        # current frame played back
        # currentframe = Int()

        trait_widget_mapper: ClassVar[dict[str, type]] = {
            'channels': DataTable,
        }

        trait_widget_args: ClassVar[dict[str, dict[str, object]]] = {
            'channels': {'disabled': False, 'columns': columns},
        }

        @cached_property
        def _get_digest(self):
            return ac.internal.digest(self)

        def _get_device(self):
            return list(sd.default.device)

        def _set_device(self, device):
            sd.default.device = device

        def play(self):
            """Play normalized audio from the source channels in :attr:`channels`."""
            if self.channels:
                if isinstance(self.source, ac.MaskedTimeSamples):
                    sig = self.source.data[self.source.start : self.source.stop, self.channels].sum(1)
                else:
                    sig = self.source.data[:, self.channels].sum(1)
                norm = abs(sig).max()
                sd.play(sig / norm, samplerate=self.sample_freq, blocking=False)

        def stop(self):
            """Stop audio playback of the file content."""
            sd.stop()

        def result(self, num):
            """Yield the output block-wise."""
            yield from self.source.result(num)
