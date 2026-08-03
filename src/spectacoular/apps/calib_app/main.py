"""Main application module for the calibration application.

This module contains:
- Bokeh server document setup (server_doc)
- Background thread management for calibration processing
- UI layout construction
- Audio source management
- Calibration state management
"""

# Longterm TODO: should be to split this out into more files to make it more readable. 
# Also it would be nice to refactor the consume_auto logic into the orchestrator or detector.

from pathlib import Path

import acoular as ac
import threading
from bokeh.layouts import row, column
from bokeh.models import Div, TextAreaInput
from spectacoular.apps.measurement_app.log import LogHandler
from spectacoular.apps.calib_app.UI.parameter_panel import ParameterPanel
from spectacoular.apps.calib_app.UI.buttons_save_upload_start import ButtonBar, PathInput, InputFile
from spectacoular.apps.calib_app.save_and_parse.save import save
from spectacoular.apps.calib_app.UI.table import CalibTable
from spectacoular.apps.calib_app.UI.notes import NotesInput
from spectacoular.apps.calib_app.UI.calib_ui_state import CalibUIState
from spectacoular.apps.calib_app.UI.visibility_switch import VisibilitySwitch
from spectacoular.apps.calib_app.save_and_parse.parse import load
from spectacoular.apps.calib_app.calibOrchestrator import CalibOrchestrator
from spectacoular.apps.calib_app.calibration.calib import StdCalib
from spectacoular.apps.calib_app.preprocessor.preprocessor import CalibPreprocessor
from spectacoular.apps.calib_app.channel_router import ChannelRouter
from spectacoular.apps.calib_app.util import dB_to_pa, pa_to_dB
from spectacoular.apps.calib_app.preprocessor.fft_preprocessor import FFT
from spectacoular.apps.calib_app.UI.fft_plot import FFTViewer
import spectacoular as sp
import sounddevice as sd
from bokeh.models import Select
import logging
from spectacoular.apps.calib_app.UI.tooltips import info_label
from spectacoular.apps.calib_app.help import help_doc
from tornado.web import StaticFileHandler


log = None  # Global logger, initialized by setup_logger()


def build_source_select(logger, phantom_files):
    """Build a Select widget for choosing audio input source.
    
    Populates options with:
    - Live audio devices (WASAPI preferred on Windows to avoid duplicates)
    - Phantom files (for testing without real audio input)
    
    Args:
        logger: Logger instance for status messages.
        phantom_files: List of Path objects for phantom sound files.
    
    Returns:
        Select: Bokeh Select widget configured with available sources.
    """
    hostapis = sd.query_hostapis()

    # On Windows: only show WASAPI to avoid duplicates
    preferred_api = next(
        (i for i, h in enumerate(hostapis) if 'WASAPI' in h['name']),
        None
    )

    devices = {}
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            if preferred_api is None or dev['hostapi'] == preferred_api:
                devices[str(i)] = '{name} ({max_input_channels} ch)'.format(**dev)

    # WASAPI filter fallback for other platforms
    if not devices:
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels'] > 0:
                api = hostapis[dev['hostapi']]['name']
                devices[str(i)] = f"{dev['name']} ({dev['max_input_channels']} ch) [{api}]"

    # Phantoms last
    options = list(devices.items())
    options += [(f.name, f"Phantom: {f.name}") for f in phantom_files]

    initial_value = options[0][0] if options else None
    select = Select(
        options=options, value=initial_value, sizing_mode="stretch_width")

    if not devices:
        logger.info("No devices connected")
    else:
        logger.info(f"{len(devices)} Live-Device(s) found.")

    return select

def setup_logger(doc):
    """Initialize the application logger with Bokeh integration.
    
    Creates a LogHandler that writes to both a file (calibration.log)
    and a TextAreaInput widget for display in the UI.
    
    Args:
        doc: Bokeh document for attaching the log widget.
    """
    log_widget = TextAreaInput(value="", disabled=True,
                               width=300, sizing_mode='stretch_both')
    global log
    log = LogHandler(doc=doc, logname="calibration.log", log_widget=log_widget,
                     loglevel=logging.DEBUG, loglength=20)

