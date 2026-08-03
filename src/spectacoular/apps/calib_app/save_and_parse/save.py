"""Save calibration data to JSON files."""

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

from spectacoular.apps.calib_app.util import pa_to_db


def open_json(filename):
    """Load a JSON template file from the save_and_parse directory.

    Args:
        filename: Name of the JSON file to load.

    Returns
    -------
        dict: Parsed JSON data.
    """
    path = Path(__file__).resolve().parent / filename
    with Path.open(path, encoding="utf-8") as file:
        return json.load(file)


def get_source_name(source_select):
    """Get the display label for the currently selected source.

    Args:
        source_select: Bokeh Select widget with source options.

    Returns
    -------
        str: Display label of the selected source, or the value if not found.
    """
    current_value = source_select.value
    for value, label in source_select.options:
        if value == current_value:
            return str(label)
    return str(current_value)


def build_calib_data(orchestrator, name_input, source_select, notes):
    """Build calibration data JSON from orchestrator state.

    Creates a JSON structure containing calibration results for all
    channels that have completed calibration (calib_value_final != 0).

    Args:
        orchestrator: CalibOrchestrator with channel data.
        name_input: Name for this calibration session.
        source_select: Bokeh Select widget for source selection.
        notes: Bokeh TextAreaInput with session notes.

    Returns
    -------
        str: JSON string of calibration data.
    """
    calib_data_template = open_json("CalibDataTemplate.json")
    calib_data = copy.deepcopy(calib_data_template)
    calib_data["Name"] = str(name_input)
    calib_data["Date"] = str(datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"))
    calib_data["Source"] = get_source_name(source_select)
    calib_data["Notes"] = str(notes.value)
    channel_template = open_json("ChannelTemplate.json")
    for channel_num in sorted(orchestrator.channels.keys()):
        if float(orchestrator.channels[channel_num].calib_value_final) != 0:
            channel = copy.deepcopy(channel_template)
            channel["CalibFactor"]["Value"] = float(orchestrator.channels[channel_num].calib_value_final)
            if str(orchestrator.channels[channel_num].unit) == "dB":
                channel["CalibFactor"]["Unit"] = "Pa/V"
                channel["CalibLevel"]["Value"] = pa_to_db(
                    float(orchestrator.channels[channel_num].calib.reference_magnitude)
                )
            else:
                channel["CalibFactor"]["Unit"] = str(orchestrator.channels[channel_num].unit)+"/V"
                channel["CalibLevel"]["Value"] = float(
                    orchestrator.channels[channel_num].calib.reference_magnitude
                )
            channel["CalibLevel"]["Unit"] = str(orchestrator.channels[channel_num].unit)
            channel["CalibTime"]["Value"] = float(orchestrator.channels[channel_num].calib_time)
            channel["CalibFrequency"]["Value"] = float(orchestrator.channels[channel_num].preprocess.band)
            channel["StabilityTolerance"]["Value"] = float(orchestrator.channels[channel_num].stability_tolerance)
            calib_data["Channels"][str(channel_num+1)] = channel
    return json.dumps(calib_data,indent=1,ensure_ascii=False)


def save(path_input, notes, source_select, orchestrator, logger):
    """Save calibration data to a JSON file.

    Args:
        path_input: Bokeh TextInput widget with the save path.
        notes: Bokeh TextAreaInput with session notes.
        source_select: Bokeh Select widget for source selection.
        orchestrator: CalibOrchestrator with channel data to save.
        logger: Logger instance for debugging.
    """
    path = Path(path_input.value)

    if not path.parent.exists():
        logger.debug("The directory does not exist: %s", path.parent)
        return

    json_str = build_calib_data(orchestrator, path.name,source_select, notes)

    path.write_text(json_str)

    logger.debug("%s saved in: %s", path.name, path.parent)


