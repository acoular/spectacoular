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
    
    def __init__(self, samplesGen, splitterObj, splitterDestination, buffer_size, event=None):
        Thread.__init__(self)
        self.splitterObj = splitterObj
        self.splitterDestination = splitterDestination
        self.samplesGen = samplesGen
        self.event = event
        self.breakThread = False
        
    def run(self):
        if self.event: 
            self.event.clear()
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
                                
