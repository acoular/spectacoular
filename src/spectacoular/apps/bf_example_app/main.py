# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""
Frequency-domain beamforming application.

Start from an installed package with:

    bf_example_app --show
"""

from pathlib import Path

import acoular as ac
import spectacoular as sp

import numpy as np

# bokeh imports
from bokeh.io import curdoc
from bokeh.layouts import column, layout, row
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    HoverTool,
    LinearColorMapper,
    Range1d,
    Spacer,
)
from bokeh.models.glyphs import Scatter
from bokeh.models.tools import BoxEditTool
from bokeh.models.widgets import (
    Div,
    NumberEditor,
    NumberFormatter,
    RangeSlider,
    Select,
    TableColumn,
    Toggle,
)
from bokeh.palettes import Spectral11, viridis
from bokeh.plotting import figure
from bokeh.server.server import Server

COLORS = list(Spectral11)
RED = '#961400'
BLUE = '#3288bd'
MIN_SPL_DB = -300

doc = curdoc()

# %% Build processing chain
invalid = [1, 7]
ts = sp.MaskedTimeSamples(
    file=Path(__file__).parent.parent / 'example_data.h5',
    invalid_channels=invalid,
    start=0,
    stop=16000,
)
cal = sp.Calib(
    source=ts,
    file=Path(__file__).parent / 'example_calib.xml',
    invalid_channels=ts.invalid_channels,
)
mg = sp.MicGeom(
    file=Path(ac.__file__).parent / 'xml' / 'array_56.xml',
    invalid_channels=ts.invalid_channels,
)
ps = sp.PowerSpectra(source=cal, block_size=1024, overlap='50%')
rg = sp.RectGrid(x_min=-0.6, x_max=-0.1, y_min=-0.3, y_max=0.3, z=0.68, increment=0.01)
env = sp.Environment(c=346.04)
st = sp.SteeringVector(grid=rg, mics=mg, env=env)


# %%  Beamforming Algorithms
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

bv = sp.BeamformerPresenter(source=bb, num=3, freq=4000.0)
mgp = sp.MicGeomPresenter(source=mg, auto_update=True)
mgp.update()

# %% figures

# CDS
grid_data = ColumnDataSource(
    data={
        # x and y are the centers of the rectangle!
        'x': [(rg.x_max + rg.x_min) / 2],
        'y': [(rg.y_max + rg.y_min) / 2],
        'width': [rg.x_max - rg.x_min],
        'height': [rg.y_max - rg.y_min],
    }
)

f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
freqdata = ColumnDataSource(
    data={
        'freqs': [np.array(f_ticks)],  # initialize
        'amp': [np.array([0] * len(f_ticks))],
        'colors': ['white'],
    }
)

sectordata = ColumnDataSource(data={'x': [], 'y': [], 'width': [], 'height': []})


# Beamforming Plot
bf_plot = figure(title='Source Map', tools='pan,wheel_zoom,reset', width=700, match_aspect=True)
# draw airfoil
bf_plot.rect(
    -0.38,
    0.0,
    0.2,
    0.5,
    alpha=1.0,
    color='gray',
    fill_alpha=0.8,
    line_width=5,
    line_color='#1e3246',
)
bf_plot.rect(  # draw rect grid bounds
    alpha=1.0, color='#d2d6da', fill_alpha=0, line_width=2, source=grid_data
)  # line_color="#213447")
bf_plot.toolbar.logo = None
bf_plot.xgrid.visible = False
bf_plot.ygrid.visible = False
color_mapper = LinearColorMapper(palette=viridis(100), low=40, high=50, low_color=(1, 1, 1, 0))
bf_image = bf_plot.image(
    image='bfdata',
    x='x',
    y='y',
    dw='dw',
    dh='dh',
    alpha=0.9,
    color_mapper=color_mapper,
    source=bv.cdsource,
    anchor='bottom_left',
    origin='bottom_left',
)
bf_plot.add_layout(
    ColorBar(color_mapper=color_mapper, location=(0, 0), title='dB', title_standoff=10),
    'right',
)
mic_layout = sp.layouts.MicGeomComponent(
    glyph=Scatter(marker='circle_cross', x='xi', y='yi', size=15, fill_alpha=0.2),
    presenter=mgp,
    figure=bf_plot,
)
bf_plot.add_tools(
    HoverTool(
        tooltips=[
            ('L_p (dB)', '@bfdata'),
            ('mic', '@channels'),
        ],
        mode='mouse',
        renderers=[bf_image, mic_layout._glyph_renderer],  # noqa: SLF001
    )
)


# set up widgets for Microphone Geometry
editor = NumberEditor()
formatter = NumberFormatter(format='0.00')
mpos_columns = [
    TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
    TableColumn(field='y', title='x/m', editor=editor, formatter=formatter),
    TableColumn(field='z', title='x/m', editor=editor, formatter=formatter),
]
mic_layout.mics_trait_widget_args.update(
    {
        'pos_total': {
            'width': 280,
            'editable': True,
            'transposed': True,
            'columns': mpos_columns,
        },
        'invalid_channels': {
            'width': 280,
            'options': [str(i) for i in range(mg.pos_total.shape[1])],
        },
    }
)

# FrequencySignalPlot
f_ticks_override = {
    20: '0.02',
    50: '0.05',
    100: '0.1',
    200: '0.2',
    500: '0.5',
    1000: '1',
    2000: '2',
    5000: '5',
    10000: '10',
    20000: '20',
}
freqplot = figure(
    title='Sector-Integrated Spectrum',
    width=800,
    match_aspect=True,
    x_axis_type='log',
    x_axis_label='f / kHz',
    y_axis_label='SPL / dB',
)  # tooltips=TOOLTIPS)
freqplot.toolbar.logo = None
freqplot.xaxis.axis_label_text_font_style = 'normal'
freqplot.yaxis.axis_label_text_font_style = 'normal'
freqplot.xgrid.minor_grid_line_color = 'navy'
freqplot.xgrid.minor_grid_line_alpha = 0.05
freqplot.xaxis.ticker = f_ticks
freqplot.x_range = Range1d(20, 20000)
freqplot.y_range = Range1d(0, 120)
freqplot.xaxis.major_label_overrides = f_ticks_override
fr_line = freqplot.multi_line('freqs', 'amp', color='colors', alpha=0.0, line_width=3, source=freqdata)


# %% widgets

beamformer_dict = {
    'Conventional Beamforming': (bb, bb.get_widgets()),
    'Functional Beamforming': (bf, bf.get_widgets()),
    'Capon Beamforming': (bc, bc.get_widgets()),
    'Eigenvalue Beamforming': (be, be.get_widgets()),
    'Music Beamforming': (bm, bm.get_widgets()),
    'Damas Deconvolution': (bd, bd.get_widgets()),
    'DamasPlus Deconvolution': (bdp, bdp.get_widgets()),
    'Orthogonal Beamforming': (bo, bo.get_widgets()),
    'CleanSC Deconvolution': (bs, bs.get_widgets()),
    'Clean Deconvolution': (bl, bl.get_widgets()),
    'CMF': (bcmf, bcmf.get_widgets()),
    'GIB': (bgib, bgib.get_widgets()),
}

# create Select Button to select Beamforming Algorithm
beamformer_selector = Select(
    title='Beamforming Method:',
    options=list(beamformer_dict.keys()),
    value=next(iter(beamformer_dict.keys())),
    height=75,
    sizing_mode='stretch_width',
)

# use additional classes for data evaluation/view
bv.trait_widget_args.update({'num': {'width': 40}, 'freq': {'width': 100}})
# get widgets to control settings
ts_widgets = ts.get_widgets()
mg_widgets = mic_layout.widgets
env_widgets = env.get_widgets()
cal_widgets = cal.get_widgets()
ps_widgets = ps.get_widgets()
rg_widgets = rg.get_widgets()
st_widgets = st.get_widgets()
bb_widgets = bb.get_widgets()
bv_widgets = bv.get_widgets()
ts_widgets.pop('invalid_channels')

invalid_widget = mg_widgets['invalid_channels']
ts.set_widgets(invalid_channels=invalid_widget)
cal.set_widgets(invalid_channels=invalid_widget)

settings_dict = {
    'Time Data': ts_widgets,
    'Microphone Geometry': mg_widgets,
    'Environment': env_widgets,
    'Calibration': cal_widgets,
    'FFT/CSM': ps_widgets,
    'Focus Grid': rg_widgets,
    'Steering Vector': st_widgets,
    'Beamforming Method': bb_widgets,
}


# %% Widgets for display

dynamic_slider = RangeSlider(
    start=0,
    end=120,
    step=1.0,
    value=(40, 50),
    width=220,
    height=50,
    title='Dynamic Range',
)
spl_slider = RangeSlider(start=0, end=140, step=1.0, value=(10, 120), width=350, height=50, title='SPL Range')

freq_slider = RangeSlider(
    start=20,
    end=20000,
    step=1.0,
    value=(20, 20000),
    width=350,
    height=50,
    title='Frequency Range',
)


def dynamic_slider_callback(_attr, _old, _new):
    """Update the source-map color range."""
    color_mapper.low, color_mapper.high = dynamic_slider.value


dynamic_slider.on_change('value', dynamic_slider_callback)


def spl_slider_callback(_attr, _old, _new):
    """Update the y-axis limits of the frequency plot."""
    freqplot.y_range.start, freqplot.y_range.end = spl_slider.value


spl_slider.on_change('value', spl_slider_callback)


def freq_slider_callback(_attr, _old, _new):
    """Update the x-axis limits of the frequency plot."""
    freqplot.x_range.start, freqplot.x_range.end = freq_slider.value


freq_slider.on_change('value', freq_slider_callback)

# create Button to trigger beamforming result calculation
calc_button = Toggle(button_type='primary', width=125, height=50, label='Calculate')
sp.set_calc_button_callback(bv.update, calc_button)


def update_grid(_attr, _old, _new):
    """Update grid data source when grid settings change."""
    grid_data.data = {
        # x and y are the centers of the rectangle!
        'x': [(rg.x_max + rg.x_min) / 2],
        'y': [(rg.y_max + rg.y_min) / 2],
        'width': [rg.x_max - rg.x_min],
        'height': [rg.y_max - rg.y_min],
    }


rg_widgets['x_min'].on_change('value', update_grid)
rg_widgets['x_max'].on_change('value', update_grid)
rg_widgets['y_min'].on_change('value', update_grid)
rg_widgets['y_max'].on_change('value', update_grid)


# %% Property Tabs
selected_bf_widgets = column(*bb_widgets.values(), height=1000)

# create Select Button to select Beamforming Algorithm
setting_selector = Select(
    title='Select Setting',
    options=list(settings_dict.keys()),
    value=next(iter(settings_dict.keys())),
    height=75,
)

selected_setting_col = column(list(settings_dict['Time Data'].values()), height=1000)


def select_setting_handler(_attr, _old, new):
    """Change the displayed widget column for the selected Acoular object."""
    if new != 'Beamforming Method':
        selected_setting_col.children = list(settings_dict[new].values())
    else:
        selected_setting_col.children = selected_bf_widgets.children


setting_selector.on_change('value', select_setting_handler)


def beamformer_handler(_attr, _old, new):
    """Switch the active beamformer and its settings widgets."""
    bv.source = beamformer_dict.get(new)[0]
    selected_bf_widgets.children = list(beamformer_dict.get(new)[1].values())
    if setting_selector.value == 'Beamforming Method':
        selected_setting_col.children = selected_bf_widgets.children


beamformer_selector.on_change('value', beamformer_handler)


# %% Integration sector
def integrate_result(_attr, _old, _new):
    """Update the integrated sector spectrum."""
    numsectors = len(sectordata.data['x'])
    if numsectors > 0:
        fr_line.glyph.line_alpha = 0.8
        famp = []
        ffreq = []
        colors = []
        for i in range(numsectors):
            sector = np.array(
                [
                    sectordata.data['x'][i] - sectordata.data['width'][i] / 2,
                    sectordata.data['y'][i] - sectordata.data['height'][i] / 2,
                    sectordata.data['x'][i] + sectordata.data['width'][i] / 2,
                    sectordata.data['y'][i] + sectordata.data['height'][i] / 2,
                ]
            )
            sector[0] = np.clip(sector[0], rg.x_min, rg.x_max)
            sector[2] = np.clip(sector[2], rg.x_min, rg.x_max)
            sector[1] = np.clip(sector[1], rg.y_min, rg.y_max)
            sector[3] = np.clip(sector[3], rg.y_min, rg.y_max)
            if sector[0] >= sector[2] or sector[1] >= sector[3]:
                continue
            specamp = ac.L_p(bv.source.integrate(sector))
            specamp[specamp < MIN_SPL_DB] = np.nan
            famp.append(specamp)
            ffreq.append(ps.fftfreq())
            colors.append(COLORS[i])
        if famp:
            freqdata.data = {'amp': famp, 'freqs': ffreq, 'colors': colors}
        else:
            fr_line.glyph.line_alpha = 0.0
            freqdata.data = {
                'freqs': [np.array(f_ticks)],
                'amp': [np.array([0] * len(f_ticks))],
                'colors': ['white'],
            }
    else:
        fr_line.glyph.line_alpha = 0.0  # make transparent if no integration sector exist
        freqdata.data = {
            'freqs': [np.array(f_ticks)],
            'amp': [np.array([0] * len(f_ticks))],
            'colors': ['white'],
        }


isector = bf_plot.rect(
    'x',
    'y',
    'width',
    'height',
    alpha=1.0,
    fill_alpha=0.2,
    color='black',
    line_width=3,
    source=sectordata,
)
tool = BoxEditTool(renderers=[isector], num_objects=len(COLORS))  # allow only as many boxes as Colors
bf_plot.add_tools(tool)
sectordata.on_change('data', integrate_result)
bv.cdsource.on_change('data', integrate_result)  # also change integration result when source map changes

# %% Instructions

instruction_calculation = Div(
    text=(
        '<p><b>Calculate Source Map:</b></p>'
        ' <b>Select a desired beamforming method</b> via the "Beamforming Method" widget '
        'and <b>press the Calculate Button</b>. Depending on the method, this may take '
        'some time. You may also want to change the desired frequency and bandwith of '
        'interest with the "freq" and "num" text field widgets.'
    )
)

instruction_sector_integration = Div(
    text=(
        '<p><b>Integrate over Source Map Region:</b></p>'
        ' <b>Select the "Box Edit Tool"</b> in the upper right corner of the source map '
        'figure after calculating the source map. <b>Hold down the shift key to draw an '
        'integration sector</b> in the source map. A sector-integrated spectrum should '
        'appear. You can <b>remove the sector by pressing the Backspace key</b>. If the '
        'rectangle extends beyond the source-map grid, it is clipped to the valid grid '
        'bounds automatically.'
    )
)


# %% Document layout

left_layout = layout(
    [
        [Spacer(width=40), calc_button, *bv_widgets.values(), dynamic_slider],
        [bf_plot],
    ]
)

center_layout = layout(
    [
        [Spacer(width=40), spl_slider, Spacer(width=20), freq_slider],
        [freqplot],
    ]
)

right_layout = column(
    beamformer_selector,
    setting_selector,
    Spacer(height=20),
    selected_setting_col,
    sizing_mode='stretch_width',
)
instructions_col = column(instruction_calculation, instruction_sector_integration)
layout = column(
    instructions_col,
    Spacer(height=50),
    row(left_layout, Spacer(width=10), center_layout, Spacer(width=20), right_layout),
)


# make Document
def server_doc(doc):
    """Add the beamforming application layout to a Bokeh document."""
    doc.add_root(layout)
    doc.title = 'Frequency Domain Beamforming App'


if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    server.io_loop.add_callback(server.show, '/')
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)
