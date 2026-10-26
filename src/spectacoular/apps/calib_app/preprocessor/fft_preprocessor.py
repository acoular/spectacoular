"""FFT preprocessing for spectrum visualization."""

import logging

import acoular as ac

from traits.api import Any, observe


class FFT(ac.Generator):
    """Real FFT generator for spectrum visualization.

    Computes RFFT (Real Fast Fourier Transform) of the input signal
    and yields spectrum data reshaped for per-channel display.

    Attributes
    ----------
        source: Input audio source.
        log: Logger instance.
        rfft: RFFT processor instance.
        frequencies: Array of frequency bins from the RFFT.
        switch: Visibility switch to enable/disable processing.
    """

    source = Any()
    log = Any()
    rfft = Any()
    frequencies = Any()
    switch = Any()

    def __init__(self, source, switch, logger=None):
        """Initialize the FFT generator.

        Args:
            source: Input audio source.
            switch: Visibility toggle widget.
            logger: Optional logger instance.
        """
        super().__init__()
        self.log = logger or logging.getLogger(__name__)
        self.source = source
        self.switch = switch

    @observe('source')
    def _update_source(self, event):
        """Rebuild RFFT pipeline when source changes."""
        new_source = event.new

        self.rfft = ac.RFFT(source=new_source, block_size=1024, scaling='amplitude')

        new_source.register_object(self.rfft, buffer_overflow_treatment='none')
        self.frequencies = self.rfft.freqs

    def result(self):
        """Yield FFT spectrum data when switch is active.

        Yields
        ------
            ndarray: Spectrum data reshaped as (num_freq_bins, num_channels).
        """
        if self.switch.active:
            for data in self.rfft.result(1):
                yield data.reshape(len(self.frequencies), -1).T
