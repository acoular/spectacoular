"""Calibration orchestration: channel detection and management."""

import logging
import acoular as ac
import numpy as np
from .calibration.calib import Calib
from .preprocessor.per_channel_detection_preprocessor import PerChannelDetectionPreprocessor
from traits.api import Dict, Float, Instance, Int, List, observe

logger = logging.getLogger(__name__)


class ChannelDetector(ac.TimeOut):
    """Detects which channel currently carries the calibration reference signal.
    
    Uses amplitude analysis to identify the active calibration channel.
    The source must provide all channels (unmasked).
    
    Attributes:
        source: Acoular source.
        required_stable: Number of consecutive blocks needed to confirm detection.
        exclude_channels: Channel indices to ignore (already calibrated).
        detected_channel: Index of detected channel, or -1 if none.
        min_ratio: Active channel must be at least this many times louder than average.
    """

    source = Instance(ac.SampleSplitter)
    required_stable = Int(50, desc="consecutive matching blocks required to confirm a channel")

    # channel indices to ignore (already calibrated)
    exclude_channels = List(Int)
    detected_channel = Int(-1, desc="index of the detected calibration channel, -1 if none yet")

    _stable_count = Int(0)
    _candidate = Int(-1)
    channel_freqs = Dict()
    min_ratio = Float(5.0)  # active channel should be at least 5X louder than average of the other channels
    _detection_preproc = Instance(PerChannelDetectionPreprocessor, transient=True)

    @observe('source')
    def _update_source(self, event):
        """Initialize detection preprocessor when source is set."""
        self._detection_preproc = PerChannelDetectionPreprocessor(
            channel_freqs=self.channel_freqs
        )
        self._detection_preproc.source = self.source
        self.source.register_object(self._detection_preproc, buffer_overflow_treatment='none')

    # no support for num
    def result(self, num):
        """Yield blocks while detecting the calibration channel.
        
        Uses amplitude analysis: finds the channel that is significantly
        louder (min_ratio ×) than the average of all other channels.
        Confirms detection after required_stable consecutive blocks.
        
        Args:
            num: Not used (inherited from parent class).
        
        Yields:
            ndarray: Audio blocks with detected_channel updated.
        """
        self.detected_channel = -1
        self._stable_count = 0
        self._candidate = -1

        if self._detection_preproc is None:
            self._update_source(None)

        for block in self._detection_preproc.result(1):
            levels = block.copy()[0]
            # if self.exclude_channels:
            #     levels[self.exclude_channels] = -np.inf

            idx = int(np.argmax(levels))
            max_val = levels[idx]

            other_mask = np.ones(len(levels), dtype=bool)
            other_mask[idx] = False

            if self.exclude_channels:
                for ch in self.exclude_channels:
                    if 0 <= ch < len(other_mask):
                        other_mask[ch] = False
            other_mean = np.mean(levels[other_mask]) if other_mask.any() else 0.0
            amplitude_ratio = np.sqrt(max_val / other_mean) if other_mean > 0 else np.inf

            if amplitude_ratio < self.min_ratio:
                self._candidate = -1
                self._stable_count = 0
            elif idx == self._candidate:
                self._stable_count += 1
            else:
                self._candidate = idx
                self._stable_count = 1

            if self._stable_count >= self.required_stable:
                self.detected_channel = idx

            yield block


class Channel:
    """Represents a single calibration channel.
    
    Attributes:
        calib: Calibration instance for this channel.
        preprocess: Preprocessor instance for signal conditioning.
        calib_value: Current running calibration value.
        calib_value_final: Final confirmed calibration value (0 until complete).
        unit: Measurement unit ('dB', 'Pa', etc.).
        calib_time: Required stable time for calibration.
        stability_tolerance: Allowed variance for stability detection.
    """
    def __init__(self, calib: Calib, preprocess: ac.TimeOut, unit: str, calib_time: float, stability_tolerance: float):
        self.calib = calib
        self.preprocess = preprocess
        self.calib_value = 0.0
        self.calib_value_final = 0.0
        self.unit = unit
        self.calib_time = calib_time
        self.stability_tolerance = stability_tolerance


