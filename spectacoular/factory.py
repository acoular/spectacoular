# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements factory for trait to widget translation.

.. autosummary::
    :toctree: generated/

    BaseSpectacoular
    TraitWidgetMapper
    TextInputMapper
    SelectMapper
    SliderMapper
    DataTableMapper
    TraitCastDispatcher
"""

from bokeh.models.widgets import TextInput, Select, Slider, DataTable, \
TableColumn
from bokeh.models import ColumnDataSource
from traits.api import CTrait, TraitEnum, TraitMap, CArray, Dict, Any, \
List,Float, Str, Int, Enum, Range, TraitListObject, Bool, Tuple, \
HasPrivateTraits, TraitCoerceType
from functools import singledispatch
from numpy import array, ndarray
from collections.abc import Iterable

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
    
    obj = None # the source object the trait belongs to.

    widget = object()
    
    def __init__(self,obj,traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        self.traitvalue = getattr(obj,traitname)
#        self.widgetdtype = str
        
    def factory(obj,traitname,widgetType): 
        '''
        returns an instance of a TraitWidgetMapper class that corresponds
        to the desired widget type.
        '''
        if widgetType is TextInput: return TextInputMapper(obj,traitname) 
        elif widgetType is Select: return SelectMapper(obj,traitname)
        elif widgetType is Slider: return SliderMapper(obj,traitname) 
        elif widgetType is DataTable: return DataTableMapper(obj,traitname) 
        else: raise ValueError("mapping for widget type does not exist!")
    
    # might be better come from a factory. always type checking might be uneccessary         
    def _set_traitvalue(self,widgetvalue):
        '''
        # value of Select, TextInput, ..., widgets is always type str. However,
        traitvalues can be of arbitrary dtype. Thus, widgetvalues are casted to
        traittype before setting traitvalue. 
        #TODO: This function only works when trait has single dtype as default 
        # how to know the desired dtype of trait? What about traits with different dtypes?       
        '''
        
        if not self.traittype.is_valid(self.obj,self.traitname,widgetvalue): 
            widgetvalue = self._cast_to_trait_type(widgetvalue)
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
        return self.get_settable_trait_values()

    def get_settable_trait_values(self):
        '''
        takes trait_type of trait object and returns list with settable values
        '''
        if isinstance(self.traittype,TraitEnum):
            return list(self.traittype.values)
        elif isinstance(self.traittype,Enum):
            return list(self.traittype.values)
        elif isinstance(self.traittype, TraitMap):
            return list(self.traittype.map.keys())
        elif isinstance(self.traittype, Bool):
            return [True,False]
        else:
            raise ValueError("currently unsupported trait-type {} for \
                             mapping to Select widget".format(self.traittype))


class SliderMapper(TraitWidgetMapper):
    
    def create_widget(self,**args):
        '''
        creates a bokeh Slider instance 
        ´value´, ´start´ and ´end´ attributes of Slider instance need to be 
        of type float
        '''
        if not isinstance(self.traittype,Range):
            self.raise_unsupported_traittype()
        
        self.widget = Slider(title=self.traitname,**args)
        self._set_widgetvalue(self.traitvalue)
        self._set_range()
        self._set_callbacks()
        return self.widget
    
    def _set_range(self):
        self.widget.start = self.traittype._low
        self.widget.end = self.traittype._high

    def _set_widgetvalue(self,traitvalue):
        '''
        widgetvalue needs to be always of type str  
        '''
        if not isinstance(traitvalue,float):
            traitvalue = cast_to_float(traitvalue)
        self.widget.value = traitvalue

    def raise_unsupported_traittype(self):
        raise ValueError("currently unsupported trait-type {} for \
                         mapping to RangeSlider widget".format(self.traittype))



class DataTableMapper(TraitWidgetMapper):
    
    cds = ColumnDataSource() # TODO: Include ColumnDataSource
    
    def create_widget(self,**args):
        '''
        creates a bokeh DataTable instance 
        '''
        self.widget = DataTable(columns=[self.get_table_column()],**args) 
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def get_table_column(self):
        return TableColumn(field=self.traitname, title=self.traitname,
#                editor=IntEditor()
                )

    def _set_widgetvalue(self,traitvalue):
        '''
        create ColumnDataSource   
        '''
        self.widget.source = ColumnDataSource(
                data={self.traitname: traitvalue})

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
        if self.widget.editable:
            trait_setter_func = self._widget_changed_callback_factory()
            self.widget.source.on_change("data",trait_setter_func)

    def raise_unsupported_traittype(self):
        raise ValueError("currently unsupported trait-type {} for \
                         mapping to DataTable widget".format(self.traittype))



class TraitCastDispatcher(object):
    '''
    This class dynamically returns a function for casting widget values to 
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
            itemtype = self._get_item_type(traittype)
            return self.get_cast_to_itemtype_func(itemtype)
        elif isinstance(traittype, Tuple):
            return lambda x: eval(x)
        elif isinstance(traittype,Dict):
            raise NotImplementedError("Dict casting currently not supported")
            
        if isinstance(traittype,Float):
            return float
        elif isinstance(traittype,Str):
            return str
        elif isinstance(traittype,Int):
            return get_cast_func[(str,int)]
        elif isinstance(traittype, CArray):
#            print(traitwidgetmapper.traittype.dtype,
#                  traitwidgetmapper.traitvalue,
#                  traitwidgetmapper.traitname)
            return self._cast_to_ndarray_func()
        else:
            return get_cast_func[(str,type(traitwidgetmapper.traitvalue))]            

    def get_cast_to_itemtype_func(self, itemtype):
            def cast_func(var):
                cast_var_to_list = get_cast_func[(type(var),list)]
                return [itemtype(val) for val in cast_var_to_list(var)]
            return cast_func

    def _cast_to_ndarray_func(self):
            def cast_func(var):
                return [float(val) for val in cast_str_to_list(var)]
            return cast_func
        
    def _get_item_type( self, traittype ):
        itemType = traittype.item_trait.trait_type
        if isinstance(itemType,TraitCoerceType): # in case of ListStr, ListInt,...
            itemType = itemType.aType # returns basic type str, float, ...
            return itemType
        elif isinstance(itemType,str) or isinstance(itemType,Str):
            return str
        elif isinstance(itemType,float) or isinstance(itemType,Float):
            return float
        elif isinstance(itemType,bool) or isinstance(itemType,Bool):
            return bool
        elif isinstance(itemType,int) or isinstance(itemType,Int):
            return int
        elif isinstance(itemType, Any):
            return lambda x: x # simple identity mapping
        else:
            raise ValueError("currently unsupported traititemtype {} for \
                             trait of type {}".format(
                             itemType, 
                             traittype)
                             )
            
        
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

@cast_to_str.register(ndarray)
@cast_to_str.register(array)
@cast_to_str.register(CArray)
def _(ndarray_):
    if len(ndarray_.shape) == 1:
        return cast_list_to_str(list(ndarray_))
    else:
        raise NotImplementedError("Multi-dimension array dispatch not implemented yet!")

@singledispatch
def cast_to_float(value):
    return float(value)
        
def cast_list_to_str(list_): 
    if all(isinstance(element,str) for element in list_):
        return ', '.join(list_)
    else:
        return str(list_).strip('[]')

def cast_str_to_list(var): 
    print(var)
    varlist = list(var.replace(" ","").split(",")) 
    if [] in varlist: varlist.remove([])
    if '' in varlist: varlist.remove('')
    print(varlist)
    return varlist

def cast_str_to_bool(var): 
    if var == 'False' or var == '0': return False
    else: return True

def cast_str_to_int(var):
    return int(float(var))
        
get_cast_func = {
        (int,str) : str,
        (str,int) : cast_str_to_int,
        (bool,str) : str,
        (float,str) : str,
        (str,float) : float,
        (str,bool) : cast_str_to_bool,
        (list,str) : cast_list_to_str,
        (str,list) : cast_str_to_list,
        (TraitListObject,str) : cast_list_to_str,
        (str,TraitListObject) : cast_str_to_list
                 }
