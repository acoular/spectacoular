"""SpectAcoular application themes."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from bokeh.core.templates import get_env
from bokeh.themes import Theme

DARK = 'dark'
LIGHT = 'light'
ThemeMode = Literal['dark', 'light']
MODELS_WITH_THEME_CSS = ('Widget', 'Tooltip')
MODE_COLOR_NAMES = {
    LIGHT: {
        'background': 'background-light',
        'text': 'background-dark',
        'muted': 'background-dark',
        'border': 'muted-light',
    },
    DARK: {
        'background': 'background-dark',
        'text': 'brand-light',
        'muted': 'muted-light',
        'border': 'muted-dark',
    },
}
DARK_WIDGET_CSS = """
:host {
  color: var(--acoular-color-brand-light);
  --color: var(--acoular-color-brand-light);
  --icon-color: var(--acoular-color-brand-light);
  --inverted-color: var(--acoular-color-brand-light);
  --background-color: var(--acoular-color-background-dark);
  --tooltip-text: var(--acoular-color-brand-light);
  --tooltip-color: var(--acoular-color-background-dark);
  --default: var(--acoular-color-background-dark);
  --default-border: var(--acoular-color-muted-dark);
  --default-hover: var(--acoular-color-background-dark);
  --default-active: color-mix(in srgb, var(--acoular-color-background-dark) 85%, black);
  --primary: var(--acoular-color-brand);
  --primary-hover: var(--acoular-color-brand);
  --primary-active: color-mix(in srgb, var(--acoular-color-brand) 85%, black);
  --light: var(--acoular-color-background-dark);
  --light-hover: var(--acoular-color-background-dark);
  --light-active: color-mix(in srgb, var(--acoular-color-background-dark) 85%, black);
  --active-bg: var(--acoular-color-brand-light);
  --active-fg: var(--acoular-color-background-dark);
  --inactive-bg: var(--acoular-color-muted-dark);
  --inactive-fg: var(--acoular-color-muted-light);
}

:host .bk-btn {
  color: var(--acoular-color-brand-light);
}

:host .bk-input {
  background-color: var(--acoular-color-brand-light);
  color: var(--acoular-color-background-dark);
}
"""
DOCUMENT_TEMPLATE = get_env().from_string(
    """
{% extends "file.html.jinja" %}
{% block preamble %}
{{ super() }}
<style>
{{ acoular_css | safe }}
html,
body {
  min-height: 100%;
}

:root,
html[data-theme="light"],
html[data-theme="light"] body {
  background-color: var(--acoular-color-background-light);
  color: var(--acoular-color-background-dark);
}

html[data-theme="dark"],
html[data-theme="dark"] body {
  background-color: var(--acoular-color-background-dark);
  color: var(--acoular-color-brand-light);
}
</style>
{% endblock %}
"""
)


@dataclass(frozen=True)
class SpectacoularTheme:
    """SpectAcoular-level theme composed around a Bokeh theme."""

    mode: ThemeMode
    bokeh_theme: Theme

    def root_styles(self):
        """Return CSS variable styles for the app shell root."""
        colors = MODE_COLOR_NAMES[self.mode]
        return {
            'background-color': f'var(--acoular-color-{colors["background"]})',
            'color': f'var(--acoular-color-{colors["text"]})',
        }

    def data_theme_script(self):
        """Return JS that selects the matching acoular.css theme block."""
        return f'document.documentElement.setAttribute("data-theme", "{self.mode}");'


def _load_brand_bokeh_theme_json() -> dict[str, object]:
    return json.loads(files('acoular_brand.assets').joinpath('acoular.bokeh.json').read_text())


def _load_brand_color_tokens() -> dict[str, str]:
    theme_toml = tomllib.loads(files('acoular_brand').joinpath('theme.toml').read_text())
    return theme_toml['colors']


def get_acoular_color(name: str) -> str:
    """Return an Acoular corporate color from theme.toml [colors]."""
    return _load_brand_color_tokens()[name]


def _load_brand_theme_colors(mode: ThemeMode) -> dict[str, str]:
    color_tokens = _load_brand_color_tokens()
    return {name: color_tokens[token_name] for name, token_name in MODE_COLOR_NAMES[mode].items()}


def _apply_plot_theme_colors(theme_json: dict[str, object], mode: ThemeMode) -> None:
    colors = _load_brand_theme_colors(mode)
    attrs = theme_json['attrs']
    figure_attrs = {
        'background_fill_color': colors['background'],
        'border_fill_color': colors['background'],
        'outline_line_color': colors['border'],
    }
    for model_name in ('Figure', 'figure', 'Plot'):
        attrs.setdefault(model_name, {}).update(figure_attrs)
    attrs['Axis'].update(
        {
            'axis_line_color': colors['border'],
            'major_label_text_color': colors['muted'],
            'axis_label_text_color': colors['text'],
        }
    )
    attrs['Grid'].update({'grid_line_color': colors['border']})
    attrs['Title'].update({'text_color': colors['text']})
    attrs.setdefault('ColorBar', {}).update(
        {
            'background_fill_color': colors['background'],
            'title_text_color': colors['text'],
            'major_label_text_color': colors['muted'],
            'major_tick_line_color': colors['border'],
            'border_line_color': colors['border'],
        }
    )


def _load_brand_css() -> str:
    return files('acoular_brand.assets').joinpath('acoular.css').read_text()


def document_template_variables() -> dict[str, str]:
    """Return template variables needed by the SpectAcoular document template."""
    return {'acoular_css': _load_brand_css()}


def _load_widget_stylesheets(mode: ThemeMode) -> list[str]:
    stylesheets = [files('spectacoular.themes').joinpath('bokeh_widgets.css').read_text()]
    if mode == DARK:
        stylesheets.append(DARK_WIDGET_CSS)
    return stylesheets


def _add_widget_theme_attrs(theme_json: dict[str, object], mode: ThemeMode) -> None:
    widget_attrs = {
        'stylesheets': _load_widget_stylesheets(mode),
    }
    for model_name in MODELS_WITH_THEME_CSS:
        theme_json['attrs'][model_name] = widget_attrs


def _load_bokeh_theme_json(mode: ThemeMode) -> dict[str, object]:
    theme_json = _load_brand_bokeh_theme_json()
    _apply_plot_theme_colors(theme_json, mode)
    _add_widget_theme_attrs(theme_json, mode)
    return theme_json


def _make_theme(mode: ThemeMode) -> SpectacoularTheme:
    return SpectacoularTheme(
        mode=mode,
        bokeh_theme=Theme(json=_load_bokeh_theme_json(mode)),
    )


_THEMES = {
    DARK: _make_theme(DARK),
    LIGHT: _make_theme(LIGHT),
}


def get_theme(mode: str) -> SpectacoularTheme:
    """Return the SpectAcoular theme for *mode*."""
    try:
        return _THEMES[mode]
    except KeyError as exc:
        msg = f"Unknown SpectAcoular theme {mode!r}; expected one of: {', '.join(_THEMES)}"
        raise ValueError(msg) from exc
