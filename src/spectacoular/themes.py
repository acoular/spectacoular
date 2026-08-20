"""SpectAcoular application themes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from bokeh.themes import Theme

DARK = 'dark'
LIGHT = 'light'
ThemeMode = Literal['dark', 'light']


@dataclass(frozen=True)
class SpectacoularTheme:
    """SpectAcoular-level theme composed around a Bokeh theme."""

    mode: ThemeMode
    bokeh_theme: Theme
    colors: dict[str, str]

    def root_styles(self):
        """Return CSS styles for the app shell root."""
        return {
            'background-color': self.colors['background'],
            'color': self.colors['text'],
        }


def _theme_json(colors):
    return {
        'attrs': {
            'Plot': {
                'background_fill_color': colors['plot_background'],
                'border_fill_color': colors['background'],
                'outline_line_color': colors['muted_text'],
            },
            'Grid': {
                'grid_line_color': colors['grid'],
                'grid_line_alpha': 0.35,
            },
            'Axis': {
                'axis_line_color': colors['muted_text'],
                'major_label_text_color': colors['text'],
                'axis_label_text_color': colors['text'],
                'major_tick_line_color': colors['muted_text'],
                'minor_tick_line_color': colors['muted_text'],
            },
            'Title': {
                'text_color': colors['text'],
            },
            'Line': {
                'line_color': colors['plot_line_primary'],
            },
            'Legend': {
                'label_text_color': colors['text'],
                'background_fill_color': colors['plot_background'],
                'border_line_color': colors['grid'],
            },
            'BaseColorBar': {
                'title_text_color': colors['text'],
                'major_label_text_color': colors['text'],
                'background_fill_color': colors['plot_background'],
                'major_tick_line_color': colors['muted_text'],
            },
        },
    }


def _make_theme(mode: ThemeMode, colors: dict[str, str]) -> SpectacoularTheme:
    return SpectacoularTheme(mode=mode, bokeh_theme=Theme(json=_theme_json(colors)), colors=colors)


_DARK_THEME = _make_theme(
    DARK,
    {
        'background': '#15191c',
        'plot_background': '#20262b',
        'text': '#e0e0e0',
        'muted_text': '#b0b0b0',
        'grid': '#4a525a',
        'plot_line_primary': '#00a6d6',
    },
)

_LIGHT_THEME = _make_theme(
    LIGHT,
    {
        'background': '#ffffff',
        'plot_background': '#ffffff',
        'text': '#333333',
        'muted_text': '#5b5b5b',
        'grid': '#d9d9d9',
        'plot_line_primary': '#0076a8',
    },
)

_THEMES = {
    DARK: _DARK_THEME,
    LIGHT: _LIGHT_THEME,
}


def get_theme(mode: str) -> SpectacoularTheme:
    """Return the SpectAcoular theme for *mode*."""
    try:
        return _THEMES[mode]
    except KeyError as exc:
        msg = f"Unknown SpectAcoular theme {mode!r}; expected one of: {', '.join(_THEMES)}"
        raise ValueError(msg) from exc
