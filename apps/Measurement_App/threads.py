#------------------------------------------------------------------------------
# Copyright (c) 2007-2021, Acoular Development Team.
#------------------------------------------------------------------------------

from threading import Thread

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
    
    def __init__(self, gen, splitter, register, register_args, event=None):
        Thread.__init__(self)
        self.splitter = splitter
        self.register = register
        self.register_args = register_args
        self.gen = gen
        self.event = event
        self.breakThread = False
        
    def run(self):
        if self.event: 
            self.event.clear()
        self.splitter.register_object(self.register, **self.register_args)
        for sample in self.gen:
            if self.breakThread:
                break
        if self.event: 
            self.event.set()
        self.splitter.remove_object(self.register)
        return
                                
