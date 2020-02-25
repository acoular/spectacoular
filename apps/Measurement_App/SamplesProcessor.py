# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------

from traits.api import Int, Instance, on_trait_change, Bool, Float, \
Dict, File, CArray,cached_property,Property
from threading import Thread
from numpy import shape

# acoular imports
from acoular import TimeInOut, TimeSamples,\
L_p,TimeAverage,FiltFiltOctave, SampleSplitter
   
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
                                
