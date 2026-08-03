"""Load calibration data from JSON files."""

import json
import base64
from ..calibration.calib import StdCalib
from ..preprocessor.preprocessor import CalibPreprocessor
from ..util import dB_to_pa



def load(orchestrator, notes, logger):
    """Create a callback for loading base64-encoded JSON calibration data.
    
    Returns a function suitable for use as a Bokeh widget on_change callback.
    The callback decodes the base64 data, parses the JSON, applies it to the
    orchestrator, and updates the notes widget.
    
    Args:
        orchestrator: CalibOrchestrator to populate with loaded data.
        notes: Bokeh TextAreaInput widget to update with notes from file.
        logger: Logger instance for debugging.
    
    Returns:
        function: Callback that accepts (attr, old, new) arguments.
    """

    def load_json_from_file(attr, old, new):
        decoded = base64.b64decode(new)
        calib_data = json.loads(decoded.decode("utf-8"))
        set_calib_data(orchestrator, calib_data, logger)
        notes_str = calib_data["Notes"]
        notes.value = notes_str
        
    return load_json_from_file
        

def set_calib_data(orchestrator, calib_data, logger):
    """Apply calibration data from parsed JSON to the orchestrator.
    
    Creates channels in the orchestrator for each channel in the JSON data,
    setting up calibration and preprocessor objects with the loaded parameters.
    Also sets the final calibration factor for each channel.
    
    Args:
        orchestrator: CalibOrchestrator to populate.
        calib_data: Parsed JSON data with Channels dict.
        logger: Logger instance for debugging.
    """

    for channel_num in calib_data["Channels"].keys():
        channel_num_int = int(channel_num)-1
        unit =  calib_data["Channels"][channel_num]["CalibLevel"]["Unit"]
        unit_log = unit
        if unit =="dB":
            level = dB_to_pa(calib_data["Channels"][channel_num]["CalibLevel"]["Value"])
            unit_log = "Pa"
        else:
            level = calib_data["Channels"][channel_num]["CalibLevel"]["Value"]
        freq = calib_data["Channels"][channel_num]["CalibFrequency"]["Value"]
        calib_time = calib_data["Channels"][channel_num]["CalibTime"]["Value"]
        stability_tolerance = calib_data["Channels"][channel_num]["StabilityTolerance"]["Value"]
        orchestrator.add_channel(channel_num_int, calib=StdCalib(referenceMagnitude=level), preproc=CalibPreprocessor(band=freq), unit=unit, calib_time = calib_time, stability_tolerance=stability_tolerance)
        logger.debug(f"Orchestrator updated: ch={channel_num_int}, level={level:.6f} {unit_log} , freq={freq}, calib_time = {calib_time},  stability_tolerance = {stability_tolerance}")
        orchestrator.channels[channel_num_int].calib_value_final =  calib_data["Channels"][channel_num]["CalibFactor"]["Value"]
        logger.debug(f'{calib_data["Channels"][channel_num]["CalibFactor"]["Value"]} saved as the final calibration factor for channel {channel_num}')
