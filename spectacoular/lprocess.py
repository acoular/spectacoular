# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements classes for live processing.

.. autosummary::
    :toctree: generated/

    TimeSamplesPhantom
    TimeInOutPresenter
"""
 
from numpy import logical_and,savetxt,mean,array,newaxis, zeros
from scipy.signal import lfilter
from datetime import datetime
from time import time,sleep
from bokeh.models.widgets import TextInput,DataTable,TableColumn, NumberEditor

from bokeh.models import ColumnDataSource, LogColorMapper, ColorBar
from traits.api import Property, File, CArray,Int,\
cached_property, on_trait_change, Float,Bool, Instance, ListInt
import sounddevice as sd

# acoular imports
from acoular import TimeInOut, L_p,TimeAverage,FiltFiltOctave, MaskedTimeSamples
from acoular.internal import digest
# 
from .dprocess import BasePresenter
from .bokehview import get_widgets, set_widgets
from .factory import BaseSpectacoular



class TimeSamplesPhantom(MaskedTimeSamples):

    time_delay = Float()     
    
    # Indicates if samples are collected, helper trait to break result loop
    collectsamples = Bool(True,
        desc="Indicates if samples are collected")

    get_widgets = get_widgets
    
    set_widgets = set_widgets
    
    trait_widget_mapper = {'name': TextInput,
                           'basename': TextInput,
                           'start' : TextInput,
                           'stop' : TextInput,
                           'numsamples': TextInput,
                           'sample_freq': TextInput,
                           'invalid_channels':TextInput,
                           'numchannels' : TextInput,
                           'time_delay': TextInput,
                       }

    trait_widget_args = {'name': {'disabled':False},
                         'basename': {'disabled':True},
                         'start':  {'disabled':False},
                         'stop':  {'disabled':False},
                         'numsamples':  {'disabled':True},
                         'sample_freq':  {'disabled':True},
                         'invalid_channels': {'disabled':False},
                         'numchannels': {'disabled':True},
                         'time_delay': {'disabled':False},
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
        Samples in blocks of shape (num, numchannels). 
            The last block may be shorter than num.
        """
        
        if self.time_delay:
            slp_time = self.time_delay
        else:
            slp_time = (1/self.sample_freq)*num
        
        if self.numsamples == 0:
            raise IOError("no samples available")
        i = 0
        if self.calib:
            if self.calib.num_mics == self.numchannels:
                cal_factor = self.calib.data[newaxis]
            else:
                raise ValueError("calibration data not compatible: %i, %i" % \
                            (self.calib.num_mics, self.numchannels))
            while i < self.numsamples and self.collectsamples:
                yield self.data[i:i+num]*cal_factor
                sleep(slp_time)
                i += num
        else:
            while i < self.numsamples and self.collectsamples:
                yield self.data[i:i+num]
                sleep(slp_time)
                i += num        
                
                
class TimeInOutPresenter(TimeInOut,BasePresenter):
    """
    Base Class for presenting of live data
    
    ColumnDataSource is updated from data trait.
    
    Generator fashion
    """       

    data = ColumnDataSource(data={'data':array([])}) # does not need to be a ColumnDataSource, a simple dict might be enough here

    def result(self,num):
        for temp in self.source.result(num):
            self.data.data['data'] = temp
            yield temp

                

class TimeSamplesPlayback(TimeInOut,BaseSpectacoular):
    """
    In the future, this class should work in buffer mode and 
    also write the current frame that is played to its columndatasource.
    """
    
    # internal identifier
    digest = Property( depends_on = ['source.digest', '__class__'])

    #: index of the channel to play
    channels = ListInt()
    
    # device property
    device = Property()
    
    # current frame played back
    # currentframe = Int()
    
    trait_widget_mapper = {'channels': TextInput,
                       }

    trait_widget_args = {'channels': {'disabled':False},
                     }

    @cached_property
    def _get_digest( self ):
        return digest(self)
    
    def _get_device( self ):
        return list(sd.default.device)
    
    def _set_device( self, device ):
        sd.default.device = device
    
    def play( self ):
        '''
        normalized playback of channel
        '''
        if self.channels:
            if isinstance(self.source,MaskedTimeSamples):
                sig = self.source.data[
                    self.source.start:self.source.stop,self.channels].sum(1)
            else:
                sig = self.source.data[:,self.channels].sum(1)
            norm = abs(sig).max()
            sd.play(sig/norm,
                    samplerate=self.sample_freq,
                    blocking=False)
        
    def stop( self ):
        '''
        simply stops playback of file
        '''
        sd.stop()
    
    
    
