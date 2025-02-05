#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
import acoular as ac
from pathlib import Path
import spectacoular as sp
import numpy as np 

# bokeh imports
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TabPanel as Panel, Tabs, Spacer
from bokeh.models.widgets import Select, Slider, NumberEditor, DataTable, TableColumn, NumberFormatter
from bokeh.models import LinearColorMapper, ColorBar, PointDrawTool, ColumnDataSource
from bokeh.events import Reset
from bokeh.plotting import figure
from bokeh.palettes import Viridis256 
from bokeh.server.server import Server


ac.config.global_caching = 'none' # no result cachings
PALETTE = Viridis256
# define selectable microphone geometries
mfiles = [str(file) for file in (Path(ac.__file__).parent / 'xml').glob('*')]

#%%

# build processing chain
mg = sp.MicGeom(file=mfiles[0])
rg = sp.RectGrid(x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5, z=.5,increment=0.02)
st = sp.SteeringVector(mics = mg, grid = rg, ref=1.0)
psf = sp.PointSpreadFunction(steer=st,freq=8000.0,grid_indices=np.array([1300]))
psf.psf # precalc
psf_presenter = sp.PointSpreadFunctionPresenter(auto_update=True)
psf_presenter.source = psf

#%%           

# make Document
def server_doc(doc):

    # create Select widget to choose Microphone Geometry
    micGeomSelect = Select(title='Geometry',value=mfiles[0],options=mfiles) 
    # create Slider widget to choose Frequency of PSF
    psfFreqSlider = Slider(title='Frequency [Hz]',value=psf.freq, start=10.0, end=20000.0)

    # get widgets from acoular objects                      
    mgWidgets = mg.get_widgets()
    mg.set_widgets(**{'file':micGeomSelect}) # set from file attribute with select widget
    mgWidgets['file'] = micGeomSelect
    rgWidgets = rg.get_widgets()
    stWidgets = st.get_widgets()
    psfWidgets = psf.get_widgets()
    psf.set_widgets(**{'freq':psfFreqSlider}) # set from file attribute with select widget

    # position table
    editor = NumberEditor()
    formatter = NumberFormatter(format="0.00")
    mpos_columns = [TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
                    TableColumn(field='y', title='x/m', editor=editor, formatter=formatter),
                    TableColumn(field='z', title='x/m', editor=editor, formatter=formatter)]
    trait_widget_mapper = {'pos_total': DataTable}
    trait_widget_args = {'pos_total':  {'editable':True, 'transposed':True, 'columns':mpos_columns,}}
    pos_total_table = mg.get_widgets(trait_widget_mapper=trait_widget_mapper, trait_widget_args=trait_widget_args)['pos_total']

    # location for which the PSF is calculated
    src_pos = ColumnDataSource(data={'x':[0],'y':[0]}) 
    def change_pos(attr, old, new):
        source_pos = (src_pos.data['x'][0],src_pos.data['y'][0],rg.z) #(x,y,z), will be snapped to grid
        grid_index = np.array([np.ravel_multi_index(rg.index(*source_pos[:2]), rg.shape)])
        psf.grid_indices = grid_index
    src_pos.on_change('data', change_pos) # automatically re-calc if set  


    #%% MicGeomPlot
    mgPlot = figure(title='Microphone Geometry', 
                    tools = 'pan,wheel_zoom,reset,lasso_select',
                    frame_width=500, frame_height=500)
    mgPlot.toolbar.logo=None
    micRenderer = mgPlot.scatter(marker='circle_cross', x='x',y='y',size=20,fill_alpha=.8,
                                    source=pos_total_table.source)
    drawtool = PointDrawTool(renderers=[micRenderer],empty_value=0.) 
    # empty_value: a value of 0. is inserted for the third column (z-axis) when
    # new points/mics are added to the geometry
    mgPlot.add_tools(drawtool)
    mgPlot.toolbar.active_tap = drawtool

    def update(attr,old,new):
        psf_presenter.update()
    pos_total_table.source.on_change('data', update) # automatically re-calc if set  


    #%% PSF Plot

    # Tooltips for additional information
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
                source=psf_presenter.cdsource, color_mapper=cm)
    psfPlot.add_layout(ColorBar(color_mapper=cm,location=(0,0),title="Lp/dB",\
                                title_standoff=5,
                                background_fill_color = '#f6f6f6'),'right')

    srcRenderer = psfPlot.scatter(marker='cross', x='x',y='y',size=10, fill_alpha=.8, source=src_pos)
    marktool = PointDrawTool(renderers=[srcRenderer], num_objects=1)
    psfPlot.add_tools(marktool)
    psfPlot.toolbar.active_tap = marktool

    def resetpos(event):
        src_pos.data={'x':[0],'y':[0]}
    psfPlot.on_event(Reset, resetpos)


    #%% CREATE LAYOUT ### 

    # Tabs
    twidth = 600

    pos_total_table.height = 280
    mgTab = Panel(child=column(mgWidgets['file'],
                            row(mgWidgets['num_mics'],width = twidth),
                            Spacer(width=400, height=10),
                            pos_total_table, 
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
    ControlTabs = Tabs(tabs=[
        mgTab,gridTab,psfTab,stTab])
        

    ControlBox = column(Spacer(width=400, height=10),
            row(psfFreqSlider,width=600,height=80),
            ControlTabs,
            width=400)
        
    layout = row(
            Spacer(width=10, height=1000),
            mgPlot,psfPlot,
            Spacer(width=10, height=1000),
            ControlBox
            )

    doc.add_root(layout)
    doc.title = "MicGeomExample"

doc = curdoc()
server_doc(doc)

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

