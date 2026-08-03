"""Calibration base classes for channel calibration."""

import acoular as ac

import numpy as np
from traits.api import Float, Instance, Int


class Calib(ac.TimeOut):
    """Base class/Interface for calibration of individual source channels.

    Subclass this to implement custom calibration algorithms.
    Provides the basic infrastructure for tracking calibration state,
    stability, and completion.

    Attributes
    ----------
        source: Data source (Average or derived object).
        reference_magnitude: Known reference level of the calibration device.
        buffer_size: Number of blocks to buffer for stability calculation.
        calibstd: Allowed relative standard deviation threshold.
        calibstd_measured: Current measured relative std of the buffer.
        calibfactor: Final calibration factor once complete.
        current_estimate: Live estimate of the calibration factor.
        required_stable: Number of consecutive stable blocks needed.
        stable_count: counter for stable blocks.
    """

    #: Data source; :class:`~acoular.sources.Average` or derived object.
    source = Instance(ac.TimeOut)

    #: calibration level of calibration device
    reference_magnitude = Float(
        0.0, desc="reference magnitude of calibration device (Pa, m/s², N or V depending on sensor)"
    )

    #: max elements/averaged blocks to calculate calibration value.
    buffer_size = Int(
        100, desc="number of blocks considered to determine calibration value"
    )

    #: channel-wise allowed standard deviation of calibration values in buffer
    calibstd = Float(
        0.058, desc="allowed relative standard deviation (std/mean) of calibration values in buffer"
    )
    calibstd_measured = Float(float("inf"), desc="measured standard deviation of the current buffer")

    #: calibration factor S_hat determined during result()
    calibfactor = Float(0.0, desc="determined calibration factor")
    current_estimate = Float(0.0, desc="current live estimate of calibration factor")

    #: stability criteria
    required_stable = Int(100, desc="consecutive stable blocks to complete calibration")
    stable_count = Int(0)

    def is_stable(self) -> bool:
        """Check if the current measurement is stable.

        Returns
        -------
            bool: True if measured std is below the threshold.
        """
        return self.calibstd_measured < self.calibstd

    def is_complete(self) -> bool:
        """Check if calibration is complete.

        Returns
        -------
            bool: True if required number of stable blocks have been achieved.
        """
        return self.stable_count >= self.required_stable



class StdCalib(Calib):
    """Standard calibration using a known reference signal.

    Computes the calibration factor as:
        S_hat = reference_magnitude / mean(buffer)

    Tracks stability by measuring relative standard deviation (std/mean)
    of the buffered signal values. Calibration is complete when the
    signal remains stable for required_stable consecutive blocks.
    """

    def result(self, num):
        """Yield blocks while computing calibration factor.

        Maintains a sliding buffer of samples, computes mean and std,
        and tracks stability. When stable, computes current_estimate as
        reference_magnitude / mean. When complete, saves final calibfactor.

        Args:
            num: Number of blocks to process.

        Yields
        ------
            ndarray: Processed audio blocks.
        """
        buffer = np.zeros(self.buffer_size)
        self.calibfactor = 0.0          # result array
        self.current_estimate = 0.0
        self.stable_count = 0

        for block in self.source.result(num):
            ns = block.shape[0]

            # Shift buffer forward and insert new block at the end
            buffer[0 : self.buffer_size - ns] = buffer[ns:]
            buffer[-ns:] = block[:, 0]

            # Check stability: std of all buffer values per channel
            mean_val = np.mean(buffer)
            std_val = np.std(buffer)
            self.calibstd_measured = std_val / mean_val if mean_val > 0 else np.inf

            # Counter for stability
            if self.is_stable():
                self.stable_count += 1
            else:
                self.stable_count = 0

            # Calculating current calibration factor
            if mean_val > 0:
                self.current_estimate = self.reference_magnitude / mean_val

            # Calculating final calibration factor
            if self.is_complete():
                self.calibfactor = self.current_estimate

            yield block
