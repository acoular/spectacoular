# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------
"""Implements factory for trait to widget translation.

.. autosummary::

    :toctree: generated/

    get_widgets
    set_widgets
    BaseSpectacoular
    NumericInputMapper
    ToggleMapper
    TextInputMapper
    SelectMapper
    SliderMapper
    DataTableMapper
"""

from warnings import warn

import numpy as np
from bokeh.core.property.descriptors import UnsetValueError
from bokeh.models.widgets import (
    DataTable,
    MultiSelect,
    NumberEditor,
    NumericInput,
    Select,
    Slider,
    StringEditor,
    TableColumn,
    TextInput,
    Toggle,
)
from traits.api import (
    Any,
    Array,
    BaseFile,
    BaseStr,
    Bool,
    CArray,
    CFloat,
    CInt,
    Delegate,
    Dict,
    Enum,
    Float,
    HasPrivateTraits,
    Int,
    List,
    Map,
    Range,
    Str,
    TraitCompound,
    TraitEnum,
    TraitMap,
    Tuple,
    Union,
)

NUMERIC_TYPES = (Int, int, Float, float, CInt, CFloat)
# Complex, complex) # Complex Numbers Missing at the Moment

ALLOWED_WIDGET_TRAIT_MAPPINGS = {
    NumericInput: (*NUMERIC_TYPES, TraitCompound, Any, Delegate, Union),  # (Trait,Property,Delegate)
    Toggle: (Bool, TraitCompound, Any, Delegate, Union),
    Select: (
        Enum,
        TraitEnum,
        Map,
        TraitMap,
        BaseStr,
        BaseFile,
        Union,
        *NUMERIC_TYPES,
    ),  # Also allow numeric and string types for predefined options.
    Slider: (Range, Union, *NUMERIC_TYPES),
    DataTable: (Array, CArray, List, Tuple, Union),
    TextInput: (
        BaseStr,
        Str,
        BaseFile,
        TraitCompound,
        Any,
        Delegate,
        Union,
    ),
    MultiSelect: (List, Union),
}

DEFAULT_TRAIT_WIDGET_MAPPINGS = {
    Int: NumericInput,
    CInt: NumericInput,
    Float: NumericInput,
    CFloat: NumericInput,
    Bool: Toggle,
    Map: Select,
    Enum: Select,
    TraitEnum: Select,
    TraitMap: Select,
    Range: Slider,
    Array: DataTable,
    CArray: DataTable,
    List: DataTable,
    Tuple: DataTable,
    Str: TextInput,
    BaseStr: TextInput,
}


def as_str_list(func):
    """Wrap list entries into string type."""

    def wrapper(*args):
        list_ = func(*args)
        return [str(val) for val in list_]

    return wrapper


def validate_mapping_is_allowed(obj, traitname, widget_type):
    """Validate that a given trait can be mapped to a given Bokeh widget type."""
    allowed_trait_types = ALLOWED_WIDGET_TRAIT_MAPPINGS.get(widget_type)
    given_trait_type = obj.trait(traitname).trait_type
    if allowed_trait_types:
        is_allowed_instance = any(isinstance(given_trait_type, allowed_type) for allowed_type in allowed_trait_types)
        is_allowed_type = given_trait_type in allowed_trait_types
        if not (is_allowed_instance or is_allowed_type):
            msg = (
                f'cannot create widget for {traitname} attribute of class {obj}.'
                f'{widget_type} widget cannot be connected to trait of type '
                f'{obj.trait(traitname).trait_type.__class__}!'
            )
            raise NotImplementedError(msg)


