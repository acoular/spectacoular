#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 17:23:01 2019

@author: kujawski
"""
from bokeh.palettes import Spectral11
from bokeh.models.widgets import CheckboxGroup, Slider, Toggle


COLOR = Spectral11
MODE_COLORS = {'display':COLOR[1],'calib':COLOR[5],'msm':COLOR[8]}
CLIP_COLORS = {'display':COLOR[8],'calib':COLOR[8],'msm':COLOR[8]}

# status Definitions
toggle_labels =     {('msm',False): "START MEASUREMENT",
                    ('msm',True): "STOP MEASUREMENT",
                    ('display',False): "Start Display",
                    ('display',True): "Stop Display",
                    ('calib',True): "Stop Calibration",
                    ('calib',False): "Start Calibration",
                    ('beamf',True): "Stop Beamforming",
                    ('beamf',False): "Start Beamforming"}

plot_colors =       {('msm',True): [MODE_COLORS['msm'],CLIP_COLORS['msm']],
                    ('msm',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('display',True): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('display',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('calib',True): [MODE_COLORS['calib'],CLIP_COLORS['calib']],
                    ('calib',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('beamf',True): [],
                    ('beamf',False): []}


ClipSlider = Slider(start=0, end=120, value=0, step=.5, title="Clip Level (only in auto level mode)")

# Checkboxes
checkbox_paint_mode = CheckboxGroup(labels=["paint mode"], active=[])
autolevel_toggle = Toggle(label="Auto Level", button_type="success",active=True)
