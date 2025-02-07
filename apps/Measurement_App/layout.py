#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 17:23:01 2019

@author: kujawski
"""
from bokeh.palettes import Spectral11, Viridis256
from bokeh.models import LogColorMapper
from bokeh.models.widgets import Button, RangeSlider,\
CheckboxGroup, Slider

COLOR = Spectral11
MODE_COLORS = {'display':COLOR[1],'calib':COLOR[5],'msm':COLOR[8]}
CLIP_COLORS = {'display':COLOR[8],'calib':COLOR[8],'msm':COLOR[8]}

# status Definitions
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

# Buttons
select_all_channels_button = Button(label="select all channels")


# Range Slider 
dynamicSlider = RangeSlider(start=30, end=110, 
                            value=(bfColorMapper.low,bfColorMapper.high), 
                            step=.5, title="Level",disabled=True)

ClipSlider = Slider(start=0, end=120, value=0, step=.5, title="Clip Level (only in auto level mode)")

# Checkboxes
checkbox_paint_mode = CheckboxGroup(labels=["paint mode"], active=[])
checkbox_autolevel_mode = CheckboxGroup(labels=["auto level mode"], active=[0])
