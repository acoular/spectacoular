#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
import acoular as ac
from pathlib import Path
import spectacoular as sp
import numpy as np 

# bokeh imports
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import TabPanel as Panel, Tabs, Spacer
from bokeh.models.widgets import Slider, NumberEditor, TableColumn, NumberFormatter
from bokeh.models import LinearColorMapper, ColorBar, PointDrawTool, ColumnDataSource
from bokeh.events import Reset
from bokeh.plotting import figure
from bokeh.palettes import Viridis256 
from bokeh.server.server import Server


ac.config.global_caching = 'none' # no result cachings
TAB_WIDTH = 600  

# build processing chain
mg = sp.MicGeom(file=Path(ac.__file__).parent / 'xml' / 'tub_vogel64.xml')
rg = sp.RectGrid(x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5, z=.5,increment=0.02)
st = sp.SteeringVector(mics = mg, grid = rg, ref=1.0)
psf = sp.PointSpreadFunction(steer=st,freq=2000.0,grid_indices=np.array([1300]))
psf.psf # precalc
psf_presenter = sp.PointSpreadFunctionPresenter(auto_update=True)
psf_presenter.source = psf

mgp = sp.MicGeomPresenter(source=mg, auto_update=True)
mgp.update()

#%% server document          

def server_doc(doc):

    # Microphone Geometry Plot
    mic_layout = sp.layouts.MicGeomComponent(
        figure=figure(title='Microphone Geometry', 
                    tools = 'pan,wheel_zoom,reset,lasso_select',frame_width=500, frame_height=500),
        allow_point_draw=True, presenter=mgp)

    # set up widgets for Microphone Geometry
    editor = NumberEditor()
    formatter = NumberFormatter(format="0.00")
    mpos_columns = [TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
                    TableColumn(field='y', title='x/m', editor=editor, formatter=formatter),
                    TableColumn(field='z', title='x/m', editor=editor, formatter=formatter)]
    mic_layout.mics_trait_widget_args.update(
        {'pos_total':  {'height' : 280, 'editable':True, 'transposed':True, 'columns':mpos_columns,}}
    )

    def update(attr,old,new):
        psf_presenter.update()
    mic_layout.presenter.cdsource.on_change('data', update) # automatically re-calc if set  

    # create Slider widget to choose Frequency of PSF
    psfFreqSlider = Slider(title='Frequency [Hz]',value=psf.freq, start=10.0, end=20000.0)
    psf.set_widgets(**{'freq':psfFreqSlider}) # set from file attribute with select widget

    # location for which the PSF is calculated
    src_pos = ColumnDataSource(data={'x':[0],'y':[0]}) 
    def change_pos(attr, old, new):
        source_pos = (src_pos.data['x'][0],src_pos.data['y'][0],rg.z) #(x,y,z), will be snapped to grid
        grid_index = np.array([np.ravel_multi_index(rg.index(*source_pos[:2]), rg.shape)])
        psf.grid_indices = grid_index
    src_pos.on_change('data', change_pos) # automatically re-calc if set
    rg.on_trait_change(change_pos, 'digest') # automatically re-calc if set 



    #%% PSF Plot

    psf_figure = figure(title='Point-Spread Function', tools = 'pan,wheel_zoom,reset',
                    tooltips=[("Lp/dB", "@psf"),("(x,y)", "($x, $y)")],
                    frame_width=500, frame_height=500)
    psf_figure.toolbar.logo=None
    psf_figure.x_range.range_padding = psf_figure.y_range.range_padding = 0
    cm = LinearColorMapper(low=-20, high=0,palette=Viridis256, low_color= '#f6f6f6')
    psf_figure.image(image='psf', x='x', y='y', dw='dw', dh='dh',
                source=psf_presenter.cdsource, color_mapper=cm)
    psf_figure.add_layout(ColorBar(color_mapper=cm,location=(0,0),title="Lp/dB",\
                                title_standoff=5,
                                background_fill_color = '#f6f6f6'),'right')

    srcRenderer = psf_figure.scatter(marker='cross', x='x',y='y',size=10, fill_alpha=.8, source=src_pos)
    marktool = PointDrawTool(renderers=[srcRenderer], num_objects=1)
    psf_figure.add_tools(marktool)
    psf_figure.toolbar.active_tap = marktool

    def resetpos(event):
        src_pos.data={'x':[0],'y':[0]}
    psf_figure.on_event(Reset, resetpos)


#%% App layout

    # Microphone Geometry Tab
    mgTab = Panel(
        child=layout([
            [mic_layout.widgets['file']],
            [mic_layout.widgets['num_mics']],
            [mic_layout.widgets['invalid_channels']],
            [Spacer(width=400, height=10)],
            [mic_layout.widgets['pos_total']],
        ], width=TAB_WIDTH),
        title='Microphone Geometry'
    )

    # Point-Spread Function Tab
    psfTab = Panel(
        child=layout([list(psf.get_widgets().values())]),
        title='Point-Spread Function'
    )

    # Grid Tab
    rgWidgets = rg.get_widgets()
    gridTab = Panel(
        child=layout([
            [rgWidgets['x_min'], rgWidgets['x_max']],
            [rgWidgets['y_min'], rgWidgets['y_max']],
            [rgWidgets['z'], rgWidgets['increment']],
            [rgWidgets['nxsteps'], rgWidgets['nysteps']],
        ], width=TAB_WIDTH),
        title='Grid'
    )

    # Steering Tab
    stTab = Panel(
        child=layout([list(st.get_widgets().values())]),
        title='Steering'
    )

    # Control Panel with Tabs
    control = layout([
        [Spacer(width=400, height=10)],
        [psfFreqSlider],
        [Tabs(tabs=[mgTab, gridTab, psfTab, stTab])]
    ], width=TAB_WIDTH)

    # Overall Layout
    layout_dom = layout([
        [mic_layout.figure, psf_figure, control]
    ])

    doc.add_root(layout_dom)
    doc.title = "MicGeomExample"

doc = curdoc()
server_doc(doc)

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

