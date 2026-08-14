
# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------
"""Implement utilities for multi-channel calibration JSON files.

.. autosummary::
    :toctree: generated/

    json_write
    json_validation
    json_read
"""

import importlib
import json
import math
from datetime import UTC, datetime
from numbers import Real
from pathlib import Path

CALIBRATION_FIELDS = (
    'CalibLevel',
    'CalibFrequency',
    'CalibFactor',
    'CalibTime',
    'StabilityTolerance',
)
JSON_FIELDS = {
    'Name',
    'Description',
    'Date',
    'Source',
    'ChannelCount',
    'Calibration',
}
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_DESCRIPTION = (
    'Single-point calibration measurements for the specified channels.'
)


def _get_channel_count(audio_interface):
    """Return the maximum input channel count reported by SoundDevice."""
    try:
        sounddevice = importlib.import_module('sounddevice')
    except ModuleNotFoundError as error:
        msg = 'sounddevice is required to query the audio interface.'
        raise RuntimeError(msg) from error

    device = getattr(audio_interface, 'device', audio_interface)
    return sounddevice.query_devices(device)['max_input_channels']


def _load_json(json_file):
    """Load a JSON object and report file and syntax errors clearly."""
    path = Path(json_file)
    try:
        with path.open(encoding='utf-8') as stream:
            return json.load(stream)
    except FileNotFoundError as error:
        msg = f'Calibration file not found: {path}.'
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = f'Invalid JSON in {path}: {error.msg} at line {error.lineno}.'
        raise ValueError(msg) from error


