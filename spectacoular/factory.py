#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements factory for trait to widget translation.

.. autosummary::
    :toctree: generated/

    get_widgets
    BaseSpectacoular
    NumericInputMapper
    ToggleMapper
    TextInputMapper
    SelectMapper
    SliderMapper
    DataTableMapper
"""

from bokeh.models.widgets import TextInput, Select, Slider, DataTable, \
TableColumn, NumberEditor, StringEditor, NumericInput, Toggle
from bokeh.core.property.descriptors import UnsetValueError
from traits.api import Enum, Map, TraitEnum, TraitMap, Array, CArray, Any, \
List, Float, CFloat, Int, CInt, Range, Long, Dict,\
CLong, HasPrivateTraits, TraitCompound,\
BaseStr, BaseFile, Delegate, Bool, Tuple, Str
from numpy import array, newaxis, array_equal,\
    concatenate, stack
from warnings import warn

NUMERIC_TYPES = (Int,Long,CLong,int, 
                 Float,float, )
                 #Complex, complex) # Complex Numbers Missing at the Moment

ALLOWED_WIDGET_TRAIT_MAPPINGS = {
    NumericInput : NUMERIC_TYPES + (TraitCompound,Any,Delegate), # (Trait,Property,Delegate)
    Toggle : (Bool,) + (TraitCompound,Any,Delegate), 
    Select : (Enum, TraitEnum, Map, TraitMap, BaseStr, BaseFile, ) + NUMERIC_TYPES, # Numeric types and Str types should also be allowed here, to further use the set_widgets method with predefined options
    Slider : (Range, ) + NUMERIC_TYPES,
    DataTable : (Array,CArray,List,Tuple, ),
    TextInput : (BaseStr, Str, BaseFile, ) + (TraitCompound,Any,Delegate),
}

DEFAULT_TRAIT_WIDGET_MAPPINGS = {
    Int : NumericInput,
    CInt : NumericInput,
    Long: NumericInput,
    CLong : NumericInput,
    Float : NumericInput,
    CFloat : NumericInput,
    Bool : Toggle,
    Map : Select,
    Enum : Select,
    TraitEnum : Select,
    TraitMap : Select,
    Range : Slider,
    Array : DataTable,
    CArray : DataTable,
    List : DataTable,
    Tuple : DataTable,
    Str : TextInput,
    BaseStr : TextInput,
    }

def as_str_list(func):
    """ decorator to wrap list entries into string type """
    def wrapper(*args):
        list_ = func(*args)
        return [str(val) for val in list_]
    return wrapper

def validate_mapping_is_allowed(obj,traitname,widgetType):
    """validates that a given trait can is allowed to be mapped to a given Bokeh widget type"""
    allowed_trait_types = ALLOWED_WIDGET_TRAIT_MAPPINGS.get(widgetType)
    given_trait_type = obj.trait(traitname).trait_type
    if allowed_trait_types:
        is_allowed_instance = any([isinstance(given_trait_type,allowed_type) for allowed_type in allowed_trait_types])
        is_allowed_type = given_trait_type in allowed_trait_types
        if is_allowed_instance or is_allowed_type:
            pass
        else:
            raise NotImplementedError(
                f"cannot create widget for {traitname} attribute of class {obj}." + 
        f"{widgetType} widget cannot be connected to trait of type {obj.trait(traitname).trait_type.__class__}!")

def widget_mapper_factory(obj,traitname,widgetType): 
    """
    returns an instance of a TraitWidgetMapper class that corresponds
    to the desired widget type.

    Parameters
    ----------
    obj : class object 
        the class object that the trait attribute belongs to.
    traitname : str
        name of the class trait attribute to be mapped.
    widgetType : cls
        type of the widget.

    Raises
    ------
    NotImplementedError
        raises error when widget type is not supported.

    Returns
    -------
    None.

    """
    #validation
    validate_mapping_is_allowed(obj,traitname,widgetType)
    # factory 
    if widgetType is NumericInput: return NumericInputMapper(obj,traitname)
    if widgetType is Toggle: return ToggleMapper(obj,traitname)
    if widgetType is TextInput: return TextInputMapper(obj,traitname) 
    elif widgetType is Select: return SelectMapper(obj,traitname)
    elif widgetType is Slider: return SliderMapper(obj,traitname) 
    elif widgetType is DataTable: return DataTableMapper(obj,traitname) 
    else: raise NotImplementedError(
        "mapping for widget type {} does not exist!".format(widgetType))


def get_widgets(self, trait_widget_mapper={}, trait_widget_args={}): 
    """This function creates a View (a bunch of instanciated widgets without a layout) 
    defined by the :attr:`trait_widget_mapper` mapping attribute
    of the given object (or specified via :meth:`get_widgets` method arguments). 
    
    This function is implemented in all SpectAcoular classes and is added to
    Acoular's classes in bokehview.py. It builds Bokeh widgets from 
    corresponding class trait attributes by utilizing the :class:`TraitWidgetMapper` 
    derived classes. The desired mapping is defined by the :attr:`trait_widget_mapper` 
    dictionary. 

    This function implements multiple cases of View construction:

    * (Case 1 - Default View) get_widgets() is called by a BaseSpectacoular 
      derived instance without specifying trait_widget_mapper and trait_widget_args 
      as function arguments. In this case, the mapping defined by the object instance attributes
      (`self.trait_widget_mapper`,self.`trait_widget_args`) will be used to 
      construct the View.     

    * (Case 2 - Custom View (a)) get_widgets() is called by a BaseSpectacoular 
      derived instance and the desired mapping is given by the 
      :meth:`get_widgets` function arguments (trait_widget_mapper and trait_widget_args).
      In this case, the mapping defined by the function arguments will be used to
      create the View. The instance attributes (`self.trait_widget_mapper`,self.`trait_widget_args`) 
      will be superseded. 

    * (Case 3 - No Predefined View) :meth:`get_widgets` is called and a HasTraits derived instance 
      is given as the first argument to the function. The instance object has no 
      trait_widget_mapper and trait_widget_args attributes. 
      In this case, a default mapping is created from all editable traits to create the view. 
    
    * (Case 4 - Custom View (b)) :meth:`get_widgets` is called and a HasTraits derived instance 
      is given as the first argument to the function. The instance object has no 
      trait_widget_mapper and trait_widget_args attributes, but a mapping is defined by the 
      second (and third) function argument. In this case, the mapping defined by the function arguments will be used to create the View. 
    
    Parameters
    ----------
    trait_widget_mapper : dict, optional
        contains the desired mapping of a variable name (dict key) 
        to a Bokeh widget type (dict value), by default {}
    trait_widget_args : dict, optional
        contains the desired widget kwargs (dict values) for each variable name (dict key),
         by default {}

    Returns
    -------
    dict
        A dictionary containing the variable names as the key and the Bokeh widget
        instance as value.
    """

    widgetdict = {}
    if not hasattr(self,'trait_widget_mapper'): # in case of classes that are not part of Spectacoular
        if not trait_widget_mapper: # if no trait_widget_mapper defined, take the default
            for traitname in self.editable_traits():
                traittype = self.trait(traitname).trait_type
                defaultWidgetType = DEFAULT_TRAIT_WIDGET_MAPPINGS.get(traittype.__class__)
                if defaultWidgetType:
                    widgetMapper = widget_mapper_factory(self,traitname,defaultWidgetType)
                    widgetdict[traitname] = widgetMapper.create_widget()                
                else: # in case no default widget exists, a simple TextInput that is readonly will
                    #be created
                    widgetMapper = widget_mapper_factory(self,traitname,TextInput)
                    widgetdict[traitname] = widgetMapper.create_widget(disabled=True)         
            return widgetdict
    else: # in case of BaseSpectacoular derived classes
        # check if a custom view is defined via function arguments trait_widget_mapper
        # and trait_widget_args
        if not trait_widget_mapper:
            trait_widget_mapper = self.trait_widget_mapper
        if not trait_widget_args:
            trait_widget_args = self.trait_widget_args                                           
    # create widgets for spectacoular derived classes
    for (traitname,widgetType) in list(trait_widget_mapper.items()):
        widgetMapper = widget_mapper_factory(self,traitname,widgetType)
        kwargs = trait_widget_args.get(traitname)
        if kwargs:
            widgetdict[traitname] = widgetMapper.create_widget(**kwargs)
        else:
            widgetdict[traitname] = widgetMapper.create_widget()          
    return widgetdict

def set_widgets(self,**kwargs):
    """
    Set instances of Bokeh widgets to certain trait attributes 
    
    This function is implemented in all SpectAcoular classes and is added to
    Acoular's classes in bokehview.py.
    It allows to reference an existing widget to a certain class trait attribute.
    Expects a class traits name as parameter and the widget instance as 
    value. 
    
    For example: 
        >>> from spectacoular import RectGrid
        >>> from bokeh.models.widgets import Select
        >>>
        >>> rg = RectGrid()
        >>> sl = Select(value="10.0")
        >>> rg.set_widgets(x_max=sl)
    
    The value of the trait attribute changes to the widgets value when it is 
    different.    

    Parameters
    ----------
    **kwargs : 
        The name of the class trait attributes. Depends on the class.

    Returns
    -------
    None.

    """
    for traitname, widget in kwargs.items():
        widgetMapper = widget_mapper_factory(self,traitname,widget.__class__)
        widgetMapper.set_widget(widget)
        


class BaseSpectacoular(HasPrivateTraits):
    """
    Base class for any class defined in the SpectAcoular module.
    
    It provides the necessary methods to create widgets from trait attributes 
    and to assign Bokeh's widgets to trait attributes.
    This class has no real functionality on its own and should not be 
    used directly.
    """
    
    #: dictionary containing the mapping between a class trait attribute and 
    #: a Bokeh widget. Keys: name of the trait attribute. Values: Bokeh widget.
    trait_widget_mapper = Dict({
                       })

    #: dictionary containing arguments that belongs to a widget that is created
    #: from a trait attribute and should be considered when the widget is built.
    #: For example: {"traitname":{'disabled':True,'background_color':'red',...}}.
    trait_widget_args = Dict({
                     })
    
    #: function to create widgets from class trait attributes 
    get_widgets = get_widgets
    
    #: function to assign widget instances to class trait attributes
    set_widgets = set_widgets



class TraitWidgetMapper(object):
    """
    Widget Factory which depending on the trait and widget type returns the 
    corresponding mapper class to instantiate the widget.
    
    The :class:`TraitWidgetMapper` derived classes are used to create an instance
    of the desired widget.
    Further, they implement dependencies between a class trait attribute and
    the corresponding widget.
    """

    #: name of the class trait attribute to be mapped (type: str)
    traitname = object()
    
    #: value of the class trait attribute. Can be of arbitrary type
    traitvalue = object()
    
    #: type of the class trait attribute
    traittype = object()
    
    #: the class object that the trait attribute belongs to
    obj = None 

    #: instance of a Bokeh widget that is created by the :class:`TraitWidgetMapper`
    widget = object()
    
    traitvaluetype = object() 
    
    def __init__(self,obj,traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        try:
            self.traitvalue = getattr(obj,traitname)
        except AttributeError: # in case of Delegate
            self.traitvalue = None
        self.traitvaluetype = type(getattr(obj,traitname))

    def _set_traitvalue(self,widgetvalue):
        """
        Sets the value of a class trait attribute to the widgets value.       

        Parameters
        ----------
        widgetvalue : str
            value of the widget.

        Returns
        -------
        None.
        
        """
#        print("set traitvalue for trait {}".format(self.traitname))
        setattr(self.obj,self.traitname,widgetvalue)

    def _set_widgetvalue(self,traitvalue,widgetproperty="value"):
        """
        Sets the value of a widget to the class traits attribute value.
        In case, the widget value and the trait value are of different type, 
        a cast function is used.        

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.
        
        """
        #print(f"trait value: {traitvalue}")
        setattr(self.widget,widgetproperty,traitvalue)

    def create_trait_setter_func(self):
        """
        creates a function that casts the type of a widget value into the type
        of the class trait attribute.
        
        the function is evoked every time the widget value changes. The value 
        of a :class:`Select`, :class: `TextInput`, ..., widget is always type str. 
        However, traitvalues can be of arbitrary type. Thus, widgetvalues need to 
        be casted. 

        Returns
        -------
        callable.

        """
        def callback(attr, old, new):
            #print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj,self.traitname,new): 
                new = self.traitvaluetype(new)
            self._set_traitvalue(new)
        return callback
    
    def create_widget_setter_func(self, widgetproperty="value"):
        """
        creates a function that casts a variable `new` into a valid type
        to be set as the widget value.

        Returns
        -------
        callable.

        """
        def callback(new):
        #    print("{} widget changed".format(self.traitname))
            self._set_widgetvalue(new, widgetproperty)
        return callback

    def _set_callbacks(self,widgetproperty="value"):
        """
        function that sets on_change callbacks between widget and class trait 
        attribute.
        
        function implements:
            1. dynamic trait listener. on changes of 'traitvalue' -> widget.value
            is set
            2. widget listener. On changes of 'widget.value' -> attribute of traitvalue
            is set

        Returns
        -------
        None.

        """
        widget_setter_func = self.create_widget_setter_func(widgetproperty)
        self.obj.on_trait_change(widget_setter_func,self.traitname)
        if not self.widget.disabled:
            trait_setter_func = self.create_trait_setter_func()
            self.widget.on_change(widgetproperty,trait_setter_func)


class NumericInputMapper(TraitWidgetMapper):
    """
    Factory that creates :class:`NumericInput` widget from a class trait attribute of type Int.
    """

    def __init__(self,obj,traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        try:
            self.traitvalue = getattr(obj,traitname)
        except AttributeError: # in case of Delegate
            self.traitvalue = None
            
    def create_widget(self,**kwargs):
        """
        creates a Bokeh NumericInput instance 

        Parameters
        ----------
        **kwargs : args of NumericInput
            additional arguments of NumericInput widget.

        Returns
        -------
        instance(NumericInput).

        """
        self.widget = NumericInput(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        connects a Bokeh NumericInput widget instance to a class trait attribute 

        Parameters
        ----------
        widget : instance(NumericInput)
            instance of a NumericInput widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.value) # set traitvalue to widgetvalue
        self._set_callbacks()

    def create_trait_setter_func(self):
        """
        creates a function that sets the value of a trait on the widget value.
        
        The function is evoked every time the widget value changes. No casting 
        necessary for NumericInput widgets

        Returns
        -------
        callable.

        """
        def callback(attr, old, new):
            self._set_traitvalue(new)
        return callback



class ToggleMapper(NumericInputMapper):
    """
    Factory that creates :class:`Toggle` widget from a class trait attribute of type Bool.
    """
    
    def create_widget(self,**kwargs):
        """
        creates a Bokeh Toggle instance 

        Parameters
        ----------
        **kwargs : args of Toggle
            additional arguments of Toggle widget.

        Returns
        -------
        instance(Toggle).

        """
        self.widget = Toggle(label=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue,widgetproperty="active")
        self._set_callbacks(widgetproperty="active")
        return self.widget

    def set_widget(self, widget):
        """
        connects a Bokeh Toggle widget instance to a class trait attribute 

        Parameters
        ----------
        widget : instance(Toggle)
            instance of a Toggle widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.active) # set traitvalue to widgetvalue
        self._set_callbacks(widgetproperty="active")

    def _set_widgetvalue(self,traitvalue,widgetproperty="value"):
        """ Sets the value of a widget to the class traits attribute value.
        In case, the widget value and the trait value are of different type, 
        a cast function is used.        

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.
        widgetproperty : str, optional
            name of the widgets property that is set 
            to the traitvalue, by default "value"

        Returns
        -------
        None.

        """
        #print(f"trait value: {traitvalue}")
        self.widget.active = traitvalue
        setattr(self.widget,widgetproperty,traitvalue)



