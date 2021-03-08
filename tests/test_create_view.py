from traits.api import HasTraits, Int, Long, CLong, Float, Complex,\
    BaseBool,Bool,CBool
from bokeh.models.widgets import NumericInput, Toggle
import unittest
from spectacoular import BaseSpectacoular, get_widgets, set_widgets
from hypothesis.strategies import integers, floats, tuples,booleans
from hypothesis import given

class HasTraitsTestClass(HasTraits):
    """ class that is used for widget mapping tests that has
    no trait_widget_mapping dict, get_widgets and set_widgets
    method as class attribute """ 
    pass

class BaseSpectacoularTestClass(BaseSpectacoular):
    """ class that is used for widget mapping tests that has
    trait_widget_mapping dict, get_widgets and set_widgets
    method as class attribute """ 
    pass

class BaseMapperTest(unittest.TestCase):
    """Base class that verifies that mappings are 
    working correctly.
    """
    widget = object

    test_types = []

    mapper = {}

    mapper_args = {'test_trait': {'visible':False}}

    def get_has_traits_derived_class_instance(self,trait_type):
        """ returns a class instance that is HasTraits derived, but no
        BaseSpectacoular derived"""
        cls_instance = HasTraitsTestClass()
        cls_instance.add_trait('test_trait',trait_type())
        return cls_instance

    def get_spectacoular_derived_class_instance(self,trait_type):
        """ returns a class instance that is BaseSpectacoular derived"""
        cls_instance = BaseSpectacoularTestClass()
        cls_instance.add_trait('test_trait',trait_type())
        return cls_instance

    def get_widget_from_default_view_definition_spectacoular(self,trait_type):
        cls_instance = self.get_spectacoular_derived_class_instance(trait_type)
        cls_instance.trait_widget_mapper = self.mapper
        widget = cls_instance.get_widgets().get('test_trait')
        return widget

    def get_widget_from_custom_view_definition_spectacoular(self,trait_type):
        cls_instance = self.get_spectacoular_derived_class_instance(trait_type)
        widget = get_widgets(cls_instance,self.mapper,self.mapper_args).get('test_trait')
        return widget

    def get_widget_without_view_definition_has_traits(self,trait_type):
        cls_instance = self.get_has_traits_derived_class_instance(trait_type)
        widget = get_widgets(cls_instance).get('test_trait')
        return widget

    def get_widget_from_custom_view_definition_has_traits(self,trait_type):
        cls_instance = self.get_has_traits_derived_class_instance(trait_type)
        widget = get_widgets(cls_instance,self.mapper,self.mapper_args).get('test_trait')
        return widget

    def test_get_widgets_spectacoular(self):
        """tests that creating NumericInput widget from numeric trait types works
        for BaseSpectacoular derived classes """
        for trait_type in self.test_types:
            with self.subTest(trait_type):
                # with default mapper 
                widget = self.get_widget_from_default_view_definition_spectacoular(trait_type)
                self.assertIsInstance(widget,self.widget)
                # with custom mapper
                widget = self.get_widget_from_custom_view_definition_spectacoular(trait_type)
                self.assertIsInstance(widget,self.widget)
                self.assertEqual(widget.visible,False)

    def test_get_widgets_hastraits(self):
        """tests that creating NumericInput widget from numeric trait types works
        for HasTraits derived classes """
        for trait_type in self.test_types:
            with self.subTest(trait_type):
            #print(trait_type)
                # from editable traits 
                widget = self.get_widget_without_view_definition_has_traits(trait_type)
                self.assertIsInstance(widget,self.widget)
                # with custom mapper
                widget = self.get_widget_from_custom_view_definition_has_traits(trait_type)
                self.assertIsInstance(widget,self.widget)
                self.assertEqual(widget.visible,False)

    def set_widgets_spectacoular(self,value,widgetproperty="value"):
        """tests that set a widget via set_widget() method works correctly
        for spectacoular derived classes. """
        for trait_type in self.test_types:
            with self.subTest(trait_type):
            #print(trait_type)
                widget = self.widget()
                setattr(widget,widgetproperty,value)
                cls_instance = self.get_spectacoular_derived_class_instance(trait_type)
                cls_instance.set_widgets(test_trait=widget)
                self.assertEqual(cls_instance.test_trait,value)

    def set_widgets_hastraits(self,value,widgetproperty="value"):
        """tests that set a widget via set_widget() method works correctly
        for HasTraits derived classes. """
        for trait_type in self.test_types:
            with self.subTest(trait_type):
            #print(trait_type)
                widget = self.widget()
                setattr(widget,widgetproperty,value)
                cls_instance = self.get_has_traits_derived_class_instance(trait_type)
                set_widgets(cls_instance,test_trait=widget)
                self.assertEqual(cls_instance.test_trait,value)

    def test_set_widgets(self):
        self.set_widgets_spectacoular(value=10)
        self.set_widgets_hastraits(value=10)


