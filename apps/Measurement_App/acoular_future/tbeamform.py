#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------


# imports from other packages
from traits.api import Property, Trait, Bool, cached_property, Instance


# acoular imports
from acoular.internal import digest
from acoular.fbeamform import BeamformerBase
from acoular.tbeamform import BeamformerTime
from acoular.tprocess import TimeInOut

from .spectra import CSMInOut, PowerSpectraSetCSM

                      

class BeamformerFreqTime( BeamformerTime,TimeInOut ):
    """
    Provides a basic time-dependent frequency domain beamformer with frequency output
    for a spatially fixed grid.
    """
    #: :class:`~acoular.fbeamform.BeamformerBase` object that provides the beamformer and it parameters.
    beamformer = Instance(BeamformerBase(),BeamformerBase)
    
    #: Boolean flag, if 'True' (default), the main diagonal is removed before beamforming.
    r_diag = Bool(True, 
                  desc="removal of diagonal")
    
    
    #: :class:`~acoular.spectra.CSMInOut` object that provides the time-dependent
    #: cross spectral matrix and eigenvalues
    source = Trait(CSMInOut, 
                      desc="freq data object")
    
    # internal identifier
    digest = Property( 
        depends_on = ['steer.digest', 'source.digest', 'beamformer.digest'], 
        )

    @cached_property
    def _get_digest( self ):
        return digest(self)

    def result( self, num=1 ):
        """
        Python generator that yields the beamformer output block-wise.
        
        Parameters
        ----------
        num : integer, defaults to 1
            This parameter defines the size of the blocks to be averaged
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (1, :attr:`numchannels`). 
            :attr:`numchannels` is usually very large.
            The last block may be shorter than num.
        """
        fdata = PowerSpectraSetCSM(block_size = self.source.block_size,
                                   sample_freq = self.source.sample_freq,
                                   _fftfreq = self.source.fftfreq(),
                                   indices = self.source.indices)
        self.beamformer.freq_data = fdata
        #self.beamformer.steer = self.steer
        #self.beamformer.r_diag = self.r_diag
        for csm in self.source.result(num):
            fdata.csm = csm
            fdata._fftfreq = self.source.fftfreq()
            fdata.indices = self.source.indices
            yield self.beamformer.result



