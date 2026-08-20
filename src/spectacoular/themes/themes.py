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
WIDGET_MODELS_WITH_THEME_CSS = ('Button', 'Switch', 'Toggle')
DOCUMENT_TEMPLATE = get_env().from_string(
    """
{% extends "file.html.jinja" %}
{% block preamble %}
{{ super() }}
<style>
{{ acoular_css | safe }}
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
        return {
            'background-color': 'var(--ac-color-background)',
            'color': 'var(--ac-color-text)',
        }

    def data_theme_script(self):
        """Return JS that selects the matching acoular.css theme block."""
        return f'document.documentElement.setAttribute("data-theme", "{self.mode}");'


def _load_brand_bokeh_theme_json() -> dict[str, object]:
    return json.loads(files('acoular_brand.assets').joinpath('acoular.bokeh.json').read_text())


def _load_brand_theme_colors(mode: ThemeMode) -> dict[str, str]:
    theme_toml = tomllib.loads(files('acoular_brand').joinpath('theme.toml').read_text())
    return theme_toml[mode]


def _apply_plot_theme_colors(theme_json: dict[str, object], mode: ThemeMode) -> None:
    colors = _load_brand_theme_colors(mode)
    attrs = theme_json['attrs']
    attrs['Figure'].update(
        {
            'background_fill_color': colors['background'],
            'border_fill_color': colors['background'],
            'outline_line_color': colors['border'],
        }
    )
    attrs['Axis'].update(
        {
            'axis_line_color': colors['border'],
            'major_label_text_color': colors['muted'],
            'axis_label_text_color': colors['text'],
        }
    )
    attrs['Grid'].update({'grid_line_color': colors['border']})
    attrs['Title'].update({'text_color': colors['text']})


def _load_brand_css() -> str:
    return files('acoular_brand.assets').joinpath('acoular.css').read_text()


def document_template_variables() -> dict[str, str]:
    """Return template variables needed by the SpectAcoular document template."""
    return {'acoular_css': _load_brand_css()}


def _load_widget_stylesheets() -> list[str]:
    return [files('spectacoular.themes').joinpath('bokeh_widgets.css').read_text()]


def _add_widget_theme_attrs(theme_json: dict[str, object]) -> None:
    widget_attrs = {
        'stylesheets': _load_widget_stylesheets(),
    }
    for model_name in WIDGET_MODELS_WITH_THEME_CSS:
        theme_json['attrs'][model_name] = widget_attrs


def _load_bokeh_theme_json(mode: ThemeMode) -> dict[str, object]:
    theme_json = _load_brand_bokeh_theme_json()
    _apply_plot_theme_colors(theme_json, mode)
    _add_widget_theme_attrs(theme_json)
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
