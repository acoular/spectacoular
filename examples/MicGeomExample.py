# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
import os
from os import path
import acoular
from bokeh.layouts import column, row,widgetbox
from bokeh.models.widgets import Panel,Tabs, Select, Toggle, Slider
from bokeh.models import LogColorMapper, ColorBar, PointDrawTool
from bokeh.plotting import figure
from bokeh.palettes import viridis
from bokeh.server.server import Server
from spectacoular import MicGeom, SteeringVector, RectGrid, PointSpreadFunction,\
PointSpreadFunctionPresenter
from pylab import ravel_multi_index, array

acoular.config.global_caching = 'none' # no result cachings
PALETTE = viridis(100)

# define selectable microphone geometries
micgeofiles = path.join( path.split(acoular.__file__)[0],'xml')
options = [path.join(micgeofiles,name) for name in os.listdir(micgeofiles)]
options.append('')

# build processing chain
mg = MicGeom(from_file=options[0])
rg = RectGrid(x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5, z=.5,increment=0.01)
st = SteeringVector(mics = mg, grid = rg)
psf = PointSpreadFunction(steer=st,freq=1000.0)
psfPresenter = PointSpreadFunctionPresenter(source=psf)
           
# create Select widget to choose Microphone Geometry
micGeomSelect = Select(title='Geometry',value=options[0],options=options) 
# create Slider widget to choose Frequency of PSF
psfFreqSlider = Slider(title='Frequency [Hz]',value=1000.0, start=10.0, end=20000.0)

# get widgets from acoular objects                      
mgWidgets = mg.get_widgets()
mg.set_widgets(**{'from_file':micGeomSelect}) # set from file attribute with select widget
mgWidgets['from_file'] = micGeomSelect
rgWidgets = rg.get_widgets()
stWidgets = st.get_widgets()
psfWidgets = psf.get_widgets()
psf.set_widgets(**{'freq':psfFreqSlider}) # set from file attribute with select widget

# create Button to trigger PSF calculation
calcButton = Toggle(label="Calculate PSF",button_type="success")
def calc(arg):
    if arg:
        calcButton.label = 'Calculating ...'
        source_pos = (0,0,rg.z) #(x,y,z), will be snapped to grid
        grid_index = array([ravel_multi_index(rg.index(*source_pos[:2]), rg.shape)])
        psf.grid_indices = grid_index
        psfPresenter.update()
        calcButton.active = False
        calcButton.label = 'Calculate'
    if not arg:
        calcButton.label = 'Calculate'
calcButton.on_click(calc)

# calculate psf on change of:
psf_update = lambda attr, old, new: psfPresenter.update()        
psfFreqSlider.on_change('value',psf_update) # change psf plot when frequency changes
# mgWidgets['mpos_tot'].source.on_change('data',psf_update)

def server_doc(doc):
    #MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', 
                    tools = 'pan,wheel_zoom,reset,lasso_select',
                    match_aspect=True,)
    micRenderer = mgPlot.circle_cross(x='x',y='y',size=10,fill_alpha=0.2,
                                      source=mgWidgets['mpos_tot'].source)
    drawtool = PointDrawTool(renderers=[micRenderer])
    mgPlot.add_tools(drawtool)
    mgPlot.toolbar.active_tap = drawtool
    
    # PSF Plot
    # Tooltips for additional information
    PSF_TOOLTIPS = [
        ("Level [dB]", "@psf"),
    ("(x,y)", "($x, $y)"),]
    psfPlot = figure(title='Point-Spread Function', tools = 'pan,wheel_zoom,reset',
                     tooltips=PSF_TOOLTIPS,match_aspect=True)
    psfPlot.x_range.range_padding = psfPlot.y_range.range_padding = 0
    cm = LogColorMapper(low=74, high=94,palette=PALETTE)
    psfPlot.image(image='psf', x='x', y='y', dw='dw', dh='dh',
                 source=psfPresenter.cdsource, color_mapper=cm)
    psfPlot.add_layout(ColorBar(color_mapper=cm,location=(0,0),title="Level [dB]",\
                                title_standoff=10),'right')
                        
    ### CREATE LAYOUT ### 
    # Tabs
    mgTab = Panel(child=column(*mgWidgets.values()),title='Microphone Geometry')
    psfTab = Panel(child=column(*psfWidgets.values()),title='Point-Spread Function')
    gridTab = Panel(child=column(*rgWidgets.values()),title='Grid')
    stTab = Panel(child=column(*stWidgets.values()),title='Steering')
    ControlTabs = Tabs(tabs=[mgTab,psfTab,gridTab,stTab],width=500)

    # make Document
    doc.add_root(row(mgPlot,psfPlot,widgetbox(
        calcButton,psfFreqSlider,ControlTabs,width=500)))
    
server = Server({'/': server_doc}, num_procs=1)
server.start()

if __name__ == '__main__':
    print('Opening Microphone Geometry application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()