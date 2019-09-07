#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 15:05:37 2019

@author: kujawski
"""

from acoular import TimeSamples, PowerSpectra
from traits.api import *

from traits.traits import KindMap


a = PowerSpectra()
a.block_size = 128


a = Trait(10,1,2,3)
kind = a.get_validate()[0]
print(KindMap[kind])

ts = TimeSamples()
'''
each instance has a trait_view() method implemented which is called by 
configure_traits() method

trait_view() method: Gets or sets a ViewElement instance associated with an object's class.

'''

# get ViewElement instance
viewelement = ts.trait_view()


# returns all traits of a HasTraits instanciated class
ts.editable_traits()

# returns type or defaults of given trait
ts.trait("sample_freq").get_validate()[1:]

#tv1 = ts.trait_view_elements()
#tv2 = ts.trait_view()
name = ts.trait('name')
name.get_validate()


ps = PowerSpectra()
ps.trait('window').get_validate()
ps.trait('block_size').get_validate()

#            self.trait = trait_from( trait )
#            validate   = self.trait.get_validate()
#            if validate is not None:
#                self.fast_validate = validate
#
#def validate ( self, object, name, value ):
#    """ Validates that the value is a Python callable.
#    """
#    if isinstance( value, self.fast_validate[1:] ):
#        return value
#
#    self.error( object, name, value )


#%%

from acoular import TimeSamples
from bokeh.models.widgets import TextInput

trait_widget_mapper = {'name': TextInput}
trait_widget_args = {'name': {'disabled':False}}

class TraitWidgetMapper(object):
    '''
    
    '''
    
    def factory(widget):
        if widget is TextInput:
            return TextInputMapper()
        else:
            pass
    
class TextInputMapper(TraitWidgetMapper):
    
    def create_widget(self,obj,trait_name,**args):
        '''
        creates a bokeh TextInput instance 
        '''
        textInput = TextInput(value=getattr(obj,trait_name),**args)
        if not textInput.disabled:
            textInputCallback = self.callback_factory(obj,trait_name)
            textInput.on_change("value",textInputCallback)
        return textInput

    def callback_factory(self,obj,trait_name):
        def _callback(attr, old, new):
            setattr(obj,trait_name,new)
        return _callback


def create_widgets_from_traits(self):
    widgetlist = []
    for (traitname,widgetType) in list(self.trait_widget_mapper.items()):
        widgetMapper = TraitWidgetMapper.factory(widgetType)
        args = self.trait_widget_args[traitname]
        widget = widgetMapper.create_widget(self,traitname,**args)
        widgetlist.append(widget)
    return widgetlist

setattr(TimeSamples,"trait_widget_mapper",trait_widget_mapper)
setattr(TimeSamples,"trait_widget_args",trait_widget_args)
setattr(TimeSamples,"create_widgets_from_traits",create_widgets_from_traits)

        
ts = TimeSamples()
widgets = ts.create_widgets_from_traits()
ti = widgets[0]
ti.value = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/three_sources.h5"
ts.numchannels

#
#wm = TraitWidgetMapper()
##widget = wm.map_trait_to_widget(ts,'name')
