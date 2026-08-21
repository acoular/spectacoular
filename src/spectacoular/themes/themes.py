"""SpectAcoular application themes."""

from __future__ import annotations

import json
import tomllib
from base64 import b64encode
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from bokeh.core.templates import get_env
from bokeh.themes import Theme

DARK = 'dark'
LIGHT = 'light'
ThemeMode = Literal['dark', 'light']
MODELS_WITH_THEME_CSS = ('Widget', 'Tooltip')
BEAMFORMING_COLORMAP_TAG = 'spectacoular-beamforming-colormap'
PLOT_THEME_COLORS_PLACEHOLDER = '__SPECTACOULAR_PLOT_THEME_COLORS__'
LOGO_HTML_PLACEHOLDER = '__SPECTACOULAR_LOGO_HTML__'
LOGO_MODEL_TAG = 'spectacoular-app-logo'
LOGO_RESOURCE_CANDIDATES = {
    DARK: (
        ('acoular_brand.assets', 'acoular_logo_dark.svg'),
        ('acoular_brand.assets', 'acoular_logo_dark_inverted.svg'),
        ('acoular_brand.assets', 'acoular_logo_dark.png'),
        ('acoular_sphinx._static', 'acoular_logo_dark.png'),
    ),
    LIGHT: (
        ('acoular_brand.assets', 'acoular_logo.svg'),
        ('acoular_brand.assets', 'acoular_logo_light.svg'),
        ('acoular_brand.assets', 'acoular_logo_light.png'),
        ('acoular_sphinx._static', 'acoular_logo_light.png'),
    ),
}
LOGO_MIME_TYPES = {
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
}
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
DOCUMENT_TEMPLATE = get_env().from_string(
    """
{% extends "file.html.jinja" %}
{% block preamble %}
{{ super() }}
<style>
{{ acoular_css | safe }}
{{ page_css | safe }}
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


def _brand_bokeh_theme_json() -> dict[str, object]:
    return {'attrs': {'Figure': {}, 'Axis': {}, 'Grid': {'grid_line_alpha': 0.7}, 'Title': {}}}


def _load_brand_color_tokens() -> dict[str, str]:
    theme_toml = tomllib.loads(files('acoular_brand').joinpath('theme.toml').read_text())
    return theme_toml['colors']


def get_acoular_color(name: str) -> str:
    """Return an Acoular corporate color from theme.toml [colors]."""
    return _load_brand_color_tokens()[name]


def _load_brand_theme_colors(mode: ThemeMode) -> dict[str, str]:
    color_tokens = _load_brand_color_tokens()
    return {name: color_tokens[token_name] for name, token_name in MODE_COLOR_NAMES[mode].items()}


def beamforming_colormap_palette(mode: ThemeMode, size: int = 256) -> list[str]:
    """Return the Acoular Beamforming colormap for *mode* as Bokeh hex colors."""
    from acoular_brand.colormaps import register_colormaps  # noqa: PLC0415
    from matplotlib import colormaps  # noqa: PLC0415
    from matplotlib.colors import to_hex  # noqa: PLC0415

    register_colormaps()
    name = 'acoular_r' if mode == LIGHT else 'acoular'
    return [to_hex(colormaps[name](index / (size - 1)), keep_alpha=False) for index in range(size)]


def client_plot_theme_colors() -> dict[ThemeMode, dict[str, object]]:
    """Return concrete plot colors for the client-side theme switcher.

    Bokeh plot colors and color-mapper palettes are model properties used by
    canvas/SVG renderers, not normal DOM CSS.  They cannot reliably be
    represented as inherited CSS variables, so the runtime switch callback
    patches those properties directly in the browser while keeping
    ``Document.theme`` stable.
    """
    return {
        mode: {
            **_load_brand_theme_colors(mode),
            'beamforming_palette': beamforming_colormap_palette(mode),
        }
        for mode in (DARK, LIGHT)
    }


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
    attrs.setdefault('Axis', {}).update(
        {
            'axis_line_color': colors['border'],
            'major_label_text_color': colors['muted'],
            'axis_label_text_color': colors['text'],
        }
    )
    attrs.setdefault('Grid', {}).update({'grid_line_color': colors['border']})
    attrs.setdefault('Title', {}).update({'text_color': colors['text']})
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


def _logo_mime_type(filename: str) -> str:
    for suffix, mime_type in LOGO_MIME_TYPES.items():
        if filename.endswith(suffix):
            return mime_type
    return 'application/octet-stream'


def _load_logo_data_uri(mode: ThemeMode) -> str | None:
    for package, filename in LOGO_RESOURCE_CANDIDATES[mode]:
        try:
            logo_bytes = files(package).joinpath(filename).read_bytes()
        except (FileNotFoundError, ModuleNotFoundError):
            continue
        encoded_logo = b64encode(logo_bytes).decode('ascii')
        return f'data:{_logo_mime_type(filename)};base64,{encoded_logo}'
    return None


def _logo_html(mode: ThemeMode) -> str:
    data_uri = _load_logo_data_uri(mode)
    if data_uri is None:
        return '<span class="spectacoular-app-logo-fallback">acoular</span>'
    return f'<img class="spectacoular-app-logo-image" src="{data_uri}" alt="Acoular logo">'


def acoular_logo_html(mode: ThemeMode = DARK) -> str:
    """Return single-logo HTML for the Acoular application header."""
    return f'<div class="spectacoular-app-logo" aria-label="Acoular">{_logo_html(mode)}</div>'


def client_logo_html() -> dict[ThemeMode, str]:
    """Return per-theme logo HTML for browser-side theme switching."""
    return {mode: acoular_logo_html(mode) for mode in (DARK, LIGHT)}


def _load_page_css() -> str:
    return files('spectacoular.themes').joinpath('page.css').read_text()


def _load_client_theme_js() -> str:
    return files('spectacoular.themes').joinpath('client_theme.js').read_text()


def client_theme_switch_code() -> str:
    """Return runtime theme-switch JavaScript with concrete plot colors injected."""
    return (
        _load_client_theme_js()
        .replace(PLOT_THEME_COLORS_PLACEHOLDER, json.dumps(client_plot_theme_colors()))
        .replace(LOGO_HTML_PLACEHOLDER, json.dumps(client_logo_html()))
    )


def document_template_variables() -> dict[str, str]:
    """Return template variables needed by the SpectAcoular document template."""
    return {'acoular_css': _load_brand_css(), 'page_css': _load_page_css()}


def _load_widget_stylesheets(_mode: ThemeMode) -> list[str]:
    return [files('spectacoular.themes').joinpath('bokeh_widgets.css').read_text()]


def _add_widget_theme_attrs(theme_json: dict[str, object], mode: ThemeMode) -> None:
    widget_attrs = {
        'stylesheets': _load_widget_stylesheets(mode),
    }
    for model_name in MODELS_WITH_THEME_CSS:
        theme_json['attrs'][model_name] = widget_attrs


def _load_bokeh_theme_json(mode: ThemeMode) -> dict[str, object]:
    theme_json = _brand_bokeh_theme_json()
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
