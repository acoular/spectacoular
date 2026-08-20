"""SpectAcoular application themes."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from importlib.resources import files
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


def _load_acoular_brand_colors() -> dict[str, dict[str, str]]:
    return tomllib.loads(files('acoular_brand').joinpath('theme.toml').read_text())


def _load_brand_bokeh_theme_json() -> dict[str, object]:
    return json.loads(files('acoular_brand.assets').joinpath('acoular.bokeh.json').read_text())


def _theme_json_from_tokens(colors: dict[str, str]) -> dict[str, object]:
    return {
        'attrs': {
            'Figure': {
                'background_fill_color': colors['background'],
                'border_fill_color': colors['background'],
                'outline_line_color': colors['border'],
            },
            'Axis': {
                'axis_line_color': colors['border'],
                'major_label_text_color': colors['muted'],
                'axis_label_text_color': colors['text'],
            },
            'Grid': {
                'grid_line_color': colors['border'],
                'grid_line_alpha': 0.7,
            },
            'Title': {
                'text_color': colors['text'],
            },
        },
    }


def _make_theme(mode: ThemeMode, colors: dict[str, str], theme_json: dict[str, object]) -> SpectacoularTheme:
    return SpectacoularTheme(mode=mode, bokeh_theme=Theme(json=theme_json), colors=colors)


def _build_themes() -> dict[str, SpectacoularTheme]:
    acoular_brand_colors = _load_acoular_brand_colors()
    return {
        DARK: _make_theme(DARK, acoular_brand_colors[DARK], _theme_json_from_tokens(acoular_brand_colors[DARK])),
        LIGHT: _make_theme(LIGHT, acoular_brand_colors[LIGHT], _load_brand_bokeh_theme_json()),
    }


_THEMES = _build_themes()


def get_theme(mode: str) -> SpectacoularTheme:
    """Return the SpectAcoular theme for *mode*."""
    try:
        return _THEMES[mode]
    except KeyError as exc:
        msg = f"Unknown SpectAcoular theme {mode!r}; expected one of: {', '.join(_THEMES)}"
        raise ValueError(msg) from exc
