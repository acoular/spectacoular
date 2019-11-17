#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:32:15 2019

@author: kujawski
"""

from bokeh.models.widgets import TextInput, Select
from traits.api import CTrait, TraitEnum, TraitMap,\
List,TraitListObject, Bool, HasPrivateTraits
from functools import singledispatch

def as_str_list(func):
    def wrapper(*args):
        list_ = func(*args)
        return [str(val) for val in list_]
    return wrapper


class BaseSpectacoular(HasPrivateTraits):
    

    # shadow trait that holds a list of widgets that belong to the class
    _widgets = List()

    def get_widgets(self):
        """ 
        Function to access the widgets of this class.
        
        Returns
        -------
        A list of interactive control elements (widgets)
        No output since `BasePresenter` only represents a base class to derive
        other classes from.
        """
        return self._widgets



class TraitWidgetMapper(object):
    '''
    Widget Factory for trait objects. Implements dependencies between a class 
    trait and a corresponding widget.
    '''

    traitname = object()
    
    traitvalue = object()
    
    traittype = object()
    
    obj = object() # the source object the trait belongs to.

    widget = object()

    def __init__(self,obj,traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        self.traitvalue = getattr(obj,traitname)
        
    def factory(obj,traitname,widgetType): 
        '''
        returns an instance of a TraitWidgetMapper class that corresponds
        to the desired widget type.
        '''
        if widgetType is TextInput: return TextInputMapper(obj,traitname) 
        elif widgetType is Select: return SelectMapper(obj,traitname)
        else: raise ValueError("mapping for widget type does not exist!")
            
    def _set_traitvalue(self,widgetvalue):
        '''
        # widgetvalue is always type str, traitvalue can be of arbitrary type   
        #TODO: This function only works when trait has single dtype as default 
        # how to know the desired dtype of trait? What about traits with different dtypes?       
        '''
        if not self.traittype.is_valid(self.obj,self.traitname,widgetvalue): 
            widgetvalue = self._cast_to_trait_type(widgetvalue)
        # TODO: Better hanndling for unsupported values may be needed here
        setattr(self.obj,self.traitname,widgetvalue)

    def _set_widgetvalue(self,traitvalue):
        '''
        widgetvalue needs to be always of type str  
        '''
        if not isinstance(traitvalue,str):
            traitvalue = cast_to_str(traitvalue)
        self.widget.value = traitvalue

    def _widget_changed_callback_factory(self):
        def _callback(attr, old, new):
            self._set_traitvalue(new)
        return _callback
    
    def _trait_changed_callback_factory(self):
        def _callback(new):
            self._set_widgetvalue(new)
        return _callback

    def _set_callbacks(self):
        '''
        function implements:
            1. dynamic trait listener. on changes of 'traitname' textInput value
            is set
            2. widget listener. On changes of widget value, attribute of traitname
            is set
        '''
        widget_setter_func = self._trait_changed_callback_factory()
        self.obj.on_trait_change(widget_setter_func,self.traitname)
        if not self.widget.disabled:
            trait_setter_func = self._widget_changed_callback_factory()
            self.widget.on_change("value",trait_setter_func)

    def _cast_to_trait_type(self,widgetvalue):
        ''' casts given string value of widget to traittype'''
        cast_func = traitdispatcher.cast_func_factory(self)
        return cast_func(widgetvalue)



class TextInputMapper(TraitWidgetMapper):
    
    def create_widget(self,**args):
        '''
        creates a bokeh TextInput instance 
        '''
        self.widget = TextInput(title=self.traitname,**args)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget



class SelectMapper(TraitWidgetMapper):
    
    def create_widget(self,**args):
        '''
        creates a bokeh Select instance with on trait change listeners
        and on widget change listeners.
        '''

        self.widget = Select(title=self.traitname,**args)
        self._set_widgetvalue(self.traitvalue)
        self._set_options()
        self._set_callbacks()
        return self.widget

    def _set_options(self):
        ''' sets the options of a select widget '''
        self.widget.options = self._get_options()

    @as_str_list
    def _get_options(self): 
        '''
        get settable trait values as options for Select Widget
        returns options as string list
        '''
        return self.get_settable_trait_values(self.traittype)

    def get_settable_trait_values(self,trait_type):
        '''
        takes trait_type of trait object and returns list with settable values
        '''
        if isinstance(trait_type,TraitEnum):
            return list(trait_type.values)
        elif isinstance(trait_type, TraitMap):
            return list(trait_type.map.keys())
        elif isinstance(trait_type, Bool):
            return [True,False]
        else:
            raise ValueError("unsupported trait type {}".format(trait_type))



class TraitCastDispatcher(object):
    '''
    This class dynamically returns a function for casting string values to 
    a given trait type.
    '''
    
    def cast_func_factory(self,traitwidgetmapper):
        '''
        TraitEnum type is a difficult type! Solution needed! 
        '''
        traittype = traitwidgetmapper.traittype
        # if CTrait get trait_type of CTrait 
        if isinstance(traittype,CTrait):
            traittype = traittype.trait_type
            
        if isinstance(traittype, List):
            return self._cast_to_list_func(traittype)
        else:
            return get_cast_func[(str,type(traitwidgetmapper.traitvalue))]

    def _cast_to_list_func(self,traittype):
            listElementType = self._get_listElementType(traittype)
            def cast_func(var):
                varlist = cast_str_to_list(var)
                return [listElementType(val) for val in varlist]
            return cast_func

    def _get_listElementType(self,traittype):
        if not traittype.item_trait.trait_type.aType:
            return int
        elif traittype.item_trait.trait_type.aType is str:
            return str
        elif traittype.item_trait.trait_type.aType is float:
            return float
        elif traittype.item_trait.trait_type.aType is bool:
            return bool
        
traitdispatcher = TraitCastDispatcher()

# =============================================================================
# basic functions
# =============================================================================

@singledispatch        
def cast_to_str(value):
    return str(value)
@cast_to_str.register(list)
@cast_to_str.register(TraitListObject)
def _(list_):
    return cast_list_to_str(list_)

def cast_str_to_list(var): 
    varlist = list(var.replace(" ","").split(",")) 
    if [] in varlist: varlist.remove([])
    if '' in varlist: varlist.remove('')
#    print(varlist)
    return varlist
    
def cast_list_to_str(list_): 
    if all(isinstance(element,str) for element in list_):
        return ', '.join(list_)
    else:
        return str(list_).strip('[]')

def cast_str_to_bool(var): 
    if var == 'False' or var == '0': return False
    else: return True
        
get_cast_func = {
        (int,str) : str,
        (str,int) : int,
        (bool,str) : str,
        (float,str) : str,
        (str,float) : float,
        (str,bool) : cast_str_to_bool,
        (list,str) : cast_list_to_str,
        (str,list) : cast_str_to_list,
        (TraitListObject,str) : cast_list_to_str,
        (str,TraitListObject) : cast_str_to_list
                 }
