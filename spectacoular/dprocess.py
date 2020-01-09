# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements data processing classes.

.. autosummary::
    :toctree: generated/
    BasePresenter
    MicGeomPresenter
    BeamformerPresenter
    PointSpreadFunctionPresenter
    TimeSamplesPresenter
"""
from bokeh.models.widgets import TextInput, Button, RangeSlider,Select
from bokeh.models import ColumnDataSource
from traits.api import Trait, HasPrivateTraits, Property, Int, Float, \
cached_property, on_trait_change, Instance, ListInt
import numpy as np
from acoular.internal import digest
from acoular import TimeSamples,BeamformerBase, L_p, MicGeom, SteeringVector,\
PointSpreadFunction
from .factory import BaseSpectacoular



class BasePresenter(BaseSpectacoular):
    """
    Base class for any object that serves as a mediator between acoular sources
    (models) and a corresponding user interface. 
    
    It provides methods for filtering and translating data of an acoular class 
    into the format of a ColumnDataSource which can be consumed by plots and glyphs
    of the interface. 
    Interactive elements (widgets) than can be used to control the data 
    transformation can be accessed via the :meth:`get_widgets` method.
    
    This class has no real functionality on its own and should not be 
    used directly.    
    """

    #: Data source (Model)
    source = Trait()
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = ColumnDataSource()

    # # internal identifier
    # digest = Property( depends_on = ['source.digest'])

    def update(self,attr,old,new):
        """
        Function that updates the `cdsource` trait.    
        No processing since `BasePresenter` only represents a base class to derive
        other classes from.             
        """
        pass



class MicGeomPresenter(BasePresenter):
    """
    This class provides data for visualization of a Microphone Geometrie.
    
    The data of its ColumnDataSource fits to different bokeh glyphs (e.g. circle).
   
    Example: 
                
        >>>    import spectacoular
        >>>    mg = spectacoular.MicGeom(from_file='/path/to/file.xml')
        >>>    mv = spectacoular.MicGeomPresenter(source=mg)
        >>>    
        >>>    mgPlot = figure(title='Microphone Geometry')
        >>>    mgPlot.circle(x='x',y='y',source=mv.cdsource)
    """

    #: Data source; :class:`~acoular.microphones.MicGeom` or derived object.
    source = Trait(MicGeom)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = ColumnDataSource(data={'x':[],'y':[], 'channels':[]})

    @on_trait_change("digest")
    def _update(self):
        self.update()
    
    def update(self):
        if self.source.num_mics > 0:
            self.cdsource.data = {
                    'x' : self.source.mpos[0,:],
                    'y' : self.source.mpos[1,:],
                    'channels' : [str(_) for _ in range(self.source.num_mics)],
#                    'sizes' : [1 for _ in range(self.source.num_mics)]
                    }        
        else:
            self.cdsource.data = {'x':[],'y':[], 'channels':[]}        



class BeamformerPresenter(BasePresenter):
    """
    This class provides data for visualization of beamformed data.
    
    The data of its ColumnDataSource fits to bokehs image glyph.
    """
    
    #: Data source; :class:`~acoular.fbeamform.BeamformerBase` or derived object.
    source = Trait(BeamformerBase)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = ColumnDataSource(data={'bfdata':[],'x':[],'y':[],'dw':[],'dh':[]})

    #: :class:`~acoular.fbeamform.SteeringVector` or derived object. 
    steer = Instance(SteeringVector)

    #: Trait to set the width of the frequency bands considered.
    #: defaults to 0 (single frequency line).
    num = Int(0, 
              desc="Controls the width of the frequency bands considered;\
              defaults to 0 (single frequency line).")

    #: Trait to set the band center frequency to be considered.
    freq = Float(None,
                 desc="Band center frequency. ")
    
    trait_widget_mapper = {'num': TextInput,
                           'freq': TextInput,
                       }

    trait_widget_args = {'num': {'disabled':False},
                         'freq': {'disabled':False},
                     }
    
    def update(self):
        res = self.source.synthetic(float(self.freq), int(self.num))
        if res.size > 0: 
            dx = self.steer.grid.x_max-self.steer.grid.x_min
            dy = self.steer.grid.y_max-self.steer.grid.y_min
            self.cdsource.data = {'bfdata' : [L_p(res).T],
            'x':[self.steer.grid.x_min], 
            'y':[self.steer.grid.y_min], 
            'dw':[dx], 
            'dh':[dy]
            }


class PointSpreadFunctionPresenter(BasePresenter):
    
    #: Data source; :class:`~acoular.fbeamform.PointSpreadFunction` or derived object.
    source = Trait(PointSpreadFunction)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = ColumnDataSource(data={'psf':[],'x':[],'y':[],'dw':[],'dh':[]})

    def update(self):
        data = self.source.psf.reshape(self.source.grid.shape)
        data /= np.max(np.abs(data))
        dx = self.source.grid.x_max-self.source.grid.x_min
        dy = self.source.grid.y_max-self.source.grid.y_min
        self.cdsource.data = {'psf' : [L_p(data).T],
        'x':[self.source.grid.x_min], 
        'y':[self.source.grid.y_min], 
        'dw':[dx], 
        'dh':[dy]
            }            
        

class TimeSamplesPresenter(BasePresenter):
    """
    This class implements methods to select channel data for visualization.
    
    The data of its ColumnDataSource fits bokehs MultiLine Glyph.
   
    Example: 
                
        >>>    import spectacoular
        >>>    ts = spectacoular.TimeSamples(name='/path/to/file.h5')
        >>>    tv = spectacoular.TimeSamplesPresenter(source=ts)  
        >>>    
        >>>    tsPlot = figure(title="Channel Data") 
        >>>    tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
        
    """

    #: Data source; :class:`~acoular.sources.TimeSamples` or derived object.
    source = Trait(TimeSamples)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = ColumnDataSource(data={'xs':[],'ys':[]})
    
    channels = ListInt([])
    
    trait_widget_mapper = {'channels': TextInput,
                       }

    trait_widget_args = {'channels': {'disabled':False},
                     }

    def update(self):
        samples = list(range(0,self.source.numsamples))
        numSelected = len(self.channels)
        ys = [list(self.source.data[:,int(idx)]) for idx in self.channels]
        xs = [samples for _ in range(numSelected)]
        if self.source.numsamples > 0 and numSelected > 0:
            self.cdsource.data = {'xs' : xs, 
                                  'ys' : ys}
        else:
            self.cdsource.data = {'xs' :[],'ys' :[]}
