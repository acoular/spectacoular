#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
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
from bokeh.models.widgets import NumericInput, DataTable
from bokeh.models import ColumnDataSource
from traits.api import Trait, Int, Float, Instance, Bool, observe, List
import numpy as np
from acoular import TimeSamples,BeamformerBase, L_p, MicGeom,\
PointSpreadFunction, MaskedTimeSamples
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
    used.    
    """

    #: Data source (Model)
    source = Trait()
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = Instance(ColumnDataSource, args=())

    auto_update = Bool(False, 
        desc="If True, the presenter will update the data source when the digest changes.")

    @observe("source.digest")
    def _auto_update(self, event):
        if self.auto_update:
            self.update()

    def update(self, **optional_items):
        """
        Function that updates the `cdsource` attribute.    
        
        No processing here, since `BasePresenter` only represents a base class 
        to derive other classes from.             
        """
        pass



class MicGeomPresenter(BasePresenter):
    """
    This class provides data for visualization of a Microphone Geometry.
    
    The data of its ColumnDataSource fits to different bokeh glyphs (e.g. circle).
   
    Example: 
                
        >>>    import spectacoular
        >>>    mg = spectacoular.MicGeom(file='/path/to/file.xml')
        >>>    mv = spectacoular.MicGeomPresenter(source=mg)
        >>>    
        >>>    mgPlot = figure(title='Microphone Geometry')
        >>>    mgPlot.circle(x='x',y='y',source=mv.cdsource)
    """

    #: Data source; :class:`~acoular.microphones.MicGeom` or derived object.
    source = Instance(MicGeom)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = Instance(ColumnDataSource, kw={'data':{
        'x':[],'y':[],'z':[],'xi':[],'yi':[],'zi':[], 'channels':[], 'alpha':[]}})

    @observe("source.digest")
    def _update(self, event):
        if self.auto_update:
            self.update()
    
    def update(self, **optional_items):
        nmics_total = self.source.pos_total.shape[1]
        if self.source.num_mics > 0:
            pos = self.source.pos_total.copy()
            pos[:,self.source.invalid_channels] = np.nan
            self.cdsource.data.update({
                    'x' : self.source.pos_total[0,:], 
                    'y' : self.source.pos_total[1,:],
                    'z' : self.source.pos_total[2,:],
                    'xi' : pos[0,:], # invalid channels are set to np.nan
                    'yi' : pos[1,:], # invalid channels are set to np.nan
                    'zi' : pos[2,:], # invalid channels are set to np.nan
                    'channels' : [str(_) for _ in range(nmics_total)],
                    'alpha' : np.ones(nmics_total),
                    **optional_items
                    })        
        else:
            self.cdsource.data = {
                'x':[],'y':[], 'z':[], 'xi' : [], 'yi' : [], 'zi' : [],'channels':[], **optional_items}   


class BeamformerPresenter(BasePresenter):
    """
    This class provides data for visualization of beamformed data.
    
    The data of its ColumnDataSource fits to Bokeh's image glyph.
    """
    
    #: Data source; :class:`~acoular.fbeamform.BeamformerBase` or derived object.
    source = Trait(BeamformerBase)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = Instance(ColumnDataSource, kw={'data':{
        'bfdata':[],'x':[],'y':[],'pdata':[],'dw':[],'dh':[]}})

    #: Trait to set the width of the frequency bands considered.
    #: defaults to 0 (single frequency line).
    num = Int(0, 
              desc="Controls the width of the frequency bands considered;\
              defaults to 0 (single frequency line).")

    #: Trait to set the band center frequency to be considered.
    freq = Float(None,
                 desc="Band center frequency. ")
    
    trait_widget_mapper = {'num': NumericInput,
                           'freq': NumericInput,
                       }

    trait_widget_args = {'num': {'disabled':False},
                         'freq': {'disabled':False},
                     }

    @observe("source.digest, freq, num")
    def _auto_update(self, event):
        if self.auto_update:
            self.update()

    def update(self, **optional_items):
        """
        Function that updates the keys and values of :attr:`cdsource` attribute.    
        
        Returns
        -------
        None.

        """
        res = self.source.synthetic(float(self.freq), int(self.num))
        if res.size > 0: 
            dx = self.source.steer.grid.x_max-self.source.steer.grid.x_min
            dy = self.source.steer.grid.y_max-self.source.steer.grid.y_min
            self.cdsource.data = {'bfdata' : [L_p(res).T], 'pdata' : [(res).T], 
            'x':[self.source.steer.grid.x_min], 
            'y':[self.source.steer.grid.y_min], 
            'dw':[dx], 
            'dh':[dy],
            **optional_items
            }


class PointSpreadFunctionPresenter(BasePresenter):
    
    #: Data source; :class:`~acoular.fbeamform.PointSpreadFunction` or derived object.
    source = Trait(PointSpreadFunction)
    
        #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = Instance(ColumnDataSource, kw={'data':{
        'psf':[],'x':[],'y':[],'dw':[],'dh':[]}})

    @observe("source.digest, source.freq, source.grid_indices")
    def _auto_update(self, event):
        if self.auto_update:
            self.update()

    def update(self, **optional_items):
        """
        Function that updates the keys and values of :attr:`cdsource` attribute.    
        
        Returns
        -------
        None.

        """
        psf = self.source.psf
        data = L_p(psf.reshape(self.source.steer.grid.shape)).T
        data -= data.max()
        dx = self.source.steer.grid.x_max-self.source.steer.grid.x_min
        dy = self.source.steer.grid.y_max-self.source.steer.grid.y_min
        self.cdsource.data = {'psf' : [data],
        'x':[self.source.steer.grid.x_min], 
        'y':[self.source.steer.grid.y_min], 
        'dw':[dx], 
        'dh':[dy],
        **optional_items
        }            
        

class TimeSamplesPresenter(BasePresenter):
    """
    This class implements methods to select channel data for visualization.
    
    The data of its ColumnDataSource fits bokehs MultiLine Glyph.
   
    Example: 
                
        >>>    import spectacoular
        >>>    ts = spectacoular.TimeSamples(file='/path/to/file.h5')
        >>>    tv = spectacoular.TimeSamplesPresenter(source=ts)  
        >>>    
        >>>    tsPlot = figure(title="Channel Data") 
        >>>    tsPlot.multi_line(xs='xs', ys='ys',source=tv.cdsource)
        
    """
        
    #: Data source; :class:`~acoular.sources.TimeSamples` or derived object.
    source = Trait(TimeSamples)
    
    #: ColumnDataSource that holds data that can be consumed by plots and glyphs
    cdsource = Instance(ColumnDataSource, kw={'data':{
        'xs':[],'ys':[],'ch':[]}})
    
    #: Indices of channel to be considered for updating of ColumnDataSource 
    channels = List(int)
    
    # Number of samples to appear in the plot, best practice is to use the width of the plot
    _numsubsamples = Int(-1)
    
    trait_widget_mapper = {'channels': DataTable,
                       }

    trait_widget_args = {'channels': {'disabled':False},
                     }

    def update(self, **optional_items):
        """
        Function that updates the keys and values of :attr:`cdsource` attribute.    
        
        Returns
        -------
        None.

        """
        numSelected = len(self.channels)

        
        if isinstance(self.source,MaskedTimeSamples):
            start = self.source.start
            stop = self.source.stop
        else:
            start = 0
            stop = None
        
        plotlen = self._numsubsamples 
        if plotlen>0 and plotlen < self.source.num_samples:
            used_samples = self.source.num_samples//plotlen * plotlen
            newstop = start + used_samples
            sigraw = self.source.data[start:newstop,self.channels].reshape(plotlen,-1, numSelected)
            sig = np.reshape(np.array([sigraw.min(1), sigraw.max(1)]), (2*plotlen, numSelected), order='F') # use min/max of each plot block
            samples = list(np.linspace(start, newstop, 2*plotlen))
            #sig = sigraw[:,0,:] # only use first sample
            #samples = list(np.linspace(start, newstop, plotlen))
        else:
            samples = list(range(0,self.source.num_samples))
            sig = self.source.data[start:stop,self.channels]
        
        ys = [list(_) for _ in sig.T]
        xs = [samples for _ in range(numSelected)]
        if self.source.num_samples > 0 and numSelected > 0:
            self.cdsource.data = {'xs' : xs, 
                                  'ys' : ys,
                                  'ch' : [[c] for c in self.channels],
                                  **optional_items}
        else:
            self.cdsource.data = {'xs' :[],'ys' :[], 'ch':[], **optional_items}
