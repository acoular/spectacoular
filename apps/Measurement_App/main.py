#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
app can be started with:
bokeh serve --show Measurement_App --args --argName=argValue

# Processing / Acoular
#
#                                    |-> TimePower -> Average -> Amplitude Bar
#                                    |-> FiltOctave ->  TimePower -> Average -> Calibration    
# SamplesGenerator -> SampleSplitter |-> BeamformerTime -> FiltOctave -> TimePower -> Average -> Beamforming
#                                    |-> WriteH5   

In case of SINUS Devices:
if sync order of pci cards should be specified use
bokeh serve --show Measurement_App --args --device=typhoon --syncorder SerialNb1 SerialNb2 ...
"""
import argparse
from pathlib import Path

import acoular as ac
import numpy as np
from app import Calibration, _get_channel_labels
from bokeh.layouts import column, layout, row
from bokeh.models import (
    ColumnDataSource,
    FactorRange,
    LogColorMapper,
    Spacer,
    Tabs,
)
from bokeh.models import TabPanel as Panel
from bokeh.models.glyphs import Scatter
from bokeh.models.widgets import (
    Button,
    Div,
    MultiSelect,
    NumberEditor,
    NumberFormatter,
    Select,
    Slider,
    TableColumn,
    Toggle,
)

# bokeh imports
from bokeh.models.widgets.inputs import NumericInput
from bokeh.palettes import Viridis256
from bokeh.plotting import curdoc, figure
from layout import COLOR
from log import LogWidget

import spectacoular as sp

try:
    import cv2
    cam_enabled=True
    from cam import cameraCDS, camWidgets, set_alpha_callback, set_camera_callback
except:
    cam_enabled=False
    camWidgets = []


parser = argparse.ArgumentParser()
parser.add_argument(
  '--device',
  type=str,
  default="phantom",
  choices=["phantom","sounddevice","tornado","typhoon","apollo"],
  help='Connected device.')
parser.add_argument(
  '--blocksize',
  type=int,
  default=4096,
  help='Size of data blocks to be processed')
parser.add_argument(
    '--td_dir',
    type=str,
    default=None,
    help='Directory for saving HDF5 files')
parser.add_argument(
    '--mics_dir',
    type=str,
    default=Path(__file__).resolve().parent / "micgeom",
    help='Directory containing microphone geometry files')
parser.add_argument(
    '--config_dir',
    default=Path(__file__).resolve().parent / "config_files",
    help='Directory containing config files for setting up SINUS Messtechnik Devices'
)
parser.add_argument(
    '--config_name',
    default=None,
    help='Name of config file for setting up SINUS Messtechnik Devices'
)
parser.add_argument(
  '--inventory_no',
  type=str,
  default='TA181',
  help='Inventory number of the Apollo device. (Not required for other devices)')

args = parser.parse_args()

DEVICE = args.device
MICSIZE = 20
XCAM = (-0.5,-0.375,1.,0.75)

# set up logging
doc = curdoc()
log = LogWidget(doc=doc)
if cam_enabled: 
    set_camera_callback(doc)

# directory containing microphone geometry files
mics_dir = args.mics_dir
log.logger.debug(f"mics_dir: {mics_dir}")

# set up directory for saving td files
td = args.td_dir
if td is None:
    td = Path(__file__).resolve().parent / "td"
    if not td.exists():
        td.mkdir()
ac.config.td_dir = td
log.logger.debug(f"td_dir: {td}")

# =============================================================================
# load device
# =============================================================================
use_sinus = False
if DEVICE == 'sounddevice':
    import sounddevice as sd
    from app import SoundDeviceControl
    mics = sp.MicGeom()
    grid = sp.RectGrid()
    control = SoundDeviceControl(
        doc=doc, logger=log.logger, blocksize=args.blocksize,
        steer=ac.SteeringVector(grid=grid, mics=mics, ref=[0,0,0]),
    )    
elif DEVICE == 'phantom':
    from app import PhantomControl
    mics = sp.MicGeom(file = mics_dir / 'array_64.xml')
    grid = sp.RectGrid( x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=.3, increment=0.01)
    control = PhantomControl(
        doc=doc, logger=log.logger, blocksize=args.blocksize,
        steer=ac.SteeringVector(grid=grid, mics=mics, ref=[0,0,0]),
    )   
else: 
    from app import SinusControl
    mics = sp.MicGeom(file = mics_dir / 'tub_vogel64.xml')
    grid = sp.RectGrid( x_min=-0.75, x_max=0.75, y_min=-0.5, y_max=0.5, z=1.3, increment=0.015)
    control = SinusControl(
        doc=doc, logger=log.logger, blocksize=args.blocksize,
        steer=ac.SteeringVector(grid=grid, mics=mics, ref=[0,0,0]),
        device=DEVICE, config_dir=args.config_dir, config_name=args.config_name, inventory_no=args.inventory_no)
    use_sinus = True


# =============================================================================
# DEFINE FIGURES
# =============================================================================

# Amplitude Figure
amp_fig = figure(
    title='SPL/dB',tooltips=[("Lp/dB", "@level"), ("Channel", "@channels"),], tools="",
    x_range=FactorRange(*_get_channel_labels(control.source)), 
    y_range=(0,120), width=1400, height=750)
amp_fig.xgrid.visible = False
amp_fig.xaxis.major_label_orientation = np.pi/2
amp_fig.toolbar.logo=None

# MicGeom / Sourcemap Figure
mics_beamf_fig = figure(
        tooltips=[("Lp/dB", "@level"), ("Channel Index", "@channels"),("(x,y)", "(@x, @y)"),],
        tools = 'pan,wheel_zoom,reset',
         match_aspect=True, aspect_ratio=1, width=1000,
        )

# =============================================================================
# DEFINE COLUMN DATA SOURCES
# =============================================================================

amp_cds = ColumnDataSource({'channels':[], 'level':[],'colors':[]})#[COLOR[1]]*num_channels} )
beamf_cds = ColumnDataSource({'level':[]})
grid_data = ColumnDataSource(data={# x and y are the centers of the rectangle!
    'x': [(grid.x_max + grid.x_min)/2], 'y': [(grid.y_max + grid.y_min)/2],
    'width': [grid.x_max-grid.x_min], 'height': [grid.y_max-grid.y_min]
})

# =============================================================================
# DEFINE GLYPHS
# =============================================================================

mic_presenter = sp.MicGeomPresenter(source=mics, auto_update=True)
calibration = Calibration(doc=doc, control=control)

# Amplitude Bar Plot
amp_bar = amp_fig.vbar(
    x='channels', width=0.5, bottom=0,top='level', color='colors', source=amp_cds)

if cam_enabled:
    mics_beamf_fig.image_rgba(image='image_data',
                        x=XCAM[0], y=XCAM[1], dw=XCAM[2], dh=XCAM[3],
                        source=cameraCDS)
beamf_color_mapper = LogColorMapper(palette=Viridis256, low=70, high=90,low_color=(1,1,1,0))
bfImage = mics_beamf_fig.image(image='level', x=grid.x_min, y=grid.y_min, 
        dw=grid.x_max-grid.x_min, dh=grid.y_max-grid.y_min,
                color_mapper=beamf_color_mapper,
                source=beamf_cds)
if cam_enabled: 
    set_alpha_callback(bfImage)

# Microphone Geometry Plot
mic_layout = sp.layouts.MicGeomComponent(mic_alpha=0.4,
    glyph=Scatter(marker='circle_cross', x='x', y='y', fill_color='colors', size='sizes', 
    fill_alpha='alpha', line_alpha='alpha'),
    figure=mics_beamf_fig, presenter=mic_presenter, allow_point_draw=True,
    )
mic_presenter.update(**{
     'sizes':np.array([MICSIZE]*mics.mpos_tot.shape[1]),'colors':[COLOR[1]]*mics.mpos_tot.shape[1]})

mics_beamf_fig.rect( # draw rect grid bounds (dotted)
    alpha=1.,color='black',fill_alpha=0,line_width=2, source=grid_data)#line_color="#213447")


# =============================================================================
# DEFINE WIDGETS
# =============================================================================


# set up widgets for Microphone Geometry
editor = NumberEditor()
formatter = NumberFormatter(format="0.00")
mpos_columns = [TableColumn(field='x', title='x/m', editor=editor, formatter=formatter),
                TableColumn(field='y', title='y/m', editor=editor, formatter=formatter),
                TableColumn(field='z', title='z/m', editor=editor, formatter=formatter)]
mic_layout.mics_trait_widget_args.update(
    {'pos_total':  {'height': 200, 'editable':True, 'transposed':True, 'columns':mpos_columns,}})
mics_widgets = mic_layout.widgets
# disable widgets on display tab
[control.widgets_disable['display'].append(w) for w in mics_widgets.values()]
all_mics_valid = Button(label="All Valid", button_type="success",sizing_mode="stretch_width")
def _all_mics_valid(event): 
    mics.invalid_channels = []
all_mics_valid.on_click(_all_mics_valid)

# set up widgets for Beamforming
invalid_input_channels = MultiSelect(
    title="Not-Array Channels", height=150, 
    description="Select which input channels should not be used for beamforming",
    value=[], options=_get_channel_labels(control.source, 'Index'))
control.beamf.source.source.source.source.source.set_widgets(**{'invalid_channels':invalid_input_channels})
auto_level_toggle = Toggle(label="Auto Level", button_type="success",active=True)
dynamic_range = NumericInput(value=20, title="Dynamic Range/dB")
bf_max_level = Slider(start=0, end=140, value=100, step=1, title="Peak Level/dB")

rgWidgets = grid.get_widgets()
zSlider = Slider(start=0.01, end=10.0, value=grid.z, step=.02, title="z",disabled=False)
grid.set_widgets(**{'z':zSlider})
rgWidgets['z'] = zSlider # replace textfield with slider
freqSlider = Slider(start=50, end=10000, value=4000, step=1, title="Frequency",disabled=False)
control.beamf.source.source.source.set_widgets(**{'band':freqSlider}) # 
all_bf_valid = Button(label="All Valid", button_type="success",sizing_mode="stretch_width")
def _all_valid(event):
    control.beamf.source.source.source.source.source.invalid_channels = []
all_bf_valid.on_click(_all_valid)

# set up widgets for Amplitude Bar
clip_level = NumericInput(value=120, title="Clip Level/dB",width=100)
label_options = ["Index","Number"]
if use_sinus:
    label_options.insert(0, "Physical")
labelSelect = Select(title="Select Channel Labeling:", value='Index', options=label_options)

for w in rgWidgets.values():
    control.widgets_disable['beamf'].append(w)

control.widgets_disable['beamf'].append(auto_level_toggle)
control.widgets_enable['beamf'].append(auto_level_toggle)
control.widgets_disable['beamf'].append(bf_max_level)
control.widgets_enable['beamf'].append(bf_max_level)
control.widgets_disable['beamf'].append(dynamic_range)
control.widgets_enable['beamf'].append(dynamic_range)

# =============================================================================
# DEFINE CALLBACKS
# =============================================================================

def update_app():  # only update figure when tab is active
    if tabs.active == 0: 
        update_amp_bar_plot()
    if tabs.active == 1:
        if control.beamf_toggle.active:
            update_beamforming_plot()
        else:
            update_mic_geom_plot()
    if use_sinus:
        control.update_buffer_bar()

def update_amp_bar_plot():
    if control.disp.cdsource.data['data'].size > 0:
        levels = ac.L_p(control.disp.cdsource.data['data'][0])
        amp_cds.data['level'] =  levels
        amp_cds.data['colors'] = np.where(levels < clip_level.value, control.modecolor, control.clipcolor)

def update_mic_geom_plot():
    log.logger.debug("update_mic_geom_plot")
    if mics.num_mics > 0: 
        p2 = control.disp.cdsource.data['data'][0]
        levels = ac.L_p(p2)
        if mics_widgets['mic_size'].value > 0:
            mic_presenter.cdsource.data['sizes'] = 20*p2/p2.max() + mics_widgets['mic_size'].value
        else:
            mic_presenter.cdsource.data['sizes'] = np.zeros(p2.shape[0])
        mic_presenter.cdsource.data['colors'] = np.where(levels < clip_level.value, control.modecolor, control.clipcolor)

def update_beamforming_plot():
    if control.beamf.cdsource.data['data'].size > 0:
        beamf_cds.data['level'] = [
            ac.L_p(control.beamf.cdsource.data['data'].reshape(grid.shape)).T]
        if auto_level_toggle.active:
            maxValue = beamf_cds.data['level'][0].max()
            beamf_color_mapper.high = maxValue
            beamf_color_mapper.low = maxValue - dynamic_range.value

def update_view(arg):
    if arg:
        control._view_callback_id = doc.add_periodic_callback(
            update_app, int(control.update_period.value))
    if not arg:
        [thread.join() for thread in control._disp_threads]
        doc.remove_periodic_callback(control._view_callback_id)
control.display_toggle.on_click(update_view)

def update_channel_labels(attr,old,new):
    log.logger.debug("update_channel_labels")
    labels = _get_channel_labels(control.source, labelSelect.value)
    # update amp bar 
    amp_cds.data.update({
        'channels': labels,
        'colors' : [COLOR[1]]*control.source.num_channels,
        'level' : np.zeros(control.source.num_channels)
    })
    amp_fig.x_range.factors = labels  # Set x_range as categorical
    amp_fig.xaxis.major_label_overrides = {label: label for label in labels}
    # update calibration table
    if labelSelect.value in ['Physical','Number']:
        calibration.cal_table.source.data['channel'] = labels

update_channel_labels(None,None,None)
labelSelect.on_change('value',update_channel_labels)
control.source.on_trait_change(lambda: update_channel_labels(None,None,None), 'num_channels')

def dynamic_slider_callback(attr, old, new):
    if not auto_level_toggle.active:
        beamf_color_mapper.high = bf_max_level.value
        beamf_color_mapper.low = bf_max_level.value - dynamic_range.value
dynamic_range.on_change('value', dynamic_slider_callback)    
bf_max_level.on_change('value', dynamic_slider_callback)

def update_bfImage_axis():
    dx = grid.x_max-grid.x_min
    dy = grid.y_max-grid.y_min
    bfImage.glyph.x = grid.x_min
    bfImage.glyph.y = grid.y_min
    bfImage.glyph.dw = dx
    bfImage.glyph.dh = dy
    bfImage.glyph.update()

def update_grid():
    """update grid data source when grid settings change"""
    grid_data.data = {
        'x': [(grid.x_max + grid.x_min) / 2],
        'y': [(grid.y_max + grid.y_min) / 2],
        'width': [grid.x_max - grid.x_min],
        'height': [grid.y_max - grid.y_min]
    }

def update_bf_plot(attr, old, new):
    update_bfImage_axis()
    update_grid()


def clear_beamforming_image(arg):
    if not arg:
        beamf_cds.data['level'] = []
        control.beamf.cdsource.data['data'] = np.array([])
control.beamf_toggle.on_click(clear_beamforming_image)


rgWidgets['x_min'].on_change('value', update_bf_plot)
rgWidgets['x_max'].on_change('value', update_bf_plot)
rgWidgets['y_min'].on_change('value', update_bf_plot)
rgWidgets['y_max'].on_change('value', update_bf_plot)

# =============================================================================
#  Set Up Bokeh Document Layout
# =============================================================================

# Tabs
amplitudesTab = Panel(child=column(
    row(Spacer(width=25),clip_level,Spacer(width=25),labelSelect),
    row(amp_fig, log.log_text), sizing_mode='stretch_both'),title='Channel Levels')


mics_widgets['invalid_channels'].title = "Invalid Mics"
mics_widgets['invalid_channels'].height = 150
mics_widgets['invalid_channels'].description = "Select which input channel indices are not part of the array"
mic_control = layout([
    [Div(text=r"""<b style="font-size:15px;">Microphone Setup</b>""")],
    [mics_widgets['file'], mics_widgets['mic_size'],mics_widgets['num_mics']],
    [column(all_mics_valid, mics_widgets['invalid_channels']), column(all_bf_valid, invalid_input_channels)],
    [mics_widgets['pos_total']],
], sizing_mode='stretch_width')

bf_control = layout([
    [Div(text=r"""<b style="font-size:15px;">Beamforming Setup</b>""")],
    [freqSlider],
    [auto_level_toggle, dynamic_range, bf_max_level],
    [rgWidgets['x_min'], rgWidgets['x_max'], rgWidgets['y_min'], rgWidgets['y_max']],
    [rgWidgets['increment'], rgWidgets['z']],
    [rgWidgets['size']]
], sizing_mode='stretch_width')

mic_bf_control = column(mic_control, Spacer(height=25),bf_control, sizing_mode='stretch_width')

mics_bf_tab = Panel(
    child=row(mics_beamf_fig, mic_bf_control),
    title='Microphone Geometry / Beamforming')

tabs = Tabs(tabs=[
    amplitudesTab,
    mics_bf_tab,
    calibration.get_tab(),
    ], sizing_mode='inherit', width=1700, height=800)

control_column = control.get_widgets()

# if sinus_enabled:
#     # Additional Panel when SINUS Messtechnik API is used
#     teds_component = get_teds_component(devInputManager,log.logger)
#     sinusTab = Panel(child=teds_component,title='SINUS Messtechnik')
#     tabs.tabs.append(sinusTab)

if DEVICE == 'sounddevice':
    # set up devices choice
    devices = {}
    for i,dev in enumerate(sd.query_devices()):
        if dev['max_input_channels']>0:
            devices["{}".format(i)] = "{name} {max_input_channels}".format(**dev)
    device_select = Select(title="Choose input device:", 
        value="{}".format(list(devices.keys())[0]), options=list(devices.items()))
    control.source.device=int(device_select.value)
    control.source.set_widgets(device=device_select)
    control_column.children.insert(1,device_select)
    # sdwidgets = list(control.source.get_widgets().values())
    # control_column.children.insert(2,sdwidgets[2]) # num_channels

    def device_update(attr,old,new):
        control.source.num_channels = sd.query_devices(control.source.device)['max_input_channels']
        update_channel_labels(None,None,None)
    device_select.on_change('value',device_update)


root = column(
    row(
        Spacer(width=10),
        control_column,
        Spacer(width=20),
        tabs,
    ),
)
doc.add_root(root)
doc.title = "Measurement App"
