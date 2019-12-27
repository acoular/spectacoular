# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------

from functools import singledispatch
from traits.api import CTrait, TraitEnum, TraitMap, CArray, Dict, Any, \
List,Float, Str, Int, Enum, Range, TraitListObject, Bool, Tuple, Long,\
CLong, HasPrivateTraits, TraitCoerceType, File, BaseRange
from numpy import array, ndarray


#%% cast to int type
        
@singledispatch
def cast_to_int(value):
    return int(value)    

@cast_to_int.register(str)
def _(str_):
    return int(float(eval(str_)))
    
    
#%% cast to float type
        
@singledispatch
def cast_to_float(value):
    return float(value)

@cast_to_float.register(str)
def _(str_):
    return float(eval(str_))

#%% cast to bool
    
@singledispatch
def cast_to_bool(value):
    return bool(value)

@cast_to_bool.register(float)
def _(float_):
    return bool(int(float_))


#%% cast to str type

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

def cast_list_to_str(list_): 
    if all(isinstance(element,str) for element in list_):
        return ', '.join(list_)
    else:
        return str(list_).strip('[]')

#%% cast to list
       
@singledispatch        
def cast_to_list(value):
    return list(value)

@cast_to_list.register(bool)
@cast_to_list.register(int)
@cast_to_list.register(float)
def _(value_):
    return list([value_])

@cast_to_list.register(str)
def _(str_):
    varlist = list(str_.replace(" ","").split(",")) 
    if [] in varlist: varlist.remove([])
    if '' in varlist: varlist.remove('')
    return varlist 


#%% short test
    
if __name__ == '__main__':
    
    floatTest = 1.
    intTest = 1
    boolTest = True
    strTest = '1'
    strBoolTest = 'True'
    strFloatTest = '1.0'
    intList = [1,2,3,4]
    floatList = [1.,2.,3.,4.]
    boolList = [True,False]
    strList = ['1','2','3','4']
    listStr = '1 , 2,3,4'
    intTuple = (1,2,3,4)
    floatTuple = (1.,2.,3.,4.)
    anyTuple = (1,'2',3.0,True)
    intArray = array(intList)
    floatArray = array(floatList)
    boolArray = array(boolList)
    
    
    # cast to float tests
    assert cast_to_float(floatTest) == 1.0
    assert cast_to_float(boolTest) == 1.0
    assert cast_to_float(strTest) == 1.0
    assert cast_to_float(strFloatTest) == 1.0
    assert cast_to_float(strBoolTest) == 1.0    
    
    # cast to int tests
    assert cast_to_int(floatTest) == 1
    assert cast_to_int(boolTest) == 1
    assert cast_to_int(strTest) == 1
    assert cast_to_int(strFloatTest) == 1
    assert cast_to_int(strBoolTest) == 1

    # cast to bool tests
    assert cast_to_bool(floatTest) == True
    assert cast_to_bool(intTest) == True
    assert cast_to_bool(strTest) == True
    assert cast_to_bool(strFloatTest) == True
    assert cast_to_bool(strBoolTest) == True

    # cast to str tests
    assert cast_to_str(floatTest) == '1.0'
    assert cast_to_str(intTest) == '1'
    assert cast_to_str(boolTest) == 'True'
    assert cast_to_str(strBoolTest) == 'True'
    assert cast_to_str(intList) == '1, 2, 3, 4'
    assert cast_to_str(floatList) == '1.0, 2.0, 3.0, 4.0'
    assert cast_to_str(boolList) == 'True, False'
    assert cast_to_str(strList) == '1, 2, 3, 4'
    assert cast_to_str(intArray) == '1, 2, 3, 4'
    assert cast_to_str(floatArray) == '1.0, 2.0, 3.0, 4.0'
    assert cast_to_str(boolArray) == 'True, False'
    assert cast_to_str(intTuple) == '(1, 2, 3, 4)'
    assert cast_to_str(floatTuple) == '(1.0, 2.0, 3.0, 4.0)'
    assert cast_to_str(anyTuple) == "(1, '2', 3.0, True)"
  
    # cast to list tests
    assert cast_to_list(floatTest) == [1.0]
    assert cast_to_list(intTest) == [1]
    assert cast_to_list(boolTest) == [True]
    assert cast_to_list(strTest) == ['1']
    assert cast_to_list(strBoolTest) == ['True']
    assert cast_to_list(strFloatTest) == ['1.0']
    assert cast_to_list(intList) == intList
    assert cast_to_list(floatList) == floatList
    assert cast_to_list(boolList) == boolList
    assert cast_to_list(strList) == strList
    assert cast_to_list(intTuple) == [1,2,3,4]
    assert cast_to_list(floatTuple) == [1.,2.,3.,4.]
    assert cast_to_list(anyTuple) == [1,'2',3.0,True]
    assert cast_to_list(intArray) == [1,2,3,4]
    assert cast_to_list(floatArray) == [1.,2.,3.,4.]
    assert cast_to_list(boolArray) == [True,False]
    assert cast_to_list(listStr) == ['1', '2', '3', '4']

    
    
    
    
