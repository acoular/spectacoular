"""Channel routing for calibration signal processing.

Routes audio channels between source and calibration positions, with optional
noise channel simulation.
This is mainly used to create different scenarios for testing the automatic calibration.
"""

import random
from threading import Timer

import acoular as ac

from traits.api import Any, Bool, Int


class ChannelRouter(ac.TimeOut):
    """Routes audio channels for calibration.

    Swaps samples between source_channel and calib_channel to simulate
    moving a calibration reference between physical channels.

    Attributes
    ----------
        calib_channel: Target channel for calibration (0-based).
        source_channel: Source channel providing the reference signal (0-based).
        noise_channel: Channel to use for noise simulation (0-based).
        logger: Logger instance for debugging.
        noise_enabled: Whether noise simulation is active.
    """

    calib_channel = Int(0)
    source_channel = Int(0)
    noise_channel = Int(0)

    logger = Any()

    noise_enabled = Bool(default=False)

    def switch_channel(self, channel):
        """Immediately switch calibration to the specified channel.

        Args:
            channel: Channel number (1-based) to switch to.
        """
        self.noise_enabled = False

        self.calib_channel = channel - 1
        self.logger.debug("Switched to channel %d.", channel)

    def schedule_switch(self, delay, channel):
        """Schedule a channel switch after a delay.

        Args:
            delay: Delay in seconds before switching.
            channel: Channel number (1-based) to switch to.
        """
        Timer(delay, self.switch_channel, args=(channel,)).start()

    def enable_noise(self, channel):
        """Enable noise simulation mode.

        Randomly selects a noise channel (different from source_channel)
        and routes it to the calibration channel.

        Args:
            channel: Channel number (1-based) for calibration.
        """
        self.calib_channel = channel - 1
        self.noise_channel = random.choice(
            [i for i in range(self.num_channels) if i != self.source_channel]
        )

        self.noise_enabled = True
        self.logger.debug(
            "Noise enabled: calib_channel=%d, noise_channel=%d",
            self.calib_channel+1, self.noise_channel+1
        )

    def schedule_noise(self, delay, channel):
        """Schedule noise simulation to start after a delay.

        Args:
            delay: Delay in seconds before enabling noise.
            channel: Channel number (1-based) for calibration.
        """
        Timer(delay, self.enable_noise, args=(channel,)).start()

    def result(self, num):
        """Yield processed audio blocks with channel routing applied.

        If noise_enabled: swaps calib_channel with noise_channel
        Otherwise: swaps calib_channel with source_channel

        Args:
            num: Number of blocks to process.

        Yields
        ------
            ndarray: Processed audio blocks with channels swapped.
        """
        for block in self.source.result(num):
            out = block.copy()

            if self.noise_enabled:
                out[:, self.calib_channel] = block[:, self.noise_channel]
                out[:, self.source_channel] = block[:, self.calib_channel]
            else:
                out[:, self.calib_channel] = block[:, self.source_channel]
                out[:, self.source_channel] = block[:, self.calib_channel]

            yield out
