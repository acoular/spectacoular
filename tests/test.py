#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
from traits.api import HasPrivateTraits, Str, CArray, Range, Int, Float,\
File, Property, Trait, List, ListStr, ListInt, ListFloat, \
Bool,Tuple, Any
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TextInput, Slider,DataTable, Select,TableColumn
from spectacoular import get_widgets, set_widgets
from numpy import array, float64

#TODO: see below:
# List mapping to ColumnDataSource/DataTable/...
# TraitMapping Test
# Delegate Mapping Test
# Enum Mapping Test
# trait description implementation
# BeamformerTime/Sequence Example
# three sources gui example
# 2. trait notification handling for CArrays


class Test(HasPrivateTraits):
    
    get_widgets = get_widgets

    set_widgets = set_widgets

columns = [TableColumn(field='x', title='x'),
           TableColumn(field='y', title='y'),
           TableColumn(field='z', title='z')]

class CArrayWidgetMapping(Test):
    
    testIntCArray = CArray( dtype=int )
    
    testIntCArray2 = CArray(dtype=int )
    
    testFloatCArray = CArray(dtype=int, shape=(3,3))
    
    trait_widget_mapper = {
                'testIntCArray': TextInput,
                'testIntCArray2': DataTable,
                'testFloatCArray': DataTable,
                }
    
    trait_widget_args = {
                'testIntCArray' : {'disabled':False},
                'testIntCArray2' : {'editable':True},
                'testFloatCArray' : {'editable':True,'columns':columns}, #TODO: when editable=True -> on change callback of CDS does not trigger
                }

    def _test_textinput(self,widget):
        widget.value = "1,2,3"
        assert all(self.testIntCArray == array([1,2,3]))
        self.testIntCArray = array([10.0,2.1,3.2])
        assert widget.value == '10, 2, 3'
##    mappingTest.testCArrayInt[0] = 100 # does not trigger the on changed handler of traits package!
##    assert widgetUnderTest.value == '100, 2, 3'

    def _test_datatable(self,widget):
        # One Dimensional Datatable
        self.testIntCArray2 = array([11.0,2.1,3.2])
        assert all(widget.source.data['testIntCArray2'] == array([11,2,3]))
        widget.source.data['testIntCArray2'] = array([100,2,3])
        assert not False in self.testIntCArray2.T == array([100,2,3])
#        print(self.testIntCArray2)
#
    def _test_multidim_datatable(self,widget):
        # Two Dimensional Datatable 
        testArray = array([[1,2,3],[1,2,3],[1,2,3]],dtype=float64)
        self.testFloatCArray = testArray
        assert all(widget.source.data['x'] == testArray[:,0])
        # change table
        widget.source.data['x'] = [4.0,4.0,4.0] # if only one value is changed -> callback is not triggered
        assert all(self.testFloatCArray[:,0] == array([4.0,4.0,4.0]))


    def _test_set_widgets(self,widgets):
        # test DataTable
        cds = ColumnDataSource(data={'testIntCArray2':[4]})
        dt = DataTable(source=cds,columns=[TableColumn(field='testIntCArray2', title='testIntCArray2')])
        self.set_widgets(**{'testIntCArray2':dt})
    
    def test( self ):
        widgets = self.get_widgets()
        self._test_textinput(widgets['testIntCArray'])
        # self._test_datatable(widgets['testIntCArray2'])
        self._test_multidim_datatable(widgets['testFloatCArray'])
        self._test_set_widgets(widgets)



testOptions = ['test','test1','test2']
class StrWidgetMapping(Test):
    
    testTrait = Str('test')
    
    testTraitSelect = Str('test')
    
    testTraitSelectWithOptions = Str('test')

    trait_widget_mapper = {
                'testTrait': TextInput,
                'testTraitSelect': Select,
                'testTraitSelectWithOptions': Select,
                }
    
    trait_widget_args = {
                'testTrait' : {'disabled':False},
                'testTraitSelect' : {'disabled':False},
                'testTraitSelectWithOptions' : {'options':testOptions},
                }    

    def _textinput_test(self, widgets):
        widget = widgets['testTrait']
        # assign value to widget
        widget.value = 'newtest'
        # prove correct change of trait value
        assert self.testTrait == 'newtest' 
        # assign value to trait
        self.testTrait = 'test'
        # prove correct change of widget value
        assert widget.value == 'test'
        
    def _select_test(self, widgets):
        assert widgets['testTraitSelect'].options == ['test']    
        assert widgets['testTraitSelectWithOptions'].options == testOptions   
        # assign value to widget
        widgets['testTraitSelectWithOptions'].value = 'test1'
        assert self.testTraitSelectWithOptions == 'test1'

    def test( self ):
        widgets = self.get_widgets()
        self._textinput_test(widgets)
        self._select_test(widgets)