columns = [TableColumn(field='calibvalue', title='calibvalue', editor=NumberEditor()),
           TableColumn(field='caliblevel', title='caliblevel', editor=NumberEditor())]

class CalibHelper(TimeInOut, BaseSpectacoular):
    
    '''
    Only in chain with TimeAverage!
    '''
    
    source = Instance(TimeAverage)
    
    #: Name of the file to be saved. If none is given, the name will be
    #: automatically generated from a time stamp.
    name = File(filter=['*.txt'], 
        desc="name of data file")    

    #: calibration level [dB] or pressure [Pa] of calibration device 
    magnitude = Float(114)
    
    # calib values of source channels
    calibdata = CArray(dtype=float)

    #: max elements/averaged blocks in buffer to calculate calib value. 
    buffer_size = Int(100)

    # standarddeviation
    calibstd = Float(.5)

    #: delta of magnitude to consider a channels as calibrating
    delta = Float(10)
    
    # internal identifier
    digest = Property( depends_on = ['source.digest', '__class__'])

    trait_widget_mapper = {'name': TextInput,
                           'magnitude': TextInput,
                            'calibdata' : DataTable,
                           'buffer_size' : TextInput,
                           'calibstd': TextInput,
                           'delta': TextInput,
                       }

    trait_widget_args = {'name': {'disabled':False},
                         'magnitude': {'disabled':False},
                           'calibdata':  {'editable':True,'columns':columns},
                         'buffer_size':  {'disabled':False},
                         'calibstd':  {'disabled':False},
                         'delta': {'disabled':False},
                         }

    @cached_property
    def _get_digest( self ):
        return digest(self)

    @on_trait_change('source, source.numchannels')
    def adjust_calib_values(self):
        diff = self.numchannels-self.calibdata.shape[0]
        if self.calibdata.size == 0 or diff != 0:
            self.calibdata = zeros((self.numchannels,2))

    def create_filename(self):
        if self.name == '':
            stamp = datetime.fromtimestamp(time()).strftime('%H:%M:%S')
            self.name = 'calib_file_'+stamp.replace(':','')+'.out'

    def save(self):
        self.create_filename()
        savetxt(self.name,self.calibdata,'%f')

    def result(self, num):
        """
        Parameters
        ----------
        num : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self.adjust_calib_values()
        nc = self.numchannels
        buffer = zeros((self.buffer_size,nc))
        for temp in self.source.result(num):
            ns = temp.shape[0]
            bufferidx = self.buffer_size-ns
            buffer[0:bufferidx] = buffer[-bufferidx:]  # copy remaining samples in front of next block
            buffer[-ns:,:] = L_p(temp)
            calibmask = logical_and(buffer > (self.magnitude-self.delta),
                                  buffer < (self.magnitude+self.delta)
                                  ).sum(0) 
            # print(calibmask)
            if (calibmask.max() == nc) and (calibmask.sum() == nc):
                idx = calibmask.argmax()
                # print(buffer[:,idx].std())
                if buffer[:,idx].std() < self.calibstd:
                    calibdata = self.calibdata.copy()
                    calibdata[idx,:] = [mean(L_p(buffer[:,idx])), self.magnitude]
                    # self.calibdata[idx,:] = [mean(L_p(buffer[:,idx])), self.magnitude]
                    self.calibdata = calibdata
                    # print(self.calibdata[idx,:])
            yield temp
            
            
class FiltOctaveLive( FiltFiltOctave, BaseSpectacoular ):
    """
    Octave or third-octave filter (not zero-phase).
    """

    trait_widget_mapper = {'band': TextInput,
                       }

    trait_widget_args = {'band': {'disabled':False},
                         }

    def result(self, num):
        """ 
        Python generator that yields the output block-wise.

        
        Parameters
        ----------
        num : integer
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (num, numchannels). 
            Delivers the bandpass filtered output of source.
            The last block may be shorter than num.
        """
        
        for block in self.source.result(num):
            b, a = self.ba(3) # filter order = 3
            zi = zeros((max(len(a), len(b))-1, self.source.numchannels))
            block, zi = lfilter(b, a, block, axis=0, zi=zi)
            yield block
