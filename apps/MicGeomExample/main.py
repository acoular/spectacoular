# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2022, Acoular Development Team.
#------------------------------------------------------------------------------
import os
from os import path
import acoular
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TabPanel as Panel, Tabs
from bokeh.models.widgets import Select, Toggle, Slider
from bokeh.models import LinearColorMapper, ColorBar, PointDrawTool, ColumnDataSource
from bokeh.events import Reset
from bokeh.plotting import figure
from bokeh.palettes import Viridis256 
from bokeh.server.server import Server
from spectacoular import MicGeom, SteeringVector, RectGrid, PointSpreadFunction,\
PointSpreadFunctionPresenter,set_calc_button_callback
from numpy import ravel_multi_index, array
PALETTE = Viridis256

doc = curdoc()
acoular.config.global_caching = 'none' # no result cachings

#%%

# define selectable microphone geometries
micgeofiles = path.join( path.split(acoular.__file__)[0],'xml')
options = [path.join(micgeofiles,name) for name in os.listdir(micgeofiles)]
options.append('')

# build processing chain
mg = MicGeom(from_file=options[0])
rg = RectGrid(x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5, z=.5,increment=0.02)
st = SteeringVector(mics = mg, grid = rg)
psf = PointSpreadFunction(steer=st,freq=1000.0,grid_indices=array([1300]))
psfPresenter = PointSpreadFunctionPresenter(source=psf)

#%%           
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

#%%

# create Button to trigger PSF calculation
def calc():
    source_pos = (src_pos.data['x'][0],src_pos.data['y'][0],rg.z) #(x,y,z), will be snapped to grid
    grid_index = array([ravel_multi_index(rg.index(*source_pos[:2]), rg.shape)])
    psf.grid_indices = grid_index
    psfPresenter.update()
calcButton = Toggle(label="Calculate",button_type="primary")
set_calc_button_callback(calc,calcButton)

# calculate psf on change of:
psf_update = lambda attr, old, new: psfPresenter.update()        
psfFreqSlider.on_change('value',psf_update) # change psf plot when frequency changes

#%% MicGeomPlot
mgPlot = figure(title='Microphone Geometry', 
                tools = 'pan,wheel_zoom,reset,lasso_select',
                frame_width=500, frame_height=500)
mgPlot.toolbar.logo=None
micRenderer = mgPlot.scatter(marker='circle_cross', x='x',y='y',size=20,fill_alpha=.8,
                                  source=mgWidgets['mpos_tot'].source)
drawtool = PointDrawTool(renderers=[micRenderer],empty_value=0.) 
# empty_value: a value of 0. is inserted for the third column (z-axis) when
# new points/mics are added to the geometry
mgPlot.add_tools(drawtool)
mgPlot.toolbar.active_tap = drawtool


#%% PSF Plot
# Tooltips for additional information
psfPresenter.update()

PSF_TOOLTIPS = [
    ("Lp/dB", "@psf"),
    ("(x,y)", "($x, $y)"),]
psfPlot = figure(title='Point-Spread Function', tools = 'pan,wheel_zoom,reset',
                 tooltips=PSF_TOOLTIPS,
                 frame_width=500, frame_height=500)
psfPlot.toolbar.logo=None
psfPlot.x_range.range_padding = psfPlot.y_range.range_padding = 0
cm = LinearColorMapper(low=-20, high=0,palette=PALETTE, low_color= '#f6f6f6')
psfPlot.image(image='psf', x='x', y='y', dw='dw', dh='dh',
             source=psfPresenter.cdsource, color_mapper=cm)
psfPlot.add_layout(ColorBar(color_mapper=cm,location=(0,0),title="Lp/dB",\
                            title_standoff=5,
                            background_fill_color = '#f6f6f6'),'right')

src_pos = ColumnDataSource(data={'x':[0],'y':[0]}) 
src_pos.on_change('data',lambda attr,old,new:calc()) # automatically re-calc if set  
srcRenderer = psfPlot.scatter(marker='cross', x='x',y='y',size=10, fill_alpha=.8, source=src_pos)
marktool = PointDrawTool(renderers=[srcRenderer], num_objects=1)
psfPlot.add_tools(marktool)
psfPlot.toolbar.active_tap = marktool

def resetpos(event):
    src_pos.data={'x':[0],'y':[0]}

psfPlot.on_event(Reset, resetpos)


#%% CREATE LAYOUT ### 
from bokeh.models.widgets import NumberFormatter,Div

vspace = Div(text='',width=10, height=1000) # just for vertical spacing
hspace = Div(text='',width=400, height=10) # just for horizontal spacing
twidth = 600

formatter = NumberFormatter(format="0.00")
for f in mgWidgets['mpos_tot'].columns:
    f.formatter = formatter

# Tabs
mgWidgets['mpos_tot'].height = 280
mgTab = Panel(child=column(mgWidgets['from_file'],
                           row(mgWidgets['num_mics'],width = twidth),
                           hspace,
                          mgWidgets['mpos_tot'],
                          ),
                          title='Microphone Geometry')
psfTab = Panel(child=column(*psfWidgets.values()),
               title='Point-Spread Function')
gridTab = Panel(child=column(
                        row(rgWidgets['x_min'],rgWidgets['x_max'],width = twidth),
                        row(rgWidgets['y_min'],rgWidgets['y_max'],width = twidth),
                        row(rgWidgets['z'],rgWidgets['increment'],width = twidth),
                        row(rgWidgets['nxsteps'],rgWidgets['nysteps'],width = twidth),),
                title='Grid')
stTab = Panel(child=column(*stWidgets.values()),title='Steering')
ControlTabs = Tabs(tabs=[mgTab,gridTab,psfTab,stTab])

ControlBox = column(hspace,
        row(calcButton,psfFreqSlider,width=600,height=80),
        #hspace,
        ControlTabs,width=400)
    
# make Document
def server_doc(doc):
    doc.add_root(row(vspace,mgPlot,psfPlot,vspace,ControlBox))
    doc.title = "MicGeomExample"

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)