class IntWidgetMapping(Test):
    
    testTrait = Int(1)
    
    trait_widget_mapper = {
                'testTrait': TextInput,

                }
    
    trait_widget_args = {
                'testTrait' : {'disabled':False},
                }    

    test_widget_values = {'10':10,'10.0':10}
    
    def test( self ):
        widgets = self.get_widgets()
        for value in list(self.test_widget_values.keys()):
            for i,widget in enumerate(widgets.values()):
                # assign value to widget
                widget.value = value
            assert self.testTrait == 10
        # assign value to trait
        self.testTrait = 1
        # prove correct change of widget value
        for widget in widgets.values():
            assert widget.value == '1'

    def test_set_widgets( self ):
        # test TextInput
        ti = TextInput(value='10')
        self.set_widgets(**{'testTrait':ti})
        assert self.testTrait == 10
        self.testTrait = 1
        assert ti.value == '1'
        # test Select
        sl = Select(value='2',options=['1','2','3','4'])
        self.set_widgets(**{'testTrait':sl})
        assert self.testTrait == 2
        assert ti.value == '2'
        self.testTrait = 4
        assert sl.value == '4'
        # test Slider
        sr = Slider(value=3, start=1, end=4)
        self.set_widgets(**{'testTrait':sr})
        assert self.testTrait == 3
        assert ti.value == '3' and sl.value == '3'



class FloatWidgetMapping(Test):
    
    testTrait = Float(1.0)
    
    trait_widget_mapper = {
                'testTrait': TextInput,
                }
    
    trait_widget_args = {
                'testTrait' : {'disabled':False},
                }    

    test_widget_values = ['10','10.0']
    
    def test( self ):
        widgets = self.get_widgets()
        widget = widgets['testTrait']
        assert widget.value == '1.0'
        for value in self.test_widget_values:
            # assign value to widget
            widget.value = value
            # prove correct change of trait value
            assert self.testTrait == 10.0
        # assign value to trait
        self.testTrait = 1.0
        # prove correct change of widget value
        assert widget.value == '1.0'


class BoolWidgetMapping(Test):
    
    testTrait1 = Bool(False)
    
    testTrait2 = Bool(False)

    
    trait_widget_mapper = {
                'testTrait1': TextInput,
                'testTrait2': Select,
                }
    
    trait_widget_args = {
                'testTrait1' : {'disabled':False},
                'testTrait2' : {'disabled':False},
                }    

    def test( self ):
        widgets = self.get_widgets()
        assert widgets['testTrait1'].value == 'False'
        assert widgets['testTrait2'].value == 'False'
        widgets['testTrait1'].value = 'True'
        widgets['testTrait2'].value = 'True'
        assert self.testTrait1 == True
        assert self.testTrait2 == True
        self.testTrait1 = False
        self.testTrait2 = False
        assert widgets['testTrait1'].value == 'False'
        assert widgets['testTrait2'].value == 'False'


class FileWidgetMapping(Test):
    
    testTrait = File(filter=['*.xml'])
    
    trait_widget_mapper = {
                'testTrait': TextInput,
                }
    
    trait_widget_args = {
                'testTrait' : {'disabled':False},
                } 

    def test( self ):
        widgets = self.get_widgets()
        widget = widgets['testTrait']
        widget.value = 'test.xml'
        assert self.testTrait == 'test.xml'

class RangeWidgetMapping(Test):
    """
    from traits.api doc of Range:
        
        Default Value
        -------------
        *value*; if *value* is None or omitted, the default value is *low*,
        unless *low* is None or omitted, in which case the default value is
        *high*.
    """
    # low,high,value    
    testTrait = Range(0.01, 1.0, 0.6)
    
    testTrait1 = Range(0.01, 1.0, None)

    testTrait2 = Range(0, 10, 5)


# TODO: Range to TextInput Mapping. Currently raises error     
#    testTrait2 = Range(0.01, 1.0, 0.6)  
    
    trait_widget_mapper = {
                'testTrait' : Slider,
                'testTrait1' : Slider,
                'testTrait2' : Slider
                }
    
    trait_widget_args = {
                'testTrait' : {'disabled':False, 'step':0.01},
                'testTrait1' : {'disabled':False},
                'testTrait2' : {'disabled':False},
                }
    
    def test( self ):
        widgets = self.get_widgets()
        # test Slider Mapping 
        widget = widgets['testTrait']
        widget1 = widgets['testTrait1']
        widget2 = widgets['testTrait2']
        assert (widget.start, widget.end, widget.value) == (0.01, 1.0, 0.6)
        assert (widget1.start, widget1.end, widget1.value) == (0.01, 1.0, 0.01)
        assert (widget2.start, widget2.end, widget2.value) == (0, 10, 5)
        # assign value to widget
        widget.value = 1.0
        widget1.value = 1.0 
        widget2.value = 1 
        # prove correct change of trait value
        assert self.testTrait == 1.0
        assert self.testTrait1 == 1.0
        assert self.testTrait2 == 1
        # assign value to trait
        self.testTrait = 0.6
        self.testTrait1 = 0.6
        self.testTrait2 = 6
        # prove widget value
        assert widget.value == 0.6
        assert widget1.value == 0.6
        assert widget2.value == 6