def widget_mapper_factory(obj, traitname, widget_type):
    """Return a ``TraitWidgetMapper`` instance for the desired widget type.

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
    validate_mapping_is_allowed(obj, traitname, widget_type)

    mapper_types = {
        NumericInput: NumericInputMapper,
        Toggle: ToggleMapper,
        TextInput: TextInputMapper,
        Select: SelectMapper,
        Slider: SliderMapper,
        DataTable: DataTableMapper,
        MultiSelect: MultiSelectMapper,
    }
    mapper_type = mapper_types.get(widget_type)
    if mapper_type is None:
        msg = f'mapping for widget type {widget_type} does not exist!'
        raise NotImplementedError(msg)
    return mapper_type(obj, traitname)


def get_widgets(self, trait_widget_mapper=None, trait_widget_args=None):
    """Create a mapping between several class trait attributes and Bokeh widgets.

    This function is implemented in all SpectAcoular classes and is added to
    Acoular's classes via the :mod:`~spectacoular.bokehview` module. For each
    attribute provided, it builds a corresponding Bokeh widget.

    The function handles multiple cases of View construction:

    * **Default View:** the function is called as a method by a
      :class:`~spectacoular.factory.BaseSpectacoular` derived instance without
      specifying :attr:`trait_widget_mapper` and :attr:`trait_widget_args`
      explicitly as function arguments. In this case, the default widget mapping, defined in
      :mod:`~spectacoular.bokehview`, will be used:

      .. bokeh-plot::
          :source-position: above

          from spectacoular import RectGrid
          from bokeh.io import show
          from bokeh.layouts import gridplot

          grid = RectGrid()

          widgets = list(grid.get_widgets().values())
          show(gridplot(widgets, ncols=5, sizing_mode='stretch_both'))

    * **No Predefined View:** :meth:`get_widgets` is called and a HasTraits derived instance
      is given as the first argument to the function without any further arguments.
      In this case, a default mapping is created from all editable traits to create the view.

    .. bokeh-plot::
        :source-position: above

        from acoular import RectGrid
        from spectacoular import get_widgets
        from bokeh.io import show
        from bokeh.layouts import gridplot

        grid = RectGrid()

        widgets = list(get_widgets(grid).values())
        show(gridplot(widgets, ncols=5, sizing_mode='stretch_both'))

    * **Custom View:** :meth:`~spectacoular.factory.get_widgets` is called by a
      :class:`~spectacoular.factory.BaseSpectacoular` derived instance and an
      explicit mapping is given. In this case, the instance attributes
      (``self.trait_widget_mapper``, ``self.trait_widget_args``) are superseded.

      .. bokeh-plot::
          :source-position: above

          from spectacoular import RectGrid
          from bokeh.io import show
          from bokeh.models.widgets import Slider
          from bokeh.layouts import column

          grid = RectGrid()

          trait_widget_mapper = {'x_min': Slider}
          trait_widget_args = {'x_min': {'title': 'X Min', 'start': -1, 'end': 1, 'step':0.1}}

          widgets = list(grid.get_widgets(
                trait_widget_mapper=trait_widget_mapper,
                trait_widget_args=trait_widget_args
          ).values())
          show(column(widgets,sizing_mode='stretch_both'))

      The same functionality can also be used with ``HasTraits``-derived
      classes that are not part of SpectAcoular:

      .. bokeh-plot::
          :source-position: above

          from acoular import RectGrid
          from spectacoular import get_widgets
          from bokeh.io import show
          from bokeh.models.widgets import Slider
          from bokeh.layouts import column

          grid = RectGrid()

          trait_widget_mapper = {'x_min': Slider}
          trait_widget_args = {'x_min': {'title': 'X Min', 'start': -1, 'end': 1, 'step':0.1}}

          widgets = list(get_widgets(grid,
                trait_widget_mapper=trait_widget_mapper,
                trait_widget_args=trait_widget_args
          ).values())
          show(column(widgets,sizing_mode='stretch_both'))


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
    trait_widget_mapper = {} if trait_widget_mapper is None else trait_widget_mapper
    trait_widget_args = {} if trait_widget_args is None else trait_widget_args
    widgetdict = {}
    if not hasattr(self, 'trait_widget_mapper'):  # in case of classes that are not part of Spectacoular
        if not trait_widget_mapper:  # if no trait_widget_mapper defined, take the default
            for traitname in self.editable_traits():
                traittype = self.trait(traitname).trait_type
                default_widget_type = DEFAULT_TRAIT_WIDGET_MAPPINGS.get(traittype.__class__)
                if default_widget_type:
                    widget_mapper = widget_mapper_factory(self, traitname, default_widget_type)
                    widgetdict[traitname] = widget_mapper.create_widget()
                else:  # in case no default widget exists, a simple TextInput that is readonly will
                    # be created
                    widget_mapper = widget_mapper_factory(self, traitname, TextInput)
                    widgetdict[traitname] = widget_mapper.create_widget(disabled=True)
            return widgetdict
    else:  # in case of BaseSpectacoular derived classes
        # check if a custom view is defined via function arguments trait_widget_mapper
        # and trait_widget_args
        if not trait_widget_mapper:
            trait_widget_mapper = self.trait_widget_mapper
        if not trait_widget_args:
            trait_widget_args = self.trait_widget_args
    # create widgets for spectacoular derived classes
    for traitname, widget_type in list(trait_widget_mapper.items()):
        widget_mapper = widget_mapper_factory(self, traitname, widget_type)
        kwargs = trait_widget_args.get(traitname)
        if kwargs:
            widgetdict[traitname] = widget_mapper.create_widget(**kwargs)
        else:
            widgetdict[traitname] = widget_mapper.create_widget()
    return widgetdict