def consume(orchestrator, state, ui_state):
    """Background thread: reads from orchestrator and writes to CalibUIState.
    
    This is the main calibration processing loop. It:
    - Reads calibration blocks from the orchestrator
    - Extracts channel data (factor, band, magnitude, etc.)
    - Updates CalibUIState which the UI reads from
    - After completion, syncs all final values from orchestrator
    
    Args:
        orchestrator: CalibOrchestrator providing calibration data.
        state: Dict with 'iter' (block iterator) and 'ch' (channel index).
        ui_state: CalibUIState to write results to.
    """
    for _ in state['iter']:
        if not getattr(state.get('thread'), 'do_run', True):
            break

        ch = state['ch']
        channel = orchestrator.channels.get(ch)
        if channel is None:
            continue

        factor = channel.calib_value
        final_factor = channel.calib_value_final

        band = channel.preprocess.band
        unit =  channel.unit
        calib_time = float(channel.calib_time)
        stability_tolerance = float(channel.stability_tolerance)

        if unit == "dB":
            magnitude = pa_to_dB(channel.calib.referenceMagnitude)
        else:
            magnitude = channel.calib.referenceMagnitude


        is_stable = orchestrator.channels[ch].calib.is_stable()

        ui_state.update(ch=ch, factor=factor, band=band, magnitude=magnitude, is_stable=is_stable, final_factor=final_factor, unit = unit, calib_time = calib_time,stability_tolerance=stability_tolerance)
    
    # Update UI from orchestrator to ensure all final values are displayed
    ui_state.init_from_orchestrator(orchestrator)


def update_orchestrator(orchestrator, params, ui_state):
    """Update orchestrator channels with parameters from the UI panel.
    
    Creates or updates channels based on the Edit Channel selector.
    If "All" is selected, updates all channels. Otherwise, updates only
    the selected channel.
    
    Args:
        orchestrator: CalibOrchestrator to update.
        params: ParameterPanel with current UI values.
        ui_state: CalibUIState to update with new values.
    """
    if str(params.edit_channel_select.value) == "All":
        edit_channels = [int(ch.split()[-1])-1 for ch in params.edit_channel_select.options[1:]]
    else:
        edit_channels = [int(params.edit_channel_select.value.split()[-1]) - 1]
    for edit_ch in edit_channels:
        unit = params.pegel_unit_select.value
        unit_log = unit
        if str(params.pegel_unit_select.value) == "dB":
            level = dB_to_pa(float(params.pegel_input.value))
            unit_log = "Pa"
            log.logger.debug("Reference value converted from dB to Pa.")
        else:
            level = float(params.pegel_input.value)
        freq = float(params.freq_input.value)
        calib_time = float(params.calib_time_input.value)
        stability_tolerance = float(params.stability_tolerance_input.value)
        orchestrator.add_channel(edit_ch, calib=StdCalib(referenceMagnitude=level),
                                preproc=CalibPreprocessor(band=freq),unit=unit, calib_time = calib_time,stability_tolerance=stability_tolerance)
        orchestrator.configure_detector()
        log.logger.debug(f"Orchestrator updated: ch={edit_ch}, level={level:.6f} {unit_log} , freq={freq}, calib_time = {calib_time},stability_tolerance = {stability_tolerance}")
        ui_state.update(ch=edit_ch, band=freq, magnitude=params.pegel_input.value,final_factor=orchestrator.channels[edit_ch].calib_value_final, unit=unit, calib_time = calib_time,stability_tolerance=stability_tolerance)


