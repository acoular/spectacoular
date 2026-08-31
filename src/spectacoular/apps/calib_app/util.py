"""Utility functions."""

import json
import math
from pathlib import Path

import numpy as np


def db_to_pa(level_db: float) -> float:
    """Convert decibels to Pascals."""
    return math.sqrt(4e-10 * 10 ** (level_db / 10))


def pa_to_db(level_pa: float) -> float:
    """Convert Pascals to decibels."""
    # Return -350 for non-positive values to avoid math domain error (Acoular convention see L_p)
    if level_pa <= 0:
        return -350.0
    return 10 * math.log10(level_pa**2 / 4e-10)


def v_to_dbv(level_volt: float) -> float:
    """Convert Volt to decibel volt."""
    # Return -350 for non-positive values to avoid math domain error (Acoular convention see L_p)
    if np.any(level_volt <= 0):
        return np.full_like(level_volt, -350.0)
    return 20 * np.log10(level_volt)


def load_calib_factors(json_file, array_length=None, default_value=1.0):
    """Load calibration factors from a JSON file into a numpy array.

    Args:
        json_file: Path to JSON calibration file.
        array_length: Length of output array. If None, uses max channel number from file.
        default_value: Default value for uninitialized channels (default: 1.0).

    Returns
    -------
        ndarray: Array of calibration factors, indexed by channel (0-based).
    """
    with Path.open(json_file) as f:
        data = json.load(f)

    channels = data['Channels']

    channel_numbers = [int(ch) for ch in channels]

    if array_length is None:
        array_length = max(channel_numbers)

    calib_array = np.full(array_length, default_value, dtype=float)

    for ch, channel_data in channels.items():
        channel_index = int(ch) - 1

        if channel_index < array_length:
            calib_array[channel_index] = channel_data['CalibFactor']['Value']

    return calib_array
