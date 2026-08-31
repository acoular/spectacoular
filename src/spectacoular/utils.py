# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------
"""Implement utilities for multi-channel calibration JSON files.

.. autosummary::
    :toctree: generated/

    json_write
    is_valid_json
    json_read
"""

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
DEFAULT_DESCRIPTION = 'Single-point calibration measurements for the specified channels.'


def is_valid_json(data_or_path):
    """Validate calibration data against the multi-channel JSON schema.

    Parameters
    ----------
    data_or_path : str, pathlib.Path or dict
        Calibration file to validate, or an already loaded calibration dictionary.

    Returns
    -------
    bool
        ``True`` when the calibration data is valid.

    Raises
    ------
    TypeError
        If a value does not have the expected type.
    ValueError
        If the calibration data does not match the schema.

    """
    if isinstance(data_or_path, dict):
        data = data_or_path
    else:
        path = Path(data_or_path)
        with path.open(encoding='utf-8') as stream:
            data = json.load(stream)

    if not isinstance(data, dict):
        msg = 'The JSON root must be a dictionary.'
        raise TypeError(msg)

    missing_fields, extra_fields = JSON_FIELDS - data.keys(), data.keys() - JSON_FIELDS
    if missing_fields or extra_fields:
        fields = missing_fields | extra_fields
        msg = f'Missing or unexpected top level fields: {", ".join(sorted(fields))}.'
        raise ValueError(msg)

    invalid_metadata = next(
        (field for field in ('Name', 'Description', 'Date', 'Source') if not isinstance(data[field], str)),
        None,
    )
    empty_metadata = next((field for field in ('Name', 'Source') if not data[field]), None)
    parsed_date = datetime.strptime(data['Date'], DATE_FORMAT).replace(tzinfo=UTC)
    channel_count, calibration = data['ChannelCount'], data['Calibration']
    valid_channel_count = isinstance(channel_count, int) and not isinstance(channel_count, bool) and channel_count > 0
    if not isinstance(calibration, dict):
        msg = 'Calibration must be an dictionary.'
        raise TypeError(msg)
    missing_fields, extra_fields = (
        set(CALIBRATION_FIELDS) - calibration.keys(),
        calibration.keys() - set(CALIBRATION_FIELDS),
    )
    if missing_fields or extra_fields:
        fields = missing_fields | extra_fields
        msg = f'Missing or unexpected calibration fields: {", ".join(sorted(fields))}.'
        raise ValueError(msg)

    invalid_list = next((field for field in CALIBRATION_FIELDS if not isinstance(calibration[field], list)), None)
    invalid_length = next(
        (
            field
            for field in CALIBRATION_FIELDS
            if isinstance(calibration[field], list) and valid_channel_count and len(calibration[field]) != channel_count
        ),
        None,
    )
    invalid_length_value = len(calibration[invalid_length]) if invalid_length else 0
    invalid_number = next(
        (
            (field, channel)
            for field in CALIBRATION_FIELDS
            if isinstance(calibration[field], list)
            for channel, value in enumerate(calibration[field], 1)
            if not isinstance(value, Real) or isinstance(value, bool) or not math.isfinite(value)
        ),
        None,
    )
    invalid_number_field, invalid_number_channel = invalid_number or ('', 0)
    invalid_positive = next(
        (
            field
            for field in ('CalibFrequency', 'CalibFactor', 'CalibTime')
            if isinstance(calibration[field], list)
            and any(
                isinstance(value, Real) and not isinstance(value, bool) and value <= 0 for value in calibration[field]
            )
        ),
        None,
    )
    invalid_tolerance = isinstance(calibration['StabilityTolerance'], list) and any(
        isinstance(value, Real) and not isinstance(value, bool) and value < 0
        for value in calibration['StabilityTolerance']
    )
    errors = (
        (invalid_metadata, TypeError, f'{invalid_metadata} must be a string.'),
        (empty_metadata, ValueError, f'{empty_metadata} must not be empty.'),
        (
            parsed_date.strftime(DATE_FORMAT) != data['Date'],
            ValueError,
            f'Date must use the format {DATE_FORMAT}.',
        ),
        (not valid_channel_count, ValueError, 'ChannelCount must be a positive integer.'),
        (invalid_list, TypeError, f'Calibration.{invalid_list} must be a list.'),
        (
            invalid_length,
            ValueError,
            f'Calibration.{invalid_length} must contain {channel_count} values, got {invalid_length_value}.',
        ),
        (
            invalid_number,
            ValueError,
            f'Calibration.{invalid_number_field} for channel {invalid_number_channel} must be a finite number.',
        ),
        (invalid_positive, ValueError, f'Calibration.{invalid_positive} values must be greater than zero.'),
        (
            invalid_tolerance,
            ValueError,
            'Calibration.StabilityTolerance values must be greater than or equal to zero.',
        ),
    )
    error = next(((error_type, message) for condition, error_type, message in errors if condition), None)
    if error:
        error_type, message = error
        raise error_type(message)
    return True


def json_write(data_or_path, source, channel_data, description=DEFAULT_DESCRIPTION, date=None):
    """Write multi-channel calibration data with :func:`json.dump`.

    Parameters
    ----------
    data_or_path : str or pathlib.Path
        Path of the JSON file to write.
    source : str
        Name of the source used for calibration.
    channel_data : dict
        Calibration values indexed by one-based channel numbers.
    description : str, optional
        Description stored in the JSON file.
    date : datetime.datetime or str, optional
        Calibration date. The current UTC date is used if omitted.

    Returns
    -------
    dict
        Data written to the JSON file.

    """
    if not isinstance(channel_data, dict):
        msg = 'channel_data must be a dictionary indexed by channel number.'
        raise TypeError(msg)
    if not channel_data:
        msg = 'channel_data must not be empty.'
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
            raise TypeError(msg)
        missing_fields = expected_fields - values.keys()
        extra_fields = values.keys() - expected_fields
        if missing_fields or extra_fields:
            fields = missing_fields or extra_fields
            issue = 'missing' if missing_fields else 'has unexpected fields'
            separator = ': ' if missing_fields else ' '
            msg = f'Channel {channel} {issue}{separator}{", ".join(sorted(fields))}.'
            raise ValueError(msg)
        for field in CALIBRATION_FIELDS:
            calibration[field].append(values[field])

    if isinstance(date, datetime):
        date = date.strftime(DATE_FORMAT)
    elif date is None:
        date = datetime.now(tz=UTC).strftime(DATE_FORMAT)

    path = Path(data_or_path)
    data = {
        'Name': path.name,
        'Description': description,
        'Date': date,
        'Source': source,
        'ChannelCount': len(channels),
        'Calibration': calibration,
    }
    is_valid_json(data)
    with path.open('w', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return data


def json_read(data_or_path):
    """Read validated calibration data into a channel-indexed dictionary.

    Parameters
    ----------
    data_or_path : str or pathlib.Path
        Path of the JSON file to read.

    Returns
    -------
    dict
        File metadata and calibration values indexed by channel number.

    """
    is_valid_json(data_or_path)
    with Path(data_or_path).open(encoding='utf-8') as stream:
        data = json.load(stream)
    channel_data = {
        channel: {field: data['Calibration'][field][index] for field in CALIBRATION_FIELDS}
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
