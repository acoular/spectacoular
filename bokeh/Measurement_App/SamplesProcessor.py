#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 13:23:25 2018

@author: adamkujawski
"""


from traits.api import Dict, Int, Instance, Property,cached_property, Delegate,\
on_trait_change, Trait,List,HasTraits,Str,Bool, Float, CLong,File,Array  
from collections import deque
from inspect import currentframe
import threading
from threading import Thread
from functools import partial
from tornado import gen
from numpy import delete, arange,shape, concatenate, where,logical_and,savetxt,\
mean,array,newaxis, zeros
import warnings
from six import next
from traitsui.api import View, Item
from traitsui.menu import OKCancelButtons
from os import path
import tables
from datetime import datetime
from time import time,sleep
from scipy.signal import butter, lfilter, filtfilt

# acoular imports
from acoular import SamplesGenerator, TimeInOut, TimeSamples,\
L_p,TimeAverage,FiltFiltOctave, SampleSplitter
from acoular.internal import digest
from acoular.h5cache import td_dir

                    

class CalibHelper(TimeInOut):
    
    '''
    Only in chain with TimePower!
    '''
    
    source = Instance(TimeAverage)
    
    calib_level = Float(114)
    
    calib_delta = Float(10)
    
    calib_value = List([])
    
    iscalib = Bool(False)
    
    calib_nblocks = Int(100)
    
#    @on_trait_change('digest')
#    def calib_value_init(self):
#        self.calib_value = [None for _ in self.numchannels]
        
    @on_trait_change('numchannels')
    def adjust_calib_values(self):
        if self.calib_value == []: 
            self.calib_value = [None for _ in range(self.numchannels)]
        elif len(self.calib_value) < self.numchannels:
            [self.calib_value.append(None) for _ in range(self.numchannels-len(self.calib_value))]
        elif len(self.calib_value) > self.numchannels:
            [self.calib_value.pop() for _ in range(len(self.calib_value)-self.numchannels)]
            
    def result(self, num):
        """ 
        """
        stamp = datetime.fromtimestamp(time()).strftime('%H:%M:%S')
        
        clev = self.calib_level # calibration level, default 94 dB
        clev_low = clev-self.calib_delta # lower bound, default 91 dB
        clev_upper = clev+self.calib_delta # lower bound, default 97 dB
        cal_dict = {ind: deque([],maxlen=self.calib_nblocks+10) for ind in range(self.numchannels)} 

        for temp in self.source.result(num):
            if self.iscalib:
                data = L_p(temp[0]) 
                cal_msk = logical_and(data > clev_low,data < clev_upper)
                
                if where(cal_msk)[0].size == 1 and self.calib_value[where(cal_msk)[0][0]] is None: # only if one channel has calib level 
                    channel=where(cal_msk)[0][0] # calibrating channel index 
                    level=data[cal_msk][0] # calibrating channel level
    #                print(level)
    #                print('mean:',mean(cal_dict[channel]))
                    cal_dict[channel].append(level) # add to block cache
                    if len(cal_dict[channel]) == self.calib_nblocks+10 and array(cal_dict[channel]).std() < 1: 
                        vals = array(cal_dict[channel])
                        self.calib_value[channel] = mean(vals[10:])
                        savetxt('calib_file_'+stamp.replace(':','')+'.out',array(self.calib_value,dtype=float),'%f')
                        print("channel: {} = {}".format(channel,mean(cal_dict[channel])))
                    yield 1
                else:
                    yield 0
            else:
                break


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

