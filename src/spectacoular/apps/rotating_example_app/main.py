# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""Example that demonstrates different beamforming algorithms."""

from pathlib import Path

import acoular as ac
import spectacoular as sp

# bokeh imports
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColorBar, LogColorMapper, Tabs
from bokeh.models import TabPanel as Panel
from bokeh.models.widgets import (
    DataTable,
    NumberEditor,
    NumberFormatter,
    RangeSlider,
    Select,
    TableColumn,
    Toggle,
)
from bokeh.palettes import viridis
from bokeh.plotting import figure
from bokeh.server.server import Server

doc = curdoc()
# build processing chain
micgeofile = Path(ac.__file__).parent / 'xml' / 'array_56.xml'
tdfile = Path(__file__).parent / 'rotating_source.h5'
ts = sp.MaskedTimeSamples(file=tdfile)

mg = sp.MicGeom(file=micgeofile)

si = sp.SpatialInterpolatorConstantRotation(source=ts, mics=mg, rotational_speed=15.0, array_dimension='2D')

ps = sp.PowerSpectra(source=si)
rg = sp.RectGrid(x_min=-0.8, x_max=0.8, y_min=-0.8, y_max=0.8, z=1.00, increment=0.05)
env = sp.Environment(c=346.04)
st = sp.SteeringVector(grid=rg, mics=mg, env=env)

# Beamforming Algorithms
bb = sp.BeamformerBase(freq_data=ps, steer=st)
bf = sp.BeamformerFunctional(freq_data=ps, steer=st, gamma=4)
bc = sp.BeamformerCapon(freq_data=ps, steer=st)
be = sp.BeamformerEig(freq_data=ps, steer=st, n=54)
bm = sp.BeamformerMusic(freq_data=ps, steer=st, n=6)
bd = sp.BeamformerDamas(freq_data=ps, n_iter=100)
bdp = sp.BeamformerDamasPlus(freq_data=ps, n_iter=100)
bo = sp.BeamformerOrth(freq_data=ps, eva_list=list(range(38, 54)))
bs = sp.BeamformerCleansc(freq_data=ps, steer=st, r_diag=True)
bl = sp.BeamformerClean(freq_data=ps, n_iter=100)
bcmf = sp.BeamformerCMF(freq_data=ps, steer=st, method='LassoLarsBIC')
bgib = sp.BeamformerGIB(freq_data=ps, steer=st, method='LassoLars', n=10)

beamformer_dict = {
    'Conventional Beamforming': bb,
    'Functional Beamforming': bf,
    'Capon Beamforming': bc,
    'Eigenvalue Beamforming': be,
    'Music Beamforming': bm,
    'Damas Deconvolution': bd,
    'DamasPlus Deconvolution': bdp,
    'Orthogonal Beamforming': bo,
    'CleanSC Deconvolution': bs,
    'Clean Deconvolution': bl,
    'CMF': bcmf,
    'GIB': bgib,
}

# create Select Button to select Beamforming Algorithm
beamformer_selector = Select(
    title='Select Beamforming Method:',
    options=list(beamformer_dict.keys()),
    value=next(iter(beamformer_dict.keys())),
)


# use additional classes for data evaluation/view
bv = sp.BeamformerPresenter(source=bb, num=3, freq=4000.0)

# get widgets to control settings
ts_widgets = ts.get_widgets()
ts_widgets.pop('invalid_channels')
si_widgets = si.get_widgets()
env_widgets = env.get_widgets()
ps_widgets = ps.get_widgets()
rg_widgets = rg.get_widgets()
st_widgets = st.get_widgets()
bb_widgets = bb.get_widgets()
bv_widgets = bv.get_widgets()

# position table
editor = NumberEditor()
formatter = NumberFormatter(format='0.00')
mpos_columns = [
    TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
    TableColumn(field='y', title='x/m', editor=editor, formatter=formatter),
    TableColumn(field='z', title='x/m', editor=editor, formatter=formatter),
]
trait_widget_mapper = {'pos_total': DataTable}
trait_widget_args = {
    'pos_total': {
        'editable': True,
        'transposed': True,
        'columns': mpos_columns,
    }
}
mg_widgets = mg.get_widgets(trait_widget_mapper=trait_widget_mapper, trait_widget_args=trait_widget_args)

color_mapper = LogColorMapper(palette=viridis(100), low=50, high=65, low_color=(1, 1, 1, 0))
dynamic_slider = RangeSlider(start=0, end=120, step=1.0, value=(50, 65), title='Dynamic Range')


def dynamic_slider_callback(_attr, _old, _new):
    """Update the beamforming plot color range."""
    (color_mapper.low, color_mapper.high) = dynamic_slider.value


dynamic_slider.on_change('value', dynamic_slider_callback)

# create Button to trigger beamforming result calculation
calc_button = Toggle(label='Calculate', button_type='primary')
sp.set_calc_button_callback(bv.update, calc_button)

# MicGeomPlot
mg_plot = figure(title='Microphone Geometry', tools='hover,pan,wheel_zoom,reset')
mg_plot.circle(x='x', y='y', radius=1, source=mg_widgets['pos_total'].source)

# beamformerPlot
bf_plot = figure(title='Beamforming Result', tools='pan,wheel_zoom,reset')
bf_plot.image(
    image='bfdata',
    x='x',
    y='y',
    dw='dw',
    dh='dh',
    color_mapper=color_mapper,
    source=bv.cdsource,
)
bf_plot.add_layout(
    ColorBar(color_mapper=color_mapper, location=(0, 0), title='Level [dB]', title_standoff=10),
    'right',
)

# Plot Tabs
mg_plot_tab = Panel(child=row(mg_plot), title='Microphone Geometry Plot')
bf_plot_tab = Panel(child=row(bf_plot), title='Source Plot')
plot_tabs = Tabs(tabs=[mg_plot_tab, bf_plot_tab], width=600)

# Property Tabs
selected_bf_widgets = column(*bb_widgets.values())
ts_tab = Panel(child=column(*ts_widgets.values()), title='Time Data')
si_tab = Panel(child=column(*si_widgets.values()), title='Virtual Rotation')
mg_tab = Panel(child=column(*mg_widgets.values()), title='MicGeometry')
env_tab = Panel(child=column(*env_widgets.values()), title='Environment')
grid_tab = Panel(child=column(*rg_widgets.values()), title='Grid')
st_tab = Panel(child=column(*st_widgets.values()), title='Steering')
ps_tab = Panel(child=column(*ps_widgets.values()), title='FFT')
bf_tab = Panel(child=column(beamformer_selector, selected_bf_widgets), title='Beamforming')
property_tabs = Tabs(
    tabs=[
        ts_tab,
        si_tab,
        mg_tab,  # env_tab
    ],
    sizing_mode='stretch_both',
)

property_tabs_2 = Tabs(tabs=[grid_tab, st_tab, ps_tab, bf_tab], sizing_mode='stretch_both')


calc_column = column(calc_button, *bv_widgets.values(), dynamic_slider)


def beamformer_handler(_attr, _old, new):
    """Switch the active beamforming algorithm widgets and source."""
    bv.source = beamformer_dict.get(new)
    selected_bf_widgets.children = list(beamformer_dict.get(new).get_widgets().values())


beamformer_selector.on_change('value', beamformer_handler)

# make Document
main_layout = row(plot_tabs, calc_column, property_tabs, property_tabs_2)


# make Document
def server_doc(doc):
    """Populate a Bokeh document for the rotating example app."""
    doc.add_root(main_layout)
    doc.title = 'RotatingExample'


if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, '/')
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)
