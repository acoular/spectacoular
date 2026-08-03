"""Preprocessor pipeline for calibration signals."""

import acoular as ac
import spectacoular as sp
from traits.api import Float, Int, Instance, observe
import numpy as np


class CalibPreprocessor(ac.TimeOut):
    """Default preprocessor pipeline for calibration.
    
    Pipeline stages:
    1. FiltOctave: Filters signal to the specified frequency band
    2. TimePower: Squares the signal (power = x²)
    3. Average: Averages over _num_per_average samples
    4. result(): Takes sqrt to yield RMS value
    
    This computes: RMS = √(mean(x²)) for the filtered signal.
    
    Attributes:
        band: Center frequency of the octave band filter (Hz).
        _num_per_average: Number of samples per average.
    """

    band = Float(1000.0, transient=True)
    _num_per_average = Int(512, desc="Number of samples to be averaged")

    _filt = Instance(sp.FiltOctave, transient=True)
    _square = Instance(ac.TimePower, transient=True)
    _avg = Instance(ac.Average, transient=True)

    def __init__(self, band=1000.0, num_per_average=512, **kwargs):
        """Initialize with frequency band and averaging settings.
        
        Args:
            band: Center frequency for octave filter (Hz).
            num_per_average: Samples per averaging window.
        """
        super().__init__(**kwargs)
        self.band = band
        self._num_per_average = num_per_average

    @observe('source')
    def _update_pipeline(self, event):
        """Rebuild pipeline when source changes."""
        self._filt = sp.FiltOctave(source=self.source, band=self.band)
        self._square = ac.TimePower(source=self._filt)
        self._avg = ac.Average(source=self._square, num_per_average=self._num_per_average)

    def result(self, num):
        """Yield RMS values for the filtered signal.
        
        Args:
            num: Number of blocks to process.
        
        Yields:
            float: RMS value = sqrt(mean(x²)) for each block.
        """
        if self._filt is None:
            self._update_pipeline(None)
        for block in self._avg.result(num):
            yield np.sqrt(block)
