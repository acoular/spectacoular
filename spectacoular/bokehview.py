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
from acoular import SampleSplitter, BeamformerBase, BeamformerFunctional, \
BeamformerCapon, BeamformerEig, BeamformerMusic, BeamformerDamas, \
BeamformerDamasPlus, BeamformerOrth, BeamformerCleansc, BeamformerClean, \
BeamformerCMF, BeamformerGIB, PointSpreadFunction, RectGrid, RectGrid3D, \
MicGeom, Calib, Environment, SteeringVector, PowerSpectra, TimeSamples, MaskedTimeSamples, PointSource, \
Average, TimeAverage, FiltOctave, Trigger, AngleTracker, SpatialInterpolator, \
SpatialInterpolatorRotation, SpatialInterpolatorConstantRotation, WriteH5, SoundDeviceSamplesGenerator, MaskedTimeOut

from bokeh.models.widgets import TextInput, Select, Slider, DataTable,\
TableColumn, NumberEditor, NumericInput, Toggle, MultiSelect
from .factory import get_widgets, set_widgets

def add_bokeh_attr(cls, trait_widget_mapper, trait_widget_args):
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


trait_widget_mapper = {'buffer_size': NumericInput,
                       }

trait_widget_args = {'buffer_size': {'disabled':False, 'mode':'int'},
                     }

add_bokeh_attr(SampleSplitter,trait_widget_mapper,trait_widget_args)


#%% calib.py

cal_columns = [TableColumn(field='data', title='calib factors', editor=NumberEditor()),]

trait_widget_mapper = {'file': TextInput,
                       'num_mics': NumericInput,
                       'data': DataTable,
                       }
trait_widget_args = {'file': {'disabled':False},
                     'num_mics':  {'disabled':True,'mode':'int'},
                     'data':  {'disabled':True, 'editable':False, 'columns':cal_columns},
                     }

add_bokeh_attr(Calib,trait_widget_mapper,trait_widget_args)

#%% environments.py

trait_widget_mapper = {'c': NumericInput,
                       }

trait_widget_args = {'c': {'disabled':False, 'mode':'float'},
                     }

add_bokeh_attr(Environment,trait_widget_mapper,trait_widget_args)

#%% fbeamform.py 

trait_widget_mapper = {'steer_type': Select,
                       }
trait_widget_args = {'steer_type': {'disabled':False},
                     }

add_bokeh_attr(SteeringVector,trait_widget_mapper,trait_widget_args)


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


trait_widget_mapper = {'gamma': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'gamma': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerFunctional,trait_widget_mapper,trait_widget_args)


trait_widget_mapper = {
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCapon,trait_widget_mapper,trait_widget_args)


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


