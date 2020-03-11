# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2020-2021, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Implements widget mappings for spectAcoular classes
"""

from bokeh.models.widgets import TextInput, Select, Slider, DataTable,\
TableColumn, NumberEditor
from .factory import get_widgets, set_widgets

def add_bokeh_attr(cls,trait_widget_mapper,trait_widget_args):
    ''' 
    adds functionality for mapping traits to widgets
    '''
    setattr(cls,"trait_widget_mapper",trait_widget_mapper)
    setattr(cls,"trait_widget_args",trait_widget_args)
    setattr(cls,"get_widgets",get_widgets)
    setattr(cls,"set_widgets",set_widgets)

    
# =============================================================================
# extend acoular classes
# =============================================================================



from acoular import SampleSplitter

trait_widget_mapper = {'buffer_size': TextInput,
                       }

trait_widget_args = {'buffer_size': {'disabled':False},
                     }

add_bokeh_attr(SampleSplitter,trait_widget_mapper,trait_widget_args)


#%% calib.py

from acoular import Calib

trait_widget_mapper = {'from_file': TextInput,
                       'basename': TextInput,
                       'num_mics': TextInput,
                       'data': DataTable,
                       }
trait_widget_args = {'from_file': {'disabled':False},
                     'basename': {'disabled':True},
                     'num_mics':  {'disabled':True},
                     'data':  {'disabled':True},
                     }

add_bokeh_attr(Calib,trait_widget_mapper,trait_widget_args)

#%% environments.py

from acoular import Environment

trait_widget_mapper = {'c': TextInput,
                       }

trait_widget_args = {'c': {'disabled':False},
                     }

add_bokeh_attr(Environment,trait_widget_mapper,trait_widget_args)

#%% fbeamform.py 

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


from acoular import BeamformerFunctional

trait_widget_mapper = {'gamma': TextInput,
                       'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'gamma': {'disabled':False},
                     'r_diag': {'disabled':True},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerFunctional,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerCapon

trait_widget_mapper = {'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'r_diag': {'disabled':True},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCapon,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerEig

trait_widget_mapper = {'n': TextInput,
                        'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'n' : {'disabled':False},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerEig,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerMusic

trait_widget_mapper = {'n': TextInput,
                        'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'n' : {'disabled':False},
                    'r_diag': {'disabled':True},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerMusic,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerDamas

trait_widget_mapper = {'damp': TextInput,
                        'n_iter' : TextInput,
                        'calcmode' : Select,
                        'psf_precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'damp' : {'disabled':False},
                     'n_iter' : {'disabled':False},
                     'calcmode' : {'disabled':False},
                     'psf_precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerDamas,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerDamasPlus

trait_widget_mapper = {'method': Select,
                       'alpha': TextInput,
                       'max_iter' : TextInput,
                       'unit_mult' : TextInput,
                        'damp': TextInput,
                        'n_iter' : TextInput,
                        'calcmode' : Select,
                        'psf_precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'method' : {'disabled':False},
                     'alpha' : {'disabled':False},
                     'max_iter' : {'disabled':False},
                     'unit_mult' : {'disabled':False},
                     'damp' : {'disabled':False},
                     'n_iter' : {'disabled':False},
                     'calcmode' : {'disabled':False},
                     'psf_precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerDamasPlus,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerOrth

trait_widget_mapper = {'eva_list' : TextInput,
                        'n' : TextInput,
                        'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {'eva_list': {'disabled':False},
                    'n': {'disabled':False},
                    'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerOrth,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerCleansc

trait_widget_mapper = {
                        'n' : TextInput,
                        'damp' : Slider,
                        'stopn' : TextInput,
                        'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {
                    'n': {'disabled':False},
                    'damp': {'disabled':False,'step':0.01},
                    'stopn': {'disabled':False},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCleansc,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerClean

trait_widget_mapper = {
                        'damp' : Slider,
                        'n_iter' : TextInput,
                        'calcmode' : Select,
                       'cached': Select,
                       }
trait_widget_args = {
                    'damp': {'disabled':False,'step':0.01},
                    'n_iter': {'disabled':False},
                    'calcmode' : {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerClean,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerCMF

trait_widget_mapper = {
                        'method' : Select,
                        'alpha' : Slider,
                        'max_iter' : TextInput,
                        'unit_mult' : TextInput,
                        'r_diag': Select,
                        'r_diag_norm': TextInput,
                        'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {
                    'method': {'disabled':False},
                    'alpha': {'disabled':False,'step':0.01},
                    'max_iter': {'disabled':False},
                    'unit_mult' : {'disabled':False},
                    'r_diag': {'disabled':False},
                    'r_diag_norm': {'disabled':False},
                    'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCMF,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerGIB

trait_widget_mapper = {
                        'unit_mult' : TextInput,
                        'max_iter' : TextInput,
                        'method' : Select,
                        'alpha' : Slider,
                        'pnorm' : TextInput,
                        'beta' : TextInput,
                        'eps_perc' : TextInput,
                        'm' : TextInput,
                        'n': TextInput,
                        'r_diag': Select,
                       'r_diag_norm': TextInput,
                       'precision': Select,
                       'cached': Select,
                       }
trait_widget_args = {
                    'unit_mult' : {'disabled':False},
                    'max_iter': {'disabled':False},
                    'method': {'disabled':False},
                    'alpha': {'disabled':False,'step':0.01},
                    'pnorm': {'disabled':False},
                    'beta': {'disabled':False},
                    'eps_perc': {'disabled':False},
                    'm': {'disabled':False},
                    'n' : {'disabled':False},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerGIB,trait_widget_mapper,trait_widget_args)


from acoular import PointSpreadFunction

trait_widget_mapper = {
                        'calcmode' : Select,
                        'precision' : Select,
                        'freq' : TextInput,

                       }
trait_widget_args = {
                    'calcmode' : {'disabled':False},
                    'precision' : {'disabled':False},
                    'freq' : {'disabled':False},
                     }

add_bokeh_attr(PointSpreadFunction,trait_widget_mapper,trait_widget_args)


#%% grids.py

from acoular import RectGrid

trait_widget_mapper = {'x_min': TextInput,
                       'x_max': TextInput,
                       'y_min' : TextInput,
                       'y_max' : TextInput,
                       'z': TextInput,
                       'increment': TextInput,
                       'nxsteps':TextInput,
                       'nysteps' : TextInput,
                       'size' : TextInput,
                       'shape' : TextInput
                       }
trait_widget_args = {'x_min': {'disabled':False},
                     'x_max': {'disabled':False},
                     'y_min':  {'disabled':False},
                     'y_max':  {'disabled':False},
                     'z':  {'disabled':False},
                     'increment':  {'disabled':False},
                     'nxsteps': {'disabled':True},
                     'nysteps': {'disabled':True},
                     'size': {'disabled':True},
                     'shape': {'disabled':True},
                     }

add_bokeh_attr(RectGrid,trait_widget_mapper,trait_widget_args)


# currently, bokeh library does not support 3D plotting capabilities
from acoular import RectGrid3D

trait_widget_mapper = {'x_min': TextInput,
                       'x_max': TextInput,
                       'y_min' : TextInput,
                       'y_max' : TextInput,
                       'z_min' : TextInput,
                       'z_max' : TextInput,
                       'z': TextInput,
                       '_increment': TextInput,
                       'nxsteps':TextInput,
                       'nysteps' : TextInput,
                       'nzsteps' : TextInput,
                       'size' : TextInput,
                       'shape' : TextInput
                       }
trait_widget_args = {'x_min': {'disabled':False},
                     'x_max': {'disabled':False},
                     'y_min':  {'disabled':False},
                     'y_max':  {'disabled':False},
                     'z_min':  {'disabled':False},
                     'z_max':  {'disabled':False},
                     'z':  {'disabled':False},
                     '_increment':  {'disabled':False},
                     'nxsteps': {'disabled':True},
                     'nysteps': {'disabled':True},
                     'nzsteps': {'disabled':True},
                     'size': {'disabled':True},
                     'shape': {'disabled':True},
                     }

add_bokeh_attr(RectGrid3D,trait_widget_mapper,trait_widget_args)

#%% microphones.py

from acoular import MicGeom

columns = [TableColumn(field='x', title='X', editor=NumberEditor()),
           TableColumn(field='y', title='Y', editor=NumberEditor()),
           TableColumn(field='z', title='Z', editor=NumberEditor())]

trait_widget_mapper = {'from_file': TextInput,
                       'basename': TextInput,
                       'invalid_channels': TextInput,
                       'num_mics': TextInput,
                       'center': TextInput,
                       'mpos_tot': DataTable
                       }

trait_widget_args = {'from_file': {'disabled':False},
                     'basename': {'disabled':True},
                     'invalid_channels':  {'disabled':False},
                     'num_mics':  {'disabled':True},
                     'center':  {'disabled':True},
                     'mpos_tot':  {'editable':True,'columns':columns},
                     }

add_bokeh_attr(MicGeom,trait_widget_mapper,trait_widget_args)

#%% spectra.py

from acoular import PowerSpectra

trait_widget_mapper = {'numchannels' :TextInput,
                        'block_size': Select,
                       'window' : Select,
                       'overlap' : Select,
                       'ind_low' : TextInput,
                       'ind_high' : TextInput,
                       'freq_range' : TextInput,
                       'cached' : Select,
                       'num_blocks':TextInput,
                       'precision' : Select,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'numchannels': {'disabled':True},
                    'block_size': {'disabled':False},
                     'window' : {'disabled':False},
                     'overlap' : {'disabled':False},
                     'ind_low' :{'disabled':False},
                     'ind_high' :{'disabled':False},
                     'freq_range' :{'disabled':True},
                     'cached' : {'disabled':False},
                     'num_blocks': {'disabled':True},
                     'precision' : {'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(PowerSpectra,trait_widget_mapper,trait_widget_args)

#%% sources.py

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


from acoular import PointSource

trait_widget_mapper = {
                       'loc' : TextInput,
                       'start_t' : TextInput,
                       'start' : TextInput,
                       'up' : TextInput,
                      'numsamples': TextInput, # is a Delegate -> currently raises error 
                      'sample_freq': TextInput,
                      'numchannels' : TextInput
                       }
trait_widget_args = {
                    'loc':  {'disabled':False},
                    'start_t':  {'disabled':False},
                    'start':  {'disabled':False},
                    'up':  {'disabled':False},
                    'numsamples':  {'disabled':True},
                    'sample_freq':  {'disabled':True},
                    'numchannels': {'disabled':True},
                     }

add_bokeh_attr(PointSource,trait_widget_mapper,trait_widget_args)


#%% tprocess.py

from acoular import TimeAverage

trait_widget_mapper = {'naverage' : TextInput,
                        'numsamples': TextInput,
                        'sample_freq': TextInput,
                       # 'numchannels' : TextInput
                       }
trait_widget_args = {'naverage':  {'disabled':False},
                      'numsamples':  {'disabled':True},
                      'sample_freq':  {'disabled':True},
                     # 'numchannels': {'disabled':True},
                     }

add_bokeh_attr(TimeAverage,trait_widget_mapper,trait_widget_args)



from acoular import Trigger

trait_widget_mapper = {'threshold' :TextInput,
                       'trigger_type': Select,
                       'max_variation_of_duration' : TextInput,
                       'hunk_length' : TextInput,
                       'multiple_peaks_in_hunk' : Select,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'threshold': {'disabled':False},
                    'trigger_type': {'disabled':False},
                     'max_variation_of_duration' : {'disabled':False},
                     'hunk_length' : {'disabled':False},
                     'multiple_peaks_in_hunk' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }


add_bokeh_attr(Trigger,trait_widget_mapper,trait_widget_args)


from acoular import AngleTracker


trait_widget_mapper = {'trigger_per_revo' :TextInput,
                       'rot_direction': TextInput,
                       'interp_points' : TextInput,
                       'start_angle' : TextInput,
                       'average_rpm' : TextInput,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'trigger_per_revo': {'disabled':False},
                    'rot_direction': {'disabled':False},
                     'interp_points' : {'disabled':False},
                     'start_angle' : {'disabled':False},
                     'average_rpm' :{'disabled':True},
#                     'indices' : {'disabled':True},
                     }


add_bokeh_attr(AngleTracker,trait_widget_mapper,trait_widget_args)




from acoular import SpatialInterpolator

trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : TextInput,
                       'numchannels' : TextInput,
                       'interp_at_zero' : Select,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True},
                     'numchannels' : {'disabled':True},
                     'interp_at_zero' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolator,trait_widget_mapper,trait_widget_args)



from acoular import SpatialInterpolatorRotation

trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : TextInput,
                       'numchannels' : TextInput,
                       'interp_at_zero' : Select,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True},
                     'numchannels' : {'disabled':True},
                     'interp_at_zero' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolatorRotation,trait_widget_mapper,trait_widget_args)



from acoular import SpatialInterpolatorConstantRotation

trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : TextInput,
                       'numchannels' : TextInput,
                       'interp_at_zero' : Select,
                       'rotational_speed' : TextInput,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True},
                     'numchannels' : {'disabled':True},
                     'interp_at_zero' :{'disabled':False},
                     'rotational_speed' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolatorConstantRotation,trait_widget_mapper,trait_widget_args)




from acoular import WriteH5

trait_widget_mapper = {'name': TextInput,
                        'precision' : Select
                       }
trait_widget_args = {'name': {'disabled':False},
                       'precision': {'disabled':False},
                     }

add_bokeh_attr(WriteH5,trait_widget_mapper,trait_widget_args)
