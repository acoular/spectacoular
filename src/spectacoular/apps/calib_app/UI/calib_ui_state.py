from datetime import datetime
from ..util import pa_to_dB


class CalibUIState:
    """Shared state between background thread and UI components.
    
    Concurrency model:
    - At most ONE background thread (consume/consume_auto) writes via update()
    - Main thread (Bokeh) reads via get()/all_channels() for UI refresh
    - Main thread also writes via init_from_orchestrator(), but ONLY after
      stopping the background thread (see main.py: load_callback, on_source_change)
    - Therefore: no concurrent writes, no concurrent read/write
    - No lock needed, but this relies on callers maintaining the contract:
      STOP background thread BEFORE modifying orchestrator or calling init_from_orchestrator()
    """

    def __init__(self):
        """Initialize empty channel state."""
        self._channels = {}  # ch -> {factor, band, magnitude, unit, is_stable, final_factor, calib_time, stability_tolerance}

    def update(self, ch: int, factor: float = None, band: float = None, magnitude: float = None, is_stable: bool = None, final_factor: float = None, unit: str = None, calib_time: float = None, stability_tolerance: float = None):
        """Update channel data. Called by background thread during calibration.
        
        Args:
            ch: Channel index (0-based).
            factor: Current calibration factor (calib_value).
            band: Frequency band for this channel's preprocessor.
            magnitude: Reference magnitude (converted to Pa if unit is dB).
            is_stable: Whether the calibration has stabilized.
            final_factor: Final calibration factor (calib_value_final).
            unit: Unit of measurement ('Pa' or 'dB').
            calib_time: Calibration time setting.
            stability_tolerance: Tolerance for stability detection.
        """
        if ch not in self._channels:
            self._channels[ch] = {}
        
        channel_data = self._channels[ch]
        if factor is not None:
            channel_data['factor'] = factor
        if band is not None:
            channel_data['band'] = band
        if magnitude is not None:
            channel_data['magnitude'] = magnitude
        if is_stable is not None:
            channel_data['is_stable'] = is_stable
        if final_factor is not None:
            channel_data['final_factor'] = final_factor
        if unit is not None:
            channel_data['unit'] = unit
        if calib_time is not None:
            channel_data['calib_time'] = calib_time
        if stability_tolerance is not None:
            channel_data['stability_tolerance'] = stability_tolerance
        channel_data['timestamp'] = datetime.now().strftime("%H:%M:%S")

    def get(self, ch: int):
        """Get channel data dict, or None if channel doesn't exist.
        
        Args:
            ch: Channel index (0-based).
        
        Returns:
            dict or None: Channel data dictionary.
        """
        return self._channels.get(ch)

    def all_channels(self):
        """Get a copy of all channel data.
        
        Returns:
            dict: Mapping of channel index to channel data dict.
        """
        return dict(self._channels)

    def reset(self):
        """Clear all channel data. Called when source changes or before repopulating from orchestrator."""
        self._channels = {}

    def init_from_orchestrator(self, orchestrator):
        """Populate UI state from orchestrator's channels.
        
        Called from main thread after stopping the background thread.
        Converts dB reference magnitudes to Pa for consistent UI display.
        
        Args:
            orchestrator: CalibOrchestrator instance with channel configuration.
        """
        self.reset() 
        for ch, channel_obj in orchestrator.channels.items():
            factor = float(channel_obj.calib_value)
            final_factor = float(channel_obj.calib_value_final)
            band = channel_obj.preprocess.band
            unit = str(channel_obj.unit)
            calib_time = float(channel_obj.calib_time)
            stability_tolerance = float(channel_obj.stability_tolerance)
            if unit == "dB":
                magnitude = pa_to_dB(channel_obj.calib.referenceMagnitude)
            else: 
                magnitude = channel_obj.calib.referenceMagnitude
            is_stable = channel_obj.calib.is_stable()
            self.update(ch, factor, band, magnitude, is_stable, final_factor=final_factor, unit=unit, calib_time=calib_time, stability_tolerance=stability_tolerance)
