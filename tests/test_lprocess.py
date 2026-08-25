"""Tests for live-processing sources."""

from itertools import islice

import spectacoular as sp

import numpy as np
import pytest


def test_time_samples_phantom_can_repeat_data(monkeypatch):
    """A repeating phantom source restarts at the first sample after EOF."""
    monkeypatch.setattr('spectacoular.lprocess.sleep', lambda _seconds: None)
    source = sp.TimeSamplesPhantom(data=np.arange(6).reshape(3, 2), sample_freq=10, repeat=True)

    if source.num_samples != -1:
        pytest.fail(f'expected repeating phantom source num_samples=-1, got {source.num_samples}')

    blocks = list(islice(source.result(2), 4))
    actual = [block.tolist() for block in blocks]
    expected = [
        [[0, 1], [2, 3]],
        [[4, 5]],
        [[0, 1], [2, 3]],
        [[4, 5]],
    ]
    if actual != expected:
        pytest.fail(f'expected repeated blocks {expected}, got {actual}')


def test_time_samples_phantom_does_not_repeat_by_default(monkeypatch):
    """The default phantom source remains finite for non-measurement use cases."""
    monkeypatch.setattr('spectacoular.lprocess.sleep', lambda _seconds: None)
    source = sp.TimeSamplesPhantom(data=np.arange(6).reshape(3, 2), sample_freq=10)

    blocks = list(source.result(2))
    actual = [block.tolist() for block in blocks]
    expected = [
        [[0, 1], [2, 3]],
        [[4, 5]],
    ]
    if actual != expected:
        pytest.fail(f'expected finite blocks {expected}, got {actual}')