class NumericInputTest(BaseMapperTest):
    """Verifies that mappings of trait types to NumericInputs are 
    working correctly.
    """

    widget = NumericInput

    # allowed numeric trait types that can be mapped to NumericInput widget
    test_types = [Int,Float,CLong,Long,] # Complex] # complex types are not supported at the moment (only mode int or float)

    int_types = [Int,CLong,Long]

    float_types = [Float]

    mapper = {'test_trait': NumericInput}

    @given(tuples(integers(),floats(allow_nan=False)))
    def test_trait_widget_callback(self,value_tuple):
        """test verifies that a widget value is changing when a new value
        is assigned to the referenced trait. 
        """
        #print(value_tuple)
        # test in types
        for trait_type in self.int_types:
            cls_instance = self.get_has_traits_derived_class_instance(trait_type)
            widget = get_widgets(cls_instance).get('test_trait')
            # set trait to value
            cls_instance.test_trait = value_tuple[0]
            self.assertEqual(widget.value,value_tuple[0])
        #test float types
        for trait_type in self.float_types:
            cls_instance = self.get_has_traits_derived_class_instance(trait_type)
            widget = get_widgets(cls_instance).get('test_trait')
            # set trait to value
            cls_instance.test_trait = value_tuple[1]
            self.assertEqual(widget.value,value_tuple[1])

    @given(tuples(integers(),floats(allow_nan=False)))
    def test_widget_trait_callback(self,value_tuple):
        """test verifies that a traits value is changing when a new value
        is assigned to the widget
        """
        #print(value)
        # test in types
        for trait_type in self.int_types:
            cls_instance = self.get_has_traits_derived_class_instance(trait_type)
            widget = get_widgets(cls_instance).get('test_trait')
            # set widget to value
            widget.value = value_tuple[0]
            self.assertEqual(cls_instance.test_trait,value_tuple[0])
        # test float types
        for trait_type in self.float_types:
            cls_instance = self.get_has_traits_derived_class_instance(trait_type)
            widget = get_widgets(cls_instance).get('test_trait')
            # set widget to value
            widget.value = value_tuple[1]
            self.assertEqual(cls_instance.test_trait,value_tuple[1])

class ToggleTest(BaseMapperTest):
    """Verifies that mappings of trait types to NumericInputs are 
    working correctly.
    """
    widget = Toggle

    # allowed numeric trait types that can be mapped to NumericInput widget
    test_types = [Bool] # Complex] # complex types are not supported at the moment (only mode int or float)

    mapper = {'test_trait': Toggle}

    def test_set_widgets(self):
        self.set_widgets_spectacoular(value=True,widgetproperty="active")
        self.set_widgets_hastraits(value=True,widgetproperty="active")

    def test_trait_widget_callback(self,value=False):
        """test verifies that a widget value is changing when a new value
        is assigned to the referenced trait. 
        """
        #print(value_tuple)
        # test in types
        for trait_type in self.test_types:
            cls_instance = self.get_has_traits_derived_class_instance(trait_type)
            widget = get_widgets(cls_instance).get('test_trait')
            # set trait to value
            cls_instance.test_trait = value
            self.assertEqual(widget.active,value)

    def test_widget_trait_callback(self,value=False):
        """test verifies that a traits value is changing when a new value
        is assigned to the widget
        """
        # test in types
        for trait_type in self.test_types:
            cls_instance = self.get_has_traits_derived_class_instance(trait_type)
            widget = get_widgets(cls_instance).get('test_trait')
            # set widget to value
            widget.active = value
            self.assertEqual(cls_instance.test_trait,value)

    

if __name__ == '__main__':

    unittest.main()
