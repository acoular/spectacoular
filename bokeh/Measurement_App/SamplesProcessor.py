#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 13:23:25 2018

@author: adamkujawski
"""

from traits.api import Int, Instance, on_trait_change, Bool, Float, \
Dict, File, CArray
from threading import Thread
from numpy import shape,logical_and,savetxt,mean,array,newaxis,zeros,append
from datetime import datetime
from time import time,sleep
from scipy.signal import lfilter
from bokeh.models.widgets import TextInput, DataTable,TableColumn, NumberEditor

# acoular imports
from acoular import TimeInOut, TimeSamples,\
L_p,TimeAverage,FiltFiltOctave, SampleSplitter
                     
from spectacoular import BaseSpectacoular

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
    calibdata = CArray()

    #: max elements/averaged blocks in buffer to calculate calib value. 
    buffer_size = Int(100)

    # standarddeviation
    calibstd = Float(.5)

    #: delta of magnitude to consider a channels as calibrating
    delta = Float(10)
    
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

    @on_trait_change('numchannels')
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
            bufferidx = self.buffer_size-temp.shape[0]
            buffer[0:bufferidx] = buffer[-bufferidx:]  # copy remaining samples in front of next block
            buffer[-temp.shape[0]:,:] = L_p(temp)
            calibmask = logical_and(buffer > (self.magnitude-self.delta),
                                  buffer < (self.magnitude+self.delta)
                                  ).sum(0) 
            if (calibmask.max() == nc) and (calibmask.sum() == nc):
                idx = calibmask.argmax()
                if buffer[:,idx].std() < self.calibstd:
                    self.calibdata[idx,:] = [mean(L_p(buffer[:,idx])), self.magnitude]
            yield temp
                                             
            
class LastInOut(TimeInOut):
    
    source = Instance(SampleSplitter)
    
    def result(self,num):
        for temp in self.source.result(num):
#            if len(self.source.buffer[self]) >= 1: pass
#            else:
            anz = min(num,shape(temp)[0])
            yield temp[:anz]
            self.source._clear_block_buffer(self)


class EventThread(Thread):
    
    def __init__(self,event,doc,pre_callback=None, post_callback=None):
        Thread.__init__(self)
        self.pre_callback = pre_callback
        self.post_callback = post_callback
        self.doc = doc
        self.event = event
        
    def run(self):
        if self.pre_callback: 
            self.doc.add_next_tick_callback(self.pre_callback)
        self.event.wait()
        if self.post_callback:
            self.doc.add_next_tick_callback(self.post_callback)
        return    

class SamplesThread(Thread):
    '''
    event is set when thread finishes
    '''
    
    def __init__(self,samplesGen,splitterObj,splitterDestination,event=None):
        Thread.__init__(self)
        self.splitterObj = splitterObj
        self.splitterDestination = splitterDestination
        self.samplesGen = samplesGen
        self.event = event
        self.breakThread = False
        
    def run(self):
        if self.event: self.event.clear()
        self.splitterObj.register_object(self.splitterDestination)
        while not self.breakThread:
            try:
                next(self.samplesGen)
            except StopIteration: 
                break
            except Exception as e_text:
                print(e_text)
                break
        if self.event: 
            self.event.set()
        self.splitterObj.remove_object(self.splitterDestination)
        return
                                
class TimeSamplesPhantom(TimeSamples):

    time_delay = Float()        
    
    #: Indicates if samples are collected, helper trait to break result loop
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


class FiltOctaveLive( FiltFiltOctave ):
    """
    Octave or third-octave filter (not zero-phase).
    """

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

