import acoular as ac
import spectacoular as sp
from traits.api import Property, List, cached_property, Instance, Delegate
from numpy import array 

class MaskedChannels(ac.TimeOut, sp.BaseSpectacoular):
    """Signal processing block for channel and sample selection.

    This class serves as intermediary to define (in)valid
    channels and samples for any
    :class:`~acoular.sources.SamplesGenerator` (or derived) object.
    It gets samples from :attr:`~acoular.base.TimeOut.source`
    and generates output via the generator :meth:`result`.
    """

    # Data source; :class:`~acoular.base.SamplesGenerator` or derived object.
    source = Instance(ac.SamplesGenerator)

    # Channels that are to be treated as invalid.
    invalid_channels = List(int, desc='list of invalid channels')

    # Channel mask to serve as an index for all valid channels, is set automatically.
    channels = Property(depends_on=['invalid_channels', 'source.num_channels'], desc='channel mask')

    # Number of channels in input, as given by :attr:`~acoular.base.TimeOut.source`.
    num_channels_total = Delegate('source', 'num_channels')

    # Number of valid channels, is set automatically.
    num_channels = Property(
        depends_on=['invalid_channels', 'source.num_channels'], desc='number of valid input channels'
    )

    # internal identifier
    digest = Property(depends_on=['source.digest', 'invalid_channels'])

    @cached_property
    def _get_digest(self):
        return ac.internal.digest(self)

    @cached_property
    def _get_channels(self):
        if len(self.invalid_channels) == 0:
            return slice(0, None, None)
        allr = [i for i in range(self.num_channels_total) if i not in self.invalid_channels]
        return array(allr)

    @cached_property
    def _get_num_channels(self):
        if len(self.invalid_channels) == 0:
            return self.num_channels_total
        return len(self.channels)

    def result(self, num):
        """Python generator that yields the output block-wise.

        Parameters
        ----------
        num : integer
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).

        Returns
        -------
        Samples in blocks of shape (num, :attr:`num_channels`).
            The last block may be shorter than num.

        """
        for block in self.source.result(num):
            yield block[:, self.channels]

