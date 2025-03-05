#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------

import spectacoular as ac
import acoular
import inspect
import pytest

acoular_classes = [obj[0] for obj in inspect.getmembers(acoular, inspect.isclass)]
spectacoular_classes = [obj[0] for obj in inspect.getmembers(ac, inspect.isclass)]

@pytest.mark.parametrize('class_name', acoular_classes)
def test_view_exists(class_name):
    """Tests that for each class in Acoular a corresponding object in Acoular exists."""
    assert class_name in spectacoular_classes

@pytest.mark.parametrize('class_name', spectacoular_classes)
def test_get_widgets(class_name):
    """ test that get_widgets can be called"""
    if hasattr(class_name,'get_widgets') and hasattr(class_name,'trait_widget_mapper'):
        acoular_class = class_name()
        # now test each default mapping individually
        for key,value in acoular_class.trait_widget_mapper.items():
            arg = acoular_class.trait_widget_args.get(key)
            if arg:
                acoular_class.get_widgets({key:value},{key:arg})
            else:
                acoular_class.get_widgets({key:value})

