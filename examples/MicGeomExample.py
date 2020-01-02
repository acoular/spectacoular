# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
import os
from os import path
import acoular
from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs, Select, Toggle
from bokeh.models import LogColorMapper, ColorBar, PointDrawTool
from bokeh.plotting import figure
from bokeh.palettes import viridis
from bokeh.server.server import Server
from spectacoular import MicGeom, SteeringVector, RectGrid, PointSpreadFunction,\
PointSpreadFunctionPresenter
from pylab import ravel_multi_index, array

acoular.config.global_caching = 'none' # no result cachings

micgeofiles = path.join( path.split(acoular.__file__)[0],'xml')
options = [path.join(micgeofiles,name) for name in os.listdir(micgeofiles)]
options.append('')

# build processing chain
mg = MicGeom(from_file=options[0])
rg = RectGrid(x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5, z=.5,increment=0.01)
st = SteeringVector(mics = mg, grid = rg)
psf = PointSpreadFunction(steer=st,freq=1000.0)
psfPresenter = PointSpreadFunctionPresenter(source=psf)
           
# get widgets                       
mg.trait_widget_mapper['from_file'] = Select # Replace TextInput with Select Widget
mgWidgets = mg.get_widgets()
mgWidgets[0].options = options # add options to Select File Widget
rgWidgets = rg.get_widgets()
stWidgets = st.get_widgets()
psfWidgets = psf.get_widgets()

# Tooltips for additional information
PSF_TOOLTIPS = [
    ("Level", "@psf"),
("(x,y)", "($x, $y)"),]

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

def server_doc(doc):
    #MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', 
                    tools = 'pan,wheel_zoom,reset,lasso_select',
                    match_aspect=True,)
    micRenderer = mgPlot.circle_cross(x='x',y='y',size=10,fill_alpha=0.2,
                                      source=mgWidgets[-1].source)
    drawtool = PointDrawTool(renderers=[micRenderer])
    mgPlot.add_tools(drawtool)
    mgPlot.toolbar.active_tap = drawtool
    
    # PSF Plot
    psfPlot = figure(title='Point-Spread Function', tools = 'pan,wheel_zoom,reset',
                     tooltips=PSF_TOOLTIPS,match_aspect=True, )
    cm = LogColorMapper(low=74, high=94,palette=viridis(100))
    psfPlot.image(image='psf', x='x', y='y', dw='dw', dh='dh',
                 source=psfPresenter.cdsource, color_mapper=cm)
    psfPlot.add_layout(ColorBar(color_mapper=cm),
                        'right')
    ### CREATE LAYOUT ### 
    # Tabs
    mgTab = Panel(child=column(*mgWidgets),title='Microphone Geometry')
    psfTab = Panel(child=column(*psfWidgets),title='Point-Spread Function')
    gridTab = Panel(child=column(*rgWidgets),title='Grid')
    stTab = Panel(child=column(*stWidgets),title='Steering')
    ControlTabs = Tabs(tabs=[mgTab,psfTab,gridTab,stTab],width=850)

    # make Document
    doc.add_root(row(mgPlot,psfPlot,column(calcButton,ControlTabs)))

server = Server({'/': server_doc}, num_procs=1,port=5101)
server.start()

if __name__ == '__main__':
    print('Opening Microphone Geometry application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
