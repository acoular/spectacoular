# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements processing in the time domain.

.. autosummary::
    :toctree: generated/

    BasePresenter
    TimeSamplesPresenter
    MicGeomPresenter
    BeamformerPresenter
"""

from bokeh.layouts import column, row
from bokeh.palettes import viridis, plasma, inferno, magma
from bokeh.models.widgets import MultiSelect, TextInput, Button, RangeSlider,\
CheckboxGroup, Select, Dropdown, Toggle
from bokeh.models import ColumnDataSource, LogColorMapper, ColorBar
from traits.api import Trait, HasPrivateTraits, Property, \
cached_property, on_trait_change, List, Instance
import numpy as np
from acoular.internal import digest
from acoular import TimeSamples,BeamformerBase, L_p, MicGeom, Grid

from .controller import SingleChannelController, MultiChannelController
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
    cdsource = Trait(ColumnDataSource)

    # internal identifier
    digest = Property( depends_on = ['source.digest'])

    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(data={})
        HasPrivateTraits.__init__(self,*args,**kwargs)
        self._widgets = []

    @cached_property
    def _get_digest( self ):
        return digest(self) 

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
    
    tooltips = [("(x,y)", "($x, $y)")]

    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(data={'x':[],'y':[], 'channels':[]})
        HasPrivateTraits.__init__(self,*args,**kwargs)

    @on_trait_change("digest")
    def _update(self):
        print("update micgeom")
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
    
    #: :class:`~acoular.grids.Grid`-derived object that provides the grid locations.
    grid = Trait(Grid, 
        desc="beamforming grid")
    
    #: TextInput widget to set the width of the frequency bands considered.
    #: defaults to 0 (single frequency line).
    num = TextInput(title="Frequency Band Width:", value='0')

    #: TextInput widget to set the band center frequency to be considered.
    freqInput = TextInput(title="Center Frequency:", value='1000')
    
    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(
                data = {'bfdata':[],'x':[],'y':[],'dw':[],'dh':[]} )
        HasPrivateTraits.__init__(self,*args,**kwargs)
        self._widgets = [self.num,self.freqInput]

    @cached_property
    def _get_digest( self ):
        return digest(self) 

    def update(self):
        res = self.source.synthetic(float(self.freqInput.value), int(self.num.value))
        if res.size > 0: 
            dx = self.grid.x_max-self.grid.x_min
            dy = self.grid.y_max-self.grid.y_min
            self.cdsource.data = {'bfdata' : [L_p(res).T],
            'x':[self.grid.x_min], 
            'y':[self.grid.y_min], 
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
        >>>    tsPlot.multi_line(xs='xs', ys='ys',color='color',source=tv.cdsource)
        
    """

    #: Data source; :class:`~acoular.sources.TimeSamples` or derived object.
    source = Trait(TimeSamples)
    
    #: Select channel controller; :class:`~spectacoular.controller.SingleChannelController` or derived object.
    controller = Instance(SingleChannelController, MultiChannelController)
    
    #: RangeSlider widget to control the amount of samples to be plotted
    samplesRange = RangeSlider(start=0, end=1, value=(0,1), step=1, 
                               title="Show Samples:")

    #: button widget that applies the users selection on click
    applyButton = Button(label="Plot Time Data", button_type="success")

    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(data={'xs':[],'ys':[],'color':[]})
        HasPrivateTraits.__init__(self,*args,**kwargs)
        self.applyButton.on_click(self.update)
        self._widgets = [self.samplesRange,self.applyButton]

    @on_trait_change('source, controller')
    def pass_source(self):
        self.controller.source = self.source

    @on_trait_change("source.numsamples")
    def change_samplesRange(self):
        if not self.source.numsamples == 0:
            self.samplesRange.end = self.source.numsamples
            self.samplesRange.value = (0,self.source.numsamples)
        else:
            self.samplesRange.end = 1
            self.samplesRange.value = (0,1)

    def _get_srange(self):
        i1 = int(self.samplesRange.value[0])
        if hasattr(self.source,'start'): i1 += self.source.start
        i2 = i1+int(self.samplesRange.value[1])
        return (i1,i2)

    def update(self):
        sRange = self._get_srange()
        samples = list(range(sRange[0],sRange[1]))
        if not isinstance(self.controller,MultiChannelController): # if SingleChannelController
            if self.controller.selectChannel.value: 
                numSelected = 1
                colors = [self.controller.colorSelector.children[0].value]
                ys = [list(self.source.data[sRange[0]:sRange[1],int(
                        self.controller.selectChannel.value)])] 
                xs = [samples]
            else: 
                numSelected = 0
                colors = []
                ys = []
                xs = []
        else: # if MultiCannelController
            numSelected = len(self.controller.selectChannel.value)
            colors = [c.value for c in self.controller.colorSelector.children[0].children]
            ys = [list(self.source.data[sRange[0]:sRange[1],int(idx)]) 
                            for idx in self.controller.selectChannel.value]
            xs = [samples for _ in range(numSelected)]
        if self.source.numsamples > 0 and numSelected > 0:
            self.cdsource.data = {'xs' : xs, 'ys' : ys, 'color':colors }
        else:
            self.cdsource.data = {'xs' :[],'ys' :[], 'colors':[]}

