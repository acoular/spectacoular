#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 17:41:52 2020

@author: arne_holter
"""
# App folder
paths = ['MicGeomExample', 'FreqBeamformingExample', 'LiveViewExample',
         'TimeSamplesExample']
############### THEME COLOR SELECTIONS ################
# Set background color
bg_col = '#2F2F2F'
# Set text color
txt_col = 'white'
# Set selection color
sel_col = 'darkred'
# Set link color: [color, hovered color]
link_col = ['green', 'white']

# read Acoular Logo:
logo_height = 100
logo_width = 500
Ac_logo = open('Acoular_logo', 'r').read()
for path in paths:
############### WRITE THEME.YAML AND INDEX.HTML #######
    # yaml file
    yaml_file = open('examples/' + path + '/theme.yaml', 'w')
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
                  f'        grid_line_color: "{txt_col}"',
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
                  f'    Legend:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        border_line_color: "{bg_col}"',
                  f'        title_text_color: "{txt_col}"',
                  f'        label_text_color: "{txt_col}"',
                  f'    ColorBar:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        title_text_color: "{txt_col}"',
                  f'        major_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'        major_label_text_color: "{txt_col}"']
    
    yaml_file.write('\n'.join(yaml_lines))
    yaml_file.close()
    
    # html file
    html_file = open('examples/' + path + '/templates/index.html', 'w')
    html_lines = ['{% extends base %}',
                  '{% block title %}Bokeh Msm Example{% endblock %}',
                  '{% block preamble %}',
                 f'<img alt="Logo" src="{Ac_logo}" width="{logo_width}" height="{logo_height}">',
                  '<style>',
                  '  a:link {',
                 f'    color: {link_col[0]};', # set link color
                  '    }',
                  '  a:visited {',
                 f'    color: {link_col[0]};', # set link color
                  '    }',   
                  '  a:hover {',
                 f'    color: {link_col[1]};', # set hovered link color
                  '    }',
                  '  a:active {',
                 f'    color: {link_col[0]};', # set link color
                  '    }',
                  '  @import url(https://fonts.googleapis.com/css?family=Noto+Sans);',
                  '  .slick-header-column {',                   # datatable header
                 f'    background-color: {bg_col} !important;',  
                 f'    background-image: none !important;',     
                  '    }',
                  '  .slick-row {',                             # datatable rows
                 f'    background-color: {bg_col} !important;',
                 f'    background-image: none !important;',
                 f'    color: {txt_col} !important;',
                 f'    overflow: hidden;',
    		      '    }',
                  '  .bk-cell-index {',                         # datatable index column
                 f'    background-color: {bg_col} !important;',
                 f'    background-image: none !important;',
                 f'    color: {txt_col} !important;',
    		      '    }',
                  '  .slick-cell.selected {',                   # datable selection color
                 f'    background-color: {sel_col} !important;',
                  '    }',
                  '  body::-webkit-scrollbar {',                # absolute width of browser scrollbar
                  '   width: 8px;',
                  '  }',
                  '  body {',
                  '    font-family: "Noto Sans", sans-serif;'   # font
                  '    -webkit-font-smoothing: antialiased;',
                  '    text-rendering: optimizeLegibility;',
                 f'    color: {txt_col};',                      # text color
                 f'    background: {bg_col};',                  # background color
                 f'    scrollbar-width: thin;',
                 f'    scrollbar-color: {txt_col} {bg_col};',   # scrollbar <slider color> <background color>
                  '    }',
                  '  body::-webkit-scrollbar-track {',          # scrollbar background
                 f'    background: {bg_col}',
                  '    }',
                  '  body::-webkit-scrollbar-thumb {',          # scrollbar slider
                 f'    background-color: {txt_col};',
                  '    border-radius: 4px;',
                  '    border: 2px;',
                  '    }',
                  '</style>',
                  '{% endblock %}']
    html_file.write('\n'.join(html_lines))
    html_file.close()