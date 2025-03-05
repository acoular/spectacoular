#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
import acoular as ac
import numpy as np
from spectacoular import BaseSpectacoular
from traits.api import  Int, Property, Trait, \
Range, Bool, cached_property, property_depends_on, CArray, Float
from .fastFuncs import calcCSMmav


class CSMInOut( ac.SpectraOut,BaseSpectacoular ):
    """Provides the CSM of multichannel Spectra data.  
    
    Returns CSM for every block over a Generator.
    """

    #: time data source
    source = Trait(ac.SamplesGenerator)

    #: FFT block size, one of: 128, 256, 512, 1024, 2048 ... 16384,
    #: defaults to 1024.
    block_size = Trait(1024, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 
        desc="number of samples per FFT block")

    #: Index of lowest frequency line to compute, integer, defaults to 1,
    #: is used only by objects that fetch the csm, PowerSpectra computes every
    #: frequency line.
    ind_low = Range(1,
        desc="index of lowest frequency line")

    #: Index of highest frequency line to compute, integer, 
    #: defaults to -1 (last possible line for default block_size).
    ind_high = Int(-1, 
        desc="index of highest frequency line")
    
    
    #: Array with a sequence of indices for all frequencies 
    #: between :attr:`ind_low` and :attr:`ind_high` within the result, readonly.
    indices = Property(
        desc = "index range" )
    
    band_width = Int(0)
    
    center_freq = Float(0)
    
    # SPL time weighting : SLOW: 1.0, FAST: 0.125 (default), arbitrary values possible
    weight_time = Float(0.125)
    
    #: Flag, if tru (default), current csm will be calculated with cumulated average of past CSMs
    accumulate = Bool(False, 
        desc="CSM accumulation flag")  
    
    @property_depends_on( 'block_size, ind_low, ind_high, band_width' )
    def _get_indices ( self ):
        try:
            if self.band_width == 0:
                return np.arange(self.block_size/2+1,dtype=int)[ self.ind_low: self.ind_high ]
            else:
                return np.array([0])
        except IndexError:
            return range(0)
    
    def fftfreq_fine ( self ):
        return abs(np.fft.fftfreq(self.block_size, 1./self.sample_freq)\
                       [:int(self.block_size/2+1)])
    
    def fftfreq ( self ):
        """
        Return the Discrete Fourier Transform sample frequencies.
        
        Returns
        -------
        f : ndarray
            Array of length *block_size/2+1* containing the sample frequencies.
        """
        if self.band_width == 0:
            return self.fftfreq_fine()
        else:
            return np.array([self.center_freq])
    
    def result(self, num=1):
        """ 
        Python generator that yields the output block-wise.
        
        Parameters
        ----------
        num : integer
            number of FFT blocks to average
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (numfreq, :attr:`num_channels`,:attr:`num_channels`). 
            The last block may be shorter than num.
            """
        bs = self.block_size
        block_sample_freq = self.sample_freq/bs
        #init csm
        numfreq = bs//2 + 1
        csm_shape = (numfreq, self.source.num_channels, self.source.num_channels)
        csmBlock = np.zeros(csm_shape, dtype=self.precision)
        #calc the weight function
        wind = self.window_( bs )
        block_weight = np.dot( wind, wind )
        wind = wind[:,np.newaxis]
        #upper diagonal
        csmUpper = np.zeros(csm_shape, dtype=self.precision)
        # dsm dummy needed for single band workaround
        block=0
        alpha = 1.0 # initial value
        numblocks = 1 # num
        for temp in self.source.result(bs):
            ft = np.fft.rfft(temp*wind, None, 0).astype(self.precision)
            #calc csm 
            calcCSMmav(csmUpper, ft, alpha) #calcCSM(csmUpper, ft)

            block += 1
        
            if block % num == 0:
                #put together
                csmLower = csmUpper.conj().transpose(0,2,1)
                [np.fill_diagonal(csmLower[cntFreq, :, :], 0) for cntFreq in range(csmLower.shape[0])]
                #fill csm 
                csmBlock = csmLower + csmUpper
                if self.band_width == 0:
                    yield csmBlock*(2.0/bs/block_weight)
                else:
                    yield ac.synthetic(csmBlock*(2.0/bs/block_weight),
                                    self.fftfreq_fine(),
                                    self.center_freq,
                                    self.band_width)
                if self.accumulate:
                    numblocks += num
                    alpha = 1./numblocks
                else:
                    numblocks = num
                    alpha = 1./(1.+self.weight_time*block_sample_freq)
                    #fullnum = num
                    #csmUpper *= 0
               

        
class PowerSpectraSetCSM( ac.PowerSpectra ):
    """
    currently only helper class for BeamformerFreqTime
    """
    _fftfreq = CArray()

    csm = CArray(dtype=complex)
    
    #: Array with a sequence of indices for all frequencies 
    indices = CArray(
        desc = "index range" )
   
    
    #: Sampling frequency of the signal, defaults to 1.0
    sample_freq = Float(1.0, 
        desc="sampling frequency")
    
    num_channels = Property()
    
    cached = False
    
    #: Basename dummy
    basename = 'dummy'
    
    # internal identifier
    digest = Property( 
        depends_on = ['csm', 'sample_freq'], 
        )
    
    def _get_num_channels ( self ):
        return self.csm.shape[1]
    
    
    @cached_property
    def _get_digest( self ):
        return ac.internal.digest( self )
    
    def fftfreq ( self ):
        """
        Return the Discrete Fourier Transform sample frequencies.
        
        Returns
        -------
        f : ndarray
            Array of length *block_size/2+1* containing the sample frequencies.
        
        Now _fftfreq has to be set by calling instance!
        """
        return self._fftfreq
        #return abs(fft.fftfreq(self.block_size, 1./self.sample_freq)\
        #            [:int(self.block_size/2+1)])
        
  