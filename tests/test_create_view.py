from traits.api import HasTraits, Int, Long, CLong, Float, Complex,\
    BaseBool,Bool,CBool, Enum, Trait, Map, Range, CTrait
from bokeh.models.widgets import NumericInput, Toggle, Select, Slider, TextInput
import unittest
from spectacoular import BaseSpectacoular, get_widgets, set_widgets
from spectacoular.factory import DEFAULT_TRAIT_WIDGET_MAPPINGS
from hypothesis.strategies import integers, floats, tuples,booleans, lists
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

    test_traits = []

    mapper = {}

    mapper_args = {'test_trait': {'visible':False}}

    def get_has_traits_derived_class_instance(self,trait):
        """ returns a class instance that is HasTraits derived, but no
        BaseSpectacoular derived"""
        cls_instance = HasTraitsTestClass()
        cls_instance.add_trait('test_trait',trait)
        return cls_instance

    def get_spectacoular_derived_class_instance(self,trait):
        """ returns a class instance that is BaseSpectacoular derived"""
        cls_instance = BaseSpectacoularTestClass()
        cls_instance.add_trait('test_trait',trait)
        return cls_instance

    def get_widget_from_default_view_definition_spectacoular(self,trait):
        cls_instance = self.get_spectacoular_derived_class_instance(trait)
        cls_instance.trait_widget_mapper = self.mapper
        cls_instance.trait_widget_args = self.mapper_args
        widget = cls_instance.get_widgets().get('test_trait')
        return widget

    def get_widget_from_custom_view_definition_spectacoular(self,trait):
        cls_instance = self.get_spectacoular_derived_class_instance(trait)
        widget = get_widgets(cls_instance,self.mapper,self.mapper_args).get('test_trait')
        return widget

    def get_widget_without_view_definition_has_traits(self,trait):
        cls_instance = self.get_has_traits_derived_class_instance(trait)
        widget = get_widgets(cls_instance).get('test_trait')
        return widget

    def get_widget_from_custom_view_definition_has_traits(self,trait):
        cls_instance = self.get_has_traits_derived_class_instance(trait)
        widget = get_widgets(cls_instance,self.mapper,self.mapper_args).get('test_trait')
        return widget

    def test_get_widgets_spectacoular_default_view(self):
        """tests that creating widget from trait types works
        for BaseSpectacoular derived classes with the default view 
        (specified via trait_widget_mapper)"""
        for test_trait in self.test_traits:
            with self.subTest(type(test_trait)):
                widget = self.get_widget_from_default_view_definition_spectacoular(test_trait)
                self.assertIsInstance(widget,self.widget)
                self.assertEqual(widget.visible,False)

    def test_get_widgets_spectacoular_custom_view(self):
        """tests that creating widget from trait types works
        for BaseSpectacoular derived classes with custom view 
        (specified via trait_widget_mapper in get_widgets function)"""
        for test_trait in self.test_traits:
            with self.subTest(type(test_trait)):
                widget = self.get_widget_from_custom_view_definition_spectacoular(test_trait)
                self.assertIsInstance(widget,self.widget)
                self.assertEqual(widget.visible,False)

    def test_get_widgets_hastraits_without_view(self):
        """tests that creating widget from trait types works
        for HasTraits derived classes without any pre-defined view 
        
        This test is designed to assure the following behavior:
        If no view is defined, the type of the created widget should
        match the type of the widget specified in DEFAULT_TRAIT_WIDGET_MAPPINGS.
        Since no widget arguments are given, the widget should also be visible (standard behavior).
        """
        for test_trait in self.test_traits:
            with self.subTest(type(test_trait)):
                widget = self.get_widget_without_view_definition_has_traits(test_trait)
                traittype = type(test_trait)
                if traittype == CTrait:
                    traittype = test_trait.trait_type.__class__
                default_widget_type = DEFAULT_TRAIT_WIDGET_MAPPINGS.get(traittype)
                if default_widget_type:
                    self.assertIsInstance(widget,default_widget_type)
                else:
                    self.assertIsInstance(widget,TextInput)
                self.assertEqual(widget.visible,True)

    def test_get_widgets_hastraits_custom_view(self):
        """tests that creating widget from trait types works
        for HasTraits derived classes with pre-defined view """
        for test_trait in self.test_traits:
            with self.subTest(type(test_trait)):
                widget = self.get_widget_from_custom_view_definition_has_traits(test_trait)
                self.assertIsInstance(widget,self.widget)
                self.assertEqual(widget.visible,False)

    def set_widgets_spectacoular(self,widget,test_trait,widget_property):
        """tests that set a widget via set_widget() method works correctly
        for spectacoular derived classes. """
        cls_instance = self.get_spectacoular_derived_class_instance(test_trait)
        cls_instance.set_widgets(test_trait=widget)
        return cls_instance

    def set_widgets_hastraits(self,widget,test_trait,widget_property):
        """tests that set a widget via set_widget() method works correctly
        for HasTraits derived classes. """
        cls_instance = self.get_has_traits_derived_class_instance(test_trait)
        set_widgets(cls_instance,test_trait=widget)
        return cls_instance
                
    def test_set_widgets(self):
        """ test different ways to call set_widgets method for different trait types
        """
        expected_value = 10
        for set_widgets_method in [self.set_widgets_hastraits,self.set_widgets_spectacoular]:
            for test_trait in self.test_traits:
                with self.subTest(set_widgets_method.__name__+"_"+str(test_trait.__class__)):      
                    widget = self.widget(value=expected_value)
                    cls_instance = set_widgets_method(widget,test_trait,widget_property="value")
                    self.assertEqual(cls_instance.test_trait,expected_value)


