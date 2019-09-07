#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:34:31 2019

@author: kujawski
"""

from bokeh.models.widgets import TextInput, Select

# local imports
from .factory import create_widgets_from_traits

def add_bokeh_attr(cls,trait_widget_mapper,trait_widget_args):
    setattr(cls,"trait_widget_mapper",trait_widget_mapper)
    setattr(cls,"trait_widget_args",trait_widget_args)
    setattr(cls,"create_widgets_from_traits",create_widgets_from_traits)
    
# =============================================================================
# acoular class add on's
# =============================================================================

from acoular import TimeSamples

trait_widget_mapper = {'name': TextInput,
                       'numsamples': TextInput,
                       'sample_freq': TextInput
                       }
trait_widget_args = {'name': {'disabled':False},
                     'numsamples':  {'disabled':True},
                     'sample_freq':  {'disabled':True}
                     }

add_bokeh_attr(TimeSamples,trait_widget_mapper,trait_widget_args)


from acoular import MicGeom

trait_widget_mapper = {'from_file': TextInput,
#                       'invalid_channels': TextInput,
                       'num_mics': TextInput
                       }

trait_widget_args = {'from_file': {'disabled':False},
#                     'invalid_channels':  {'disabled':False},
                     'num_mics':  {'disabled':True}
                     }

add_bokeh_attr(MicGeom,trait_widget_mapper,trait_widget_args)

 
from acoular import PowerSpectra

trait_widget_mapper = {'block_size': Select,
                       }

trait_widget_args = {'block_size': {'disabled':False},
                     }

add_bokeh_attr(PowerSpectra,trait_widget_mapper,trait_widget_args)


# =============================================================================
# 
# =============================================================================

