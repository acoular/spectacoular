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
    TimeAveragePresenter
"""
 
from numpy import delete, arange,shape, concatenate, where,logical_and,savetxt,\
mean,array,newaxis, zeros
from time import sleep
from bokeh.layouts import column, row
from bokeh.palettes import viridis, plasma, inferno, magma
from bokeh.models.widgets import MultiSelect, TextInput, Button, RangeSlider,\
CheckboxGroup, Select, Dropdown
from bokeh.models import ColumnDataSource, LogColorMapper, ColorBar
from traits.api import Trait, HasPrivateTraits, Property, \
cached_property, on_trait_change, List,Float,Bool,Any
# acoular imports
from acoular import SamplesGenerator, TimeInOut, TimeSamples,\
L_p,TimeAverage,FiltFiltOctave, TimePower, MaskedTimeSamples

# 
from .dprocess import BasePresenter

def noneFunc(x): return x

class TimeSamplesPhantom(MaskedTimeSamples):

    time_delay = Float()        
    
    # Indicates if samples are collected, helper trait to break result loop
    collectsamples = Bool(True,
        desc="Indicates if samples are collected")
    
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

                
class TimeAveragePresenter(TimeInOutPresenter):
    
    #: Data source; :class:`~acoular.sources.TimeAverage` or derived object.
    source = Trait(TimeAverage)
    
    y_transform = Trait('L_p', 
        {'L_p':L_p, 
        'None':noneFunc})
    
    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(data={'x':[],'y':[]})
        HasPrivateTraits.__init__(self,*args,**kwargs)

    def update(self):
        numchannels = self.data.data['data'].shape[1]
        if self.data.data['data'].shape[0] > 0:
            newData = {'x':list(range(0,numchannels)),
                       'y':self.y_transform_(self.data.data['data'][0])}  
            self.cdsource.stream(newData,rollover=self.numchannels)
#            self.cdsource.data = newData     


class TimeSignalLivePresenter(TimeInOutPresenter):
    """
            
    """

    #: Data source; :class:`~acoular.sources.TimeSamples` or derived object.
    source = Trait(TimeSamples)
    
    #: MultiSelect widget to select one or multiple channels to be plotted
    selectChannel = Select(title="Select Channel:", options=[])

#    # read only property. Holds Select color widgets of selected channels    
#    colorSelector = column(column())
#    
#    #: a list of possible colors that can be assigned to selected channels
#    lineColors = List(viridis(10))
    
    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(data={'xs':[],'ys':[]})
        HasPrivateTraits.__init__(self,*args,**kwargs)
#        self.selectChannel.on_change('value',self.change_color_select)
        self._widgets = [self.selectChannel]

    @on_trait_change("digest")
    def change_channel_selector(self):
        channels = [idx for idx in range(self.source.numchannels)]
        if hasattr(self.source,'invalid_channels'):
            [channels.remove(idx) for idx in self.source.invalid_channels]
        channels = [str(ch) for ch in channels]
        self.selectChannel.options = channels
        self.selectChannel.value = channels[0]

    def update(self):
        if self.data.data['data'].shape[0] > 0:
            sRange = (0,self.data.data['data'].shape[0])
            samples = list(range(sRange[0],sRange[1]))
            idx = int(self.selectChannel.value)
            newData = {
                'xs' : samples,
                'ys' : list(self.data.data['data'][sRange[0]:sRange[1],int(idx)]),
                }
            self.cdsource.stream(newData,rollover=sRange[1])
        else:
            self.cdsource.data = {'xs' :[],'ys' :[]}                
