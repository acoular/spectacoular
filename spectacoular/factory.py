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
TableColumn, NumberEditor, StringEditor
from bokeh.models import ColumnDataSource
from traits.api import CTrait, TraitEnum, TraitMap, CArray, Any, \
List,Float, Str, Int, Enum, Range, TraitListObject, Bool, Tuple, Long,\
CLong, HasPrivateTraits, TraitCoerceType, File, BaseRange, TraitCompound,\
Complex,Dict
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


class BaseSpectacoular(HasPrivateTraits):
    

    # shadow trait that holds a list of widgets that belong to the class
    _widgets = Dict()

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
        cast_func = traitdispatcher.get_trait_cast_func(self)
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
        return traitdispatcher.get_settable_trait_values(self)



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
        cast_func = traitdispatcher.get_trait_cast_func(self)
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

        
class TraitCastDispatcher(object):
    '''
    This class dynamically returns a function for casting widget values to 
    a given trait type.
    '''
    def is_numeric(self, traittype):
        return isinstance(traittype,NUMERIC_TYPES)

    def is_boolean(self, traittype):
        return isinstance(traittype,BOOLEAN_TYPES)

    def is_sequence(self, traittype):
        return isinstance(traittype,SEQUENCE_TYPES)
    
    def is_special(self,traittype):
        return isinstance(traittype,SPECIAL_TYPES)
    
    def get_trait_cast_func(self,traitwidgetmapper):
        '''
        returns a function to cast widgetvalues into dtype of a certain trait
        '''
        traittype = traitwidgetmapper.traittype
        if isinstance(traittype,CTrait): # if CTrait get trait_type of CTrait 
            traittype = traittype.trait_type

        if self.is_numeric(traittype):
            return self.get_numeric_cast_func(traittype)
        elif self.is_boolean(traittype):
            return self.get_boolean_cast_func(traittype)
        elif self.is_sequence(traittype):
            return self.get_sequence_cast_func(traittype)
        elif self.is_special(traittype):
            return self.get_special_cast_func(traitwidgetmapper)
        elif isinstance(traittype,Any) or (traittype is Any): # is Any can be True for Property() function
#            print(traitwidgetmapper.traitname, traitwidgetmapper.traittype,traitwidgetmapper.traitvalue)
            return lambda x: eval(x) # alternative: eval strings, identity map others
        else:
            raise NotImplementedError('No cast function for "{}"-trait of class "{}" which is type "{}" defined.'.format(
                    traitwidgetmapper.traitname,
                    traitwidgetmapper.obj.__class__.__name__,
                    traittype.__class__))            
        
    def get_settable_trait_values(self,traitwidgetmapper):
        '''
        takes trait_type of trait object and returns list with settable values
        '''
        if isinstance(traitwidgetmapper.traittype,(TraitEnum,Enum)):
            return list(traitwidgetmapper.traittype.values)
        elif isinstance(traitwidgetmapper.traittype, TraitMap):
            return list(traitwidgetmapper.traittype.map.keys())
        elif isinstance(traitwidgetmapper.traittype, Bool):
            return [True,False]
        elif isinstance(traitwidgetmapper.traittype,NUMERIC_TYPES) \
        or isinstance(traitwidgetmapper.traittype,(Str,File)):
            return [traitwidgetmapper.traitvalue]
        else:
            raise ValueError('can not determine Select options for trait "{}" of class "{}" which is type "{}"'.format(
                    traitwidgetmapper.traitname,
                    traitwidgetmapper.obj.__class__.__name__,
                    traitwidgetmapper.traittype.__class__))

    def get_item_type_cast_func( self, traittype ):
        itemType = traittype.item_trait.trait_type
        if isinstance(itemType,TraitCoerceType): # in case of ListStr, ListInt,...
            itemType = itemType.aType # returns basic type str, float, ...
            return itemType
        if self.is_numeric(itemType):
            return self.get_numeric_cast_func(itemType)
        elif self.is_boolean(itemType):
            return self.get_boolean_cast_func(itemType)
        elif isinstance(itemType,(Str,File,str)):
            return cast_to_str
        elif isinstance(itemType, Any) or (isinstance is Any):
            return lambda x: x # simple identity mapping
        else:
            raise NotImplementedError("currently unsupported traititemtype {} for \
                             trait of type {}".format(
                             itemType, 
                             traittype)
                             )
#        elif self.is_special(itemType):
#            return self.get_special_cast_func(traitwidgetmapper)

    def get_numeric_cast_func(self,traittype):
        if isinstance(traittype,(Int,Long,CLong,int)):
            return cast_to_int
        elif isinstance(traittype,(Float,float)):
            return cast_to_float
        else:
            raise NotImplementedError('No cast numeric function for type "{}".'.format(
                    traittype.__class__))
            
    def get_boolean_cast_func(self,traittype):
        if isinstance(traittype,(Bool,bool)):
            return cast_to_bool
        else:
            raise NotImplementedError('No boolean cast function for type "{}".'.format(
                    traittype.__class__))        
        
    def get_sequence_cast_func(self,traittype):
        if isinstance(traittype, List):
            item_cast_func = self.get_item_type_cast_func(traittype)
            return self.get_cast_to_list_func(item_cast_func)
        elif isinstance(traittype, Tuple):
            return lambda x: eval(x)
        elif isinstance(traittype,(Str,File,str)):
            return cast_to_str
        elif isinstance(traittype, CArray): 
            return self.get_cast_to_array_func(traittype.dtype) 
#            return self.get_cast_to_list_func()
        else:
            raise NotImplementedError('No sequence cast function for type "{}".'.format(
                    traittype.__class__))     

    def get_special_cast_func(self,traitwidgetmapper):
        if type(traitwidgetmapper.traitvalue) == str: return cast_to_str
        elif type(traitwidgetmapper.traitvalue) == int: return cast_to_int
        elif type(traitwidgetmapper.traitvalue) == float: return cast_to_float
        elif type(traitwidgetmapper.traitvalue) == bool: return cast_to_bool
        elif type(traitwidgetmapper.traitvalue) == list: return cast_to_list
        else:
            raise NotImplementedError('No cast function for "{}"-trait of class "{}" with value {} which is type "{}" defined.'.format(
                        traitwidgetmapper.traitname,
                        traitwidgetmapper.obj.__class__.__name__,
                        traitwidgetmapper.traitvalue,
                        traitwidgetmapper.traittype.__class__))     
            
    def get_cast_to_list_func(self, item_cast_func=None):
        if not item_cast_func: 
            item_cast_func = cast_to_float
        def cast_func(var):
            return [item_cast_func(val) for val in cast_to_list(var)]
        return cast_func 
                 
    def get_cast_to_array_func(self,dtype):
        def cast_func(var):
            return nan_to_num(cast_to_array(var).astype(dtype))
        return cast_func 
        
traitdispatcher = TraitCastDispatcher()
