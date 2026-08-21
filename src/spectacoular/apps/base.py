"""Shared Bokeh application and audio-stream lifecycle classes."""

from __future__ import annotations

import logging
from threading import Thread

from spectacoular.themes.themes import (
    DOCUMENT_TEMPLATE,
    client_theme_switch_code,
    document_template_variables,
    get_theme,
)

from .controls import CONTROL_STYLES, CONTROL_WIDTH, available_controls

from bokeh.layouts import Spacer, column, row
from bokeh.models import CustomJS, Div, NumericInput, Select, Switch
from bokeh.models.widgets import Button


class BaseApp:
    """Base class for Bokeh applications."""

    title = 'SpectAcoular'
    default_theme = 'dark'

    def __init__(self, doc, logger=None):
        self.doc = doc
        self.doc.template = DOCUMENT_TEMPLATE
        self.doc.template_variables.update(document_template_variables())
        self.logger = logger or logging.getLogger(__name__)
        self.root = None
        self.app_content = None
        self.theme_mode = self.default_theme
        self.exit_button = Button(label='⏻', button_type='danger', width=40)
        self.exit_button.js_on_click(CustomJS(code='window.location.href = "about:blank";'))
        self.theme_switch = Switch(active=False, off_icon='dark_theme', on_icon='light_theme', width=60)
        self.theme_switch.js_on_change('active', self._client_theme_switch_callback())
        self.theme_switch.on_change('active', self._theme_switched)
        self._data_theme_ready_callback = CustomJS(code='')
        self.doc.js_on_event('document_ready', self._data_theme_ready_callback)
        self._header = None
        self._title = None

    def build_root(self):
        """Build and return this application's root Bokeh layout."""
        raise NotImplementedError

    def _build_action_frame(self, *controls):
        return column(row(*controls), width=CONTROL_WIDTH, styles=CONTROL_STYLES)

    def _build_header(self):
        self._title = Div(text=f'<b>{self.title}</b>')
        spacer = Spacer(sizing_mode='stretch_width')
        actions = self._build_action_frame(self.theme_switch, self.exit_button)
        right_padding = Spacer(width=20)
        return row(self._title, spacer, actions, right_padding, sizing_mode='stretch_width')

    def _build_root_layout(self, app_content):
        self._header = self._build_header()
        return column(self._header, app_content, sizing_mode='stretch_width')

    @staticmethod
    def _client_theme_switch_callback():
        return CustomJS(code=client_theme_switch_code())

    def _apply_theme(self, mode, *, update_bokeh_theme=False):
        theme = get_theme(mode)
        self.theme_mode = theme.mode
        if update_bokeh_theme:
            self.doc.theme = theme.bokeh_theme
        self._data_theme_ready_callback.code = theme.data_theme_script()
        self.theme_switch.active = theme.mode == 'light'
        if self.root is not None:
            self.root.styles = theme.root_styles()
        if self._header is not None:
            self._header.styles = theme.root_styles()
        if self._title is not None:
            self._title.styles = theme.root_styles()

    def _theme_switched(self, _attr, _old, active):
        self._apply_theme('light' if active else 'dark')

    def server_doc(self):
        """Attach the application to its Bokeh document."""
        self.app_content = self.build_root()
        self.root = self._build_root_layout(self.app_content)
        self.doc.add_root(self.root)
        self._apply_theme(self.default_theme, update_bokeh_theme=True)
        self.doc.title = self.title


