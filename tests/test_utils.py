# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""Tests for calibration JSON utilities."""

from pathlib import Path

from spectacoular.utils import json_read, json_validation, json_write

import pytest


def test_read_and_write_calibration_json(tmp_path):
    """Read and rewrite a reference calibration file without changing it."""
    reference_file = Path(__file__).parent / 'data' / 'calibration.json'
    if json_validation(reference_file) is not True:
        pytest.fail('The reference calibration file is not valid.')

    calibration = json_read(reference_file)
    output_file = tmp_path / reference_file.name
    json_write(
        output_file,
        calibration['Source'],
        calibration['Channels'],
        calibration['Description'],
        calibration['Date'],
    )

    if output_file.read_text(encoding='utf-8') != reference_file.read_text(encoding='utf-8'):
        pytest.fail('The rewritten calibration file differs from the reference file.')
