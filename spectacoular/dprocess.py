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
CheckboxGroup, Select, Dropdown
from bokeh.models import ColumnDataSource, LogColorMapper, ColorBar
from traits.api import Trait, HasPrivateTraits, Property, \
cached_property, on_trait_change, List
import numpy as np
from acoular.internal import digest
from acoular import TimeSamples,BeamformerBase, L_p, MicGeom

colorPaletteMapper = {"Viridis":viridis,
                      "Plasma":plasma,
                      "Inferno":inferno,
                      "Magma":magma}

colorPalettes = ["Viridis","Plasma","Inferno","Magma"]


class BaseSpectacoular(HasPrivateTraits):
    

    # shadow trait that holds a list of widgets that belong to the class
    _widgets = List()

    def get_widgets(self):
        """ 
        Function to access the widgets of this class.
        
        Returns
        -------
        A list of interactive control elements (widgets)
        No output since `BasePresenter` only represents a base class to derive
        other classes from.
        """
        return self._widgets


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
    
    #: MultiSelect widget to select one or multiple channels to be plotted
    selectChannel = MultiSelect(title="Select Channel:", value=[]) 
    
    #: RangeSlider widget to control the amount of samples to be plotted
    samplesRange = RangeSlider(start=0, end=1, value=(0,1), step=1, 
                               title="Show Samples:")

    #: button widget that applies the users selection on click
    applyButton = Button(label="Plot Time Data", button_type="success")

    # read only property. Holds Select color widgets of selected channels    
    colorSelector = column(column())
    
    #: a list of possible colors that can be assigned to selected channels
    lineColors = List(viridis(10))
    
    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(data={'xs':[],'ys':[],'color':[]})
        HasPrivateTraits.__init__(self,*args,**kwargs)
        self.selectChannel.on_change('value',self.change_color_select)
        self.applyButton.on_click(self.update)
        self._widgets = [self.selectChannel,self.samplesRange,self.applyButton,
                         self.colorSelector]

    def change_color_select(self,attr,old,new):
        wlistOld = self.colorSelector.children[0].children[:]
        wTitlesOld = [w.title for w in wlistOld]
        wlist = []
        for idx in self.selectChannel.value:
            titel = "Channel {} Color:".format(idx)
            if titel in wTitlesOld: 
                wlist.append(wlistOld[wTitlesOld.index(titel)])
            else:
                wlist.append(
                Select(title=titel, value=self.lineColors[0], options=self.lineColors) 
                        )
        self.colorSelector.children[0] = column(wlist)

    @on_trait_change("source.numsamples")
    def change_samplesRange(self):
        if not self.source.numsamples == 0:
            self.samplesRange.end = self.source.numsamples
        if self.samplesRange.value[1] > self.source.numsamples:
            self.samplesRange.value = (self.samplesRange.value[0],self.source.numsamples)

    @on_trait_change("digest")
    def change_channel_selector(self):
        channels = [idx for idx in range(self.source.numchannels)]
        if hasattr(self.source,'invalid_channels'):
            [channels.remove(idx) for idx in self.source.invalid_channels]
        self.selectChannel.options = [(str(ch),str(ch)) for ch in channels]

    def _get_srange(self):
        i1 = int(self.samplesRange.value[0])
        if hasattr(self.source,'start'): i1 += self.source.start
        i2 = i1+int(self.samplesRange.value[1])
        return (i1,i2)

    def update(self):
        numSelected = len(self.selectChannel.value)
        sRange = self._get_srange()
        colors = [c.value for c in self.colorSelector.children[0].children]
        if self.source.numsamples > 0 and numSelected > 0:
            samples = list(range(sRange[0],sRange[1]))
            self.cdsource.data = {
                'xs' : [samples for _ in range(numSelected)],
                'ys' : [list(self.source.data[sRange[0]:sRange[1],int(idx)]) 
                            for idx in self.selectChannel.value],
                'color':colors
                }
        else:
            self.cdsource.data = {'xs' :[],'ys' :[], 'colors':[]}


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
   
    Example: 
                
        >>>    import spectacoular
        >>>    mg = MicGeom(from_file='/path/to/file.xml')
        >>>    mv = MicGeomPresenter(source=mg)
        >>>    
        >>>    mgPlot = figure(title='Microphone Geometry')
        >>>    mgPlot.circle(x='x',y='y',source=mv.cdsource)
    """
    
    #: Data source; :class:`~acoular.fbeamform.BeamformerBase` or derived object.
    source = Trait(BeamformerBase)
    
    #: TextInput widget to set the width of the frequency bands considered.
    #: defaults to 0 (single frequency line).
    num = TextInput(title="Frequency Band Width:", value='0')

    #: TextInput widget to set the band center frequency to be considered.
    freqInput = TextInput(title="Center Frequency:", value='1000')
    
    #: button widget that triggers beamformer calculation
    syntheticButton = Button(label='Calculate Beamforming Result')

#    checkbox_autolevel_mode = CheckboxGroup(labels=["auto level mode"], active=[])

    def __init__(self,*args,**kwargs):
        self.cdsource = ColumnDataSource(
                data = {'bfdata':[],'x':[],'y':[],'dw':[],'dh':[]} )
        HasPrivateTraits.__init__(self,*args,**kwargs)
        self._widgets = [self.num,self.freqInput,self.syntheticButton]
        self.syntheticButton.on_click(self.update)

    @cached_property
    def _get_digest( self ):
        return digest(self) 

    def update(self):
        res = self.source.synthetic(float(self.freqInput.value), int(self.num.value))
        if res.size > 0: 
            dx = self.source.grid.x_max-self.source.grid.x_min
            dy = self.source.grid.y_max-self.source.grid.y_min
            self.cdsource.data = {'bfdata' : [L_p(res).T],
            'x':[self.source.grid.x_min], 
            'y':[self.source.grid.y_min], 
            'dw':[dx], 
            'dh':[dy]
            }
            


class ColorMapperController(BaseSpectacoular):
    
    #: RangeSlider widget to adjust displayed dynamic of a source map plot
    dynamicSlider = RangeSlider(start=0, end=160, step=.5, value=(30,90),
                                title="Dynamic Range")

    #: colorMapper 
    colorMapper =  LogColorMapper(palette=viridis(100), 
                                  low=30, high=90 ,low_color=(1,1,1,0))

    #: number of colors to be used by the color mapper
    numColors = TextInput(title="Number of Colors:", value='100')

    #: Dropdown widget to choose color palette
    palette = Select(title="Option:", value="Viridis", options=colorPalettes)

    colorBar = ColorBar()
    
    def __init__(self):
        self._widgets = [self.dynamicSlider,self.numColors,self.palette]
        self.dynamicSlider.value = (self.colorMapper.low,self.colorMapper.high)
        self.dynamicSlider.on_change('value', self.dynamicSlider_callback)   
        self.numColors.on_change('value', self.change_colors_callback)
        self.palette.on_change('value',self.change_colors_callback)
        self.colorBar.color_mapper = self.colorMapper

    def dynamicSlider_callback(self, attr, old, new):
        (self.colorMapper.low, self.colorMapper.high) = self.dynamicSlider.value

    def change_colors_callback(self, attr, old, new):
        colorMapperMethod = colorPaletteMapper[self.palette.value]
        self.colorMapper.palette = colorMapperMethod(int(self.numColors.value))


        