def set_widgets(self, **kwargs):
    """
    Set instances of Bokeh widgets to certain trait attributes.

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
        >>> sl = Select(value='10.0')
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
        widget_mapper = widget_mapper_factory(self, traitname, widget.__class__)
        widget_mapper.set_widget(widget)


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
    trait_widget_mapper = Dict({})

    #: dictionary containing arguments that belongs to a widget that is created
    #: from a trait attribute and should be considered when the widget is built.
    #: For example: {"traitname":{'disabled':True,'background_color':'red',...}}.
    trait_widget_args = Dict({})

    #: function to create widgets from class trait attributes
    get_widgets = get_widgets

    #: function to assign widget instances to class trait attributes
    set_widgets = set_widgets


class TraitWidgetMapper:
    """Map a trait attribute to a corresponding Bokeh widget.

    Derived classes of :class:`TraitWidgetMapper` create widget instances and
    keep the widget value synchronized with the mapped trait attribute.

    Attributes
    ----------
    obj : class object
        The class object that the trait attribute belongs to.
    traitname : str
        Name of the class trait attribute to be mapped.
    traittype : TraitType
        Type of the class trait attribute.
    traitvalue : any
        Value of the class trait attribute.
    traitvaluetype : type
        Type of the value of the class trait attribute.
    traitdescription : str
        Description of the class trait attribute.
    widget : Widget
        Instance of the widget.
    """

    def __init__(self, obj, traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        try:
            self.traitvalue = getattr(obj, traitname)
        except AttributeError:  # in case of Delegate
            self.traitvalue = None
        self.traitvaluetype = type(getattr(obj, traitname))
        self.traitdescription = obj.trait(traitname).desc
        self.widget = None

    def _set_traitvalue(self, widgetvalue):
        """
        Set the value of a class trait attribute to the widgets value.

        Parameters
        ----------
        widgetvalue : str
            value of the widget.

        Returns
        -------
        None.

        """
        #        print("set traitvalue for trait {}".format(self.traitname))
        setattr(self.obj, self.traitname, widgetvalue)

    def _set_widgetvalue(self, traitvalue, widgetproperty='value'):
        """
        Set the value of a widget to the class traits attribute value.

        If the widget value and the trait value are of different types,
        a cast function is used.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.

        """
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription
        setattr(self.widget, widgetproperty, traitvalue)

    def create_trait_setter_func(self):
        """Create a callback that writes widget values back to the trait.

        The callback is invoked every time the widget value changes. If the
        widget value type differs from the trait value type, the value is cast
        before it is assigned.

        Returns
        -------
        callable
            Callback that updates the trait from the widget.

        """

        def callback(attr, old, new):
            del attr, old
            # print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj, self.traitname, new):
                new = self.traitvaluetype(new)
            self._set_traitvalue(new)

        return callback

    def create_widget_setter_func(self, widgetproperty='value'):
        """Create a callback that writes trait values back to the widget.

        Parameters
        ----------
        widgetproperty : str, optional
            Name of the widget property that should be updated.

        Returns
        -------
        callable
            Callback that updates the widget from the trait.

        """

        def callback(new):
            #    print("{} widget changed".format(self.traitname))
            self._set_widgetvalue(new, widgetproperty)

        return callback

    def _set_callbacks(self, widgetproperty='value'):
        """Set callbacks between the widget and the mapped trait attribute.

        This method installs both directions of synchronization:

        1. On trait changes, the widget property is updated.
        2. On widget changes, the trait attribute is updated.

        Returns
        -------
        None.

        """
        widget_setter_func = self.create_widget_setter_func(widgetproperty)
        self.obj.on_trait_change(widget_setter_func, self.traitname)
        if not self.widget.disabled:
            trait_setter_func = self.create_trait_setter_func()
            self.widget.on_change(widgetproperty, trait_setter_func)


class NumericInputMapper(TraitWidgetMapper):
    """Create a :class:`NumericInput` widget from an ``Int`` trait attribute."""

    def __init__(self, obj, traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        self.traitdescription = obj.trait(traitname).desc
        try:
            self.traitvalue = getattr(obj, traitname)
        except AttributeError:  # in case of Delegate
            self.traitvalue = None

    def create_widget(self, **kwargs):
        """
        Create a Bokeh NumericInput instance.

        Parameters
        ----------
        **kwargs : args of NumericInput
            additional arguments of NumericInput widget.

        Returns
        -------
        instance(NumericInput).

        """
        kwargs.setdefault('title', self.traitname)
        self.widget = NumericInput(**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        Connect a Bokeh NumericInput widget instance to a class trait attribute.

        Parameters
        ----------
        widget : instance(NumericInput)
            instance of a NumericInput widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.value)  # set traitvalue to widgetvalue
        self._set_callbacks()

    def create_trait_setter_func(self):
        """
        Create a function that sets the value of a trait on the widget value.

        The function is invoked every time the widget value changes. No casting is
        necessary for ``NumericInput`` widgets.

        Returns
        -------
        callable.

        """

        def callback(attr, old, new):
            del attr, old
            self._set_traitvalue(new)

        return callback


class ToggleMapper(NumericInputMapper):
    """Create a :class:`Toggle` widget from a ``Bool`` trait attribute."""

    def create_widget(self, **kwargs):
        """
        Create a Bokeh Toggle instance.

        Parameters
        ----------
        **kwargs : args of Toggle
            additional arguments of Toggle widget.

        Returns
        -------
        instance(Toggle).

        """
        kwargs.setdefault('label', self.traitname)
        self.widget = Toggle(**kwargs)
        self._set_widgetvalue(self.traitvalue, widgetproperty='active')
        self._set_callbacks(widgetproperty='active')
        return self.widget

    def set_widget(self, widget):
        """
        Connect a Bokeh Toggle widget instance to a class trait attribute.

        Parameters
        ----------
        widget : instance(Toggle)
            instance of a Toggle widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.active)  # set traitvalue to widgetvalue
        self._set_callbacks(widgetproperty='active')

    def _set_widgetvalue(self, traitvalue, widgetproperty='value'):
        """Set the value of a widget to the class trait attribute value.

        If the widget value and the trait value are of different types,
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
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription
        self.widget.active = traitvalue
        setattr(self.widget, widgetproperty, traitvalue)


class TextInputMapper(TraitWidgetMapper):
    """Create a :class:`TextInput` widget from a class trait attribute."""

    def create_widget(self, **kwargs):
        """
        Create a Bokeh TextInput instance.

        Parameters
        ----------
        **kwargs : args of TextInput
            additional arguments of TextInput widget.

        Returns
        -------
        instance(TextInput).

        """
        kwargs.setdefault('title', self.traitname)
        self.widget = TextInput(**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        Connect a Bokeh TextInput widget instance to a class trait attribute.

        Parameters
        ----------
        widget : instance(TextInput)
            instance of a TextInput widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.value)  # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_widgetvalue(self, traitvalue, widgetproperty='value'):
        """
        Set the value of a widget to the class traits attribute value.

        If the widget value and the trait value are of different types,
        a cast function is used.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.

        """
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription
        if traitvalue is None:
            traitvalue = ''
        setattr(self.widget, widgetproperty, traitvalue)


class SelectMapper(TraitWidgetMapper):
    """Create a :class:`Select` widget from a class trait attribute."""

    def create_widget(self, **kwargs):
        """
        Create a Bokeh Select widget instance.

        Parameters
        ----------
        **kwargs : args of Select
            additional arguments of Select widget.

        Returns
        -------
        instance(Select).

        """
        kwargs.setdefault('title', self.traitname)
        self.widget = Select(**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_options()
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        Connect a Bokeh Select widget instance to a class trait attribute.

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
        if not isinstance(self.traitvaluetype, str):  # checks if casting is necessary
            traitvalue = self.traitvaluetype(traitvalue)  # cast to the correct traittype
        self._set_traitvalue(traitvalue)  # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_widgetvalue(self, traitvalue, widgetproperty='value'):
        """
        Set the value of a widget to the class traits attribute value.

        If the widget value and the trait value are of different types,
        a cast function is used.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            value of the class trait attribute.

        Returns
        -------
        None.

        """
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription
        if not isinstance(traitvalue, str):
            traitvalue = str(traitvalue)
        setattr(self.widget, widgetproperty, traitvalue)

    def create_trait_setter_func(self):
        """Create a callback that casts ``Select`` values back to the trait type.

        ``Select`` widget values are always strings. This callback converts the
        selected value back to the mapped trait type before assignment.

        Returns
        -------
        callable
            Callback that updates the trait from the widget.

        """

        def callback(attr, old, new):
            del attr, old
            # print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj, self.traitname, new):
                new = self.traitvaluetype(new)
            self._set_traitvalue(new)

        return callback

    def create_widget_setter_func(self, widgetproperty='value'):
        """Create a callback that converts trait values for the widget.

        Returns
        -------
        callable
            Callback that updates the widget from the trait.

        """

        def callback(new):
            #            print("{} widget changed".format(self.traitname))
            self._set_widgetvalue(new, widgetproperty)

        return callback

    def _set_options(self):
        """
        Set the :attr:`options` of a :class:`Select` widget.

        Returns
        -------
        None.

        """
        if not self.widget.options:
            self.widget.options = self._get_options()

    def _validate_traitvalue(self, traitvalue):
        if type(traitvalue) not in [str, float, int]:
            msg = (
                'Can only handle values of type str, float or int for Select widget. '
                f'Type {type(traitvalue)} is not supported.'
            )
            raise ValueError(msg)

    def _validate_options(self, options):
        """Validate that all ``Select`` options have the same type.

        ``Select`` widgets in this mapper only support option lists whose
        entries all share one common type, for example all strings or all ints.

        Parameters
        ----------
        options : tuple
            Settable values of the trait.

        Returns
        -------
        None.

        """
        typeset = {type(o) for o in options}
        if len(typeset) > 1:
            msg = 'Can only handle options of the same type for widgets of type Select.'
            raise ValueError(msg)

    @as_str_list
    def _get_options(self):
        """Get trait values that can be used as ``Select`` widget options.

        The returned values are converted to strings because Bokeh ``Select``
        widgets store their options as strings.

        Returns
        -------
        list
            Settable trait attribute values.

        """
        if isinstance(self.traittype, (Enum, TraitEnum)):
            options = self.traittype.values
        elif isinstance(self.traittype, (Map, TraitMap)):
            options = self.traittype.map.keys()
        elif isinstance(self.traittype, ALLOWED_WIDGET_TRAIT_MAPPINGS[Select]):
            options = [self.traitvalue]
        else:
            msg = f'Unknown trait type {self.traittype}'
            raise TypeError(msg)
        self._validate_options(options)
        return options


class SliderMapper(TraitWidgetMapper):
    """Create and synchronize a Bokeh :class:`Slider` widget."""

    def create_widget(self, **kwargs):
        """Create a Bokeh :class:`Slider` widget for the mapped trait.

        The created widget is initialized from the current trait value and then
        connected to the trait via callbacks. At the moment this mapper is
        mainly intended for :class:`Range` traits.

        Parameters
        ----------
        **kwargs : args of Slider
            Additional keyword arguments for the ``Slider`` widget. The
            ``value``, ``start``, and ``end`` arguments are float-valued.

        Returns
        -------
        instance(Slider)
            Created widget instance.

        """
        kwargs.setdefault('title', self.traitname)
        self.widget = Slider(**kwargs)
        self._set_widgetvalue(self.traitvalue, widgetproperty='value')
        self._set_range()
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        Connect a Bokeh Slider widget instance to a class trait attribute.

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
        if not isinstance(traitvalue, self.traitvaluetype):
            traitvalue = self.traitvaluetype(traitvalue)
        self._set_traitvalue(traitvalue)  # set traitvalue to widgetvalue
        self._set_callbacks()

    def _set_range(self):
        """Set the ``start`` and ``end`` values of the ``Slider`` widget.

        For :class:`Range` traits, the values are taken from the trait bounds.
        For numeric trait types, the start and end values must be provided via
        ``trait_mapper_args``.

        Returns
        -------
        None.

        """
        if isinstance(self.traittype, Range):
            low = getattr(self.traittype, '_low', None)
            high = getattr(self.traittype, '_high', None)
            try:
                _start = self.widget.start
            except UnsetValueError:
                self.widget.start = low
            try:
                _end = self.widget.end
            except UnsetValueError:
                self.widget.end = high

    def _set_widgetvalue(self, traitvalue, widgetproperty='value'):
        """Set the ``Slider`` value from the mapped trait attribute.

        ``Slider`` widget values are always floats. If the mapped trait value
        has a different numeric type, it is converted before assignment.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            Value of the class trait attribute.

        Returns
        -------
        None.

        """
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription
        if not isinstance(traitvalue, float):
            traitvalue = float(traitvalue)
        setattr(self.widget, widgetproperty, traitvalue)

    def create_trait_setter_func(self):
        """Create a callback that casts slider values back to the trait type.

        Slider widgets expose numeric values that may still need conversion to
        the exact mapped trait type before assignment.

        Returns
        -------
        callable
            Callback that updates the trait from the widget.

        """

        def callback(attr, old, new):
            del attr, old
            # print(self.obj,self.traitname,new)
            if not self.traittype.is_valid(self.obj, self.traitname, new):
                new = self.traitvaluetype(new)
            self._set_traitvalue(new)

        return callback


class DataTableMapper(TraitWidgetMapper):
    """Create and synchronize a Bokeh :class:`DataTable` widget."""

    transposed = False

    def create_widget(self, **kwargs):
        """Create a Bokeh :class:`DataTable` widget for the mapped trait.

        For transposed arrays mapped to the DataTable, array data is reshaped
        and converted to the dictionary format required by
        ``ColumnDataSource``. For list types, only one-dimensional lists are
        allowed and the ``transposed`` option has no effect.

        Parameters
        ----------
        **kwargs : args of DataTable
            Additional keyword arguments for the ``DataTable`` widget.

        Returns
        -------
        instance(DataTable)
            Created widget instance.

        """
        # first filter out transposed argument (not an attribute of Bokeh's
        # DataTable widget).
        if 'transposed' in kwargs:
            self.transposed = kwargs.pop('transposed')  # remove from kwargs
        # create widget
        self.widget = DataTable(**kwargs)
        self.create_columns()
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """Connect an existing ``DataTable`` widget to the mapped trait.

        The current implementation only handles non-transposed mappings, i.e.
        columns of the mapped array trait must correspond to columns in the
        ``ColumnDataSource`` rather than rows.

        Parameters
        ----------
        widget : instance(DataTable)
            Instance of a ``DataTable`` widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        if isinstance(self.traittype, List):
            value = next(iter(self.widget.source.data.values()))
            setattr(self.obj, self.traitname, value)
        elif isinstance(self.traittype, Tuple):
            value = tuple(next(iter(self.widget.source.data.values())))
            setattr(self.obj, self.traitname, value)
        else:
            value = np.array(list(self.widget.source.data.values())).T
            self._set_traitvalue(value)  # set traitvalue to widgetvalue
        self._set_callbacks()

    def create_columns(self):
        """Create a single ``TableColumn`` and add it to the widget."""
        if not self.widget.columns:
            if isinstance(self.traittype, (List, Tuple)) or self.traitvalue.ndim == 1:
                num_cols = 1
            else:
                num_cols = self.traitvalue.shape[1]
                if self.transposed:
                    num_cols = self.traitvalue.shape[0]
            self.widget.columns = [TableColumn(field=f'{c}', title=f'{c}') for c in range(num_cols)]
            self._set_celleditor()

    def _set_celleditor(self):
        """Add a cell editor to the DataTable based on the mapped data type.

        If the trait data type cannot be determined and the DataTable is
        editable, a ``StringEditor`` is used.
        """
        if self.widget.editable:
            if isinstance(self.traittype, (List, Tuple)):
                dtype = type(self.traitvalue[0]) if len(self.traitvalue) > 0 else None
            else:  # array types
                dtype = self.traittype.dtype
            if dtype in NUMERIC_TYPES:
                editor = NumberEditor()
            else:
                if dtype is None:
                    warn(
                        f'Undefined dtype of trait {self.traitname} which is linked to an editable '
                        'DataTable widget. Setting an instance of StringEditor for each column.',
                        stacklevel=2,
                    )
                editor = StringEditor()
            for col in self.widget.columns:
                col.editor = editor

    def _set_widgetvalue(self, traitvalue, _widget_property='data'):
        """Set the table data source from the mapped trait value.

        Depending on the mapped trait type, the value is transformed into the
        column-based dictionary structure expected by ``ColumnDataSource``.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            Value of the class trait attribute.

        Returns
        -------
        None.

        """
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription

        num_columns = len(self.widget.columns)
        if isinstance(self.traittype, (List, Tuple)):
            new_data = {self.widget.columns[0].field: traitvalue}
        else:  # if array type
            if self.transposed:
                traitvalue = traitvalue.T
            dim = len(traitvalue.shape)
            if dim > 1:
                if num_columns < traitvalue.shape[1]:
                    msg = (
                        f'DataTable linked to {self.traitname} trait of {self.obj} has only '
                        f'{num_columns} columns but the assigned array has '
                        f'{traitvalue.shape[1]} columns'
                    )
                    raise ValueError(msg)
                new_data = {
                    self.widget.columns[i].field: traitvalue[:, i][:, np.newaxis] for i in range(traitvalue.shape[1])
                }
            else:
                new_data = {self.widget.columns[0].field: traitvalue}
        self.widget.source.data.update(new_data)

    def _set_callbacks(self):
        """Set callbacks between the DataTable and the mapped trait attribute.

        This method installs both directions of synchronization:

        1. On trait changes, ``ColumnDataSource.data`` is updated.
        2. On widget edits, the trait attribute is updated.

        Returns
        -------
        None.

        """
        widget_setter_func = self.create_widget_setter_func()
        self.obj.on_trait_change(widget_setter_func, self.traitname)
        if self.widget.editable:
            trait_setter_func = self.create_trait_setter_func()
            self.widget.source.on_change('data', trait_setter_func)

    def create_trait_setter_func(self):
        """Create a callback that maps edited table data back to the trait.

        Depending on the mapped trait type, the callback converts edited table
        values to a list, tuple, or NumPy array before assignment.

        Returns
        -------
        callable
            Callback that updates the trait from edited table data.

        """
        if isinstance(self.traittype, List):

            def callback(attr, old, new):
                del attr, old
                current_value = getattr(self.obj, self.traitname)
                new_value = next(iter(new.values()))
                if current_value != new_value:
                    setattr(self.obj, self.traitname, new_value)
        elif isinstance(self.traittype, Tuple):

            def callback(attr, old, new):
                del attr, old
                current_value = getattr(self.obj, self.traitname)
                new_value = tuple(next(iter(new.values())))
                if current_value != new_value:
                    setattr(self.obj, self.traitname, new_value)
        else:  # array type

            def callback(attr, old, new):
                del attr, old
                # new variable is of type dict! get dict values:
                # get all values for given Table Column field names (keys)
                fieldnames = [col.field for col in self.widget.columns]
                column_values = [new.get(fn) for fn in fieldnames]
                new_traitvalue = self._cds_to_numpy_array_transform(column_values, self.transposed)
                self._set_traitvalue(new_traitvalue)

        return callback

    def _cds_to_numpy_array_transform(self, column_values, transposed):
        """Map DataTable column values to a NumPy array.

        The resulting array is used as the new value of the trait mapped to
        this DataTable widget. When Bokeh renderers modify the data source,
        columns may become plain Python lists, so conversion back to NumPy may
        be required.

        Parameters
        ----------
        column_values : array or list
            Column values of the ``ColumnDataSource``.
        transposed : bool
            If ``True``, map columns of the ``ColumnDataSource`` to rows.

        Returns
        -------
        array
            New trait value based on the column values.
        """
        if type(column_values) is list:  # cast to array if is list type
            column_values = np.array(column_values)
        if column_values[0].ndim == 1 and len(column_values) == 1:  # mapps to arrays with -> (n,) shapes
            new_traitvalue = column_values[0]
        else:  # mapps to arrays with -> (n,number_of_columns) shapes
            if column_values[0].ndim == 1:
                new_traitvalue = np.stack(column_values, axis=1).squeeze()
            else:
                new_traitvalue = np.concatenate(column_values, axis=1)
            if transposed:
                new_traitvalue = new_traitvalue.T
        return new_traitvalue

    def _set_traitvalue(self, widgetvalue):
        """Set the value of a class trait attribute from the widget value.

        Parameters
        ----------
        widgetvalue : array
            Data from ``ColumnDataSource`` as a NumPy array.

        Returns
        -------
        None.

        """
        current_value = getattr(self.obj, self.traitname)
        if not np.array_equal(widgetvalue, current_value):
            setattr(self.obj, self.traitname, widgetvalue)


