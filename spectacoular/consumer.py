#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements consumer classes that provide Acoular data to Bokeh data sources

.. autosummary::
    :toctree: generated/
    
    TimeConsumer
    TimeBandsConsumer
"""
import threading
from numpy import arange
from acoular import TimeInOut
from bokeh.models import ColumnDataSource
from traits.api import List, Int, Trait, Float, Array, Property, on_trait_change,\
    cached_property, Callable 




class TimeConsumer(TimeInOut):
    """
    :class:`TimeInOut` derived class for building an interface from Acoular's generator 
    pipelines to Bokeh's ColumnDataSource model that serves as a source for
    plots and tables.
    
    How it works:
    :meth:`consume` runs in an extra non-GUI :attr:`thread` (must be set up by the user)
    and fetches blocks of data  with length :attr:`num` from :attr:`source`. 
    These blocks are stored in :attr:`data` and :meth:`update` is then registered 
    as a callback for GUI event loop. :meth:`update` then sends the data, downsampled 
    by a factor :attr:`down` to ColumnDataSource :meth:`ds`, which holds an overall 
    length of :attr:`rollover` samples. The elapsed time in seconds is stored in :attr:`elapsed`
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

    @on_trait_change('channels,source.numchannels')
    def init_ds(self):
        data = {}
        data['t'] = []
        for ch in self.ch_names():
            data[ch] = []
        if not self.ds:
            self.ds = ColumnDataSource()
        self.ds.data = data # ColumnDataSource wants all columns at once

    def ch_names(self):
        """
        generator that returns channel names, helper for iterating over channels
        """
        chan = self.channels
        for ch in chan:
            yield 'timedata{}'.format(ch)


    def consume(self,doc):
        """ 
        consumes samples from source, to be run in an extra non-GUI thread

        Args:
            doc: server document to register callbacks to
        """
        self.elapsed = 0.0
        self.updated = threading.Event()
        self.updated.set()
        doc.add_next_tick_callback(self.init_ds)
        for temp in self.source.result(self.num):
            if not getattr(self.thread, "do_run", True):
                break
            self.updated.wait()
            self.data = temp
            self.updated.clear()
            doc.add_next_tick_callback(self.update)


    def update(self):
        """ callback function for GUI event loop, updates data source
        """
        if not self.updated.is_set():
            newdata = {}
            newdata['t'] = self.down*arange(self.num/self.down)/self.sample_freq + self.elapsed
            self.elapsed += self.num/self.sample_freq
            for i,ch in zip(self.channels,self.ch_names()):
                newdata[ch] = self.data[::self.down,i]
            self.ds.stream(newdata, rollover=self.rollover)
            self.updated.set()

    def result(self,num):
        """
        Python generator that yields the output block-wise. Does nothing in this class.
        """
        pass

class TimeBandsConsumer(TimeConsumer):
    """
    :class:`TimeConsumer` derived class for building an interface from Acoular's generator 
    pipelines to Bokeh's ColumnDataSource which specialises in Plots over frequency bands
    (like octave spectrum)

    Works like :class:`TimeConsumer`, but ignores :attr:`down` and :attr:`rollover`. Instead,
    just the first sample of each block is taken from the input. :attr:`ds` has a column for 
    each input channel with one frequency band value in each row. :attr:`bands` gives the bands
    and :attr:`lfunc` can be used to convert to human-readable label strings.
    """
    #: Function to convert bands into list of labels
    lfunc = Callable( lambda bands: ["{:.0f}".format(f) for f in bands])

    #: List of labels for bands
    bands = Property( depends_on = ['source.digest'])

    #: Number of bands
    numbands = Property( depends_on = ['source.digest'])

    @cached_property
    def _get_bands(self):
        obj = self.source # start with source
        bands = [1] # if no FilterBank or similar is found
        while obj:
            if 'bands' in obj.all_trait_names(): # at FilterBank?
                bands = obj.bands # get the name
                break
            else:
                try:
                    obj = obj.source # traverse down until FilterBank
                except AttributeError:
                    obj = None
        return bands

    @cached_property
    def _get_numbands(self):
        obj = self.source # start with source
        numbands = 1 # if no FilterBank or similar is found
        while obj:
            if 'numbands' in obj.all_trait_names(): # at FilterBank?
                numbands = obj.numbands # get the name
                break
            else:
                try:
                    obj = obj.source # traverse down until FilterBank
                except AttributeError:
                    obj = None
        return numbands

    def update(self):
        """ callback function for GUI event loop, updates data source
        """
        if not self.updated.is_set():
            newdata = {}
            newdata['t'] = self.lfunc(self.bands)
            self.elapsed += self.num/self.sample_freq
            data = self.data[0].reshape((self.numbands,-1))
            for i,ch in zip(self.channels,self.ch_names()):
                newdata[ch] = data[:,i]
            self.ds.data = newdata
            self.updated.set()
