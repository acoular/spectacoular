#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements classes for the use in live processing applications. Some of the 
classes might move to Acoular module in the future.

.. autosummary::
    :toctree: generated/

    TimeSamplesPhantom
    TimeOutPresenter
    CalibHelper
    TimeSamplesPlayback
"""
import acoular as ac
from acoular.deprecation import deprecated_alias

import numpy as np
from datetime import datetime
from time import time, sleep
from bokeh.models.widgets import TextInput, DataTable, TableColumn, \
    NumberEditor, NumericInput
from bokeh.models import ColumnDataSource
from traits.api import Property, File, CArray, Int, cached_property, on_trait_change, Float, Bool, Instance, List

from .dprocess import BasePresenter
from .factory import BaseSpectacoular

invch_columns = [TableColumn(field='invalid_channels', title='invalid_channels', editor=NumberEditor()),]

class TimeSamplesPhantom(ac.MaskedTimeSamples, BaseSpectacoular):
    """
    TimeSamples derived class for propagating signal processing blocks with
    user-defined time delay.
    
    The functionality of the class is to deliver existing blocks of data in a
    certain time interval. Can be used to simulate a measurement (but data
    is read from file).
    """

    #: Defines the delay with which the individual data blocks are propagated.
    #: Defaults to 1/sample_freq
    time_delay = Float(
        desc="Time interval between individual blocks of data")     
    
    #: Indicates if samples are collected, helper trait to break result loop
    collectsamples = Bool(True,
        desc="Indicates if result function is running")

    trait_widget_mapper = {'file': TextInput,
                        'basename': TextInput,
                        'start' : NumericInput,
                        'stop' : NumericInput,
                        'num_samples': NumericInput,
                        'sample_freq': NumericInput,
                        'invalid_channels': DataTable,
                        'num_channels' : NumericInput,
                        'time_delay': NumericInput,
                        }
    trait_widget_args = {'file': {'disabled': False},
                        'basename': {'disabled': True},
                        'start':  {'disabled': False, 'mode': 'int'},
                        'stop':  {'disabled': False, 'mode': 'int'},
                        'num_samples':  {'disabled': True, 'mode': 'int'},
                        'sample_freq':  {'disabled': True, 'mode': 'float'},
                        'invalid_channels': {'disabled': False, 'editable': True, 'columns': invch_columns},
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
        
        if self.time_delay:
            slp_time = self.time_delay
        else:
            slp_time = (1/self.sample_freq)*num
        
        if self.num_samples == 0:
            raise IOError("no samples available")
        i = 0
        if self.calib:
            if self.calib.num_mics == self.num_channels:
                cal_factor = self.calib.data[np.newaxis]
            else:
                raise ValueError("calibration data not compatible: %i, %i" % \
                            (self.calib.num_mics, self.num_channels))
            while i < self.num_samples and self.collectsamples:
                yield self.data[i:i+num]*cal_factor
                sleep(slp_time)
                i += num
        else:
            while i < self.num_samples and self.collectsamples:
                yield self.data[i:i+num]
                sleep(slp_time)
                i += num        
                
                
                
class TimeOutPresenter(ac.TimeOut, BasePresenter):
    """
    :class:`TimeOut` derived class for building an interface from Acoular's generator 
    pipelines to Bokeh's ColumnDataSource model that serves as a source for
    plots and tables.
    
    ColumnDataSource is updated from result function. Can be used for automatic
    presenting of live data.   
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
    """
    Class for calibration of individual source channels 
    """

    #: Data source; :class:`~acoular.sources.Average` or derived object.
    source = Instance(ac.Average)
    
    #: Name of the file to be saved. If none is given, the name will be
    #: automatically generated from a time stamp.
    file = File(filter=['*.xml'], desc="name of data file")

    #: calibration level (e. g. dB or Pa) of calibration device 
    magnitude = Float(114,
        desc="calibration level of calibration device")
    
    #: calibration values determined during evaluation of :meth:`result`.
    #: array of floats with dimension (num_channels, 2)
    calibdata = CArray(dtype=float,
       desc="determined calibration values")

    #: calibration factor determined during evaluation of :meth:`save`.
    #: array of floats with dimension (num_channels)
    calibfactor = CArray(dtype=float,
       desc="determined calibration factor")

    #: max elements/averaged blocks to calculate calibration value. 
    buffer_size = Int(100,
       desc="number of blocks considered to determine calibration value" )

    #: channel-wise allowed standard deviation of calibration values in buffer 
    calibstd = Float(.5,
       desc="allowed standard deviation of calibration values in buffer")

    #: minimum allowed difference in magnitude between the channel to be 
    #: calibrated and remaining channels.
    delta = Float(10,
      desc="magnitude difference between calibrating channel and remaining channels")
    
    # internal identifier
    digest = Property( depends_on = ['source.digest', '__class__'])

    trait_widget_mapper = {'file': TextInput,
                           'magnitude': NumericInput,
                           'buffer_size' : NumericInput,
                           'calibstd': NumericInput,
                           'delta': NumericInput,
                       }

    trait_widget_args = {'file': {'disabled': False},
                         'magnitude': {'disabled': False, 'mode': 'float'},
                         'buffer_size':  {'disabled': False, 'mode': 'int'},
                         'calibstd':  {'disabled': False, 'mode': 'float'},
                         'delta': {'disabled': False, 'mode': 'float'},
                         }
    
    def to_pa(self, level):
        return (10**(level/10))*(4e-10)

    @cached_property
    def _get_digest(self):
        return ac.internal.digest(self)

    @on_trait_change('source, source.num_channels')
    def adjust_calib_values(self):
        diff = self.num_channels - self.calibdata.shape[0]
        if self.calibdata.size == 0 or diff != 0:
            self.calibdata = np.zeros((self.num_channels, 2))

    def create_filename(self):
        if self.name == '':
            stamp = datetime.fromtimestamp(time()).strftime('%H:%M:%S')
            self.name = 'calib_file_' + stamp.replace(':', '') + '.xml'

    def save(self):
        self.create_filename()

        with open(self.name, 'w') as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n<Calib name="{self.name}">\n')
            for i in range(self.num_channels):
                channel_string = str(i + 1)
                fac = self.calibfactor[i]
                f.write(f'	<pos Name="Point {channel_string}" factor="{fac}"/>\n')
            f.write('</Calib>')
        #savetxt(self.name,self.calibdata,'%f')

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
            calibmask = np.logical_and(buffer > (self.magnitude - self.delta),
                                  buffer < (self.magnitude + self.delta)
                                  ).sum(0) 
            # print(calibmask)
            if (calibmask.max() == self.buffer_size) and (calibmask.sum() == self.buffer_size):
                idx = calibmask.argmax()
                # print(buffer[:,idx].std())
                if buffer[:,idx].std() < self.calibstd:
                    calibdata = self.calibdata.copy()
                    calibdata[idx, :] = [np.mean(buffer[:, idx]), self.magnitude]
                    # self.calibdata[idx,:] = [mean(L_p(buffer[:,idx])), self.magnitude]
                    self.calibdata = calibdata
                    print(self.calibdata[idx, :])
                        
            for i in np.arange(self.num_channels):
                self.calibfactor[i] = self.to_pa(self.magnitude) / self.to_pa(float(self.calibdata[i, 0]))
            yield temp
            

