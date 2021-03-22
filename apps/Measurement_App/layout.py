#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 17:23:01 2019

@author: kujawski
"""
from numpy import pi
from bokeh.palettes import Spectral11, Viridis256
from bokeh.plotting import figure
from bokeh.models import LinearColorMapper, LogColorMapper
from bokeh.models.widgets import Toggle, Button, PreText,Select,RangeSlider,\
CheckboxGroup, Slider

CLIPVALUE = 120 # value in dB at which CLIP_COLOR is applied
COLOR = Spectral11
MODE_COLORS = {'display':COLOR[1],'calib':COLOR[5],'msm':COLOR[8]}
CLIP_COLORS = {'display':COLOR[8],'calib':COLOR[8],'msm':COLOR[8]}
AMPFIG_ARGS = {'y_range': (0,140),'plot_width':1200, 'plot_height':800} 
MGEOMFIG_ARGS = {'plot_width':800,  'plot_height':800}


# status Definitions
log_text_toggles =  {('msm',True): "collecting samples...",
                    ('msm',False): "stopped collecting samples.",
                    ('display',True): "display samples...",
                    ('display',False): "stopped to display samples.",
                    ('calib',True): "calibrating...",
                    ('calib',False): "stopped calibrating.",
                    ('beamf',True): "beamforming...",
                    ('beamf',False): "stopped beamforming."}

toggle_labels =     {('msm',False): "START MEASUREMENT",
                    ('msm',True): "STOP MEASUREMENT",
                    ('display',False): "start display",
                    ('display',True): "stop display",
                    ('calib',True): "stop calibration",
                    ('calib',False): "start calibration",
                    ('beamf',True): "stop beamforming",
                    ('beamf',False): "start beamforming"}

plot_colors =       {('msm',True): [MODE_COLORS['msm'],CLIP_COLORS['msm']],
                    ('msm',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('display',True): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('display',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('calib',True): [MODE_COLORS['calib'],CLIP_COLORS['calib']],
                    ('calib',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('beamf',True): [],
                    ('beamf',False): []}

# Color Mapper
bfColorMapper = LogColorMapper(palette=Viridis256, low=70, high=90,low_color=(1,1,1,0))
ampColorMapper = LinearColorMapper(palette=[COLOR[0],COLOR[10]], low=0.,high=CLIPVALUE*2)

# Buttons
select_all_channels_button = Button(label="select all channels")

# Toggle Buttons 
msm_toggle = Toggle(label="START MEASUREMENT", active=False,disabled=True,button_type="danger")
display_toggle = Toggle(label="start display", active=False,button_type="primary")
calib_toggle = Toggle(label="start calibration", active=False,disabled=True,button_type="warning")
beamf_toggle = Toggle(label="start beamforming", active=False,disabled=True,button_type="warning")

# Select Widgets
selectPerCallPeriod = Select(title="Select Update Period [ms]", value=str(50), options=["25","50","100", "200", "400","800"])

# Text
text_user_info = PreText(text="", width=300, height=800)

# Range Slider 
dynamicSlider = RangeSlider(start=30, end=110, 
                            value=(bfColorMapper.low,bfColorMapper.high), 
                            step=.5, title="Level",disabled=True)

ClipSlider = Slider(start=0, end=120, value=0, step=.5, title="Clip Level (only in auto level mode)")

# Checkboxes
checkbox_use_current_time = CheckboxGroup(labels=["use current time"], active=[0])
checkbox_paint_mode = CheckboxGroup(labels=["paint mode"], active=[])
checkbox_autolevel_mode = CheckboxGroup(labels=["auto level mode"], active=[])

# Amplitude Figure
amp_fig = figure(title='SPL/dB',tools="",**AMPFIG_ARGS)
amp_fig.xgrid.visible = False
amp_fig.xaxis.major_label_orientation = pi/2
amp_fig.toolbar.logo=None

# MicGeomFigure
micgeom_fig = figure(title='Array Geometry', tools = 'pan,wheel_zoom,reset',**MGEOMFIG_ARGS)
micgeom_fig.toolbar.logo=None