# test Textfield Mapping
# widget = widgets[1]    
# widget.value = 1.0


class TraitWidgetMapping(Test):
    
    testTraitStr = Trait('1','2','3','4','5') 

    testTraitInt = Trait(1,2,3,4,5) 

    testTraitFloat = Trait(1.,2.,3.,4.,5.) 
    
    #TODO: Test Mapping of Trait with mixed datatypes

    trait_widget_mapper = {
                'testTraitStr' : Select,
                'testTraitInt' : Select,
                'testTraitFloat' : Select,
                }
    
    trait_widget_args = {
                'testTraitStr' : {'disabled':False},
                'testTraitInt' : {'disabled':False},
                'testTraitFloat' : {'disabled':False},
                }
    
    def test( self ):
        widgets = self.get_widgets()
        # test Slider Mapping 
        widgetStr = widgets['testTraitStr']
        widgetInt = widgets['testTraitInt']
        widgetFloat = widgets['testTraitFloat']
        # assign value to widget
        widgetStr.value = '2'
        widgetInt.value = '2'
        widgetFloat.value = '2'
        # prove correct change of trait value
        assert self.testTraitStr == '2'
        assert self.testTraitInt == 2
        assert self.testTraitFloat == 2.
        # assign value to trait
        self.testTraitStr = '1'
        self.testTraitInt = 1
        self.testTraitFloat = 1.
        # prove widget value
        assert widgetStr.value == '1'  
        assert widgetInt.value == '1'  
        assert widgetFloat.value == '1.0'    
    

class ListWidgetMapping(Test):
    # TODO: Lists can be problematic: For traits of 
    # type List, multiple dtypes are valid inputs if the input trait is not
    # explicitly defined.
    
    testListStr = List(Str()) 
    testListStr2 = ListStr(['1','2']) 

    testListInt = List(Int()) 
    testListInt2 = ListInt([1,2,3,4,5]) 

    testListFloat = List(Float()) 
    testListFloat2 = ListFloat([1.,2.,3.,4.,5.]) 
    
    #testListTrait?
    #testListBool?
    
    #TODO: Test Mapping of List to manipulatable Datatable

    trait_widget_mapper = {
                'testListStr' : TextInput,
                'testListStr2' : TextInput,
                'testListInt' : TextInput,
                'testListInt2' : TextInput,
                'testListFloat' : TextInput,
                'testListFloat2' : TextInput,
                }
    
    trait_widget_args = {
                'testListStr' : {'disabled':False},
                'testListStr2' : {'disabled':False},
                'testListInt' : {'disabled':False},
                'testListInt2' : {'disabled':False},
                'testListFloat' : {'disabled':False},
                'testListFloat2' : {'disabled':False},
                }
    
    def _test_textinput(self,widgets):
        # assign value to widgets
        test_widget_value = ' 2, 4'
        for widget in widgets.values():
            widget.value = test_widget_value
#        # prove correct change of trait value
#        print(self.testListStr,type(self.testListStr),type(self.testListStr[0]))
        expectedListStr = ['2','4']
        expectedListInt = [2,4]
        expectedListFloat = [2.,4.]
        assert self.testListStr == expectedListStr
        assert self.testListStr2 == expectedListStr
        assert self.testListInt == expectedListInt
        assert self.testListInt2 == expectedListInt
        assert self.testListFloat == expectedListFloat
        assert self.testListFloat2 == expectedListFloat
#        # assign value to trait
        self.testListStr = ['1','2']
        self.testListStr2 = ['1','2']
        assert widgets['testListStr'].value == '1, 2'  
        assert widgets['testListStr2'].value == '1, 2'  
        self.testListInt = [1,2]
        self.testListInt2 = [1,2]
        assert widgets['testListInt'].value == '1, 2'  
        assert widgets['testListInt2'].value == '1, 2'  
        self.testListFloat = [1.,2.]
        self.testListFloat2 = [1.,2.]
        assert widgets['testListFloat'].value == '1.0, 2.0'  
        assert widgets['testListFloat2'].value == '1.0, 2.0'  

    def test( self ):
        widgets = self.get_widgets()
        self._test_textinput(widgets)
        
