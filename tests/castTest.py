# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
from numpy import array
from spectacoular.cast import * 

if __name__ == '__main__':
    
    floatTest = 1.
    intTest = 1
    trueBoolTest = True
    strTest = '1'
    strtrueBoolTest = 'True'
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
    dictTest = {'a': [1,1,1], 'b': [2,2,2], 'c':[3,3,3]}
    
    # cast to float tests
    assert cast_to_float(floatTest) == 1.0
    assert cast_to_float(trueBoolTest) == 1.0
    assert cast_to_float(strTest) == 1.0
    assert cast_to_float(strFloatTest) == 1.0
    assert cast_to_float(strtrueBoolTest) == 1.0    
    
    # cast to int tests
    assert cast_to_int(floatTest) == 1
    assert cast_to_int(trueBoolTest) == 1
    assert cast_to_int(strTest) == 1
    assert cast_to_int(strFloatTest) == 1
    assert cast_to_int(strtrueBoolTest) == 1

    # cast to bool tests
    expected_bool = {1 : True, 
                     0 : False,
                     True : True,
                     False : False,
                     'True' : True,
                     'False' : False,
                     }
    for k,v in expected_bool.items():
        assert cast_to_bool(k) == v

    # cast to str tests
    assert cast_to_str(floatTest) == '1.0'
    assert cast_to_str(intTest) == '1'
    assert cast_to_str(trueBoolTest) == 'True'
    assert cast_to_str(strtrueBoolTest) == 'True'
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
    assert cast_to_list(trueBoolTest) == [True]
    assert cast_to_list(strTest) == ['1']
    assert cast_to_list(strtrueBoolTest) == ['True']
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

    # cast to array tests    
    assert not False in (cast_to_array(dictTest) == array([[1, 2, 3],
                                            [1, 2, 3],
                                            [1, 2, 3]]))
    
    