class CalibOrchestrator:
    """Manages calibration channels and coordinates the calibration process.
    
    Creates and configures channels, runs calibration, and provides access
    to calibration results.
    
    Attributes:
        source: Acoular Audio source.
        channels: Dict mapping channel index to Channel objects.
        log: Logger instance.
        detector: ChannelDetector for auto-detection mode.
    """
    def __init__(self, source: ac.TimeOut, logger: logging.Logger = None):
        """Initialize the orchestrator.
        
        Args:
            source: Audio source (SampleSplitter) providing channel data.
            logger: Optional logger instance.
        """
        self.source = source
        self.channels: dict[int, Channel] = {}
        self.log = logger or logging.getLogger(__name__)
        self.detector = ChannelDetector()

    def configure_detector(self):
        """Connect detector to all channels for auto-detection.
        
        Sets up the detector with channel frequencies from all configured channels.
        """
        self.detector.channel_freqs = {ch: self.channels[ch].preprocess.band for ch in self.channels}
        self.detector.source = self.source

    def detect_channel(self, num):
        """Yield blocks while waiting for channel detection.
        
        Stops when the detector has confirmed a channel.
        
        Args:
            num: Number of blocks to process.
        
        Yields:
            ndarray: Audio blocks until channel is detected.
        """
        for block in self.detector.result(num):
            yield block
            if self.detector.detected_channel != -1:
                break

    def add_channel(self, i: int, calib: Calib, preproc: ac.TimeOut, unit:str, calib_time:float,stability_tolerance:float):
        self.channels[i] = Channel(calib, preproc, unit, calib_time,stability_tolerance)
        block_duration = preproc._num_per_average / self.source.sample_freq
        n_blocks = int(float(calib_time) / block_duration)
        calib.buffer_size = n_blocks
        calib.required_stable = 100
        calib.calibstd = 10 ** (stability_tolerance / 20) - 1 
        masked = ac.MaskedTimeOut(source=self.source, invalid_channels=[j for j in range(self.source.num_channels) if j != i])
        self.source.register_object(masked,buffer_overflow_treatment = 'none')
        preproc.source = masked
        calib.source = preproc
        self.log.debug(f"CalibOrchestrator: added channel {i} (calib={type(calib).__name__}, preproc={type(preproc).__name__}, unit = {unit}, calib_time = {calib_time}, stability_tolerance = {stability_tolerance})")

    def init_channels(self, calib: Calib, preproc: ac.TimeOut, unit, calib_time,stability_tolerance: float):
        """Initialize all source channels with the given calib and preproc config.
        Each channel gets its own clone, otherwise every channel's masking would
        overwrite the same shared calib/preproc instance's source."""
        self.channels.clear()          
        for i in range(self.source.num_channels):
            self.add_channel(i, calib.clone_traits(), preproc.clone_traits(), unit, calib_time,stability_tolerance)
        self.log.debug(f"CalibOrchestrator: initialized {self.source.num_channels} channels")

    def result(self, num, channel_num: int, no_progress_blocks: int=None, stop_on_complete: bool = True):
        """Yield calibration blocks for a specific channel.
        
        Monitors calibration progress, updates calib_value and calib_value_final,
        and can stop early if no progress is detected or calibration completes.
        
        Args:
            num: Number of blocks to process (passed to underlying calib.result).
            channel_num: Channel index to calibrate.
            no_progress_blocks: If set, stop after this many blocks without progress.
            stop_on_complete: Whether to stop when calibration completes (default: True).
        
        Yields:
            ndarray: Calibration blocks with updated calib_value.
        
        Raises:
            KeyError: If channel_num doesn't exist.
        """
        if channel_num not in self.channels:
            raise KeyError(f"Channel {channel_num} does not exist")
        self.log.debug(f"CalibOrchestrator: starting result for channel {channel_num + 1}")
        buffer_size = self.channels[channel_num].calib.buffer_size
        block_count = 0
        no_progress_count = 0
        for block in self.channels[channel_num].calib.result(1):
            self.channels[channel_num].calib_value = self.channels[channel_num].calib.current_estimate
            yield block
            block_count += 1
            if self.channels[channel_num].calib.is_complete():
                if self.channels[channel_num].calib_value_final == 0.0:
                    self.channels[channel_num].calib_value_final = self.channels[channel_num].calib.calibfactor
                if stop_on_complete:
                    break
            if no_progress_blocks is not None and block_count > buffer_size:
                if self.channels[channel_num].calib._stable_count == 0:
                    no_progress_count += 1
                else:
                    no_progress_count = 0
                if no_progress_count >= no_progress_blocks:
                    self.log.debug(f"CalibOrchestrator: no progress after {no_progress_count} blocks for channel {channel_num + 1}")
                    break

