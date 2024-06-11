#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
#------------------------------------------------------------------------------
"""
Implements trait-widget mapping functionality to Acoular classes. Defines which
attribute is to be mapped into which Bokeh widget type.

.. autosummary::
    :toctree: generated/

    add_bokeh_attr
"""

from bokeh.models.widgets import TextInput, Select, Slider, DataTable,\
TableColumn, NumberEditor, NumericInput, Toggle
from .factory import get_widgets, set_widgets

def add_bokeh_attr(cls,trait_widget_mapper,trait_widget_args):
    """
    helper function to add trait-widget mapping functions and dictionaries
    defining the mapping to Acoular classes
    
    Parameters
    ----------
    cls : class
        Class to which the functionalities should be added.
    trait_widget_mapper : dict
        Dictionary containing the name of the trait attributes and the 
        corresponding Bokeh widgets.
    trait_widget_args : dict
        Additional widget arguments that should be included when widget is 
        created.

    Returns
    -------
    None.

    """
    setattr(cls,"trait_widget_mapper",trait_widget_mapper)
    setattr(cls,"trait_widget_args",trait_widget_args)
    setattr(cls,"get_widgets",get_widgets)
    setattr(cls,"set_widgets",set_widgets)

    
# =============================================================================
# extend acoular classes
# =============================================================================



from acoular import SampleSplitter

trait_widget_mapper = {'buffer_size': NumericInput,
                       }

trait_widget_args = {'buffer_size': {'disabled':False, 'mode':'int'},
                     }

add_bokeh_attr(SampleSplitter,trait_widget_mapper,trait_widget_args)


#%% calib.py

from acoular import Calib

cal_columns = [TableColumn(field='data', title='calib factors', editor=NumberEditor()),]

trait_widget_mapper = {'from_file': TextInput,
                       'basename': TextInput,
                       'num_mics': NumericInput,
                       'data': DataTable,
                       }
trait_widget_args = {'from_file': {'disabled':False},
                     'basename': {'disabled':True},
                     'num_mics':  {'disabled':True,'mode':'int'},
                     'data':  {'disabled':True, 'editable':False, 'columns':cal_columns},
                     }

add_bokeh_attr(Calib,trait_widget_mapper,trait_widget_args)

#%% environments.py

from acoular import Environment

trait_widget_mapper = {'c': NumericInput,
                       }