class MultiSelectMapper(TraitWidgetMapper):
    """Create and synchronize a Bokeh :class:`MultiSelect` widget."""

    def __init__(self, obj, traitname):
        self.obj = obj
        self.traitname = traitname
        self.traittype = obj.trait(traitname).trait_type
        self.item_dtype = obj.trait(traitname).trait_type.item_trait.trait_type.fast_validate[1]
        self.traitdescription = obj.trait(traitname).desc
        try:
            self.traitvalue = getattr(obj, traitname)
        except AttributeError:  # in case of Delegate
            self.traitvalue = None

    def create_widget(self, **kwargs):
        """
        Create a Bokeh MultiSelect instance.

        Parameters
        ----------
        **kwargs : args of MultiSelect
            additional arguments of MultiSelect widget.

        Returns
        -------
        instance(MultiSelect).

        """
        kwargs.setdefault('title', self.traitname)
        self.widget = MultiSelect(**kwargs)
        self._set_widgetvalue(self.traitvalue)
        self._set_callbacks()
        return self.widget

    def set_widget(self, widget):
        """
        Connect a Bokeh MultiSelect widget instance to a class trait attribute.

        Parameters
        ----------
        widget : instance(MultiSelect)
            instance of a MultiSelect widget.

        Returns
        -------
        None.

        """
        self.widget = widget
        self._set_traitvalue(self.widget.value)  # set traitvalue to widgetvalue
        self._set_callbacks()

    def create_trait_setter_func(self):
        """Create a callback that writes ``MultiSelect`` values to the trait.

        The callback is invoked every time the widget value changes. No casting
        is needed at this stage because conversion happens in
        :meth:`_set_traitvalue`.

        Returns
        -------
        callable
            Callback that updates the trait from the widget.

        """

        def callback(attr, old, new):
            del attr, old
            self._set_traitvalue(new)

        return callback

    def _set_widgetvalue(self, traitvalue, widgetproperty='value'):
        """Set the widget value from the mapped trait attribute.

        The values are converted to strings because ``MultiSelect`` stores its
        selected entries as a list of strings.

        Parameters
        ----------
        traitvalue : depends on trait attribute type
            Value of the class trait attribute.

        Returns
        -------
        None.

        """
        if hasattr(self.widget, 'description'):
            self.widget.description = self.traitdescription
        setattr(self.widget, widgetproperty, [str(v) for v in traitvalue])

    def _set_traitvalue(self, widgetvalue):
        """Set the value of a class trait attribute from the widget value.

        The string values returned by ``MultiSelect`` are converted back to the
        configured item type before assignment.

        Parameters
        ----------
        widgetvalue : str
            Value of the widget.

        Returns
        -------
        None.

        """
        #        print("set traitvalue for trait {}".format(self.traitname))
        setattr(self.obj, self.traitname, [self.item_dtype(v) for v in widgetvalue])