def _validate_data(data, expected_channel_count):
    """Validate already-loaded calibration data against the exact schema."""
    if not isinstance(data, dict):
        msg = 'The JSON root must be an object.'
        raise ValueError(msg)

    missing_fields = JSON_FIELDS - data.keys()
    extra_fields = data.keys() - JSON_FIELDS
    if missing_fields:
        msg = f"Missing top-level fields: {', '.join(sorted(missing_fields))}."
        raise ValueError(msg)
    if extra_fields:
        msg = f"Unexpected top-level fields: {', '.join(sorted(extra_fields))}."
        raise ValueError(msg)

    for field in ('Name', 'Description', 'Date', 'Source'):
        if not isinstance(data[field], str):
            msg = f'{field} must be a string.'
            raise ValueError(msg)
    if not data['Name']:
        msg = 'Name must not be empty.'
        raise ValueError(msg)
    if not data['Source']:
        msg = 'Source must not be empty.'
        raise ValueError(msg)
    try:
        parsed_date = datetime.strptime(data['Date'], DATE_FORMAT)
    except ValueError as error:
        msg = f'Date must use the format {DATE_FORMAT}.'
        raise ValueError(msg) from error
    if parsed_date.strftime(DATE_FORMAT) != data['Date']:
        msg = f'Date must use the format {DATE_FORMAT}.'
        raise ValueError(msg)

    channel_count = data['ChannelCount']
    if (
        not isinstance(channel_count, int)
        or isinstance(channel_count, bool)
        or channel_count < 1
    ):
        msg = 'ChannelCount must be a positive integer.'
        raise ValueError(msg)
    if channel_count != expected_channel_count:
        msg = (
            f'Channel count mismatch: JSON contains {channel_count}, '
            f'audio interface exposes {expected_channel_count}.'
        )
        raise ValueError(msg)

    calibration = data['Calibration']
    if not isinstance(calibration, dict):
        msg = 'Calibration must be an object.'
        raise ValueError(msg)
    calibration_fields = set(CALIBRATION_FIELDS)
    missing_fields = calibration_fields - calibration.keys()
    extra_fields = calibration.keys() - calibration_fields
    if missing_fields:
        msg = f"Missing calibration fields: {', '.join(sorted(missing_fields))}."
        raise ValueError(msg)
    if extra_fields:
        msg = f"Unexpected calibration fields: {', '.join(sorted(extra_fields))}."
        raise ValueError(msg)

    for field in CALIBRATION_FIELDS:
        values = calibration[field]
        if not isinstance(values, list):
            msg = f'Calibration.{field} must be a list.'
            raise ValueError(msg)
        if len(values) != channel_count:
            msg = f'Calibration.{field} must contain {channel_count} values, got {len(values)}.'
            raise ValueError(msg)
        for channel, value in enumerate(values, start=1):
            if (
                not isinstance(value, Real)
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                msg = f'Calibration.{field} for channel {channel} must be a finite number.'
                raise ValueError(msg)

    for field in ('CalibFrequency', 'CalibFactor', 'CalibTime'):
        if any(value <= 0 for value in calibration[field]):
            msg = f'Calibration.{field} values must be greater than zero.'
            raise ValueError(msg)
    if any(value < 0 for value in calibration['StabilityTolerance']):
        msg = 'Calibration.StabilityTolerance values must be greater than or equal to zero.'
        raise ValueError(msg)


def json_write(
    json_file,
    source,
    channel_data,
    *,
    audio_interface=None,
    description=DEFAULT_DESCRIPTION,
    date=None,
):
    """Write calibration values using the compact multi-channel JSON schema.

    Parameters
    ----------
    json_file : str or pathlib.Path
        Path of the JSON file to write.
    source : str
        Name of the audio source used for calibration.
    channel_data : dict
        Calibration values indexed by one-based channel numbers. Each channel
        contains the fields listed in :data:`CALIBRATION_FIELDS`.
    audio_interface : int, str or object, optional
        SoundDevice device index/name or object exposing a ``device`` attribute.
        If omitted, the channel count is inferred from ``channel_data``.
    description : str, optional
        Description stored in the JSON file.
    date : datetime.datetime or str, optional
        Calibration date. The current UTC date is used if omitted.

    Returns
    -------
    dict
        Data written to the JSON file.

    Raises
    ------
    ValueError
        If the calibration data does not match the expected schema.

    """
    if not isinstance(channel_data, dict) or not channel_data:
        msg = 'channel_data must be a non-empty dictionary indexed by channel number.'
        raise ValueError(msg)

    channels = sorted(channel_data)
    expected_channels = list(range(1, len(channels) + 1))
    if channels != expected_channels:
        msg = f'channel_data keys must be exactly {expected_channels}.'
        raise ValueError(msg)
    calibration = {field: [] for field in CALIBRATION_FIELDS}
    expected_fields = set(CALIBRATION_FIELDS)
    for channel in channels:
        values = channel_data[channel]
        if not isinstance(values, dict):
            msg = f'Channel {channel} calibration data must be a dictionary.'
            raise ValueError(msg)
        missing_fields = expected_fields - values.keys()
        extra_fields = values.keys() - expected_fields
        if missing_fields:
            msg = f"Channel {channel} is missing: {', '.join(sorted(missing_fields))}."
            raise ValueError(msg)
        if extra_fields:
            msg = f"Channel {channel} has unexpected fields: {', '.join(sorted(extra_fields))}."
            raise ValueError(msg)
        for field in CALIBRATION_FIELDS:
            calibration[field].append(values[field])

    if isinstance(date, datetime):
        date = date.strftime(DATE_FORMAT)
    elif date is None:
        date = datetime.now(tz=UTC).strftime(DATE_FORMAT)

    path = Path(json_file)
    data = {
        'Name': path.name,
        'Description': description,
        'Date': date,
        'Source': source,
        'ChannelCount': len(channels),
        'Calibration': calibration,
    }
    expected_channel_count = (
        len(channels)
        if audio_interface is None
        else _get_channel_count(audio_interface)
    )
    _validate_data(data, expected_channel_count)

    with path.open('w', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return data


def json_validation(json_file, audio_interface):
    """Validate a calibration JSON file and its channel count.

    Parameters
    ----------
    json_file : str or pathlib.Path
        Path of the JSON file to validate.
    audio_interface : int, str or object
        SoundDevice device index/name or object exposing a ``device`` attribute.

    Returns
    -------
    bool
        ``True`` when the file is valid.

    Raises
    ------
    ValueError
        If the file does not match the calibration schema or device channel count.

    """
    data = _load_json(json_file)
    _validate_data(data, _get_channel_count(audio_interface))
    return True


def json_read(json_file, audio_interface):
    """Read validated calibration data into a channel-indexed dictionary.

    Parameters
    ----------
    json_file : str or pathlib.Path
        Path of the JSON file to read.
    audio_interface : int, str or object
        SoundDevice device index/name or object exposing a ``device`` attribute.

    Returns
    -------
    dict
        File metadata and calibration values indexed by channel number.

    Raises
    ------
    ValueError
        If the file does not match the calibration schema or device channel count.

    """
    data = _load_json(json_file)
    _validate_data(data, _get_channel_count(audio_interface))

    channel_data = {
        channel: {
            field: data['Calibration'][field][index] for field in CALIBRATION_FIELDS
        }
        for index, channel in enumerate(range(1, data['ChannelCount'] + 1))
    }
    return {
        'Name': data['Name'],
        'Description': data['Description'],
        'Date': data['Date'],
        'Source': data['Source'],
        'ChannelCount': data['ChannelCount'],
        'Channels': channel_data,
    }
