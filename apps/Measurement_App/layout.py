#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 17:23:01 2019

@author: kujawski
"""
from bokeh.palettes import Spectral11


COLOR = Spectral11
MODE_COLORS = {'display':COLOR[1],'calib':COLOR[5],'msm':COLOR[8]}
CLIP_COLORS = {'display':COLOR[8],'calib':COLOR[8],'msm':COLOR[8]}

button_height = 80

# status Definitions
toggle_labels =     {('msm',False): "MEASURE",
                    ('msm',True): "STOP MEASUREMENT",
                    ('display',False): "Display",
                    ('display',True): "Stop Display",
                    ('calib',True): "Stop Calibration",
                    ('calib',False): "Calibration",
                    ('beamf',True): "Stop Beamforming",
                    ('beamf',False): "Beamforming"}

plot_colors =       {('msm',True): [MODE_COLORS['msm'],CLIP_COLORS['msm']],
                    ('msm',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('display',True): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('display',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('calib',True): [MODE_COLORS['calib'],CLIP_COLORS['calib']],
                    ('calib',False): [MODE_COLORS['display'],CLIP_COLORS['display']],
                    ('beamf',True): [],
                    ('beamf',False): []}

