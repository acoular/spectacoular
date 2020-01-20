#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 17:41:52 2020

@author: arne_holter
"""
# App folder
paths = ['MicGeomExample']
############### THEME COLOR SELECTIONS ################
# Set background color
bg_col = 'pink' #'#2F2F2F'
# Set text color
txt_col = 'white'
# Set selection color
sel_col = 'darkred'

for path in paths:
############### WRITE THEME.YAML AND INDEX.HTML #######
    # yaml file
    yaml_file = open(path + '/theme.yaml', 'w')
    yaml_lines = [f'attrs:',
                  f'    Figure:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        border_fill_color: "{bg_col}"',
                  f'        outline_line_color: "{txt_col}"',
                  f'    Axis:',
                  f'        axis_line_color: "{txt_col}"',
                  f'        axis_label_text_color: "{txt_col}"',
                  f'        major_label_text_color: "{txt_col}"',
                  f'        major_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'    Grid:',
                  f'        grid_line_dash: [6, 4]',
                  f'        grid_line_alpha: .3',
                  f'    Title:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        text_color: "{txt_col}"',
                  f'    Widget:',
                  f'        background: "{bg_col}"',
                  f'    Title:',
                  f'        text_color: "{txt_col}"',
                  f'    Label:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        text_color: "{txt_col}"',
                  f'    ColorBar:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        title_text_color: "{txt_col}"',
                  f'        major_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'        major_label_text_color: "{txt_col}"']
    
    yaml_file.write('\n'.join(yaml_lines))
    yaml_file.close()
    
    # html file
    html_file = open(path + '/templates/index.html', 'w')
    html_lines = ['{% extends base %}',
                  '{% block title %}Bokeh Msm Example{% endblock %}',
                  '{% block preamble %}',
                  '<style>',
                  '  @import url(https://fonts.googleapis.com/css?family=Noto+Sans);',
                  '  .slick-header-column {',
                 f'    background-color: {bg_col} !important;',
                 f'    background-image: none !important;',
                  '    }',
                  '  .slick-row {',
                 f'    background-color: {bg_col} !important;',
                 f'    background-image: none !important;',
                 f'    color: {txt_col} !important;',
                 f'    overflow: hidden;',
    		      '    }',
                  '  .bk-cell-index {',
                 f'    background-color: {bg_col} !important;',
                 f'    background-image: none !important;',
                 f'    color: {txt_col} !important;',
    		      '    }',
                  '  .slick-cell.selected {',
                 f'    background-color: {sel_col} !important;',
                  '    }',
                  '  body {',
                  '    font-family: "Noto Sans", sans-serif;'
                  '    -webkit-font-smoothing: antialiased;',
                  '    text-rendering: optimizeLegibility;',
                 f'    color: #fff;',
                 f'    background: {bg_col};',
                  '    }',
                  '</style>',
                  '{% endblock %}']
    html_file.write('\n'.join(html_lines))
    html_file.close()