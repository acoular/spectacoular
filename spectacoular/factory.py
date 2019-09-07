#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:32:15 2019

@author: kujawski
"""

from bokeh.models.widgets import TextInput, Select
from traits.api import on_trait_change, CTrait
from functools import partial
from traits.traits import KindMap



class TraitWidgetMapper(object):
    '''
    Widget Factory for traits 
    '''
    
    def factory(widget):
        if widget is TextInput:
            return TextInputMapper()
        elif widget is Select:
            return SelectMapper()
        else:
            pass

    def get_valid_values(self,obj,trait_name): #TODO: need to be changed
        valTuple = obj.trait(trait_name).get_validate()[1]
        return [str(val) for val in valTuple]

#    def get_valid_dtype(self,trait):
#        '''
#        gets valid dtype of trait.
#        dtype validation highly differs between trait instances. 
#        '''
#        if isinstance(trait,CTrait):
#            return self._get_valid_dtype_ctrait(trait)
#        
#    def _get_valid_dtype_ctrait(self,trait):
#        kind = trait.get_validate()[0]
#        if kind == 11:
#        
#        if kind is not None:
#            kind = kind[0]
#            dtype = KindMap[kind]
            
    
class TextInputMapper(TraitWidgetMapper):
    
    textInput = object()
    
    def create_widget(self,obj,trait_name,**args):
        '''
        creates a bokeh TextInput instance 
        '''
        self.textInput = TextInput(title=trait_name, **args)
        self._set_value(obj,trait_name)
        self._set_callbacks(obj,trait_name)
        return self.textInput

    def _set_value(self,obj,trait_name):
        trait_value = getattr(obj,trait_name)
        if not isinstance(trait_value,str):
            trait_value = cast_variable(trait_value,str)
        self.textInput.value = trait_value

    def _set_callbacks(self,obj,trait_name):
        '''
        function implements:
            1. dynamic trait listener. on changes of 'trait_name' textInput value
            is set
            2. widget listener. On changes of widget value, attribute of trait_name
            is set
        '''
        setter_func = self._notify_trait_changed_factory()
        obj.on_trait_change(setter_func,trait_name)
        if not self.textInput.disabled:
            textInputCallback = self._widget_callback_factory(obj,trait_name)
            self.textInput.on_change("value",textInputCallback)

    def _widget_callback_factory(self,obj,trait_name):
        def _callback(attr, old, new):
            setattr(obj,trait_name,new)
        return _callback
    
    def _notify_trait_changed_factory(self):
        def _callback(new):
            self.textInput.value = str(new)
        return _callback


class SelectMapper(TraitWidgetMapper):
    
    select = object()
    
    def create_widget(self,obj,trait_name,**args):
        '''
        creates a bokeh Select instance 
        '''

        self.select = Select(title=trait_name, **args)
        self._set_value(obj,trait_name)
        self._set_callbacks(obj,trait_name)
        return self.select

    def _set_value(self,obj,trait_name):
        trait_value = getattr(obj,trait_name)
        if not isinstance(trait_value,str):
            trait_value = cast_variable(trait_value,str)
        self.select.value = trait_value
        
    def _set_options(self,obj,trait_name): #TODO: include this function
        self.select.options = self.get_valid_values(obj,trait_name)

    def _set_callbacks(self,obj,trait_name):
        '''
        function implements:
            1. dynamic trait listener. on changes of 'trait_name' textInput value
            is set
            2. widget listener. On changes of widget value, attribute of trait_name
            is set
        '''
        setter_func = self._notify_trait_changed_factory()
        obj.on_trait_change(setter_func,trait_name)
        if not self.select.disabled:
            selectCallback = self._widget_callback_factory(obj,trait_name)
            self.select.on_change("value",selectCallback)

    def _widget_callback_factory(self,obj,trait_name):
        def _callback(attr, old, new):
            trait_value = getattr(obj,trait_name)
            trait_type = get_trait_type(trait_value)
            # if not new value of widget is of same type as trait
            if not isinstance(new,trait_type):
                new = cast_variable(new,trait_type)
            setattr(obj,trait_name,new)
        return _callback
    
    def _notify_trait_changed_factory(self):
        def _callback(new):
            self.select.value = str(new)
        return _callback


def get_trait_type(trait_value):
    if isinstance(trait_value,list):
        return list
    elif isinstance(trait_value,str):
        return str
    elif isinstance(trait_value,int):
        return int
    elif isinstance(trait_value,float):
        return float
    elif isinstance(trait_value,dict):
        return dict
    else:
        raise ValueError("unknown type {}".format(type(trait_value)))
    pass
    
def cast_variable(var, cast_type):
    ''' casts var to type '''
    var_type = get_trait_type(var)
#    var_type = type(var)
    cast_func = get_cast_func[(var_type,cast_type)]
    return cast_func(var)
    
def cast_int_to_str(var): return str(var)
def cast_str_to_int(var): return int(var)
def cast_float_to_str(var): return str(var)
def cast_str_to_float(var): return float(var)
#(old,new)
get_cast_func = {
        (int,str) : cast_int_to_str,
        (str,int) : cast_str_to_int,
        (float,str) : cast_float_to_str,
        (str,float) : cast_str_to_float,
                 }
            
def create_widgets_from_traits(self):
    '''
    widgetlist might be better a dictionary! translate trait name to widget
    '''
    widgetlist = []
    for (traitname,widgetType) in list(self.trait_widget_mapper.items()):
        widgetMapper = TraitWidgetMapper.factory(widgetType)
        args = self.trait_widget_args[traitname]
        widget = widgetMapper.create_widget(self,traitname,**args)
        widgetlist.append(widget)
    return widgetlist

