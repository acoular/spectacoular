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
    TraitDispatch
"""

from bokeh.models.widgets import TextInput, Select, Slider, DataTable, \
TableColumn, NumberEditor, StringEditor
from bokeh.models import ColumnDataSource
from traits.api import TraitEnum, TraitMap, CArray, Any, \
List,Float, Str, Int, Enum, Range, Bool, Tuple, Long,\
CLong, HasPrivateTraits, TraitCoerceType, File, TraitCompound,\
Complex, BaseInt, BaseLong, BaseFloat, BaseBool, BaseRange,\
BaseStr, BaseFile, BaseTuple, BaseEnum, Delegate
from numpy import array, ndarray,newaxis,isscalar,nan_to_num
from .cast import cast_to_int, cast_to_str, cast_to_float, cast_to_bool,\
cast_to_list, cast_to_array, singledispatchmethod

NUMERIC_TYPES = (Int,Long,CLong,int, # Complex Numbers Missing at the Moment
                 Float,float, 
                 Complex, complex)
BOOLEAN_TYPES = (Bool,bool)   
SEQUENCE_TYPES = (Str,File,str,
                  Tuple,
                  List,
                  CArray)
SPECIAL_TYPES = (BaseRange,Range,Enum,TraitEnum,TraitMap,TraitCompound)

def as_str_list(func):
    def wrapper(*args):
        list_ = func(*args)
        return [str(val) for val in list_]
    return wrapper


def get_widgets(self): # TODO: maybe rename to 'create_widgets(self)'
    '''
    This function is implemented in all spectAcoular classes. It builds widgets 
    from corresponding traits defined in bokehview.py
    '''
    widgetdict = {}
    for (traitname,widgetType) in list(self.trait_widget_mapper.items()):
        widgetMapper = TraitWidgetMapper.factory(self,traitname,widgetType)
        widgetdict[traitname] = widgetMapper.create_widget(
                                        **self.trait_widget_args[traitname])
    return widgetdict


def set_widgets(self,**kwargs):
    '''
    This function allows to link an existing widget to a certain class trait.
    Expects a dictionary with the traitname as key and the widget instance as 
    value. For example: 
        $ widgetmapping = {'traitname' : Slider(), ... }
        $ set_widgets(**widgetmapping)
    
    The value of the trait attribute changes to the widgets value when it is 
    different.
    '''
    for traitname, widget in kwargs.items():
        widgetMapper = TraitWidgetMapper.factory(self,traitname,widget.__class__)
        widgetMapper.set_widget(widget)
        

class BaseSpectacoular(HasPrivateTraits):
    
    trait_widget_mapper = {
                       }

    trait_widget_args = {
                     }
    
    get_widgets = get_widgets
    
    set_widgets = set_widgets



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
    
    traitdispatcher = object()
    
    def __init__(self,obj,traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        try:
            self.traitvalue = getattr(obj,traitname)
        except AttributeError: # in case of Delegate
            self.traitvalue = None
        self.traitdispatcher = traitdispatcher.factory(self,self.traittype)
        
    def factory(obj,traitname,widgetType): 
        '''
        returns an instance of a TraitWidgetMapper class that corresponds
        to the desired widget type.
        '''
        if widgetType is TextInput: return TextInputMapper(obj,traitname) 
        elif widgetType is Select: return SelectMapper(obj,traitname)
        elif widgetType is Slider: return SliderMapper(obj,traitname) 
        elif widgetType is DataTable: return DataTableMapper(obj,traitname) 
        else: raise ValueError("mapping for widget type {} does not exist!".format(widgetType))
    
    def _set_traitvalue(self,widgetvalue):
        ''' set traitvalue to widgetvalue '''
#        print("set traitvalue for trait {}".format(self.traitname))
        setattr(self.obj,self.traitname,widgetvalue)

    def _set_widgetvalue(self,traitvalue):
        ''' set widgetvalue to traitvalue '''
        if not isinstance(traitvalue,str):
            traitvalue = cast_to_str(traitvalue)
        self.widget.value = traitvalue

    def create_trait_setter_func(self):
        ''' 
        traitdispatcher returns a function that casts given widget values
        to a certain traittype
        value of Select, TextInput, ..., widgets are always type str. However,
        traitvalues can be of arbitrary dtype. Thus, widgetvalues are casted to
        traits dtype before. 
        '''
        cast_func = self.traitdispatcher.get_trait_cast_func()
        def callback(attr, old, new):
#            print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj,self.traitname,new): 
                new = cast_func(new)
            self._set_traitvalue(new)
        return callback
    
    def create_widget_setter_func(self):
        def callback(new):
#            print("{} widget changed".format(self.traitname))
            self._set_widgetvalue(new)
        return callback

    def _set_callbacks(self):
        '''
        function implements:
            1. dynamic trait listener. on changes of 'traitvalue' -> widget.value
            is set
            2. widget listener. On changes of 'widget.value' -> attribute of traitvalue
            is set
        '''
        widget_setter_func = self.create_widget_setter_func()
        self.obj.on_trait_change(widget_setter_func,self.traitname)
        if not self.widget.disabled:
            trait_setter_func = self.create_trait_setter_func()
            self.widget.on_change("value",trait_setter_func)



class TextInputMapper(TraitWidgetMapper):
    
    def create_widget(self,**kwargs):
        '''
        creates a bokeh TextInput instance 
        '''
        self.widget = TextInput(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        '''
        sets a bokeh TextInput instance 
        '''
        self.widget = widget
        cast_func = self.traitdispatcher.get_trait_cast_func()
        self._set_traitvalue(cast_func(self.widget.value)) # set traitvalue to widgetvalue
        self._set_callbacks()


class SelectMapper(TraitWidgetMapper):
    
    def create_widget(self,**kwargs):
        '''
        creates a bokeh Select instance with on trait change listeners
        and on widget change listeners.
        '''
        self.widget = Select(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_options()
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        '''
        sets a bokeh Select widget instance 
        '''
        self.widget = widget
        cast_func = self.traitdispatcher.get_trait_cast_func()
        self._set_traitvalue(cast_func(self.widget.value)) # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_options(self):
        ''' sets the options of a select widget '''
        if not self.widget.options:
            self.widget.options = self._get_options()

    @as_str_list
    def _get_options(self): 
        '''
        get settable trait values as options for Select Widget
        returns options as string list
        '''
        return self.traitdispatcher.get_settable_trait_values()



class SliderMapper(TraitWidgetMapper):
    
    def create_widget(self,**kwargs):
        '''
        creates a bokeh Slider instance 
        ´value´, ´start´ and ´end´ attributes of Slider instance need to be 
        of type float
        '''
        if not isinstance(self.traittype,Range):
            self.raise_unsupported_traittype()
        
        self.widget = Slider(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_range()
        self._set_callbacks()
        return self.widget
    
    def set_widget(self, widget):
        '''
        sets a bokeh Slider widget instance 
        '''
        self.widget = widget
        cast_func = self.traitdispatcher.get_trait_cast_func()
        self._set_traitvalue(cast_func(self.widget.value)) # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_range(self):
        if not self.widget.start:
            if self.traittype._low:
                self.widget.start = self.traittype._low
        if not self.widget.end:
            if self.traittype._high:
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

    transposed = False
    
    def create_widget(self,**kwargs):
        '''
        creates a bokeh DataTable instance. For transposed arrays that are 
        mapped to the DataTable, array data is reshaped and casted to fit the
        required dictionary format of the ColumnDataSource.
        '''
        #self.widget.source = ColumnDataSource() # TODO: this would not work! -> report bug to bokeh 
        self.widget = DataTable(source=ColumnDataSource(),**kwargs) 
        self.create_columns()
        self.initialize_column_data_source()
        self.is_transposed(self.traitvalue)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        '''
        sets a bokeh DataTable widget instance 
        '''
        self.widget = widget
        cast_func = self.traitdispatcher.get_trait_cast_func()
        self._set_traitvalue(cast_func(self.widget.source.data)) # set traitvalue to widgetvalue
        self._set_callbacks()

    def initialize_column_data_source( self ):
        ''' create keys of DataTables ColumnDataSource '''
        for col in self.widget.columns:
            self.widget.source.data[col.field] = []

    def create_columns( self ):
        ''' create single TableColumn and add to widget '''
        if not self.widget.columns: 
            self.widget.columns = [
                    TableColumn(field=self.traitname, title=self.traitname)]
            self._set_celleditor()
            
    def _set_celleditor( self ):
        if self.widget.editable:
            if isinstance(self.traittype, NUMERIC_TYPES):
                editor = NumberEditor()
            else:
                editor = StringEditor()
            for col in self.widget.columns:
                col.editor = editor
            
    def _set_widgetvalue(self,traitvalue):
        ''' changes data in ColumnDataSource of DataTable widget '''
        newData = self.cast_to_dict(traitvalue)
        # isSame = [new==old for (new,old) in 
        #           zip(newData.values(),self.widget.source.data.values())]
        # if len(isSame) > 0 and False in isSame:
        self.widget.source.data = newData
        return

    def _set_callbacks( self ):
        ''' function implements dynmic trait listener and widget listener '''
        widget_setter_func = self.create_widget_setter_func()
        self.obj.on_trait_change(widget_setter_func,self.traitname)
        if self.widget.editable:
            trait_setter_func = self.create_trait_setter_func()
            self.widget.source.on_change('data',trait_setter_func)

    def create_trait_setter_func(self):
        ''' 
        traitdispatcher returns a function that casts given widget values
        to a certain traittype
        value of Select, TextInput, ..., widgets are always type str. However,
        traitvalues can be of arbitrary dtype. Thus, widgetvalues are casted to
        traits dtype before. 
        '''
        cast_func = self.traitdispatcher.get_trait_cast_func()
        def callback(attr, old, new): # any how old and new are always the same when the callback is triggered
            old = getattr(self.obj,self.traitname) # 
            new = cast_func(new)
            if isinstance(new,ndarray) and self.transposed: # if trait expects array in a transposed representation to the ColumnDataSource
                new = new.T
#            print(new,type(new),self.traitname, self.traittype,new.shape)
            if not self.is_equal(old,new):
                self._set_traitvalue(new)
        return callback

    def is_equal(self,old,new):
#        print("old values:",old, old.shape,"new values:",new, new.shape)
#        print(old == new)
        if isinstance(new,ndarray) and isinstance(old,ndarray):
            boolArray = new==old
            if isscalar(boolArray):
                return boolArray
            else:
                return boolArray.all()
        elif isscalar(new) and isscalar(old):
            return new == old
        elif isinstance(new,list) and isinstance(old,list):
            return new == old
        else:
            raise NotImplementedError("can not compare {} and {}".format(type(old),type(new)))

    def is_transposed(self,traitvalue):
        numCols = len(self.widget.columns)
        if isinstance(traitvalue,ndarray):
            arrayShape = traitvalue.shape
            if arrayShape[0] == numCols and not arrayShape[1] == numCols:
                self.transposed = True

    @singledispatchmethod
    def cast_to_dict( self, traitvalue ): # int, float, str, bool
        keys = [col.field for col in self.widget.columns]
        if len(keys) > 1:
            raise ValueError('can not cast scalar value of "{}" to a dictionary with {} columns'.format(traitvalue,len(keys)))
        return {self.widget.columns[0].field: [traitvalue]}

    @cast_to_dict.register( list )
    def _(self,traitvalue):
        data = {}
        keys = [col.field for col in self.widget.columns]
        if len(keys) > 1: # expects a list of lists
            for i,key in enumerate(keys):
                data[key] = traitvalue[i]   
        elif len(keys) == 1: # expects a single list
            data[keys[0]] = traitvalue
        return data

    @cast_to_dict.register( ndarray )
    def _(self,traitvalue):
        data = {}
        if traitvalue.size > 0:
            numCols = len(self.widget.columns)
            if traitvalue.ndim < 2:
                traitvalue = traitvalue[:,newaxis]
            if traitvalue.shape[0] == numCols and traitvalue.shape[1] != numCols:
                traitvalue = traitvalue.T # reshape if necessary
                self.reshape = True
            for i,column in enumerate(self.widget.columns):
                    data[column.field] = list(traitvalue[:,i])
        else:
            for column in self.widget.columns:
                data[column.field] = []
        return data


# =============================================================================
# Trait Dispatch classes
# =============================================================================
        
class TraitDispatch(object):
    '''
    This class is an abstract factory that returns a class for casting widget values to 
    an allowed trait type.
    '''
    traitwidgetmapper = object()
    
    def __init__(self,traitwidgetmapper=None):
        self.traitwidgetmapper = traitwidgetmapper

    def factory(self,traitwidgetmapper,traittype): 
        '''
        returns an instance of a TraitDispatch class that corresponds
        to the desired trait type.
        '''
        if isinstance(traittype,(BaseInt,BaseLong)): 
            return IntDispatch(traitwidgetmapper)
        elif isinstance(traittype,BaseFloat): 
            return FloatDispatch(traitwidgetmapper)
        elif isinstance(traittype,BaseBool): 
            return BoolDispatch(traitwidgetmapper)
        elif isinstance(traittype,(BaseStr,BaseFile)): 
            return StrDispatch(traitwidgetmapper)
        elif isinstance(traittype,BaseRange):
            return RangeDispatch(traitwidgetmapper)
        elif isinstance(traittype,List):
            return ListDispatch(traitwidgetmapper)
        elif isinstance(traittype,BaseTuple):
            return TupleDispatch(traitwidgetmapper)
        elif isinstance(traittype,CArray):
            return ArrayDispatch(traitwidgetmapper)
        elif isinstance(traittype,(BaseEnum,TraitEnum)):
            return EnumDispatch(traitwidgetmapper)
        elif isinstance(traittype,Any) or (traittype is Any): # is Any can be True for Property() function
            return AnyDispatch(traitwidgetmapper)
        elif isinstance(traittype,TraitCompound):
            return TraitCompoundDispatch(traitwidgetmapper)
        elif isinstance(traittype,TraitMap):
            return TraitMapDispatch(traitwidgetmapper)
        elif isinstance(traittype,Delegate):
            return
        else:
            raise NotImplementedError('No Dispatcher class defined for "{}"-trait of class "{}" which is type "{}" defined.'.format(
                    traitwidgetmapper.traitname,
                    traitwidgetmapper.obj.__class__.__name__,
                    traittype)) 

    def get_undefined_cast_func(self):
        if type(self.traitwidgetmapper.traitvalue) == str: return cast_to_str
        elif type(self.traitwidgetmapper.traitvalue) == int: return cast_to_int
        elif type(self.traitwidgetmapper.traitvalue) == float: return cast_to_float
        elif type(self.traitwidgetmapper.traitvalue) == bool: return cast_to_bool
        elif type(self.traitwidgetmapper.traitvalue) == list: return cast_to_list
        elif isinstance(self.traitwidgetmapper.traittype,(Any,TraitCompound)) or \
        self.traitwidgetmapper.traittype is Any: return lambda x: eval(x) # TODO: only ugly temporary workaround  
        else:
            raise NotImplementedError('No cast function for "{}"-trait of class "{}" with value {} which is type "{}" defined.'.format(
                        self.traitwidgetmapper.traitname,
                        self.traitwidgetmapper.obj.__class__.__name__,
                        self.traitwidgetmapper.traitvalue,
                        self.traitwidgetmapper.traittype.__class__))   

traitdispatcher = TraitDispatch()


class IntDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        return cast_to_int
    
    def get_settable_trait_values(self):
        return [self.traitwidgetmapper.traitvalue]
        
    
    
class FloatDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        return cast_to_float

    def get_settable_trait_values(self): 
        return [self.traitwidgetmapper.traitvalue]



class StrDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        return cast_to_str

    def get_settable_trait_values(self): 
        return [self.traitwidgetmapper.traitvalue]
    
    

class BoolDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        return cast_to_bool

    def get_settable_trait_values(self): 
        return [True,False]
        


class RangeDispatch(TraitDispatch):

    def get_trait_cast_func(self):
        if type(self.traitwidgetmapper.traitvalue) == float: return cast_to_float
        elif type(self.traitwidgetmapper.traitvalue) == int: return cast_to_int
        else: raise ValueError('No cast function for "{}"-trait of class "{}" with value {} which is type "{}" defined.'.format(
                        self.traitwidgetmapper.traitname,
                        self.traitwidgetmapper.obj.__class__.__name__,
                        self.traitwidgetmapper.traitvalue,
                        self.traitwidgetmapper.traittype.__class__))    
            
    def get_settable_trait_values(self):
        return [self.traitwidgetmapper.traitvalue]
    


class ListDispatch(TraitDispatch):
    '''
    Depending on List definition in class, items can be of different trait
    types.
    '''
    def get_trait_cast_func(self): 
        item_cast_func = self.get_item_type_cast_func()
        def cast_func(var):
            return [item_cast_func(val) for val in cast_to_list(var)]
        return cast_func

    def get_settable_trait_values(self): 
        return [self.traitwidgetmapper.traitvalue]

    def get_item_type_cast_func( self ):
        itemType = self.traitwidgetmapper.traittype.item_trait.trait_type
        if isinstance(itemType,TraitCoerceType): # in case of ListStr, ListInt, List(['xyz']),...
            itemType = itemType.aType # returns basic type str, float, ...
            return itemType
        else: # in case no item defined -> List(Str())
            dispatch = traitdispatcher.factory(self.traitwidgetmapper,itemType)
            return dispatch.get_trait_cast_func()



class TupleDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        if isinstance(self.traitwidgetmapper, (TextInputMapper,SelectMapper)): 
            return lambda x: eval(x)
        else:
            raise NotImplementedError("function not defined for class {}".format(
                self.traitwidgetmapper.__class__))

    def get_settable_trait_values(self): 
        return [self.traitwidgetmapper.traitvalue]


     
class ArrayDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        return self.get_cast_to_array_func(self.traitwidgetmapper.traittype.dtype) 

    def get_settable_trait_values(self):
        return [self.traitwidgetmapper.traitvalue]
    
    def get_cast_to_array_func(self,dtype):
        def cast_func(var):
            return nan_to_num(cast_to_array(var).astype(dtype))
        return cast_func 



class EnumDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        if isinstance(self.traitwidgetmapper, (TextInputMapper,SelectMapper)): 
            return self.get_undefined_cast_func()
        else:
            raise NotImplementedError("function not defined for class {}".format(
                self.traitwidgetmapper.__class__))

    def get_settable_trait_values(self): 
        return list(self.traitwidgetmapper.traittype.values)



class AnyDispatch(TraitDispatch):
    
    def get_trait_cast_func(self): 
        if isinstance(self.traitwidgetmapper, (TextInputMapper,SelectMapper)): 
            return self.get_undefined_cast_func()
        else:
            raise NotImplementedError("function not defined for class {}".format(
                self.traitwidgetmapper.__class__))

    def get_settable_trait_values(self): 
        return list(self.traitwidgetmapper.traittype.values)
    
    
    
class TraitCompoundDispatch(TraitDispatch):
    '''
    for example: Trait(None,None,CLong) -> multiple handlers
    '''
    def get_trait_cast_func(self): 
        if isinstance(self.traitwidgetmapper, (TextInputMapper,SelectMapper)): 
            return self.get_undefined_cast_func()
        else:
            raise NotImplementedError("function not defined for class {}".format(
                self.traitwidgetmapper.__class__))

    def get_settable_trait_values(self): 
        return list(self.traitwidgetmapper.traittype.values)    
    
    
    
class TraitMapDispatch(TraitDispatch):
                 
    def get_trait_cast_func(self): 
        if isinstance(self.traitwidgetmapper, (TextInputMapper,SelectMapper)): 
            return lambda x: eval(x)
        else:
            raise NotImplementedError("function not defined for class {}".format(
                self.traitwidgetmapper.__class__))

    def get_settable_trait_values(self): 
        return list(self.traitwidgetmapper.traittype.map.keys())


 