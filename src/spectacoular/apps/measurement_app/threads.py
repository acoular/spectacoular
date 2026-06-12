"""Thread helpers for measurement app worker coordination."""

# ------------------------------------------------------------------------------
# Copyright (c) 2007-2021, Acoular Development Team.
# ------------------------------------------------------------------------------

from threading import Thread


class EventThread(Thread):
    """Wait for an event and trigger Bokeh callbacks before and after."""

    def __init__(self, event, doc, pre_callback=None, post_callback=None):
        Thread.__init__(self)
        self.pre_callback = pre_callback
        self.post_callback = post_callback
        self.doc = doc
        self.event = event

    def run(self):
        """Schedule callbacks around waiting for the thread event."""
        if self.pre_callback:
            self.doc.add_next_tick_callback(self.pre_callback)
        self.event.wait()
        if self.post_callback:
            self.doc.add_next_tick_callback(self.post_callback)


class SamplesThread(Thread):
    """Consume samples until stopped and set an event on completion."""

    def __init__(self, gen, splitter, register, register_args, event=None):
        Thread.__init__(self)
        self.splitter = splitter
        self.register = register
        self.register_args = register_args
        self.gen = gen
        self.event = event
        self.breakThread = False

    def run(self):
        """Register the target, consume samples, and clean up afterward."""
        if self.event:
            self.event.clear()
        self.splitter.register_object(self.register, **self.register_args)
        for _sample in self.gen:
            if self.breakThread:
                break
        if self.event:
            self.event.set()
        self.splitter.remove_object(self.register)
