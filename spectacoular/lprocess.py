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
 
from numpy import delete, arange,shape, concatenate, where,logical_and,savetxt,\
mean,array,newaxis, zeros
from time import sleep
from bokeh.layouts import column, row
from bokeh.palettes import viridis, plasma, inferno, magma
from bokeh.models.widgets import MultiSelect, TextInput, Button, RangeSlider,\
CheckboxGroup, Select, Dropdown,Toggle
from bokeh.models import ColumnDataSource, LogColorMapper, ColorBar
from traits.api import Trait, HasPrivateTraits, Property, \
cached_property, on_trait_change, List,Float,Bool,Any, Instance, ListInt
import sounddevice as sd

# acoular imports
from acoular import SamplesGenerator, TimeInOut, TimeSamples,\
L_p,TimeAverage,FiltFiltOctave, TimePower, MaskedTimeSamples
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
            sig = zeros((self.source.numsamples))
            for idx in self.channels:
                sig += self.source.data[self.source.start:self.source.stop,idx]
            norm = abs(sig).max()
            sd.play(sig/norm,
                    samplerate=self.sample_freq,
                    blocking=False)
        
    def stop( self ):
        '''
        simply stops playback of file
        '''
        sd.stop()
    
    