def consume_auto(orchestrator, params, state, ui_state):
    """Background thread for Auto mode: calibrates all channels sequentially.
    
    Automatically detects which channel has the calibration signal,
    calibrates it, then moves to the next channel. Continues until all
    channels are calibrated or the thread is stopped.
    
    Args:
        orchestrator: CalibOrchestrator providing calibration data.
        params: ParameterPanel for UI parameter access.
        state: Dict for thread state (completed channels, etc.).
        ui_state: CalibUIState to write results to.
    """
    completed = state.setdefault('completed', set())
    while getattr(state.get('thread'), 'do_run', True):
        if len(completed) >= orchestrator.source.num_channels:
            log.logger.debug("Auto: all channels calibrated.")
            return

        orchestrator.detector.exclude_channels = list(completed)

        for _ in orchestrator.detect_channel(512):
            if not getattr(state.get('thread'), 'do_run', True):
                return
            if orchestrator.detector.detected_channel != -1:
                break

        idx = orchestrator.detector.detected_channel

        if idx == -1:
            return  # source exhausted without finding a candidate
        
    
        log.logger.debug(f"Auto-detected calibration channel: {idx + 1}")
        params.auto_detected_channel = idx
        
       

        state['ch'] = idx
        state['iter'] = orchestrator.result(1, channel_num=idx, no_progress_blocks=300, stop_on_complete=False)
        consume(orchestrator, state, ui_state)

        if orchestrator.channels[idx].calib_value_final > 0:
            completed.add(idx)
            log.logger.debug(f"Channel {idx + 1} calibrated ")
        else:
            log.logger.debug(f"Channel {idx + 1} Timeout - re-detecting ...")


def stop_consume_thread(state):
    """Stop the currently running consume thread if any.
    
    Args:
        state: Dict containing 'thread' key with the Thread object.
    """
    if 'thread' in state and state['thread'].is_alive():
        state['thread'].do_run = False
        state['thread'].join(timeout=2.0)  # wait for thread to really end
        log.logger.debug("Consume thread stopped")


def start_consume_thread(doc, orchestrator, params, state, ui_state, router):
    """Start a consume thread for calibration processing.
    
    Stops any existing thread first, then starts a new one in either
    Auto mode (if mode_toggle is active) or manual mode (single channel).
    
    Args:
        doc: Bokeh document for scheduling UI updates.
        orchestrator: CalibOrchestrator providing calibration data.
        params: ParameterPanel with UI parameter values.
        state: Dict for thread state management.
        ui_state: CalibUIState for thread-safe data sharing.
        router: ChannelRouter for channel switching (unused in current code).
    """
    calib_ch_str = params.edit_channel_select.value

    # Stop old thread
    stop_consume_thread(state)

    if params.mode_toggle.active == 1:
        state.setdefault('completed', set()).clear()
        params.auto_detected_channel = None
        
        t = threading.Thread(target=consume_auto,
                             args=(orchestrator, params, state, ui_state),
                             daemon=True)
        t.do_run = True
        state['thread'] = t
        t.start()
        log.logger.debug("Consume thread started in Auto mode")
        return

    ch = int(calib_ch_str.split()[-1]) - 1

    # Start new consume thread for selected channel
    orchestrator.channels[ch].calib_value_final = 0.0 
    state['iter'] = orchestrator.result(1, channel_num=ch, stop_on_complete=False)
    state['ch'] = ch

    t = threading.Thread(target=consume, args=(orchestrator, state, ui_state), daemon=True)
    t.do_run = True
    state['thread'] = t
    t.start()
    log.logger.debug(f"Consume thread started for ch={ch}")


def build_channel(orchestrator, params, ui_state):
    """Rebuild pipeline: update orchestrator and restart consume thread.
    
    Called when user clicks "Set" button to apply new parameters.
    Updates the orchestrator configuration, which implicitly restarts
    the consume thread via the on_change callbacks.
    
    Args:
        orchestrator: CalibOrchestrator to update.
        params: ParameterPanel with new parameter values.
        ui_state: CalibUIState to update.
    """
    update_orchestrator(orchestrator, params, ui_state)


def refresh(calib_table, params, ui_state, fft, doc):
    """Schedule UI refresh on the main thread.
    
    Uses Bokeh's add_next_tick_callback to safely update UI from
    background threads or periodic callbacks.
    
    Args:
        calib_table: CalibTable to refresh with latest data.
        params: ParameterPanel to refresh with latest data.
        ui_state: CalibUIState with current calibration data.
        fft: FFTViewer to update with current channel spectrum.
        doc: Bokeh document for scheduling callbacks.
    """
    doc.add_next_tick_callback(lambda: calib_table.refresh(ui_state))
    doc.add_next_tick_callback(lambda: params.refresh(ui_state))
    doc.add_next_tick_callback(lambda: fft.update(params.edit_channel_select.value))

