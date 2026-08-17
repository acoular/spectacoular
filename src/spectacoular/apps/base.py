"""Shared Bokeh application and audio-stream lifecycle classes."""

from __future__ import annotations

import logging
from threading import Thread

from .controls import available_controls

from bokeh.layouts import column
from bokeh.models import Div, Select


class BaseApp:
    """Base class for Bokeh applications."""

    title = 'SpectAcoular'

    def __init__(self, doc, logger=None):
        self.doc = doc
        self.logger = logger or logging.getLogger(__name__)
        self.root = None

    def build_root(self):
        """Build and return this application's root Bokeh layout."""
        raise NotImplementedError

    def server_doc(self):
        """Attach the application to its Bokeh document."""
        self.root = self.build_root()
        self.doc.add_root(self.root)
        self.doc.title = self.title


class AudioStreamApp(BaseApp):
    """Base app that consumes a configurable audio stream control."""

    def __init__(self, doc, logger=None, controls=None):
        super().__init__(doc, logger)
        self.controls = available_controls if controls is None else controls
        self.control = None
        self._unreleased_control = None
        self._closed = False
        self._running = False
        self._changing_control = False
        self._stream_content = column()
        self._control_content = column()
        self._error = Div()
        self._empty_loading = Div(visible=False)
        self._loading = column(self._empty_loading)
        self.control_select = Select(title='Audio stream', options=[('', 'Select audio stream')], value='')
        self.control_select.on_change('value', self._select_control)
        self._set_control_options()
        self._create_initial_control()
        self.doc.on_session_destroyed(self._session_destroyed)

    def _set_control_options(self):
        options = [('', 'Select audio stream')]
        options.extend((key, control.label) for key, control in self.controls.items())
        self.control_select.options = options

    def _set_selector(self, value):
        self._changing_control = True
        try:
            self.control_select.value = value
        finally:
            self._changing_control = False

    def _clear_control(self, message):
        self.control = None
        self._control_content.children = []
        self._stream_content.children = []
        self._set_selector('')
        self._show_error(message)

    def _create_initial_control(self):
        if not self.controls:
            self._show_error('No audio stream controls are available.')
            return
        default = 'phantom' if 'phantom' in self.controls else next(iter(self.controls))
        self._activate_control(default)

    def _show_error(self, message):
        self._error.text = f'<b>{message}</b>'

    def _clear_error(self):
        self._error.text = ''

    def build_loading_widget(self, control):
        """Return the complete source-initialization widget for *control*."""
        return control.build_loading_widget()

    def _hide_loading(self, control=None):
        if control or self.control:
            (control or self.control).loading_finished()
        self._loading.children = [self._empty_loading]

    def _new_control(self, control_id):
        return self.controls[control_id](doc=self.doc, logger=self.logger)

    def _activate_control(self, control_id):
        control = None
        try:
            control = self._new_control(control_id)
            control.on_source_changed(self._source_changed)
            content = control.get_widgets()
            stream_content = column()
        except Exception as exc:  # pragma: no cover - requires broken hardware backend
            self.logger.exception('Unable to create audio stream control')
            if control is not None:
                try:
                    control.close()
                except Exception:
                    self.logger.exception('Unable to close failed audio stream control')
                    self._unreleased_control = control
            self._clear_control(f'Unable to create audio stream control: {exc}')
            self._hide_loading()
            self.control_select.disabled = False
            return False
        self.control = control
        self._set_selector(control_id)
        self._control_content.children = [content]
        self._stream_content.children = [stream_content]
        self._clear_error()
        self._loading.children = [self.build_loading_widget(control)]
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
            self._hide_loading(control)
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
        return column(self.control_select, self._loading, self._error, self._control_content, self._stream_content)

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
