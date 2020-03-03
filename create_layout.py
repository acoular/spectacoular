# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
"""
creates html and yaml layout for spectAcoular Apps
"""
# App folder
paths = ['MicGeomExample', 'FreqBeamformingExample', 'LiveViewExample',
         'TimeSamplesExample','Measurement_App','RotatingExample']
############### THEME COLOR SELECTIONS ################
# Set background color
bg_col  = '#2F2F2F'
# Set text color
txt_col = 'white'
# Set selection color
sel_col = '#1f77b4'
# Set warning button color: [color, hovered color]
# warning_but_col = ['#fdae61', '#f46d43']
# Set link color: [color, hovered color]
link_col = ['green', 'white']
# Font Sizes
ft_for_all = True # if True: font size of ft_f is valid for all
ft_f       = '10pt' # font of figures
ft_wt      = '14pt' # font of widgets and tables
# Font
ft         = "Helvetica" # bokeh default is "Helvetica"
ft_stl     = "normal" # italic, bold

if ft_for_all:
    ft_w = ft_f
else:
    ft_w = ft_wt

# read Acoular Logo:
logo_height = 50
logo_width = 50
Ac_logo = open('Acoular_logo', 'r').read()
for path in paths:
############### WRITE THEME.YAML AND INDEX.HTML #######
    # yaml file
    yaml_file = open('apps/' + path + '/theme.yaml', 'w')
    yaml_lines = [f'attrs:',
                  f'    Figure:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        border_fill_color: "{bg_col}"',
                  f'        outline_line_color: "{txt_col}"',
                  f'    Axis:',
                  f'        axis_line_color: "{txt_col}"',
                  f'        axis_label_text_color: "{txt_col}"',
                  f'        major_label_text_color: "{txt_col}"',
                  f'        major_label_text_font_size: "{ft_f}"',
                  f'        major_label_text_font: "{ft}"',
                  f'        major_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'        axis_label_text_font_size: "{ft_f}"',
                  f'        axis_label_text_font: "{ft}"',
                  f'        axis_label_text_font_style: "{ft_stl}"',
                  f'    Grid:',
                  f'        grid_line_dash: [6, 4]',
                  f'        grid_line_alpha: .3',
                  f'        grid_line_color: "{txt_col}"',
                  f'        minor_grid_line_color: "{txt_col}"',
                  f'        minor_grid_line_alpha: .1',
                  f'    Title:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        text_color: "{txt_col}"',
                  f'        text_font_size: "{ft_f}"',
                  f'        text_font: "{ft}"',
                  f'    Widget:',
                  f'        background: "{bg_col}"',
                  f'    Label:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        text_color: "{txt_col}"',
                  f'        text_font: "{ft}"',
                  f'    Legend:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        border_line_color: "{bg_col}"',
                  f'        title_text_color: "{txt_col}"',
                  f'        title_text_font: "{ft}"',
                  f'        label_text_color: "{txt_col}"',
                  f'        label_text_font: "{ft}"',
                  f'        label_text_font_size: "{ft_f}"',
                  f'    ColorBar:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        title_text_color: "{txt_col}"',
                  f'        title_text_font_size: "{ft_f}"',
                  f'        title_text_font: "{ft}"',
                  f'        major_tick_line_color: "{txt_col}"',
                  f'        minor_tick_line_color: "{txt_col}"',
                  f'        major_label_text_color: "{txt_col}"',
                  f'        major_label_text_font: "{ft}"',
                  f'        label_standoff: 7',
                  f'        major_label_text_font_size: "{ft_f}"']
    
    yaml_file.write('\n'.join(yaml_lines))
    yaml_file.close()
    
    # html file
    html_file = open('apps/' + path + '/templates/index.html', 'w')
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
# #                  '  @import url(https://fonts.googleapis.com/css?family=Noto+Sans);',
#                   '  .bk-root .bk-btn-warning:hover {', # set color of success button if hovered
#                  f'    background-color: {warning_but_col[1]} !important;',
#                  f'    border-color: {warning_but_col[1]} !important;',
#                   '    }',
                  # '  .bk-root .bk-btn-warning {', # set color of success button
                  # f'    color: {txt_col} !important;',
                  # f'    background-color: {warning_but_col[0]} !important;',
                  # f'    border-color: {warning_but_col[0]} !important;',
                  # '    }',
                  '  .slick-header-columns, .slick-headerrow-columns, .slick-footerrow-columns {',
                  '    overflow: visible !important;',
  	             f'    border-left: 0px solid {bg_col} !important;', # remove borders in header
  	             f'    border-top: 2px solid {txt_col} !important;',
  	             f'    border-bottom: 0px solid {bg_col} !important;',
  	             f'    border-right: 0px solid {bg_col} !important;',
                  '    }',
                  '  .bk-root .slick-header-column.ui-state-default {',
  	             f'    border-left: 0px solid {bg_col} !important;',
  	             f'    border-top: 0px solid {txt_col} !important;',
  	             f'    border-bottom: 1px solid {txt_col} !important;', # set bottom rule in header
  	             f'    border-right: 0px solid {bg_col} !important;',
                  '    }',
                  '  .bk-root .bk-tabs-header .bk-headers-wrapper {',
  	             f'    color: #bdbdbd', # set color of non-active tabs
                  '    }',
                  '  .bk {',
                 f'    font-size: {ft_w} !important;', 
                 f'    font-family: {ft} !important;',
                  '    }',
                  '  .slick-cell, .slick-headerrow-column, .slick-footerrow-column {',
  	             f'    border-right: 0px solid {txt_col} !important;', # remove vertical borders
  	             f'    border-left: 0px solid {txt_col} !important;',
                  '    }',
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
                  '  ::-webkit-scrollbar {',                # absolute width of browser scrollbar
                  '    width: 8px;',
                  '    }',
                  '  body {',
#                  '    font-family: "Noto Sans", sans-serif;',   # font body
                  '    -webkit-font-smoothing: antialiased;',
                  '    text-rendering: optimizeLegibility;',
                 f'    color: {txt_col};',                      # text color body
                 f'    font-size: {ft_f};',                     # font size body
                 f'    background: {bg_col};',                  # background color body
                  '    }',
                  '  ::-webkit-scrollbar-track {',          # scrollbar background
                 f'    background: {bg_col}',
                  '    }',
                  '  ::-webkit-scrollbar-thumb {',          # scrollbar slider
                 f'    background-color: {txt_col};',
                  '    border-radius: 4px;',
                  '    border: 2px;',
                  '    }',
                  '</style>',
                  '{% endblock %}']
    html_file.write('\n'.join(html_lines))
    html_file.close()