def load_callback(orchestrator, ui_state, state, logger, params, notes):
    """Create callback for loading calibration data from file.
    
    Returns a function that can be used as a Bokeh FileInput on_change
    callback. When triggered, it stops the current consume thread,
    loads the data, syncs UI state, and updates parameter inputs.
    
    Args:
        orchestrator: CalibOrchestrator to populate with loaded data.
        ui_state: CalibUIState to update.
        state: Dict with thread state.
        logger: Logger instance.
        params: ParameterPanel to update with loaded values.
        notes: NotesInput widget to update with loaded notes.
    
    Returns:
        function: Callback for FileInput on_change event.
    """
    load_cb = load(orchestrator, notes, logger)
    def callback(attr, old, new):
        # Stop any running consume thread
        stop_consume_thread(state)
        load_cb(attr, old, new)
        ui_state.init_from_orchestrator(orchestrator)
        params.pegel_input.value = params.get_value_from_ui_state("magnitude")
        params.pegel_unit_select.value = params.get_value_from_ui_state("unit")
        params.freq_input.value = params.get_value_from_ui_state("band")
        params.calib_time_input.value = params.get_value_from_ui_state("calib_time")
        params.stability_tolerance_input.value = params.get_value_from_ui_state("stability_tolerance")
    return callback

def visibility_callback(element):
    """Create callback to toggle element visibility.
    
    Args:
        element: Bokeh widget with a 'visible' property.
    
    Returns:
        function: Callback that sets element.visible = new value.
    """
    def callback(attr, old, new):
        element.visible = new
    return callback



def update_parameter_panel(params):
    """Create callback to update parameter inputs from UI state.
    
    Updates all parameter inputs (level, unit, frequency, etc.) from
    the currently selected channel in ui_state.
    
    Args:
        params: ParameterPanel with the input widgets to update.
    
    Returns:
        function: Callback for on_change events.
    """
    def update(attr, old, new):
        params.pegel_input.value = params.get_value_from_ui_state("magnitude")
        params.pegel_unit_select.value = params.get_value_from_ui_state("unit")
        params.freq_input.value = params.get_value_from_ui_state("band")
        params.calib_time_input.value = params.get_value_from_ui_state("calib_time")
        params.stability_tolerance_input.value = params.get_value_from_ui_state("stability_tolerance")
    return update

def deactivate_parameter_panel(params, button):
    """Create callback to disable parameter inputs in Auto mode.
    
    Disables parameter inputs when Auto mode is active (mode_toggle.active == 1).
    Also disables the Start button when in Edit mode with "All" selected.
    
    Args:
        params: ParameterPanel with the input widgets.
        button: Start button widget.
    
    Returns:
        function: Callback for mode_toggle on_change events.
    """
    def update(attr, old, new):
        params.pegel_input.disabled = params.mode_toggle.active == 1
        params.pegel_unit_select.disabled = params.mode_toggle.active == 1
        params.freq_input.disabled  = params.mode_toggle.active == 1
        params.edit_channel_select.disabled  = params.mode_toggle.active == 1
        params.bew_select.disabled  = params.mode_toggle.active == 1
        params.btn_set.disabled  = params.mode_toggle.active == 1
        params.calib_time_input.disabled  = params.mode_toggle.active == 1
        params.stability_tolerance_input.disabled  = params.mode_toggle.active == 1
        button.disabled = params.mode_toggle.active == 0 and params.edit_channel_select.value == "All"
    return update

def deactivate_start_button(button, params):
    """Create callback to disable Start button when "All" is selected.
    
    Args:
        button: Start button widget.
        params: ParameterPanel with edit_channel_select.
    
    Returns:
        function: Callback for edit_channel_select on_change events.
    """
    def update(attr, old, new):
        button.disabled = params.edit_channel_select.value == "All"
    return update