class AudioStreamApp(BaseApp):
    """Base app that consumes a configurable audio stream control."""

    DEFAULT_UPDATE_PERIOD_MS = 50
    MIN_UPDATE_PERIOD_MS = 8

    def __init__(self, doc, logger=None, controls=None):
        super().__init__(doc, logger)
        self.controls = available_controls if controls is None else controls
        self.control = None
        self._unreleased_control = None
        self._closed = False
        self._running = False
        self._changing_control = False
        self._stream_content = column(Spacer(width=0, height=0))
        self._control_content = column(Spacer(width=0, height=0))
        self._error = Div()
        self.update_period_input = NumericInput(
            title='Update [ms]',
            value=self.DEFAULT_UPDATE_PERIOD_MS,
            low=self.MIN_UPDATE_PERIOD_MS,
            mode='int',
            width=100,
            description=(
                'Periodic view refresh interval in milliseconds. Lower values update the UI more often and may increase load.'
            ),
        )
        self.update_period_input.on_change('value', self._update_period_changed)
        self.control_select = Select(
            title='Audio stream',
            options=[('', 'Select audio stream'), *[(key, control.label) for key, control in self.controls.items()]],
            value='',
        )
        self.control_select.on_change('value', self._select_control)
        if not self.controls:
            self._show_error('No audio stream controls are available.')
        self.doc.on_session_destroyed(self._session_destroyed)

    def _set_selector(self, value):
        self._changing_control = True
        try:
            self.control_select.value = value
        finally:
            self._changing_control = False

    def _clear_control(self, message):
        self.control = None
        self._control_content.children = [Spacer(width=0, height=0)]
        self._stream_content.children = [Spacer(width=0, height=0)]
        self._set_selector('')
        self._show_error(message)

    def _show_error(self, message):
        self._error.text = f'<b>{message}</b>'

    def _clear_error(self):
        self._error.text = ''

    @property
    def update_period_ms(self):
        """Validated periodic view update interval in milliseconds."""
        value = self.update_period_input.value
        if value is None or value < self.MIN_UPDATE_PERIOD_MS:
            value = self.MIN_UPDATE_PERIOD_MS
            self.update_period_input.value = value
        return int(value)

    def _update_period_changed(self, _attr, _old, _new):
        self.update_period_ms

    def _build_header(self):
        self._title = Div(text=f'<b>{self.title}</b>')
        spacer = Spacer(sizing_mode='stretch_width')
        actions = self._build_action_frame(self.update_period_input, self.theme_switch, self.exit_button)
        right_padding = Spacer(width=20)
        return row(self._title, spacer, actions, right_padding, sizing_mode='stretch_width')

    def _activate_control(self, control_id):
        control = None
        try:
            control = self.controls[control_id](doc=self.doc, logger=self.logger)
            control.on_source_changed(self._source_changed)
            content = control.get_widgets()
            stream_content = column(Spacer(width=0, height=0))
        except Exception as exc:  # pragma: no cover - requires broken hardware backend
            self.logger.exception('Unable to create audio stream control')
            if control is not None:
                try:
                    control.close()
                except Exception:
                    self.logger.exception('Unable to close failed audio stream control')
                    self._unreleased_control = control
            self._clear_control(f'Unable to create audio stream control: {exc}')
            if control is not None:
                control.loading_finished()
            self.control_select.disabled = False
            return False
        self.control = control
        self._set_selector(control_id)
        self._control_content.children = [content]
        self._stream_content.children = [stream_content]
        self._clear_error()
        self.control_select.disabled = True
        control.set_config_enabled(False)
        self.doc.add_next_tick_callback(lambda: self._initialize_control(control))
        return True

    def _stop_and_close(self, control):
        error = None
        try:
            self.stop_consumers()
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - consumer teardown failure
            error = exc
        if self._running:
            try:
                control.stop()
            except Exception as exc:  # noqa: BLE001  # pragma: no cover - requires broken hardware backend
                if error is None:
                    error = exc
            try:
                control.set_config_enabled(True)
            except Exception as exc:  # noqa: BLE001  # pragma: no cover - requires broken hardware backend
                if error is None:
                    error = exc
            finally:
                self.control_select.disabled = False
                self._running = False
        try:
            control.close()
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - requires broken hardware backend
            if error is None:
                error = exc
        if error is not None:
            raise error

    def _select_control(self, _attr, old, new):
        if self._changing_control:
            return
        if new == old or self._running or not new:
            self._set_selector(old)
            return
        old_control = self.control
        if old_control is not None:
            try:
                self._stop_and_close(old_control)
            except Exception as exc:  # pragma: no cover - requires broken hardware backend
                self.logger.exception('Unable to stop and close audio stream control')
                self._unreleased_control = old_control
                self._clear_control(f'Unable to close audio stream control: {exc}')
                return
            self.control = None
        self._activate_control(new)

    def _initialize_control(self, control):
        """Initialize a deferred source without blocking Bokeh's event loop."""
        Thread(target=self._create_source, args=(control,), daemon=True).start()

    def _create_source(self, control):
        try:
            control.initialize_source()
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - requires broken hardware backend
            self.doc.add_next_tick_callback(lambda error=exc: self._finish_source(control, error))
        else:
            self.doc.add_next_tick_callback(lambda: self._finish_source(control))

    def _finish_source(self, control, error=None):
        """Apply a background source-initialization result on Bokeh's event loop."""
        if control is not self.control or self._closed:
            return
        try:
            if error is not None:
                self.logger.error('Unable to create audio stream control: %s', error)
                self._clear_control(f'Unable to create audio stream control: {error}')
            else:
                try:
                    control.source_initialized()
                    control.set_config_enabled(True)
                    self._control_content.children = [control.get_widgets()]
                    self.rebuild_stream_content()
                except Exception as exc:  # pragma: no cover - requires broken hardware backend
                    self.logger.exception('Unable to create audio stream control')
                    self._clear_control(f'Unable to create audio stream control: {exc}')
        finally:
            control.loading_finished()
            self.control_select.disabled = False

    def _source_changed(self):
        if self._running:
            self.logger.warning('Ignoring source change while audio stream is running')
            return
        self.rebuild_stream_content()

    def rebuild_stream_content(self):
        """Replace source-dependent content. Subclasses provide the layout."""
        if self.control is not None:
            self._stream_content.children = [self.build_stream_content(self.control.source)]

    def build_stream_content(self, source):
        """Build content consuming *source*."""
        raise NotImplementedError

    def build_root(self):
        """Build the selector, error message, settings, and stream content."""
        return column(self.control_select, self._error, self._control_content, self._stream_content)

    def start(self):
        """Start the selected backend and lock source configuration."""
        if self._running or self.control is None:
            return
        self.control.start()
        self.control.set_config_enabled(False)
        self.control_select.disabled = True
        self._running = True

    def stop_consumers(self):
        """Stop app-owned downstream consumers. Subclasses may override."""

    def stop(self):
        """Stop app consumers before stopping the selected backend."""
        self.stop_consumers()
        if not self._running or self.control is None:
            return
        try:
            self.control.stop()
        finally:
            self.control.set_config_enabled(True)
            self.control_select.disabled = False
            self._running = False

    def _session_destroyed(self, _session_context):
        self.close()

    def close(self):
        """Release consumers and backend resources; safe to call repeatedly."""
        if self._closed:
            return
        self._closed = True
        if self.control is not None:
            try:
                self._stop_and_close(self.control)
            except Exception:
                self.logger.exception('Unable to close audio stream control')
                self._unreleased_control = self.control
            self.control = None