class TupleWidgetMapping(Test):
    
    testTuple = Tuple()

    trait_widget_mapper = {
                'testTuple' : TextInput,
                }
    
    trait_widget_args = {
                'testTuple' : {'disabled':False},
                }
    
    def _test_textinput(self,widgets):
        # assign value to widgets
        test_widget_value = '(2, "4")'
        for widget in widgets.values():
            widget.value = test_widget_value
        
#        # prove correct change of trait value
        assert self.testTuple == (2, "4")
#        # assign value to trait
        self.testTuple = (1,"2")
        assert widgets['testTuple'].value == "(1, '2')"  

    def test( self ):
        widgets = self.get_widgets()
        self._test_textinput(widgets) 
    
class PropertyWidgetMapping(Test):
    '''
    Property is special! In contrast to type Any it returns not an instance 
    (if the trait attribute of the Property function is not set)!
    
    Property: mapper.obj.trait('testTrait').trait_type
    Returns -> traits.trait_types.Any
    
    Any: mapper.obj.trait('_testTrait').trait_type
    Returns instance ->  <traits.trait_types.Any at 0x7f18f6c79208>
    
    Further -> on trait change handler works only on shadow traits, thus ->
    widget value is not set when trait value changes
    '''
    
    testTrait = Property(Any)
    #testTrait = Property() # does not work!
    
    _testTrait = Any(0.1)

    trait_widget_mapper = {
#                'testTrait' : TextInput,
                '_testTrait' : TextInput,
                }
    
    trait_widget_args = {
#                'testTrait' : {'disabled':False},
                '_testTrait' : {'disabled':False},
                }

    def _get_testTrait(self):
        return self._testTrait

    def _set_testTrait(self,testTraitValue):
        self._testTrait = testTraitValue
        
    def test( self ):
        widgets = self.get_widgets()
        assert widgets['_testTrait'].value == '0.1'
        # assign value to widget
        widgets['_testTrait'].value = '1.0'
        # prove correct change of trait value
        assert self.testTrait == 1.0
#        # assign value to trait
        self.testTrait = 0.1
#        # prove correct change of widget value
        assert widgets['_testTrait'].value == '0.1'
        

# =============================================================================
# Test explicit Mapping
# =============================================================================

# class DataTableMapping(Test):
    
#     testCArrayInt = CArray( dtype=int )
    
#     testListInt = ListInt()
    
    
#     trait_widget_mapper = {
#                 'testCArrayInt': DataTable,
#                 'testListInt': DataTable,
#                 }
    
#     trait_widget_args = {
#                 'testCArrayInt' : {'editable':True},
#                 'testListInt' : {'editable':True},
# #                'testFloatCArray' : {'editable':True,'columns':columns}, #TODO: when editable=True -> on change callback of CDS does not trigger
#                 }

        
        
if __name__ == '__main__':
    
    # String Trait Widget Mapping Test
    strTest = StrWidgetMapping()
    strTest.test()
    
    # Int Trait Widget Mapping Test
    intTest = IntWidgetMapping()
    intTest.test()
    intTest.test_set_widgets()
    
    # Float Trait Widget Mapping Test
    floatTest = FloatWidgetMapping()
    floatTest.test()
    
    # Bool Trait Widget Mapping Test
    boolTest = BoolWidgetMapping()
    boolTest.test()
    
    # File Trait Widget Mapping Test
    fileTest = FileWidgetMapping()
    fileTest.test()
    
    # Range Trait Widget Mapping Test
    rangeTest = RangeWidgetMapping()
    rangeTest.test()

#    # CArray Trait Widget Mapping test
    carrayTest = CArrayWidgetMapping()
    carrayTest.test()
    
    # Trait Widget Mapping Test
    traitTest = TraitWidgetMapping()
    traitTest.test()
    
    # List Widget Mapping Test
    listTest = ListWidgetMapping()
    listTest.test()
    
    # List Widget Mapping Test
    tupleTest = TupleWidgetMapping()
    tupleTest.test()
    
    propertyTest = PropertyWidgetMapping()
    propertyTest.test()
    # mapper = TraitWidgetMapper(propertyTest,'testTrait')
    # cast_func = traitdispatcher.get_trait_cast_func(mapper)

    # # DataTableMapping Test    
    # datatableTest = DataTableMapping()
    # widgets = datatableTest.get_widgets()
    # datatableTest.testListInt = [1,2,3,4]
    
    print("mapping tests successfull")
    
    
# =============================================================================
# Factory Tests
# =============================================================================
    
#    mapper = TraitWidgetMapper(carrayTest,'testIntCArray')
#    mapper2 = TraitWidgetMapper(propertyTest,'_testTrait')

#    from spectacoular import MicGeom
#    
#    mg = MicGeom()
#    mg.get_widgets()
    