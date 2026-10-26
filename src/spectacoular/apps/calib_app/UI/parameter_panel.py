"""Calibration parameter panel UI component."""

from .colors import ACC, BD, GRN, ORG, S1, T1, T2, T3
from .tooltips import info_label

from bokeh.layouts import column, row
from bokeh.models import Button, Div, InlineStyleSheet, RadioButtonGroup, Select, TextInput


class ParameterPanel:
    """Panel for editing and displaying calibration parameters.

    Provides UI controls for:
    - Selecting calibration mode (Edit/Select vs Automatic)
    - Selecting active channel
    - Setting calibration level and unit
    - Setting calibration frequency
    - Setting calibration time and stability tolerance
    - Displaying current calibration factor and stability status

    Attributes
    ----------
        logger: Logger instance.
        num_channels: Total number of channels available.
        on_params_change: Callback for parameter changes.
        on_calib_channel_change: Callback for channel selection changes.
        auto_detected_channel: Currently auto-detected channel (int or None).
        ui_state: CalibUIState instance for reading current state.

        Widgets: mode_toggle, edit_channel_select, pegel_input, pegel_unit_select,
        freq_input, calib_time_input, stability_tolerance_input, bew_select,
        btn_set, result_factor, result_status, layout.
    """

    def __init__(self, ui_state, logger, num_channels=8):
        """Initialize the parameter panel.

        Args:
            ui_state: CalibUIState instance for accessing current state.
            logger: Logger instance for debugging.
            num_channels: Number of available channels (default: 8).
        """
        self.logger = logger
        self.num_channels = num_channels
        self.on_params_change = None  # called when calib params or edit channel change
        self.on_calib_channel_change = None  # called when calibration channel changes
        self.auto_detected_channel = None  # set by consume_auto() while Auto mode is running
        self.logger.debug('ParameterPanel: Initialization started')
        self.ui_state = ui_state
        self._build_styles()
        self._build_widgets()
        self._build_layout()
        self.logger.debug('ParameterPanel: Initialization completed')

    @property
    def get_channel_int(self):
        """Get the currently selected channel as an integer (0-based).

        Returns
        -------
            int or None: Channel index, or None if "All" is selected.
        """
        if self.edit_channel_select.value == 'All':
            return None
        return int(self.edit_channel_select.value.split()[-1]) - 1

    def get_value_from_ui_state(self, value):
        """Get a value from UI state for the currently selected channel.

        Args:
            value: Key to retrieve from channel data (e.g., "band", "magnitude").

        Returns
        -------
            str: String representation of the value, or "0" / "" for "All" selection.
        """
        ch = self.get_channel_int
        if ch is None and value != 'unit':
            return str(0)
        if ch is None and value == 'unit':
            return ''
        return str(self.ui_state.get(ch)[value])

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _build_styles(self):
        """Create CSS styles for input widgets and buttons."""
        self.logger.debug('ParameterPanel: Building styles')
        self.input_style = InlineStyleSheet(
            css=f"""
            :host {{
                --bokeh-base-font-size: .72rem;
            }}
            .bk-input {{
                background-color: {S1};
                color:            {T1};
                border:           1px solid {BD};
                border-radius:    4px;
                font-size:        .72rem;
            }}
            .bk-input:focus {{
                border-color:     {ACC};
                box-shadow:       0 0 0 2px {ACC}33;
                outline:          none;
            }}
            label {{
                color:            {T2};
                font-size:        .7rem;
                font-weight:      600;
            }}
        """
        )

        self.select_style = InlineStyleSheet(
            css=f"""
            :host {{
                --bokeh-base-font-size: .72rem;
            }}
            .bk-input {{
                background-color: {S1};
                color:            {T1};
                border:           1px solid {BD};
                border-radius:    4px;
                font-size:        .72rem;
            }}
            .bk-input:focus {{
                border-color:     {ACC};
                outline:          none;
            }}
            label {{
                color:            {T2};
                font-size:        .7rem;
                font-weight:      600;
            }}
        """
        )
        self.radio_style = InlineStyleSheet(
            css=f"""
            :host {{
                --bokeh-base-font-size: .72rem;
            }}
            .bk-btn {{
                background-color: {S1};
                color:            {T2};
                border:           1px solid {BD};
                font-size:        .72rem;
            }}
            .bk-btn:hover {{
                border-color: {ACC};
            }}
            /* aktiver / ausgewählter Button */
            .bk-btn.bk-active {{
                background-color: {ACC}22;   /* leichtes Blau (ca. 13% Deckkraft) */
                color:            {ACC};
                border-color:     {ACC};
                font-weight:      600;
            }}
        """
        )

        self.result_box_style = InlineStyleSheet(
            css="""
        :host {
            background:    rgba(26,127,55,.04);
            border:        1px solid rgba(26,127,55,.2);
            border-radius: 8px;
            padding:       10px 12px;
            }
        """
        )
        self.logger.debug('ParameterPanel: Styles built')

    # ------------------------------------------------------------------
    # Widget Creation
    # ------------------------------------------------------------------
    def _build_widgets(self):
        """Create all UI widgets (inputs, selects, buttons, labels)."""
        self.logger.debug('ParameterPanel: Creating widgets')

        self.mode_toggle = RadioButtonGroup(
            labels=['Edit/Select', 'Automatic'],
            active=0,
            sizing_mode='stretch_width',
            stylesheets=[self.radio_style],
        )

        self.title = Div(
            text=f"<span style='font-size:11px;color:{T2};font-weight:bold;'>◈ CALIBRATION PARAMETERS</span>",
            sizing_mode='stretch_width',
        )
        self.logger.debug('     Title Div created')

        self.edit_channel_select = Select(
            value='Channel 1',
            options=['All'] + [f'Channel {i}' for i in range(1, self.num_channels + 1)],
            sizing_mode='stretch_width',
            stylesheets=[self.select_style],
        )

        self.logger.debug('     Channel Select created')

        # Info-Labels
        self.channel_label = info_label('Channel', 'Channel to edit / calibrate')
        self.calib_time_label = info_label(
            'Calibration Time (s)', "Time that the signal has to be stable until it's considered calibrated"
        )
        self.pegel_label = info_label('Calibration Level', 'Reference level of the calibrator')
        self.pegel_unit_label = info_label('Calibration Level Unit', 'Unit of the calibration level')
        self.freq_label = info_label('Calib. Freq. (Hz)', 'Frequency of the calibrator')
        self.stability_tolerance_label = info_label(
            'Stability Tolerance (dB)',
            'The maximum standard deviation divided by the mean of the current buffer to be considered stable',
        )
        self.bew_label = info_label('Filter', 'Weighting filter for the signal')
        self.logger.debug('     Info tooltips created')

        self.pegel_unit_select = Select(
            value='dB', options=['dB', 'N', 'm/s²'], sizing_mode='stretch_width', stylesheets=[self.select_style]
        )

        self.logger.debug('     Unit select created (Default: dB)')

        self.freq_input = TextInput(
            value=self.get_value_from_ui_state('band'),
            placeholder='e.g. 1000 Hz',
            sizing_mode='stretch_width',
            stylesheets=[self.input_style],
        )

        self.logger.debug('     Frequency input created (Default: 1000 Hz)')

        self.stability_tolerance_input = TextInput(
            value=self.get_value_from_ui_state('stability_tolerance'),
            placeholder='e.g. 0.5',
            sizing_mode='stretch_width',
            stylesheets=[self.input_style],
        )

        self.bew_select = Select(
            value='Octavefilter', options=['Octavefilter'], sizing_mode='stretch_width', stylesheets=[self.select_style]
        )
        self.logger.debug('     Filter select created (Default: Octave filter)')

        self.btn_set = Button(label='Set', button_type='primary', sizing_mode='stretch_width')

        self.pegel_input = TextInput(
            value=self.get_value_from_ui_state('magnitude'),
            placeholder='e.g. 94 dB',
            sizing_mode='stretch_width',
            stylesheets=[self.input_style],
        )

        self.logger.debug('     Level input created (Default: 94 dB)')

        self.calib_time_input = TextInput(
            value=self.get_value_from_ui_state('calib_time'),
            sizing_mode='stretch_width',
            stylesheets=[self.input_style],
        )

        # Result widgets
        self.result_factor = Div(text=f"<b style='font-size:16px;color:{T1};'>—</b>")
        self.result_status = Div(text=f"<b style='font-size:16px;color:{T3};'>—</b>")
        self.status_info = info_label(
            'STABILITY',
            'STABLE: the relative spread (std/mean) of the latest measurement blocks '
            'is below the threshold (stability tolerance). UNSTABLE: spread still too high. '
            'When the signal stays stable long enough, the calibration factor is applied.',
            width=320,
            direction='up',
        )
        self.factor_info = info_label(
            'CALIBRATION FACTOR',
            'Currently computed calibration factor (reference level ÷ mean value). ',
            width=320,
            direction='up',
        )
        self.logger.debug('     Result widgets created')

        self.logger.debug('ParameterPanel: All widgets created')

    # ------------------------------------------------------------------
    # Layout Creation
    # ------------------------------------------------------------------
    def _build_layout(self):
        """Assemble all widgets into the final panel layout."""
        self.logger.debug('ParameterPanel: Building layout')

        self.result_section = column(
            row(
                column(
                    self.result_factor,
                    self.factor_info,
                ),
                column(
                    self.result_status,
                    self.status_info,
                ),
                sizing_mode='stretch_width',
            ),
            sizing_mode='stretch_width',
            stylesheets=[self.result_box_style],
        )

        self.layout = column(
            self.title,
            self.mode_toggle,
            self.channel_label,
            self.edit_channel_select,
            self.pegel_label,
            self.pegel_input,
            self.pegel_unit_label,
            self.pegel_unit_select,
            row(self.freq_label, self.bew_label, sizing_mode='stretch_width'),
            row(self.freq_input, self.bew_select, sizing_mode='stretch_width'),
            row(self.calib_time_label, self.stability_tolerance_label, sizing_mode='stretch_width'),
            row(self.calib_time_input, self.stability_tolerance_input, sizing_mode='stretch_width'),
            self.btn_set,
            self.result_section,
            sizing_mode='stretch_width',
        )
        self.logger.debug('ParameterPanel: Layout complete')

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------

    def refresh(self, ui_state):
        """Update displayed calibration factor and stability status from UI state.

        Args:
            ui_state: CalibUIState instance with current channel data.
        """
        # Use calibration channel to determine which result to display
        calib_ch_str = self.edit_channel_select.value
        if calib_ch_str == 'All' and self.mode_toggle.active == 0:
            self.result_factor.text = f"<b style='font-size:16px;color:{T3};'>-</b>"
            self.result_status.text = f"<b style='font-size:16px;color:{T3};'>-</b>"
            return
        if self.mode_toggle.active == 1:
            if self.auto_detected_channel is None:
                # self.result_factor.text = f"<b style='font-size:16px;color:{T3};'>—</b>"
                # self.result_status.text = f"<b style='font-size:16px;color:{T3};'>…</b>"
                return
            ch = self.auto_detected_channel
            self.edit_channel_select.value = self.edit_channel_select.options[self.auto_detected_channel + 1]
        else:
            ch = int(calib_ch_str.split()[-1]) - 1
        d = ui_state.get(ch)
        if d is None:
            return
        final_factor = d.get('final_factor', 0.0)
        final_color = T3 if final_factor > 0 else 'transparent'
        final_text = f'{final_factor:.4f}' if final_factor > 0 else '0.0'
        self.result_factor.text = (
            f"<b style='font-size:16px;color:{T1};'>{d['factor']:.4f}</b>"
            f"<br><b style='font-size:16px;color:{final_color};'>SAVED: {final_text}</b>"
        )
        stable = d.get('is_stable', False)
        color = GRN if stable else ORG
        self.result_status.text = (
            f"<b style='font-size:16px;color:{color};'>{'STABLE' if stable else 'UNSTABLE'}</b>"
            f"<br><b style='font-size:16px;color:transparent;'>—</b>"
        )

    def update_num_channels(self, num_channels):
        """Update channel selectors after source change.

        Args:
            num_channels: New number of available channels.
        """
        self.num_channels = num_channels
        channels = [f'Channel {i}' for i in range(1, num_channels + 1)]

        self.edit_channel_select.options = ['All', *channels]
        if self.edit_channel_select.value not in self.edit_channel_select.options:
            self.edit_channel_select.value = 'Channel 1'

        self.logger.debug('ParameterPanel: Channel number updated to %d', num_channels)
