"""Layout constants for the measurement app."""

from bokeh.palettes import Spectral11

COLOR = Spectral11
MODE_COLORS = {'display': COLOR[1], 'msm': COLOR[8]}
CLIP_COLORS = {'display': COLOR[8], 'msm': COLOR[8]}

button_height = 80

# status Definitions
toggle_labels = {
    ('msm', False): 'MEASURE',
    ('msm', True): 'STOP MEASUREMENT',
    ('display', False): 'Display',
    ('display', True): 'Stop Display',
    ('beamf', True): 'Stop Beamforming',
    ('beamf', False): 'Beamforming',
}

plot_colors = {
    ('msm', True): [MODE_COLORS['msm'], CLIP_COLORS['msm']],
    ('msm', False): [MODE_COLORS['display'], CLIP_COLORS['display']],
    ('display', True): [MODE_COLORS['display'], CLIP_COLORS['display']],
    ('display', False): [MODE_COLORS['display'], CLIP_COLORS['display']],
    ('beamf', True): [],
    ('beamf', False): [],
}