class TextInputMapper(TraitWidgetMapper):
    """
    Factory that creates :class:`TextInput` widget from a class trait attribute.
    """

    def create_widget(self,**kwargs):
        """
        creates a Bokeh TextInput instance 

        Parameters
        ----------
        **kwargs : args of TextInput
            additional arguments of TextInput widget.

        Returns
        -------
        instance(TextInput).

        """
        self.widget = TextInput(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        connects a Bokeh TextInput widget instance to a class trait attribute 

        Parameters
        ----------
        widget : instance(TextInput)
            instance of a TextInput widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.value) # set traitvalue to widgetvalue
        self._set_callbacks()


class SelectMapper(TraitWidgetMapper):
    """
    Factory that creates :class:`Select` widget from a class trait attribute.
    """
    
    def create_widget(self,**kwargs):
        """
        creates a Bokeh Select widget instance 

        Parameters
        ----------
        **kwargs : args of Select
            additional arguments of Select widget.

        Returns
        -------
        instance(Select).

        """
        self.widget = Select(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_options()
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        connects a Bokeh Select widget instance to a class trait attribute 

        Parameters
        ----------
        widget : instance(Select)
            instance of a Select widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        traitvalue = self.widget.value
        if not self.traitvaluetype == str: # checks if casting is necessary 
            traitvalue = self.traitvaluetype(traitvalue) # cast to the correct traittype
        self._set_traitvalue(traitvalue) # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_widgetvalue(self,traitvalue,widgetproperty="value"):
        """
        Sets the value of a widget to the class traits attribute value.
        In case, the widget value and the trait value are of different type, 
        a cast function is used.        

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.
        
        """
        if not isinstance(traitvalue,str):
            traitvalue = str(traitvalue)
        setattr(self.widget,widgetproperty,traitvalue)

    def create_trait_setter_func(self):
        """
        creates a function that casts the type of a widget value into the type
        of the class trait attribute.
        
        the function is evoked every time the widget value changes. The value 
        of a :class:`Select`, :class: `TextInput`, ..., widget is always type str. 
        However, traitvalues can be of arbitrary type. Thus, widgetvalues need to 
        be casted. 

        Returns
        -------
        callable.

        """
        def callback(attr, old, new):
            #print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj,self.traitname,new): 
                new = self.traitvaluetype(new)
            self._set_traitvalue(new)
        return callback
    
    def create_widget_setter_func(self, widgetproperty="value"):
        """
        creates a function that casts a variable `new` into a valid type
        to be set as the widget value.

        Returns
        -------
        callable.

        """
        def callback(new):
#            print("{} widget changed".format(self.traitname))
            self._set_widgetvalue(new, widgetproperty)
        return callback


    def _set_options(self):
        """
        sets the :attr:`options` of a :class:`Select` widget

        Returns
        -------
        None.

        """
        if not self.widget.options:
            self.widget.options = self._get_options()

    def _validate_traitvalue(self, traitvalue):
        if not type(traitvalue) in [str,float,int]:
            raise ValueError("Can only handle values of type str, float or int for Select widget."+\
                             f"Type {type(traitvalue)} is not supported.")

    def _validate_options(self, options):
        """
        Mapper can only handle options of the same type (e.g. str, int or float).
        Otherwise an error is raised.

        Parameters
        ----------
        options : tuple
            settable values of the trait.

        Returns
        -------
        None.

        """
        typeset = set([type(o) for o in options])
        if len(typeset) > 1:
            raise ValueError("Can only handle options of the same type for widgets of type Select.")

    @as_str_list
    def _get_options(self): 
        """
        gets settable trait values as string list to be used as options of 
        Select widget. 

        Returns
        -------
        list
            settable trait attribute values.

        """
        if isinstance(self.traittype,(Enum,TraitEnum)):
            options = self.traittype.values
        elif isinstance(self.traittype,(Map,TraitMap)):
            options = self.traittype.map.keys()
        elif isinstance(self.traittype,ALLOWED_WIDGET_TRAIT_MAPPINGS[Select]):
            options = [self.traitvalue]
        else:
            raise ValueError(f"Unknown trait type {self.traittype}")
        self._validate_options(options)
        return options



class SliderMapper(TraitWidgetMapper):
    """
    Factory that creates :class:`Slider` widget from a class trait attribute.
    """
    
    def create_widget(self,**kwargs):
        """
        creates a Bokeh :class:`Slider` widget instance from class trait
        attribute. 
        
        Currently, only attributes of type :class:`Range` are 
        supported.

        Parameters
        ----------
        **kwargs : args of Slider
            additional arguments of Slider widget. :attr:´value´, :attr:´start´
            and :attr:´end´ are of type float

        Returns
        -------
        instance(Slider).

        """
        self.widget = Slider(title=self.traitname,**kwargs)
        self._set_widgetvalue(self.traitvalue, widgetproperty="value")
        self._set_range()
        self._set_callbacks()
        return self.widget
    
    def set_widget(self, widget):
        """
        connects a Bokeh Slider widget instance to a class trait attribute 

        Parameters
        ----------
        widget : instance(Slider)
            instance of a Slider widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        traitvalue = self.widget.value
        if not self.traitvaluetype == self.traitvaluetype: # checks if casting is necessary 
            traitvalue = self.traitvaluetype(traitvalue) # cast to the correct traittype
        self._set_traitvalue(traitvalue) # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_range(self):
        """
        sets the :attr:´start´ and :attr:´end´ of the Slider widget, depending
        on Range trait attributes `_low` and `_high`. In case of numeric trait
        types, the start and end values have to be provided via the 
        attr:`trait_mapper_args` attribute.

        Returns
        -------
        None.

        """
        if isinstance(self.traittype, Range):
            try:
                self.widget.start
            except UnsetValueError:
                self.widget.start = self.traittype._low
            try:
                self.widget.end
            except UnsetValueError:
                self.widget.end = self.traittype._high

    def _set_widgetvalue(self,traitvalue,widgetproperty="value"):
        """
        Sets the value of the Slider widget to the class traits attribute value.
        
        The Slider value is always of type float. In case, the widget value 
        and the trait value are of different type, a cast function is used. 

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.
        
        """
        if not isinstance(traitvalue,float):
            traitvalue = float(traitvalue)
        setattr(self.widget,widgetproperty,traitvalue)

    def create_trait_setter_func(self):
        """
        creates a function that casts the type of a widget value into the type
        of the class trait attribute.
        
        the function is evoked every time the widget value changes. The value 
        of a :class:`Select`, :class: `TextInput`, ..., widget is always type str. 
        However, traitvalues can be of arbitrary type. Thus, widgetvalues need to 
        be casted. 

        Returns
        -------
        callable.

        """
        def callback(attr, old, new):
            #print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj,self.traitname,new): 
                new = self.traitvaluetype(new)
            self._set_traitvalue(new)
        return callback
    
class DataTableMapper(TraitWidgetMapper):
    """
    Factory that creates :class:`DataTable` widget from a class trait attribute.
    """

    transposed = False

    def create_widget(self,**kwargs):
        """
        creates a Bokeh :class:`DataTable` widget instance from class trait
        attribute. 
        
        Creates a bokeh DataTable instance. For transposed arrays that are 
        mapped to the DataTable, array data is reshaped and casted to fit the
        required dictionary format of the ColumnDataSource.
        In case of list types, only one-dimensional lists are allowed. The
        transposed attribute will have no effect.

        Parameters
        ----------
        **kwargs : args of DataTable
            additional arguments of DataTable widget. 

        Returns
        -------
        instance(DataTable).

        """

        # first filter out transposed argument (not an attribute of Bokeh's 
        # DataTable widget).
        if 'transposed' in kwargs.keys():
            self.transposed = kwargs.pop('transposed') #remove from kwargs
        # create widget
        self.widget = DataTable(**kwargs) 
        self.create_columns()
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        connects a Bokeh DataTable widget instance to a class trait attribute.

        The current implementation of set_widget can only handle non-transposed
        mappings. Meaning that columns of the arraytrait have to be columns 
        in the ColumnDataSource (not rows). 

        Parameters
        ----------
        widget : instance(DataTable)
            instance of a DataTable widget.
        **kwargs : dict
            additional arguments of DataTableMapper. 

        Returns
        -------
        None.

        """
        self.widget = widget
        if isinstance(self.traittype,List):
            value = list(self.widget.source.data.values())[0]
            setattr(self.obj,self.traitname,value)
        elif isinstance(self.traittype,Tuple):
            value = tuple(list(self.widget.source.data.values())[0])
            setattr(self.obj,self.traitname,value)
        else:
            value = array(list(self.widget.source.data.values())).T
            self._set_traitvalue(value) # set traitvalue to widgetvalue
        self._set_callbacks()

    def create_columns( self ):
        ''' create single TableColumn and add to widget '''
        if not self.widget.columns:
            if isinstance(self.traittype,(List,Tuple)):
                num_cols=1
            else: # array
                if self.traitvalue.ndim == 1:
                    num_cols = 1
                else:
                    num_cols = self.traitvalue.shape[1]
                    if self.transposed:
                        num_cols = self.traitvalue.shape[0]
            self.widget.columns = [
                    TableColumn(field=f"{c}",title=f"{c}") for c in range(num_cols)]
            self._set_celleditor()
            
    def _set_celleditor( self ):
        ''' adds a cell editor to the DataTable depending on table content.
        If the dtype of the trait can not be determined and the DataTable is 
        editable, a StringEditor is set.
        '''
        if self.widget.editable:
            if isinstance(self.traittype,(List,Tuple)):
                if len(self.traitvalue) > 0:
                    dtype = type(self.traitvalue[0]) 
                else:
                    dtype = None
            else: # array types
                dtype = self.traittype.dtype                
            if dtype in NUMERIC_TYPES: 
                editor = NumberEditor()
            else:
                if dtype is None:
                    warn((f"Undefined dtype of trait {self.traitname} which is linked to an editable DataTable widget."+ 
                    " Setting an instance of StringEditor for each column."))
                editor = StringEditor()
            for col in self.widget.columns:
                col.editor = editor
            
    def _set_widgetvalue(self,traitvalue,widget_property="data"):
        """
        Sets the data of the DataTable's ColumnDataSource to the class traits 
        attribute value.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.
        
        """
        num_columns = len(self.widget.columns)
        if isinstance(self.traittype,(List,Tuple)):
            new_data = {self.widget.columns[0].field:traitvalue}
        else: # if array type
            if self.transposed:
                traitvalue = traitvalue.T
            dim = len(traitvalue.shape)
            if dim > 1:
                if num_columns < traitvalue.shape[1]:
                    raise ValueError(
                        f"DataTable linked to {self.traitname} trait of {self.obj} has only {num_columns} columns but the assigned array has {traitvalue.shape[1]} columns")
                new_data = {self.widget.columns[i].field: traitvalue[:,i][:,newaxis] for i in range(traitvalue.shape[1])}
            else:
                new_data = {self.widget.columns[0].field: traitvalue}
        #if new_data != self.widget.source.data:
        self.widget.source.data = new_data

    def _set_callbacks( self ):
        """
        function that sets on_change callbacks between widget and class trait 
        attribute.
        
        function implements:
            1. dynamic trait listener. on changes of 'traitvalue' -> ColumnDataSource.data
            is set
            2. widget listener. On changes of 'ColumnDataSource.data' -> attribute of traitvalue
            is set

        Returns
        -------
        None.

        """
        widget_setter_func = self.create_widget_setter_func()
        self.obj.on_trait_change(widget_setter_func,self.traitname)
        if self.widget.editable:
            trait_setter_func = self.create_trait_setter_func()
            self.widget.source.on_change('data',trait_setter_func)

    def create_trait_setter_func(self):
        """
        creates a function that casts the type of a widget value into the type
        of the class trait attribute.
        
        the function is evoked every time the widget value changes. The value 
        of a :class:`Select`, :class: `TextInput`, ..., widget is always type str. 
        However, traitvalues can be of arbitrary type. Thus, widgetvalues need to 
        be casted. 

        Returns
        -------
        callable.

        """
        if isinstance(self.traittype,List):
            def callback(attr, old, new):
                current_value = getattr(self.obj,self.traitname)
                new_value = list(new.values())[0]
                if current_value != new_value:
                    setattr(self.obj,self.traitname,new_value)
        elif isinstance(self.traittype,Tuple):
            def callback(attr, old, new):
                current_value = getattr(self.obj,self.traitname)
                new_value = tuple(list(new.values())[0])
                if current_value != new_value:
                    setattr(self.obj,self.traitname,new_value)
        else: # array type
            def callback(attr, old, new):
                # new variable is of type dict! get dict values:
                # get all values for given Table Column field names (keys)
                fieldnames = [col.field for col in self.widget.columns]
                column_values = [new.get(fn) for fn in fieldnames]
                new_traitvalue = self._cds_to_numpy_array_transform(column_values,self.transposed)
                self._set_traitvalue(new_traitvalue)
        return callback

    def _cds_to_numpy_array_transform(self,column_values,transposed):
        """Maps the column values of DataTable's ColumnDataSource to a numpy array
        to be used as new value of the array trait mapped to this DataTable widget.

        When using bokeh renderers, the columns of the ColumnDataSource will be converted
        to a list type when elements are added to or removed from these columns. In this case,
        type casting from list to array type is necessary.

        Parameters
        ----------
        column_values : array or list
            column values of the ColumnDataSource
        transposed : bool
            if true, maps the columns of the ColumnDataSource to rows. 

        Returns
        -------
        array
            the new trait value based on the column values
        """

        if type(column_values) == list: # cast to array if is list type
            column_values = array(column_values)
        if column_values[0].ndim == 1 and len(column_values) == 1: # mapps to arrays with -> (n,) shapes
            new_traitvalue = column_values[0] 
        else: # mapps to arrays with -> (n,number_of_columns) shapes
            if column_values[0].ndim == 1:
                new_traitvalue = stack(column_values,axis=1).squeeze()      
            else:
                new_traitvalue = concatenate(column_values,axis=1)      
            if transposed:
                new_traitvalue = new_traitvalue.T
        return new_traitvalue

    def _set_traitvalue(self,widgetvalue):
        """
        Sets the value of a class trait attribute to the widgets value.       

        Parameters
        ----------
        widgetvalue : array
            data from ColumnDataSource as numpy array.

        Returns
        -------
        None.
        
        """
        current_value = getattr(self.obj,self.traitname)
        if not array_equal(widgetvalue,current_value):
            setattr(self.obj,self.traitname,widgetvalue)


