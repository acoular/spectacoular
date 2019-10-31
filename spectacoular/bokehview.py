#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:34:31 2019

@author: kujawski
"""

from bokeh.models.widgets import TextInput, Select
from .factory import TraitWidgetMapper

def get_widgets(self):
    '''
    This function is implemented for acoular classes. It builds widgets to
    corresponding traits defined in bokehview.py

    widgetlist might be better a dictionary! translate trait name to widgets
    '''
    widgetlist = []
    for (traitname,widgetType) in list(self.trait_widget_mapper.items()):
        widgetMapper = TraitWidgetMapper.factory(self,traitname,widgetType)
        widget = widgetMapper.create_widget(**self.trait_widget_args[traitname])
        widgetlist.append(widget)
    return widgetlist

def add_bokeh_attr(cls,trait_widget_mapper,trait_widget_args):
    ''' 
    adds functionality for mapping traits to widgets
    '''
    setattr(cls,"trait_widget_mapper",trait_widget_mapper)
    setattr(cls,"trait_widget_args",trait_widget_args)
    setattr(cls,"get_widgets",get_widgets)
    
# =============================================================================
# extend acoular classes
# =============================================================================

# TODO: trait description implementation

from acoular import TimeSamples

trait_widget_mapper = {'name': TextInput,
                       'basename': TextInput,
                       'numsamples': TextInput,
                       'sample_freq': TextInput,
                       'numchannels' : TextInput
                       }
trait_widget_args = {'name': {'disabled':False},
                     'basename': {'disabled':True},
                     'numsamples':  {'disabled':True},
                     'sample_freq':  {'disabled':True},
                     'numchannels': {'disabled':True},
                     }

add_bokeh_attr(TimeSamples,trait_widget_mapper,trait_widget_args)


from acoular import MaskedTimeSamples

trait_widget_mapper = {'name': TextInput,
                       'basename': TextInput,
                       'start' : TextInput,
                       'stop' : TextInput,
                       'numsamples': TextInput,
                       'sample_freq': TextInput,
                       'invalid_channels':TextInput,
                       'numchannels' : TextInput
                       }
trait_widget_args = {'name': {'disabled':False},
                     'basename': {'disabled':True},
                     'start':  {'disabled':False},
                     'stop':  {'disabled':False},
                     'numsamples':  {'disabled':True},
                     'sample_freq':  {'disabled':True},
                     'invalid_channels': {'disabled':False},
                     'numchannels': {'disabled':True},
                     }

add_bokeh_attr(MaskedTimeSamples,trait_widget_mapper,trait_widget_args)

from acoular import MicGeom

trait_widget_mapper = {'from_file': TextInput,
                       'invalid_channels': TextInput,
                       'num_mics': TextInput
                       }

trait_widget_args = {'from_file': {'disabled':False},
                     'invalid_channels':  {'disabled':False},
                     'num_mics':  {'disabled':True}
                     }

add_bokeh_attr(MicGeom,trait_widget_mapper,trait_widget_args)

 
from acoular import PowerSpectra

trait_widget_mapper = {'block_size': Select,
                       'window' : Select,
                       'overlap' : Select,
                       'cached' : Select,
                       'precision' : Select
                       }

trait_widget_args = {'block_size': {'disabled':False},
                     'window' : {'disabled':False},
                     'overlap' : {'disabled':False},
                     'cached' : {'disabled':False},
                     'precision' : {'disabled':False},
                     }

add_bokeh_attr(PowerSpectra,trait_widget_mapper,trait_widget_args)


from acoular import RectGrid

trait_widget_mapper = {'x_min': TextInput,
                       'x_max': TextInput,
                       'y_min' : TextInput,
                       'y_max' : TextInput,
                       'z': TextInput,
                       'increment': TextInput,
                       'nxsteps':TextInput,
                       'nysteps' : TextInput
                       }
trait_widget_args = {'x_min': {'disabled':False},
                     'x_max': {'disabled':False},
                     'y_min':  {'disabled':False},
                     'y_max':  {'disabled':False},
                     'z':  {'disabled':False},
                     'increment':  {'disabled':False},
                     'nxsteps': {'disabled':True},
                     'nysteps': {'disabled':True},
                     }

add_bokeh_attr(RectGrid,trait_widget_mapper,trait_widget_args)


from acoular import SteeringVector

trait_widget_mapper = {'steer_type': Select,
                       }
trait_widget_args = {'steer_type': {'disabled':False},
                     }

add_bokeh_attr(SteeringVector,trait_widget_mapper,trait_widget_args)

from acoular import BeamformerBase

trait_widget_mapper = {'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerBase,trait_widget_mapper,trait_widget_args)


