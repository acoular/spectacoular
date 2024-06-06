# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2020-2021, Acoular Development Team.
#------------------------------------------------------------------------------
"""
creates html and yaml layout for spectAcoular Apps
"""
# App folder
paths = ['MicGeomExample', 'FreqBeamformingExample',
         'TimeSamplesExample','Measurement_App','RotatingExample','SLM']
############### THEME COLOR SELECTIONS ################
# Set background color
bg_col  = '#f6f6f6'#'#2F2F2F'
# Set text color
txt_col = 'black'
# Set selection color
sel_col = '#1f77b4'
# Set warning button color: [color, hovered color]
# warning_but_col = ['#fdae61', '#f46d43']
# Set link color: [color, hovered color]
link_col = ['green', 'white']
# Font Sizes
ft_for_all = True # if True: font size of ft_f is valid for all
ft_f       = '14pt' # font of figures
ft_f_major = '10pt' # major label font text size
ft_wt      = '18pt' # font of widgets and tables
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
                  f'    figure:',
                  f'        background_fill_color: "{bg_col}"',
                  f'        border_fill_color: "{bg_col}"',
                  f'        outline_line_color: "{txt_col}"',
                  f'    Axis:',
                  f'        axis_line_color: "{txt_col}"',
                  f'        axis_label_text_color: "{txt_col}"',
                  f'        major_label_text_color: "{txt_col}"',
                  f'        major_label_text_font_size: "{ft_f_major}"',
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
    html_lines = [
                '{% extends base %}',
                '{% block title %}SpectAcoular Application Layout{% endblock %}',
                '{% block postamble %}'
                '   <style>'
                '       {% include "styles.css" %}'
                '   </style>'
                #f' <img alt="Logo" src="{Ac_logo}" width="{logo_width}" height="{logo_height}">',
                '{% endblock %}'
                ]
    html_file.write('\n'.join(html_lines))
    html_file.close()

    # css file
    css_file = open('apps/' + path + '/templates/styles.css', 'w')
    css_lines = [
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
                  '  body {',
#                  '    font-family: "Noto Sans", sans-serif;',   # font body
                  '    -webkit-font-smoothing: antialiased;',
                  '    text-rendering: optimizeLegibility;',
                 f'    color: {txt_col};',                      # text color body
                 f'    font-size: {ft_f};',                     # font size body
                 f'    background: {bg_col};',                  # background color body
                  '    }',
    ]
    css_file.write('\n'.join(css_lines))
    css_file.close()