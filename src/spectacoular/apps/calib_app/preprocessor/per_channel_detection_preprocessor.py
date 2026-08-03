"""Per-channel filtering for detection preprocessing."""

import acoular as ac
from traits.api import Dict, Float, Int
from scipy.signal import butter, sosfilt, sosfilt_zi
import numpy as np


class PerChannelDetectionPreprocessor(ac.TimeOut):
    """Preprocessor for channel detection with per-channel octave frequency filtering.
    
    Each channel is filtered at its configured calibration frequency (from
    channel_freqs dict) before computing energy levels. This allows the
    detector to identify which channel has the calibration signal by finding
    the channel with the strongest response at its expected frequency.
    
    Attributes:
        channel_freqs: Dict mapping channel index to calibration frequency (Hz).
        _num_per_average: Number of samples to average for energy computation.
    """
    channel_freqs = Dict()          # {channel_idx: frequency_hz}
    _num_per_average = Int(512)

    def _make_filter(self, freq):
        """Create a Butterworth bandpass filter for the given frequency.
        
        Creates a 3rd order bandpass filter centered at freq with octave
        bandwidth (f/√2 to f*√2).
        
        Args:
            freq: Center frequency in Hz.
        
        Returns:
            tuple: SOS coefficients for the filter.
        """
        fs = self.source.sample_freq
        order = 3
        beta = np.pi / (2 * order)
        alpha = pow(2.0, 1.0 / 2.0)  # fraction=1 (Oktave)
        beta = 2 * beta / np.sin(beta) / (alpha - 1 / alpha)
        alpha = (1 + np.sqrt(1 + beta * beta)) / beta
        fr = 2 * freq / fs
        return butter(order, [fr / alpha, fr * alpha], btype='band', output='sos')

    # inspired by Acoular's Average result function
    def result(self, num):
        """Yield averaged squared signal values per channel.
        
        For each channel, applies its specific bandpass filter, squares the
        result, and averages over _num_per_average samples.
        
        Args:
            num: Number of output blocks to produce.
        
        Yields:
            ndarray: Averaged squared values, shape (num_blocks, num_channels).
        """
        filters = {ch: self._make_filter(freq) for ch, freq in self.channel_freqs.items()}
        zi = {ch: sosfilt_zi(sos) * 0 for ch, sos in filters.items()}

        for block in self.source.result(num * self._num_per_average):
            num_samples, num_channels = block.shape
            number_of_averages = int(num_samples / self._num_per_average)
            if number_of_averages > 0:
                filtered = block[: number_of_averages * self._num_per_average].copy()
                for ch, sos in filters.items():
                    if ch >= num_channels:          
                        continue
                    filtered[:, ch], zi[ch] = sosfilt(
                        sos,
                        block[: number_of_averages * self._num_per_average, ch],
                        zi=zi[ch]
                    )
                filtered_squared = filtered ** 2
                yield filtered_squared.reshape((number_of_averages, -1, num_channels)).mean(axis=1)