def server_doc(doc):
    """Bokeh server document factory for the calibration application.
    
    This is the main entry point called by Bokeh when creating a new session.
    It sets up:
    - Logging infrastructure
    - Audio source (live device or phantom file)
    - Channel router
    - Calibration orchestrator
    - All UI components (tables, panels, buttons, plots)
    - Event callbacks for user interactions
    - Periodic UI refresh
    
    Args:
        doc: Bokeh document to populate with the application UI.
    """
    setup_logger(doc)
    log.logger.info("Start with first Device in the List.")

    phantom_dir = Path(__file__).parent.parent
    phantom_files = sorted(phantom_dir.glob("*.h5"))

    source_select = build_source_select(log.logger, phantom_files)
    if not source_select.options:
        raise RuntimeError(
            "No Phantom File nor Audio Source found."
        )

    first_value, _ = source_select.options[0]
    if first_value.endswith(".h5"):
        source = sp.TimeSamplesPhantom(file=phantom_dir / first_value)
    else:
        dev = int(first_value)
        info = sd.query_devices(dev)
        source = ac.SoundDeviceSamplesGenerator(
            device=dev,
            num_channels=info['max_input_channels'],
            sample_freq=int(info['default_samplerate']),
            num_samples=int(info['default_samplerate']) * 36000,
        )

    router = ChannelRouter(source=source, source_channel=0,
                           calib_channel=0, logger=log.logger)
    

    
    splitted_source = ac.SampleSplitter(source = source)
    
    orchestrator = CalibOrchestrator(splitted_source, logger=log.logger)

    graph_switch = VisibilitySwitch("FFT").widget


    fft = FFT(source= splitted_source, switch=graph_switch,logger=log.logger)
    splitted_source.register_object(fft, buffer_overflow_treatment = 'none')

    state = {}
    ui_state = CalibUIState()
    calib_table = CalibTable()
    notes_input = NotesInput()
    notes = notes_input.textarea      
    notes_layout = notes_input.layout

    def init_all_channels():
        orchestrator.init_channels(
            calib=StdCalib(referenceMagnitude=dB_to_pa(94.0)),
            preproc=CalibPreprocessor(band=1000.0),
            unit="dB",
            calib_time = 2,
            stability_tolerance = 0.5
        )
        orchestrator.configure_detector()
        ui_state.init_from_orchestrator(orchestrator)


    init_all_channels()

  
    num_channels = source.num_channels
    params = ParameterPanel(ui_state, logger=log.logger, num_channels=num_channels)

    
    def on_source_change(attr, old, new):
        stop_consume_thread(state)
        try:
            if new.endswith(".h5"):
                new_source = sp.TimeSamplesPhantom(file=phantom_dir / new)
                log.logger.info(f"Source Changed: Phantom ({new}).")
            else:
                dev = int(new)
                info = sd.query_devices(dev)
                max_ch = info['max_input_channels']
                fs = int(info['default_samplerate'])
                new_source = ac.SoundDeviceSamplesGenerator(
                    device=dev,
                    num_channels=max_ch,
                    sample_freq=fs,
                    num_samples=fs * 36000,
                )
                log.logger.info(f"Source Changed: Live-Device {new} ({max_ch} ch).")
        except sd.PortAudioError as e:
            log.logger.error(f"Device Change Failed: {e}")
            source_select.value = old
            return
        

        new_splitted_source = ac.SampleSplitter(source = new_source)

        orchestrator.source = new_splitted_source
        


        n = new_splitted_source.num_channels
        fft.source = new_splitted_source
        new_splitted_source.register_object(fft,buffer_overflow_treatment = 'none')

        # # Kanalindizes in gültigen Bereich zwingen
        # if router.calib_channel >= n:
        #     router.calib_channel = n - 1
        #     log.logger.warning(
        #         f"calib_channel on {router.calib_channel} limited. "
        #         f"(Source has only {n} Channels).")
        # if router.source_channel >= n:
        #     router.source_channel = 0

        # Auto-Fortschritt zurücksetzen
        state.pop('completed', None)

        # Alte Kanäle entfernen, damit keine Karteileichen (z. B. 64→2) bleiben
        orchestrator.channels.clear()
        ui_state.reset()

        # Orchestrator + UI neu aufbauen
        init_all_channels()
        params.update_num_channels(n)
        ui_state.init_from_orchestrator(orchestrator)
        calib_table.refresh(ui_state)

    source_select.on_change("value", on_source_change)
    # Standard-Konfiguration aller Kanäle

    params.edit_channel_select.on_change("value",update_parameter_panel(params))

    # --- Buttons / Pfade / Datei-Input ---
    button_bar = ButtonBar(logger=log.logger)
    default_path = Path.home() / "CalibResults" / "CalibData.json"
    (default_path.parent).mkdir(exist_ok=True)

    path_input_obj = PathInput(default_path)
    path_input = path_input_obj.widget          # für save() → .value
    path_input_layout = path_input_obj.layout   # fürs Layout

    file_input_obj = InputFile()
    file_input = file_input_obj.widget           # für on_change → .value
    file_input_layout = file_input_obj.layout    # fürs Layout

    button_bar.btn_save.on_click(lambda: save(path_input, notes, source_select,orchestrator=orchestrator, logger=log.logger))
    button_bar.btn_start.on_click(lambda: start_consume_thread(doc, orchestrator, params, state, ui_state, router))
    button_bar.btn_stop.on_click(lambda: stop_consume_thread(state))
    params.edit_channel_select.on_change("value", deactivate_start_button(button_bar.btn_start,params))
    params.mode_toggle.on_change("active", deactivate_parameter_panel(params,button_bar.btn_start))

    # --- Sichtbarkeits-Switches ---
    table_switch = VisibilitySwitch("Table").widget
    geom_switch = VisibilitySwitch("Geom").widget
    log_switch = VisibilitySwitch("Log").widget
    notes_switch = VisibilitySwitch("Notes").widget

    log_group = column(
        info_label("Log window", "Displays all log messages from the calibration app "),
        log.log_widget,
        sizing_mode="stretch_both"
    )

    table_switch.on_change("active", visibility_callback(calib_table.layout))
    notes_switch.on_change("active", visibility_callback(notes_layout))
    log_switch.on_change("active", visibility_callback(log_group))
    
    # Edit Channel + parameters changes: rebuild orchestrator and consume thread
    params.btn_set.on_click(lambda: build_channel(orchestrator, params, ui_state))

    doc.add_periodic_callback(lambda: refresh(calib_table, params, ui_state, graph,doc), 50)

    file_input.on_change("value", load_callback(orchestrator, ui_state, state, log.logger, params, notes))

    # --- Layout ---
    switches = column(info_label("Display Options", "Toggle visibility of the panels below"),
        row(
            graph_switch,
            table_switch,
            log_switch,
            notes_switch,
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width"
    )

    graph =FFTViewer(fft)
    graph_switch.on_change("active", visibility_callback(graph.widget()))
    geom = Div(text="geom", sizing_mode='stretch_height')
    geom_switch.on_change("active", visibility_callback(geom))

    middle = column(
        children=[
            calib_table.layout, 
            notes_layout], 
        sizing_mode="stretch_both"
        )
    right = column(
        children=[
            graph.widget(),
            log_group], 
        sizing_mode='stretch_both'
        )
    left = column(
        children=[
                button_bar.layout,
                path_input_layout, 
                file_input_layout,
                column(
                    info_label("Audio Source", "Select the input device or a phantom file (.h5)"),
                    source_select,
                    sizing_mode="stretch_width"
                ),
                switches, 
                params.layout],
        sizing_mode="stretch_height",
    )
    doc.add_root(row(children=[left, middle, right], sizing_mode='stretch_both'))
    log.logger.debug("Loaded layout")


if __name__ == "__main__":
    from bokeh.server.server import Server

    server = Server(
        {"/": server_doc, "/help": help_doc},
        session_token_expiration=3600,  # Token 1h gültig
        extra_patterns=[
            (r"/help_static/(.*)", StaticFileHandler, {'path': str(Path(__file__).parent / "help" / "help_static")})
        ],    
    )
    server.start()
    print("Starting Calib App on http://localhost:5006/")
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

