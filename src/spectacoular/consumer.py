# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------
"""Implement consumer classes that provide Acoular data to Bokeh data sources.

.. autosummary::
    :toctree: generated/

    TimeConsumer
    TimeBandsConsumer
"""

import threading

from acoular import TimeOut

import numpy as np
from bokeh.models import ColumnDataSource
from traits.api import (
    Array,
    Callable,
    Float,
    Int,
    List,
    Property,
    Trait,
    cached_property,
    on_trait_change,
)


class TimeConsumer(TimeOut):
    """Provide Acoular time data to a Bokeh ``ColumnDataSource``.

    This :class:`TimeOut`-derived class builds an interface from Acoular's
    generator pipelines to Bokeh's ``ColumnDataSource`` model for plots and
    tables.

    :meth:`consume` runs in an extra non-GUI :attr:`thread` and fetches blocks
    of data with length :attr:`num` from :attr:`source`. These blocks are stored
    in :attr:`data`, and :meth:`update` is then registered as a callback for the
    GUI event loop. :meth:`update` sends the data, downsampled by a factor
    :attr:`down`, to :attr:`ds`, which holds an overall length of
    :attr:`rollover` samples. The elapsed time in seconds is stored in
    :attr:`elapsed`.
    """

    #: Bokeh's ColumnDataSource, updated from result loop
    ds = Trait(ColumnDataSource)

    #: channels to have in the output
    channels = List(Int)

    #: input block size
    num = Int(128)

    #: downsampling factor for output
    down = Int(8)

    #: total length of columns in ds
    rollover = Int(8192)

    #: thread in which :meth:`consume` runs
    thread = Trait(threading.Thread)

    #: elapsed time in data
    elapsed = Float(0)

    #: flag for update / consume
    updated = Trait(threading.Event)

    #: transport between consume / update
    data = Array

    @on_trait_change('channels,source.num_channels')
    def init_ds(self):
        """Initialize the ``ColumnDataSource`` with channel columns."""
        data = {}
        data['t'] = []
        for ch in self.ch_names():
            data[ch] = []
        if not self.ds:
            self.ds = ColumnDataSource()
        self.ds.data = data  # ColumnDataSource wants all columns at once

    def ch_names(self):
        """Yield channel names for iterating over channels."""
        chan = self.channels
        for ch in chan:
            yield f'timedata{ch}'

    def consume(self, doc):
        """Consume samples from the source in a non-GUI thread.

        Parameters
        ----------
        doc
            Server document used to register callbacks.

        """
        self.elapsed = 0.0
        self.updated = threading.Event()
        self.updated.set()
        doc.add_next_tick_callback(self.init_ds)
        for temp in self.source.result(self.num):
            if not getattr(self.thread, 'do_run', True):
                break
            self.updated.wait()
            self.data = temp
            self.updated.clear()
            doc.add_next_tick_callback(self.update)

    def update(self):
        """Update the data source from the GUI event loop."""
        if not self.updated.is_set():
            newdata = {}
            newdata['t'] = self.down * np.arange(self.num / self.down) / self.sample_freq + self.elapsed
            self.elapsed += self.num / self.sample_freq
            for i, ch in zip(self.channels, self.ch_names(), strict=False):
                newdata[ch] = self.data[:: self.down, i]
            self.ds.stream(newdata, rollover=self.rollover)
            self.updated.set()

    def result(self, num):
        """Yield the output block-wise.

        This method does nothing in this class.

        """


class TimeBandsConsumer(TimeConsumer):
    """Provide frequency-band data to a Bokeh ``ColumnDataSource``.

    This :class:`TimeConsumer`-derived class specializes in plots over
    frequency bands, such as octave spectra.

    It works like :class:`TimeConsumer`, but ignores :attr:`down` and
    :attr:`rollover`. Instead, only the first sample of each block is taken
    from the input. :attr:`ds` has a column for each input channel with one
    frequency-band value in each row. :attr:`bands` gives the bands, and
    :attr:`lfunc` can be used to convert them to human-readable label strings.
    """

    #: Function to convert bands into list of labels
    lfunc = Callable(lambda bands: [f'{f:.0f}' for f in bands])

    #: List of labels for bands
    bands = Property(depends_on=['source.digest'])

    #: Number of bands
    numbands = Property(depends_on=['source.digest'])

    @cached_property
    def _get_bands(self):
        obj = self.source  # start with source
        bands = [1]  # if no FilterBank or similar is found
        while obj:
            if 'bands' in obj.all_trait_names():  # at FilterBank?
                bands = obj.bands  # get the name
                break
            try:
                obj = obj.source  # traverse down until FilterBank
            except AttributeError:
                obj = None
        return bands

    @cached_property
    def _get_numbands(self):
        obj = self.source  # start with source
        numbands = 1  # if no FilterBank or similar is found
        while obj:
            if 'numbands' in obj.all_trait_names():  # at FilterBank?
                numbands = obj.numbands  # get the name
                break
            try:
                obj = obj.source  # traverse down until FilterBank
            except AttributeError:
                obj = None
        return numbands

    def update(self):
        """Update the data source from the GUI event loop."""
        if not self.updated.is_set():
            newdata = {}
            newdata['t'] = self.lfunc(self.bands)
            self.elapsed += self.num / self.sample_freq
            data = self.data[0].reshape((self.numbands, -1))
            for i, ch in zip(self.channels, self.ch_names(), strict=False):
                newdata[ch] = data[:, i]
            self.ds.data = newdata
            self.updated.set()
