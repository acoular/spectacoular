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
L_p,TimeAverage,FiltFiltOctave
from acoular.internal import digest
from acoular.h5cache import td_dir


class ThreadsafeGenerator():
    """
    Creates a Thread Safe Iterator.
    Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """
    
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __next__(self): # this function implementation is not python 2 compatible!
        with self.lock:
            return self.it.__next__()
        

class TimeSideChain(TimeInOut):
       
    source = Trait(SamplesGenerator)
    
    data = Array([])
    
    def result(self,num):
        for temp in self.source.result(num):
            self.data = temp
            yield temp
            

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


class SampleSplitter(TimeInOut): 
    '''
    This class distributes data blocks from source to several following objects.
    A separate block memory is created for each registered object.
    To do this, each subsequent object must register in this class.
    '''
    # source of data
    source = Instance(SamplesGenerator)

    # buffers as lists (Queues) with blocks of data for each subsequent object
    block_buffer = Dict(key_trait=Instance(SamplesGenerator)) # operations on deques does not produce new object like operations on lists

    # max elements/blocks in block buffers
    buffer_size = Int(100)

    # defines behaviour in case of buffer overflow
    buffer_overflow_treatment = Dict(key_trait=Instance(SamplesGenerator),
                              value_trait=Trait('error','warning','none'),
                              desc='defines behaviour when buffer overflows')       
 
    # shadow trait to monitor if source deliver samples or is empty
    _source_generator_exist = Bool(False) 

    # shadow trait to monitor if buffer of objects with overflow treatment = 'error' 
    # or warning is overfilled. Error will be raised in all threads.
    _buffer_overflow = Bool(False)

    # Helper Trait holds source generator     
    _source_generator = Trait()
           
    def _create_block_buffer(self,obj):        
        self.block_buffer[obj] = deque([],maxlen=self.buffer_size)
        
    def _create_buffer_overflow_treatment(self,obj):
        self.buffer_overflow_treatment[obj] = 'error' 
    
    def _clear_block_buffer(self,obj):
        self.block_buffer[obj].clear()
        
    def _remove_block_buffer(self,obj):
        del self.block_buffer[obj]

    def _remove_buffer_overflow_treatment(self,obj):
        del self.buffer_overflow_treatment[obj]
        
    def _is_obj_registered(self,obj):
        if obj in self.block_buffer.keys(): return True

    def _inspect_buffer_levels(self):
        inspect_objs = [obj for obj in self.buffer_overflow_treatment.keys() 
                            if not self.buffer_overflow_treatment[obj] == 'none']

        objs_has_overfilled_buffers = [obj for obj in inspect_objs 
                            if len(self.block_buffer[obj]) == self.buffer_size]

        for obj in objs_has_overfilled_buffers:
            print(self.buffer_overflow_treatment[obj])
            if self.buffer_overflow_treatment[obj] == 'error': 
                self._buffer_overflow = True
            if self.buffer_overflow_treatment[obj] == 'warning':
                warnings.warn(
                    'overfilled buffer for object: %s data will get lost' %obj,
                    UserWarning)

    def _create_source_generator(self,num):
        self._source_generator = ThreadsafeGenerator(self.source.result(num))
        self._source_generator_exist = True # indicates full generator

    def _fill_block_buffers(self): 
        next_block = next(self._source_generator)                
        [self.block_buffer[obj].appendleft(next_block) for obj in self.block_buffer.keys()]

    @on_trait_change('buffer_size')
    def _change_buffer_size(self): # 
        for obj in self.block_buffer.keys():
            self._remove_block_buffer(obj)
            self._create_block_buffer(obj)      

    def register_object(self,*objects_to_register):
        for obj in objects_to_register:
            if not obj in self.block_buffer.keys() or obj not in self.buffer_overflow_treatment.keys():
                self._create_block_buffer(obj)
                self._create_buffer_overflow_treatment(obj)

    def remove_object(self,*objects_to_remove):
        for obj in objects_to_remove:
            self._remove_block_buffer(obj)
            self._remove_buffer_overflow_treatment(obj)
            
    def result(self,num):

        calling_obj = currentframe().f_back.f_locals['self'] 
        if self._is_obj_registered(calling_obj): 
            pass
        else:
            raise IOError("calling object %s is not registered." %calling_obj)
        
        if not self._source_generator_exist: # if generator is empty, or has not been created 
            for obj in self.block_buffer.keys(): self._clear_block_buffer(obj)
            self._buffer_overflow = False # reset overflow bool
            self._create_source_generator(num) #make new generator

        while not self._buffer_overflow:
            if self.block_buffer[calling_obj]:
                yield self.block_buffer[calling_obj].pop()
            else:
                self._inspect_buffer_levels()
                try: 
                    self._fill_block_buffers()
                except StopIteration:
                    self._source_generator_exist = False
                    return
        else: 
            raise IOError('Maximum size of buffer is reached. Please increase buffer_size!')   
                         
class WriteH5( TimeInOut ):
    """
    Saves time signal as `*.h5` file
    """
    #: Name of the file to be saved. If none is given, the name will be
    #: automatically generated from a time stamp.
    name = File(filter=['*.h5'], 
        desc="name of data file")    

    #: Indicates if samples are collected, helper trait to break result loop
    collectsamples = Bool(True,
        desc="Indicates if samples are collected")
      
    # internal identifier
    digest = Property( depends_on = ['source.digest', '__class__'])

    traits_view = View(
        [Item('source', style='custom'), 
            ['name{File name}', 
            '|[Properties]'], 
            '|'
        ], 
        title='write .h5', 
        buttons = OKCancelButtons
                    )

    @cached_property
    def _get_digest( self ):
        return digest(self)

    def create_filename(self):
        name = datetime.now().isoformat('_').replace(':','-').replace('.','_')
        self.name = path.join(td_dir,name+'.h5')
            
    def create_file(self):
        f5h = tables.open_file(self.name, mode = 'w')
        return f5h
    
    def initialize_time_data(self,file):
        ac = file.create_earray(file.root, 'time_data', \
            tables.atom.Float32Atom(), (0, self.numchannels))
        ac.set_attr('sample_freq', self.sample_freq)
        return ac
        
    def save(self):
        """ 
        Saves source output to `*.h5` file 
        """
        if self.name == '': self.create_filename()
        file = self.create_file()
        ac = self.initialize_time_data(file)
        for data in self.source.result(4096):
            ac.append(data)
        file.close()
        
    def result(self,num, samples=0):
        """ 
        saves source output h5 file 
        """
        if self.name == '': self.create_filename()
        file = self.create_file()
        ac = self.initialize_time_data(file)
        count = 0
        ite = self.source.result(num)
        while count < samples and self.collectsamples:
            anz = min(num,samples-count)
            try:
                data = next(ite)
                ac.append(data[:anz])
                yield 
                count += num
            except: 
                file.close()
                break
        else:
            file.close()
            return

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