class NumericInputTest(BaseMapperTest):
    """Verifies that mappings of trait types to NumericInputs are 
    working correctly.
    """

    widget = NumericInput

    # allowed numeric trait types that can be mapped to NumericInput widget
    test_traits = [Int(),Float(),CLong(),Long(),] # Complex] # complex types are not supported at the moment (only mode int or float)

    int_types = [Int(),CLong(),Long()]

    float_types = [Float()]

    mapper = {'test_trait': NumericInput}

    @given(tuples(integers(),floats(allow_nan=False)))
    def test_trait_widget_callback(self,value_tuple):
        """test verifies that a widget value is changing when a new value
        is assigned to the referenced trait. 
        """
        #print(value_tuple)
        # test in types
        for test_trait in self.int_types:
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
            widget = get_widgets(cls_instance).get('test_trait')
            # set trait to value
            cls_instance.test_trait = value_tuple[0]
            self.assertEqual(widget.value,value_tuple[0])
        #test float types
        for test_trait in self.float_types:
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
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
        for test_trait in self.int_types:
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
            widget = get_widgets(cls_instance).get('test_trait')
            # set widget to value
            widget.value = value_tuple[0]
            self.assertEqual(cls_instance.test_trait,value_tuple[0])
        # test float types
        for test_trait in self.float_types:
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
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
    test_traits = [Bool()] # Complex] # complex types are not supported at the moment (only mode int or float)

    mapper = {'test_trait': Toggle}

    def test_set_widgets(self):
        """ test different ways to call set_widgets method for different trait types
        """
        expected_value = False
        for set_widgets_method in [self.set_widgets_hastraits,self.set_widgets_spectacoular]:
            for test_trait in self.test_traits:
                with self.subTest(set_widgets_method.__name__+"_"+str(test_trait.__class__)):      
                    widget = self.widget(active=expected_value)
                    cls_instance = set_widgets_method(widget,test_trait,widget_property="active")
                    self.assertEqual(cls_instance.test_trait,expected_value)

    def test_trait_widget_callback(self,value=False):
        """test verifies that a widget value is changing when a new value
        is assigned to the referenced trait. 
        """
        #print(value_tuple)
        # test in types
        for test_trait in self.test_traits:
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
            widget = get_widgets(cls_instance).get('test_trait')
            # set trait to value
            cls_instance.test_trait = value
            self.assertEqual(widget.active,value)

    def test_widget_trait_callback(self,value=False):
        """test verifies that a traits value is changing when a new value
        is assigned to the widget
        """
        # test in types
        for test_trait in self.test_traits:
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
            widget = get_widgets(cls_instance).get('test_trait')
            # set widget to value
            widget.active = value
            self.assertEqual(cls_instance.test_trait,value)


class SelectTest(BaseMapperTest):
    """Verifies that mappings of trait types to Select widget are 
    working correctly.
    """
    widget = Select

    test_traits = [Enum('1','2','3'),Trait('1','2','3'),Enum(1,2,3),Trait(1,2,3),Enum(1.,2.,3.),Trait(1.,2.,3.),
                    Map({'1':'1','2':'2','3':'3'}), Trait('1',{'1':'1','2':'2','3':'3'})] 

    mapper = {'test_trait': Select}

    def test_set_widgets(self):
        # test Enum and Trait
        _expected_trait_values_after_set_widgets = ['2','2',2 ,2 ,2.,2.,'2','2']
        for set_widgets_method in [self.set_widgets_hastraits,self.set_widgets_spectacoular]:
            for expected_trait_value, test_trait in zip(_expected_trait_values_after_set_widgets, self.test_traits):
                with self.subTest(set_widgets_method.__name__+"_"+str(test_trait.__class__)):      
                    widget = self.widget(value='2',options=['1','2','3'])
                    cls_instance = set_widgets_method(widget,test_trait,"value")
                    self.assertEqual(cls_instance.test_trait,expected_trait_value)

    @given(lists(floats(allow_nan=False,allow_infinity=False),min_size=2,max_size=3))
    def test_trait_widget_callback(self,options):
        """test verifies that a widget value is changing when a new value
        is assigned to the referenced trait. 
        """
        for test_trait in [Enum(*options),Trait(*options), Map({i:i for i in options}),Trait(options[0],{i:i for i in options})]: 
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
            widget = get_widgets(cls_instance).get('test_trait')
            cls_instance.test_trait = options[-1]
            self.assertEqual(widget.value,str(options[-1]))

    @given(lists(integers(),min_size=2,max_size=3))
    def test_widget_trait_callback(self,options):
        """test verifies that a traits value is changing when a new value
        is assigned to the widget
        """
        for test_trait in [Enum(*options),Trait(*options), Map({i:i for i in options}),Trait(options[0],{i:i for i in options})]: 
            cls_instance = self.get_has_traits_derived_class_instance(test_trait)
            widget = get_widgets(cls_instance).get('test_trait')
            widget.value=str(options[-1])
            self.assertEqual(cls_instance.test_trait,options[-1])


class SliderTest(NumericInputTest):
    """Verifies that mappings of trait type Range to Slider widget are 
    working correctly.
    """
    widget = Slider

    test_traits = [Range(0.01, 20.0, .6), Float(1.)] 

    mapper = {'test_trait': Slider}

    mapper_args = {'test_trait': {'start':0.01, 'end':20., 'visible':False}}




if __name__ == '__main__':

    unittest.main()