trait_widget_args = {'c': {'disabled':False, 'mode':'float'},
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

trait_widget_mapper = {'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerBase,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerFunctional

trait_widget_mapper = {'gamma': NumericInput,
                       #'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'gamma': {'disabled':False,'mode':'float'},
                     #'r_diag': {'disabled':True},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerFunctional,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerCapon

trait_widget_mapper = {#'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {#'r_diag': {'disabled':True},
                     'r_diag_norm': {'disabled':False,'mode':'float' },
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCapon,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerEig

trait_widget_mapper = {'n': NumericInput,
                        'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'n' : {'disabled':False,'mode':'int'},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerEig,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerMusic

trait_widget_mapper = {'n': NumericInput,
                        #'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'n' : {'disabled':False, 'mode':'int'},
                    #'r_diag': {'disabled':True},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerMusic,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerDamas

trait_widget_mapper = {'damp': NumericInput,
                        'n_iter' : NumericInput,
                        'calcmode' : Select,
                        'psf_precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'damp' : {'disabled':False, 'mode':'float'},
                     'n_iter' : {'disabled':False, 'mode':'int'},
                     'calcmode' : {'disabled':False},
                     'psf_precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerDamas,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerDamasPlus

trait_widget_mapper = {'method': Select,
                       'alpha': Slider,
                       'max_iter' : NumericInput,
                       'unit_mult' : NumericInput,
                        'damp': NumericInput,
                        'n_iter' : NumericInput,
                        'calcmode' : Select,
                        'psf_precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'method' : {'disabled':False},
                     'alpha': {'disabled':False,'step':0.01},
                     'max_iter' : {'disabled':False, 'mode':'int'},
                     'unit_mult' : {'disabled':False, 'mode':'float'},
                     'damp' : {'disabled':False, 'mode':'float'},
                     'n_iter' : {'disabled':False, 'mode':'int'},
                     'calcmode' : {'disabled':False},
                     'psf_precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerDamasPlus,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerOrth

eva_columns = [TableColumn(field='eva_list', title='eigenvalues', editor=NumberEditor()),]

trait_widget_mapper = {'eva_list' : DataTable,
                        'n' : NumericInput,
                        'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'eva_list': {'disabled':False, 'editable': True, 'columns':eva_columns},
                    'n': {'disabled':False, 'mode':'int'},
                    'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerOrth,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerCleansc

trait_widget_mapper = {
                        'n' : NumericInput,
                        'damp' : Slider,
                        'stopn' : NumericInput,
                        'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'n': {'disabled':False,'mode':'int'},
                    'damp': {'disabled':False,'step':0.01},
                    'stopn': {'disabled':False,'mode':'int'},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCleansc,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerClean

trait_widget_mapper = {
                        'damp' : Slider,
                        'n_iter' : NumericInput,
                        'calcmode' : Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'damp': {'disabled':False,'step':0.01},
                    'n_iter': {'disabled':False,'mode':'int'},
                    'calcmode' : {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerClean,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerCMF

trait_widget_mapper = {
                        'method' : Select,
                        'alpha' : Slider,
                        'max_iter' : NumericInput,
                        'unit_mult' : NumericInput,
                        'r_diag': Toggle,
                        'r_diag_norm': NumericInput,
                        'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'method': {'disabled':False},
                    'alpha': {'disabled':False,'step':0.01},
                    'max_iter': {'disabled':False,'mode':'int'},
                    'unit_mult' : {'disabled':False,'mode':'float'},
                    'r_diag': {'disabled':False},
                    'r_diag_norm': {'disabled':False,'mode':'float'},
                    'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCMF,trait_widget_mapper,trait_widget_args)


from acoular import BeamformerGIB

trait_widget_mapper = {
                        'unit_mult' : NumericInput,
                        'max_iter' : NumericInput,
                        'method' : Select,
                        'alpha' : Slider,
                        'pnorm' : NumericInput,
                        'beta' : NumericInput,
                        'eps_perc' : NumericInput,
                        'm' : NumericInput,
                        'n': NumericInput,
                        'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'unit_mult' : {'disabled':False,'mode':'float'},
                    'max_iter': {'disabled':False,'mode':'int'},
                    'method': {'disabled':False},
                    'alpha': {'disabled':False,'step':0.01},
                    'pnorm': {'disabled':False,'mode':'float'},
                    'beta': {'disabled':False,'mode':'float'},
                    'eps_perc': {'disabled':False,'mode':'float'},
                    'm': {'disabled':False,'mode':'int'},
                    'n' : {'disabled':False,'mode':'int'},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerGIB,trait_widget_mapper,trait_widget_args)


from acoular import PointSpreadFunction

trait_widget_mapper = {
                        'calcmode' : Select,
                        'precision' : Select,
                        'freq' : NumericInput,

                       }
trait_widget_args = {
                    'calcmode' : {'disabled':False},
                    'precision' : {'disabled':False},
                    'freq' : {'disabled':False,'mode':'float'},
                     }

add_bokeh_attr(PointSpreadFunction,trait_widget_mapper,trait_widget_args)


#%% grids.py

from acoular import RectGrid

trait_widget_mapper = {'x_min': NumericInput,
                       'x_max': NumericInput,
                       'y_min' : NumericInput,
                       'y_max' : NumericInput,
                       'z': NumericInput,
                       'increment': NumericInput,
                       'nxsteps':NumericInput,
                       'nysteps' : NumericInput,
                       'size' : NumericInput,
                       #'shape' : DataTable
                       }
trait_widget_args = {'x_min': {'disabled':False,'mode':'float'},
                     'x_max': {'disabled':False,'mode':'float'},
                     'y_min':  {'disabled':False,'mode':'float'},
                     'y_max':  {'disabled':False,'mode':'float'},
                     'z':  {'disabled':False,'mode':'float'},
                     'increment':  {'disabled':False,'mode':'float'},
                     'nxsteps': {'disabled':True,'mode':'int'},
                     'nysteps': {'disabled':True,'mode':'int'},
                     'size': {'disabled':True,'mode':'int'},
                     #'shape': {'disabled':True},
                     }

add_bokeh_attr(RectGrid,trait_widget_mapper,trait_widget_args)


# currently, bokeh library does not support 3D plotting capabilities
from acoular import RectGrid3D

trait_widget_mapper = {'x_min': NumericInput,
                       'x_max': NumericInput,
                       'y_min' : NumericInput,
                       'y_max' : NumericInput,
                       'z_min' : NumericInput,
                       'z_max' : NumericInput,
                       'z': NumericInput,
                       '_increment': NumericInput,
                       'nxsteps':NumericInput,
                       'nysteps' : NumericInput,
                       'nzsteps' : NumericInput,
                       'size' : NumericInput,
                       #'shape' : DataTable
                       }
trait_widget_args = {'x_min': {'disabled':False,'mode':'float'},
                     'x_max': {'disabled':False,'mode':'float'},
                     'y_min':  {'disabled':False,'mode':'float'},
                     'y_max':  {'disabled':False,'mode':'float'},
                     'z_min':  {'disabled':False,'mode':'float'},
                     'z_max':  {'disabled':False,'mode':'float'},
                     'z':  {'disabled':False,'mode':'float'},
                     '_increment':  {'disabled':False,'mode':'float'},
                     'nxsteps': {'disabled':True,'mode':'int'},
                     'nysteps': {'disabled':True,'mode':'int'},
                     'nzsteps': {'disabled':True,'mode':'int'},
                     'size': {'disabled':True,'mode':'int'},
                     #'shape': {'disabled':True},
                     }

add_bokeh_attr(RectGrid3D,trait_widget_mapper,trait_widget_args)

#%% microphones.py

from acoular import MicGeom

mpos_columns = [TableColumn(field='x', title='x', editor=NumberEditor()),
                TableColumn(field='y', title='y', editor=NumberEditor()),
                TableColumn(field='z', title='z', editor=NumberEditor())]
invch_columns = [TableColumn(field='invalid_channels', title='invalid_channels', editor=NumberEditor()),]

trait_widget_mapper = {'from_file': TextInput,
                       'basename': TextInput,
                       'invalid_channels': DataTable,
                       'num_mics': NumericInput,
                       #'center': DataTable,
                       'mpos_tot': DataTable
                       }

trait_widget_args = {'from_file': {'disabled':False},
                     'basename': {'disabled':True},
                     'invalid_channels':  {'disabled':False, 'editable':True,'columns':invch_columns,},
                     'num_mics':  {'disabled':True, 'mode':'int'},
                     #'center':  {'disabled':True},
                     'mpos_tot':  {'editable':True, 'transposed':True, 'columns':mpos_columns,}
                     }

add_bokeh_attr(MicGeom,trait_widget_mapper,trait_widget_args)

#%% spectra.py

from acoular import PowerSpectra

trait_widget_mapper = {'numchannels' :NumericInput,
                        'block_size': Select,
                       'window' : Select,
                       'overlap' : Select,
                       'ind_low' : NumericInput,
                       'ind_high' : NumericInput,
                       #'freq_range' : TextInput,
                       'cached' : Toggle,
                       'num_blocks':NumericInput,
                       'precision' : Select,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'numchannels': {'disabled':True, 'mode':'int'},
                    'block_size': {'disabled':False},
                     'window' : {'disabled':False},
                     'overlap' : {'disabled':False},
                     'ind_low' :{'disabled':False, 'mode':'int'},
                     'ind_high' :{'disabled':False, 'mode':'int'},
                     #'freq_range' :{'disabled':True},
                     'cached' : {'disabled':False},
                     'num_blocks': {'disabled':True, 'mode':'float'},
                     'precision' : {'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(PowerSpectra,trait_widget_mapper,trait_widget_args)

#%% sources.py

from acoular import TimeSamples

trait_widget_mapper = {'name': TextInput,
                       'basename': TextInput,
                       'numsamples': NumericInput,
                       'sample_freq': NumericInput,
                       'numchannels' : NumericInput,
                       }
trait_widget_args = {'name': {'disabled':False},
                     'basename': {'disabled':True},
                     'numsamples':  {'disabled':True,'mode':'int'},
                     'sample_freq':  {'disabled':True,'mode':'float'},
                     'numchannels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(TimeSamples,trait_widget_mapper,trait_widget_args)


from acoular import MaskedTimeSamples

invch_columns = [TableColumn(field='invalid_channels', title='invalid_channels', editor=NumberEditor()),]

trait_widget_mapper = {'name': TextInput,
                       'basename': TextInput,
                       'start' : NumericInput,
                       'stop' : NumericInput,
                       'numsamples': NumericInput,
                       'sample_freq': NumericInput,
                       'invalid_channels':DataTable,
                       'numchannels' : NumericInput
                       }
trait_widget_args = {'name': {'disabled':False},
                     'basename': {'disabled':True},
                     'start':  {'disabled':False, 'mode':'int'},
                     'stop':  {'disabled':False, 'mode':'int'},
                     'numsamples':  {'disabled':True, 'mode':'int'},
                     'sample_freq':  {'disabled':True, 'mode':'float'},
                     'invalid_channels': {'disabled':False,'editable':True, 'columns':invch_columns},
                     'numchannels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(MaskedTimeSamples,trait_widget_mapper,trait_widget_args)


from acoular import PointSource

loc_columns = [TableColumn(field='loc', title='source location', editor=NumberEditor()),]


trait_widget_mapper = {
                       'loc' : DataTable,
                       'start_t' : NumericInput,
                       'start' : NumericInput,
                       'up' : NumericInput,
                      'numsamples': NumericInput, # is a Delegate -> currently raises error 
                      'sample_freq': NumericInput,
                      'numchannels' : NumericInput
                       }
trait_widget_args = {
                    'loc':  {'disabled':False, 'editable': True, 'columns':loc_columns},
                    'start_t':  {'disabled':False,'mode':'float'},
                    'start':  {'disabled':False,'mode':'float'},
                    'up':  {'disabled':False,'mode':'int'},
                    'numsamples':  {'disabled':True,'mode':'int'},
                    'sample_freq':  {'disabled':True,'mode':'float'},
                    'numchannels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(PointSource,trait_widget_mapper,trait_widget_args)


#%% tprocess.py

from acoular import TimeAverage

trait_widget_mapper = {'naverage' : NumericInput,
                        'numsamples': NumericInput,
                        'sample_freq': NumericInput,
                       # 'numchannels' : NumericInput,
                       }
trait_widget_args = {'naverage':  {'disabled':False,'mode':'int'},
                      'numsamples':  {'disabled':True,'mode':'int'},
                      'sample_freq':  {'disabled':True,'mode':'float'},
                     # 'numchannels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(TimeAverage,trait_widget_mapper,trait_widget_args)

from acoular import FiltOctave

trait_widget_mapper = {'band' : NumericInput,
                        'fraction': Select,
                        'order': NumericInput,
                       # 'numchannels' : NumericInput,
                       }
trait_widget_args = {'band':  {'disabled':False,'mode':'float'},
                      'fraction':  {'disabled':False},
                      'order':  {'disabled':False,'mode':'int'},
                     # 'numchannels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(FiltOctave,trait_widget_mapper,trait_widget_args)



from acoular import Trigger

trait_widget_mapper = {'threshold' :NumericInput,
                       'trigger_type': Select,
                       'max_variation_of_duration' : NumericInput,
                       'hunk_length' : NumericInput,
                       'multiple_peaks_in_hunk' : Select,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'threshold': {'disabled':False,'mode':'float'},
                    'trigger_type': {'disabled':False},
                     'max_variation_of_duration' : {'disabled':False,'mode':'float'},
                     'hunk_length' : {'disabled':False,'mode':'float'},
                     'multiple_peaks_in_hunk' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }


add_bokeh_attr(Trigger,trait_widget_mapper,trait_widget_args)


from acoular import AngleTracker


trait_widget_mapper = {'trigger_per_revo' :NumericInput,
                       'rot_direction': NumericInput,
                       'interp_points' : NumericInput,
                       'start_angle' : NumericInput,
                       'average_rpm' : NumericInput,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'trigger_per_revo': {'disabled':False,'mode':'int'},
                    'rot_direction': {'disabled':False,'mode':'int'},
                     'interp_points' : {'disabled':False,'mode':'int'},
                     'start_angle' : {'disabled':False,'mode':'float'},
                     'average_rpm' :{'disabled':True,'mode':'float'},
#                     'indices' : {'disabled':True},
                     }


add_bokeh_attr(AngleTracker,trait_widget_mapper,trait_widget_args)




from acoular import SpatialInterpolator

trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : NumericInput,
                       'numchannels' : NumericInput,
                       'interp_at_zero' : Toggle,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True,'mode':'float'},
                     'numchannels' : {'disabled':True,'mode':'int'},
                     'interp_at_zero' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolator,trait_widget_mapper,trait_widget_args)



from acoular import SpatialInterpolatorRotation

trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : NumericInput,
                       'numchannels' : NumericInput,
                       'interp_at_zero' : Toggle,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True,'mode':'float'},
                     'numchannels' : {'disabled':True,'mode':'int'},
                     'interp_at_zero' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolatorRotation,trait_widget_mapper,trait_widget_args)



from acoular import SpatialInterpolatorConstantRotation

trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : NumericInput,
                       'numchannels' : NumericInput,
                       'interp_at_zero' : Toggle,
                       'rotational_speed' : NumericInput,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True,'mode':'float'},
                     'numchannels' : {'disabled':True,'mode':'int'},
                     'interp_at_zero' :{'disabled':False},
                     'rotational_speed' :{'disabled':False,'mode':'float'},
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

from acoular import SoundDeviceSamplesGenerator

trait_widget_mapper = {'device': NumericInput,
                       'sample_freq': NumericInput,
                       'numchannels' : NumericInput
                       }
trait_widget_args = {'device': {'disabled':False,'mode':'int'},
                     'numchannels' : {'disabled':False,'mode':'int'},
                     'sample_freq':  {'disabled':True,'mode':'float'},
                     }
add_bokeh_attr(SoundDeviceSamplesGenerator,trait_widget_mapper,trait_widget_args)