if ac.config.have_sounddevice:                
    import sounddevice as sd
    columns = [TableColumn(field='channels', title='channels', editor=NumberEditor()),]

    class TimeSamplesPlayback(ac.TimeOut, BaseSpectacoular):
        """
        Naive class implementation to allow audio playback of .h5 file contents. 
        
        The class uses the devices available to the sounddevice library for 
        audio playback. Input and output devices can be listed by
        
        >>>    import sounddevice
        >>>    sounddevice.query_devices()
        
        In the future, this class should work in buffer mode and 
        also write the current frame that is played to a class attribute.
        """
        
        # internal identifier
        digest = Property( depends_on = ['source.digest', '__class__'])
    
        #: list containing indices of the channels to be played back.
        channels = List(int,
            desc="channel indices to be played back")
        
        #: two-element list containing indices of input and output device to 
        #: be used for audio playback. 
        device = Property()
        
        # current frame played back
        # currentframe = Int()
        
        trait_widget_mapper = {'channels': DataTable,
                           }
    
        trait_widget_args = {'channels': {'disabled': False, 'columns': columns},
                         }
    
        @cached_property
        def _get_digest(self):
            return ac.internal.digest(self)
        
        def _get_device(self):
            return list(sd.default.device)
        
        def _set_device(self, device):
            sd.default.device = device
        
        def play(self):
            """
            normalized playback of source channels given by :attr:`channels` trait
            """
            if self.channels:
                if isinstance(self.source, ac.MaskedTimeSamples):
                    sig = self.source.data[
                        self.source.start:self.source.stop, self.channels].sum(1)
                else:
                    sig = self.source.data[:, self.channels].sum(1)
                norm = abs(sig).max()
                sd.play(sig / norm,
                        samplerate=self.sample_freq,
                        blocking=False)
            
        def stop(self):
            """method stops audio playback of file content"""
            sd.stop()

        def result(self, num):
            """simple generator that yields the output block-wise."""
            yield from self.source.result(num)