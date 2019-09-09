#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 19:30:03 2019

@author: kujawski
"""

from functools import singledispatch
from traits.api import List, HasTraits

@singledispatch
def fprint(data):
    print(f'({type(data).__name__}) {data}')


@fprint.register(list)
@fprint.register(set)
@fprint.register(tuple)
def abc_(data):
    formatted_header = f'{type(data).__name__} -> index : value'
    print(formatted_header)
    print('-' * len(formatted_header))
    for index, value in enumerate(data):
        print(f'{index} : ({type(value).__name__}) {value}')


@fprint.register(dict)
def _(data):
    formatted_header = f'{type(data).__name__} -> key : value'
    print(formatted_header)
    print('-' * len(formatted_header))
    for key, value in data.items():
        print(f'({type(key).__name__}) {key}: ({type(value).__name__}) {value}')

@fprint.register(List)
def _(data):
    print(data)


class test(HasTraits):
    
    a = List([1,2,3])


t = test()
fprint(t.trait('a'))


# >>> fprint('hello')
# (str) hello

# >>> fprint(21)
# (int) 21

# >>> fprint(3.14159)
# (float) 3.14159

# >>> fprint([2, 3, 5, 7, 11])
# list -> index : value
# ---------------------
# 0 : (int) 2
# 1 : (int) 3
# 2 : (int) 5
# 3 : (int) 7
# 4 : (int) 11

# >>> fprint({2, 3, 5, 7, 11})
# set -> index : value
# --------------------
# 0 : (int) 2
# 1 : (int) 3
# 2 : (int) 5
# 3 : (int) 7
# 4 : (int) 11

# >>> fprint((13, 17, 23, 29, 31))
# tuple -> index : value
# ----------------------
# 0 : (int) 13
# 1 : (int) 17
# 2 : (int) 23
# 3 : (int) 29
# 4 : (int) 31

# >>> fprint({'name': 'John Doe', 'age': 32, 'location': 'New York'})
# dict -> key : value
# -------------------
# (str) name: (str) John Doe
# (str) age: (int) 32
# (str) location: (str) New York