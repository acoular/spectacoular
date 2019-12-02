# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements controller classes to control filter process etc.

.. autosummary::
    :toctree: generated/

    SingleChannelController
    MultiChannelController
    ColorMapperController
"""

from bokeh.layouts import column, row
from bokeh.palettes import viridis, plasma, inferno, magma
from bokeh.models.widgets import MultiSelect, TextInput, Button, RangeSlider,\
CheckboxGroup, Select, Dropdown
from bokeh.models import ColumnDataSource, LogColorMapper, ColorBar
from traits.api import Trait, HasPrivateTraits, Property, \
cached_property, on_trait_change, List
from acoular import SamplesGenerator

from .factory import BaseSpectacoular


colorPaletteMapper = {"Viridis":viridis,
                      "Plasma":plasma,
                      "Inferno":inferno,
                      "Magma":magma}

colorPalettes = ["Viridis","Plasma","Inferno","Magma"]


class SingleChannelController(BaseSpectacoular):
    
    #: Data source; :class:`~acoular.sources.TimeSamples` or derived object.
    source = Trait(SamplesGenerator)
    
    #: MultiSelect widget to select one or multiple channels to be plotted
    selectChannel = Select(title="Select Channel:") 
    
    # read only property. Holds Select color widgets of selected channels    
    colorSelector = column(Select(title="Select Color"))
    
    #: a list of possible colors that can be assigned to selected channels
    lineColors = List(viridis(10))
    
    def __init__(self,*args,**kwargs):
        HasPrivateTraits.__init__(self,*args,**kwargs)
        self.selectChannel.on_change('value',self.change_color_select)
        self._widgets = [self.selectChannel,self.colorSelector]
                         
    @on_trait_change("source.numchannels")
    def change_channel_selector(self):
        channels = [idx for idx in range(self.source.numchannels)]
        channels.insert(0,"") # add no data field
        if hasattr(self.source,'invalid_channels'):
            [channels.remove(idx) for idx in self.source.invalid_channels]
        self.selectChannel.options = [str(ch) for ch in channels]

    def change_color_select(self,attr,old,new):
        titel = "Channel {} Color:".format(self.selectChannel.value)
        self.colorSelector.children[0] = Select(title=titel, value=self.lineColors[0], options=self.lineColors)
                


class MultiChannelController(SingleChannelController):
    
    #: MultiSelect widget to select one or multiple channels to be plotted
    selectChannel = MultiSelect(title="Select Channel:", value=[]) 
    
    # read only property. Holds Select color widgets of selected channels    
    colorSelector = column(column(Select(title="Select Color")))

    @on_trait_change("source.numchannels")
    def change_channel_selector(self):
        channels = [idx for idx in range(self.source.numchannels)]
        if hasattr(self.source,'invalid_channels'):
            [channels.remove(idx) for idx in self.source.invalid_channels]
        self.selectChannel.options = [(str(ch),str(ch)) for ch in channels]

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