trait_widget_mapper = {'n': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'n' : {'disabled':False, 'mode':'int'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerMusic,trait_widget_mapper,trait_widget_args)


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


trait_widget_mapper = {'method': Select,
                       'alpha': Slider,
                       'n_iter' : NumericInput,
                       'unit_mult' : NumericInput,
                        'damp': NumericInput,
                        'calcmode' : Select,
                        'psf_precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {'method' : {'disabled':False},
                     'alpha': {'disabled':False,'step':0.01},
                     'n_iter' : {'disabled':False, 'mode':'int'},
                     'unit_mult' : {'disabled':False, 'mode':'float'},
                     'damp' : {'disabled':False, 'mode':'float'},
                     'calcmode' : {'disabled':False},
                     'psf_precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerDamasPlus,trait_widget_mapper,trait_widget_args)

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


trait_widget_mapper = {
                        'n_iter' : NumericInput,
                        'damp' : Slider,
                        'stopn' : NumericInput,
                        'r_diag': Toggle,
                       'r_diag_norm': NumericInput,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'n_iter': {'disabled':False,'mode':'int'},
                    'damp': {'disabled':False,'step':0.01},
                    'stopn': {'disabled':False,'mode':'int'},
                    'r_diag': {'disabled':False},
                     'r_diag_norm': {'disabled':False,'mode':'float'},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCleansc,trait_widget_mapper,trait_widget_args)


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


trait_widget_mapper = {
                        'method' : Select,
                        'alpha' : Slider,
                        'n_iter' : NumericInput,
                        'unit_mult' : NumericInput,
                        'r_diag': Toggle,
                        'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'method': {'disabled':False},
                    'alpha': {'disabled':False,'step':0.01},
                    'n_iter': {'disabled':False,'mode':'int'},
                    'unit_mult' : {'disabled':False,'mode':'float'},
                    'r_diag': {'disabled':False},
                    'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerCMF,trait_widget_mapper,trait_widget_args)


trait_widget_mapper = {
                        'unit_mult' : NumericInput,
                        'n_iter' : NumericInput,
                        'method' : Select,
                        'alpha' : Slider,
                        'pnorm' : NumericInput,
                        'beta' : NumericInput,
                        'eps_perc' : NumericInput,
                        'm' : NumericInput,
                        'n': NumericInput,
                        'r_diag': Toggle,
                       'precision': Select,
                       'cached': Toggle,
                       }
trait_widget_args = {
                    'unit_mult' : {'disabled':False,'mode':'float'},
                    'n_iter': {'disabled':False,'mode':'int'},
                    'method': {'disabled':False},
                    'alpha': {'disabled':False,'step':0.01},
                    'pnorm': {'disabled':False,'mode':'float'},
                    'beta': {'disabled':False,'mode':'float'},
                    'eps_perc': {'disabled':False,'mode':'float'},
                    'm': {'disabled':False,'mode':'int'},
                    'n' : {'disabled':False,'mode':'int'},
                    'r_diag': {'disabled':False},
                     'precision': {'disabled':False},
                     'cached': {'disabled':False},
                     }

add_bokeh_attr(BeamformerGIB,trait_widget_mapper,trait_widget_args)


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

trait_widget_mapper = {'x_min': NumericInput,
                       'x_max': NumericInput,
                       'y_min' : NumericInput,
                       'y_max' : NumericInput,
                       'z': NumericInput,
                       'increment': NumericInput,
                       'nxsteps':NumericInput,
                       'nysteps' : NumericInput,
                       'size' : NumericInput,
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
                     }

add_bokeh_attr(RectGrid,trait_widget_mapper,trait_widget_args)


# currently, bokeh library does not support 3D plotting capabilities
trait_widget_mapper = {'x_min': NumericInput,
                       'x_max': NumericInput,
                       'y_min' : NumericInput,
                       'y_max' : NumericInput,
                       'z_min' : NumericInput,
                       'z_max' : NumericInput,
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
                     '_increment':  {'disabled':False,'mode':'float'},
                     'nxsteps': {'disabled':True,'mode':'int'},
                     'nysteps': {'disabled':True,'mode':'int'},
                     'nzsteps': {'disabled':True,'mode':'int'},
                     'size': {'disabled':True,'mode':'int'},
                     #'shape': {'disabled':True},
                     }

add_bokeh_attr(RectGrid3D,trait_widget_mapper,trait_widget_args)

#%% microphones.py


editor = NumberEditor() 
mpos_columns = [TableColumn(field='x', title='x', editor=editor),
                TableColumn(field='y', title='y', editor=editor),
                TableColumn(field='z', title='z', editor=editor)]

trait_widget_mapper = {'file': TextInput,
                       'invalid_channels': MultiSelect,
                       'num_mics': NumericInput,
                       'pos_total': DataTable
                       }

trait_widget_args = {'file': {'disabled':False},
                     'invalid_channels':  {'disabled':False},
                     'num_mics':  {'disabled':True, 'mode':'int'},
                     'pos_total':  {'editable':True, 'transposed':True, 'columns':mpos_columns,}
                     }

add_bokeh_attr(MicGeom,trait_widget_mapper,trait_widget_args)

#%% spectra.py

trait_widget_mapper = {'num_channels' :NumericInput,
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

trait_widget_args = {'num_channels': {'disabled':True, 'mode':'int'},
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

trait_widget_mapper = {'file': TextInput,
                       'basename': TextInput,
                       'num_samples': NumericInput,
                       'sample_freq': NumericInput,
                       'num_channels' : NumericInput,
                       }
trait_widget_args = {'file': {'disabled':False},
                     'basename': {'disabled':True},
                     'num_samples':  {'disabled':True,'mode':'int'},
                     'sample_freq':  {'disabled':True,'mode':'float'},
                     'num_channels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(TimeSamples,trait_widget_mapper,trait_widget_args)


invch_columns = [TableColumn(field='invalid_channels', title='invalid_channels', editor=NumberEditor()),]

trait_widget_mapper = {'file': TextInput,
                       'basename': TextInput,
                       'start' : NumericInput,
                       'stop' : NumericInput,
                       'num_samples': NumericInput,
                       'sample_freq': NumericInput,
                       'invalid_channels':DataTable,
                       'num_channels' : NumericInput
                       }
trait_widget_args = {'file': {'disabled':False},
                     'basename': {'disabled':True},
                     'start':  {'disabled':False, 'mode':'int'},
                     'stop':  {'disabled':False, 'mode':'int'},
                     'num_samples':  {'disabled':True, 'mode':'int'},
                     'sample_freq':  {'disabled':True, 'mode':'float'},
                     'invalid_channels': {'disabled':False,'editable':True, 'columns':invch_columns},
                     'num_channels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(MaskedTimeSamples,trait_widget_mapper,trait_widget_args)


loc_columns = [TableColumn(field='loc', title='source location', editor=NumberEditor()),]


trait_widget_mapper = {
                       'loc' : DataTable,
                       'start_t' : NumericInput,
                       'start' : NumericInput,
                       'up' : NumericInput,
                      'num_samples': NumericInput, # is a Delegate -> currently raises error 
                      'sample_freq': NumericInput,
                      'num_channels' : NumericInput
                       }
trait_widget_args = {
                    'loc':  {'disabled':False, 'editable': True, 'columns':loc_columns},
                    'start_t':  {'disabled':False,'mode':'float'},
                    'start':  {'disabled':False,'mode':'float'},
                    'up':  {'disabled':False,'mode':'int'},
                    'num_samples':  {'disabled':True,'mode':'int'},
                    'sample_freq':  {'disabled':True,'mode':'float'},
                    'num_channels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(PointSource,trait_widget_mapper,trait_widget_args)

#%% process.py 

trait_widget_mapper = {'num_per_average' : NumericInput,
                        'num_samples': NumericInput,
                        'sample_freq': NumericInput,
                       }
trait_widget_args = {'num_per_average':  {'disabled':False,'mode':'int'},
                      'num_samples':  {'disabled':True,'mode':'int'},
                      'sample_freq':  {'disabled':True,'mode':'float'},
                     }

add_bokeh_attr(Average,trait_widget_mapper,trait_widget_args)
add_bokeh_attr(TimeAverage,trait_widget_mapper,trait_widget_args)

#%% tprocess.py

trait_widget_mapper = {'band' : NumericInput,
                        'fraction': Select,
                        'order': NumericInput,
                       # 'num_channels' : NumericInput,
                       }
trait_widget_args = {'band':  {'disabled':False,'mode':'float'},
                      'fraction':  {'disabled':False},
                      'order':  {'disabled':False,'mode':'int'},
                     # 'num_channels': {'disabled':True,'mode':'int'},
                     }

add_bokeh_attr(FiltOctave,trait_widget_mapper,trait_widget_args)



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



trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : NumericInput,
                       'num_channels' : NumericInput,
                       'interp_at_zero' : Toggle,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True,'mode':'float'},
                     'num_channels' : {'disabled':True,'mode':'int'},
                     'interp_at_zero' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolator,trait_widget_mapper,trait_widget_args)



trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : NumericInput,
                       'num_channels' : NumericInput,
                       'interp_at_zero' : Toggle,
#                       'indices' : DataTable,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True,'mode':'float'},
                     'num_channels' : {'disabled':True,'mode':'int'},
                     'interp_at_zero' :{'disabled':False},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolatorRotation,trait_widget_mapper,trait_widget_args)



trait_widget_mapper = {'method' :Select,
                        'array_dimension': Select,
                       'sample_freq' : NumericInput,
                       'num_channels' : NumericInput,
                       'interp_at_zero' : Toggle,
                       'rotational_speed' : NumericInput,
                       }

trait_widget_args = {'method': {'disabled':False},
                    'array_dimension': {'disabled':False},
                     'sample_freq' : {'disabled':True,'mode':'float'},
                     'num_channels' : {'disabled':True,'mode':'int'},
                     'interp_at_zero' :{'disabled':False},
                     'rotational_speed' :{'disabled':False,'mode':'float'},
#                     'indices' : {'disabled':True},
                     }

add_bokeh_attr(SpatialInterpolatorConstantRotation,trait_widget_mapper,trait_widget_args)



trait_widget_mapper = {'file': TextInput,
                        'precision' : Select
                       }
trait_widget_args = {'file': {'disabled':False},
                       'precision': {'disabled':False},
                     }

add_bokeh_attr(WriteH5,trait_widget_mapper,trait_widget_args)


trait_widget_mapper = {'device': NumericInput,
                       'num_channels' : NumericInput,
                       'num_samples' : NumericInput,
                       'sample_freq': NumericInput,
                       }
trait_widget_args = {'device': {'disabled':False,'mode':'int'},
                     'num_channels' : {'disabled':False,'mode':'int'},
                     'num_samples':  {'disabled':False,'mode':'int'},
                     'sample_freq':  {'disabled':True,'mode':'float'},
                     }
add_bokeh_attr(SoundDeviceSamplesGenerator,trait_widget_mapper,trait_widget_args)


trait_widget_mapper = {'start': NumericInput,
                          'stop': NumericInput,
                          'invalid_channels': DataTable,
                          'num_channels': NumericInput,
                          'num_samples': NumericInput,
                          'sample_freq': NumericInput,
                          } 

trait_widget_args = {'start': {'disabled':False,'mode':'int'},
                        'stop': {'disabled':False,'mode':'int'},
                        'invalid_channels': {'disabled':False,'editable':True, 'columns':invch_columns},
                        'num_channels': {'disabled':True,'mode':'int'},
                        'num_samples': {'disabled':True,'mode':'int'},
                        'sample_freq': {'disabled':True,'mode':'float'},
                        }

add_bokeh_attr(MaskedTimeOut,trait_widget_mapper,trait_widget_args)                          