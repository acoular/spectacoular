#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 17:23:01 2019

@author: kujawski
"""
import numpy as np
from bokeh.palettes import Spectral5
from bokeh.plotting import figure
from bokeh.models import LinearColorMapper, LogColorMapper
from bokeh.models.widgets import Toggle,TextInput, Button, PreText,Select,RangeSlider,\
CheckboxGroup, Slider
from bokeh.layouts import column,row

COLOR = Spectral5
MODE_COLORS = {'display':COLOR[0],'calib':COLOR[2],'msm':COLOR[3]}
AMPFIG_ARGS = {'y_range': (0,140),'plot_width':800, 'plot_height':800} 
MGEOMFIG_ARGS = {'plot_width':800,  'plot_height':800}
BUFFBAR_ARGS = {'plot_width':280,  'plot_height':50}
IMPATH = "Measurement_App/static/Acoular_logo_grey.png"

# Color Mapper
bfColorMapper = LogColorMapper(palette="Spectral11", low=70, high=90,low_color=(1,1,1,0))
ampColorMapper = LinearColorMapper(palette=[COLOR[0],COLOR[0]], low=0.,high=180)

# Buttons
settings_button = Button(label="load settings",disabled=False)
select_all_channels_button = Button(label="select all channels")

# Toggle Buttons 
msm_toggle = Toggle(label="START MEASUREMENT", active=False,disabled=True,button_type="primary")
display_toggle = Toggle(label="start display", active=False)
calib_toggle = Toggle(label="start calibration", active=False,disabled=True)
beamf_toggle = Toggle(label="start beamforming", active=False,disabled=True)



# Select Widgets
selectPerCallPeriod = Select(title="Select Update Period [ms]", value=str(50), options=["25","50","100", "200", "400","800"])
select_setting = Select(title="Select Settings:", value="None")
selectBf = Select(title="Select Beamformer", 
                  value="Beamformer Freq", options=["Beamformer Time","Beamformer Freq"])

# Text
text_user_info = PreText(text="", width=500, height=500)

# Range Slider 
dynamicSlider = RangeSlider(start=30, end=110, 
                            value=(bfColorMapper.low,bfColorMapper.high), 
                            step=.5, title="Level",disabled=True)

ClipSlider = Slider(start=0, end=120, value=0, step=.5, title="Clip Level (only in auto level mode)")

# Checkboxes
checkbox_use_current_time = CheckboxGroup(labels=["use current time"], active=[0])
checkbox_use_camera = CheckboxGroup(labels=["use camera"], active=[])
checkbox_paint_mode = CheckboxGroup(labels=["paint mode"], active=[])
checkbox_autolevel_mode = CheckboxGroup(labels=["auto level mode"], active=[])

# Amplitude Figure
amp_fig = figure(title='SPL/dB',tools="",**AMPFIG_ARGS)
amp_fig.xgrid.visible = False
amp_fig.xaxis.major_label_orientation = np.pi/2
amp_fig.toolbar.logo=None

# MicGeomFigure
micgeom_fig = figure(title='Array Geometry', tools = 'pan,wheel_zoom,reset',**MGEOMFIG_ARGS)
micgeom_fig.toolbar.logo=None

# Buffer Bar
buffer_bar = figure(title="Buffer",y_range=['buffer'],x_range=(0,400),**BUFFBAR_ARGS)
buffer_bar.xgrid.visible = False
buffer_bar.ygrid.visible = False
buffer_bar.toolbar.logo = None
buffer_bar.toolbar_location = None
buffer_bar.axis.visible = None
buffer_bar.grid.visible = None

# Acoular Figure
x_range = (0,.1) # could be anything - e.g.(0,1)
y_range = (0,.1)
aclogo = figure(x_range=x_range, y_range=y_range,plot_width=100, plot_height=100)
aclogo.toolbar.logo = None
aclogo.toolbar_location = None
aclogo.axis.visible = None
aclogo.grid.visible = None
aclogo.outline_line_color = None
aclogo.image_url(url=[IMPATH],x=x_range[0],y=y_range[1],w=x_range[1]-x_range[0],h=y_range[1]-y_range[0])

