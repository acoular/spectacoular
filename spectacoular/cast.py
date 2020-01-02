# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------

from traits.api import CArray,  TraitListObject
from numpy import array, ndarray
from functools import singledispatch, update_wrapper
try:
    from funtools import singledispatchmethod # only for python >= 3.8
except:
    def singledispatchmethod(func):
        dispatcher = singledispatch(func)
        def wrapper(*args, **kw):
            return dispatcher.dispatch(args[1].__class__)(*args, **kw)
        wrapper.register = dispatcher.register
        update_wrapper(wrapper, func)
        return wrapper

#%% cast to int type
        
@singledispatch
def cast_to_int(value):
    return int(value)    

@cast_to_int.register(str)
def _(str_):
    if str_:
        return int(float(eval(str_)))
    else:
        return 0
    
#%% cast to float type
        
@singledispatch
def cast_to_float(value):
    return float(value)

@cast_to_float.register(str) # necessary for bool strings like 'True'
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
    if len(ndarray_.squeeze().shape) == 1:
        return cast_list_to_str(list(ndarray_.flatten()))
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

#%% cast to numpy array

# TODO: need to be tested further!
@singledispatch        
def cast_to_array(value):
#    print("cast from value")
    return array(value)

@cast_to_array.register(dict)
def _(dict_):
#    print("cast from dict")
    return array(list(dict_.values())).T
 
@cast_to_array.register(str)
def _(str_):
#    print("cast from string")
    varlist = list(str_.replace(" ","").split(",")) 
    if [] in varlist: varlist.remove([])
    if '' in varlist: varlist.remove('')
    return array(varlist) 
