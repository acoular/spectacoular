#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
from six.moves import xrange  # solves the xrange/range issue for python2/3: in py3 'xrange' is now treated as 'range' and in py2 nothing changes

from numpy import array, ones, hanning, hamming, bartlett, blackman, \
dot, newaxis, zeros,  fft, fill_diagonal, arange

from traits.api import  Int, Property, Trait, \
Range, Bool, cached_property, property_depends_on, Delegate, CArray, Float


from .fastFuncs import calcCSMmav

from acoular.internal import digest
from acoular.sources import SamplesGenerator
from acoular.spectra import PowerSpectra, synthetic
from acoular.tprocess import TimeInOut
from spectacoular import BaseSpectacoular

class SpectraInOut( TimeInOut ):
    """Provides the spectra of multichannel time data.   
        Returns Spectra per block over a Generator.
    
    """
    
    #: Data source; :class:`~acoular.sources.SamplesGenerator` or derived object.
    source = Trait(SamplesGenerator)

    #: Sampling frequency of output signal, as given by :attr:`source`.
    sample_freq = Delegate('source')
    
    #:the Windows function for the fft
    window = Trait('Rectangular', 
        {'Rectangular':ones, 
        'Hanning':hanning, 
        'Hamming':hamming, 
        'Bartlett':bartlett, 
        'Blackman':blackman}, 
        desc="type of window for FFT")
    
    #: The floating-number-precision of entries of csm, eigenvalues and 
    #: eigenvectors, corresponding to numpy dtypes. Default is 64 bit.
    precision = Trait('complex128', 'complex64', 
                      desc="precision csm, eva, eve")
    
    #generator that yields the fft for every channel
    def result(self, num=128):
        """ 
        Python generator that yields the output block-wise.
        
        Parameters
        ----------
        num : integer
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (numfreq, :attr:`numchannels`). 
            The last block may be shorter than num.
            """
        for temp in self.source.result(num):    
            wind = self.window_(num)
            wind = wind[:, newaxis]
            ft = fft.rfft(temp*wind, None, 0).astype(self.precision)
            yield ft
    
    

class CSMInOut( SpectraInOut,BaseSpectacoular ):
    """Provides the CSM of multichannel Spectra data.  
        Returns CSM for every block over a Generator.
    
    """

    #: Source of SpectraInOut
    source = Trait(SamplesGenerator)

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
                return arange(self.block_size/2+1,dtype=int)[ self.ind_low: self.ind_high ]
            else:
                return array([0])
        except IndexError:
            return range(0)
    
    def fftfreq_fine ( self ):
        return abs(fft.fftfreq(self.block_size, 1./self.sample_freq)\
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
            return array([self.center_freq])
    
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
        Samples in blocks of shape (numfreq, :attr:`numchannels`,:attr:`numchannels`). 
            The last block may be shorter than num.
            """
        bs = self.block_size
        block_sample_freq = self.sample_freq/bs
        #init csm
        numfreq = bs//2 + 1
        csm_shape = (numfreq, self.source.numchannels, self.source.numchannels)
        csmBlock = zeros(csm_shape, dtype=self.precision)
        #calc the weight function
        wind = self.window_( bs )
        block_weight = dot( wind, wind )
        wind = wind[:,newaxis]
        #upper diagonal
        csmUpper = zeros(csm_shape, dtype=self.precision)
        # dsm dummy needed for single band workaround
        block=0
        alpha = 1.0 # initial value
        numblocks = 1 # num
        for temp in self.source.result(bs):
            ft = fft.rfft(temp*wind, None, 0).astype(self.precision)
            #calc csm 
            calcCSMmav(csmUpper, ft, alpha) #calcCSM(csmUpper, ft)

            block += 1
        
            if block % num == 0:
                #put together
                csmLower = csmUpper.conj().transpose(0,2,1)
                [fill_diagonal(csmLower[cntFreq, :, :], 0) for cntFreq in xrange(csmLower.shape[0])]
                #fill csm 
                csmBlock = csmLower + csmUpper
                if self.band_width == 0:
                    yield csmBlock*(2.0/bs/block_weight)
                else:
                    yield synthetic(csmBlock*(2.0/bs/block_weight),
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
               

        
class PowerSpectraSetCSM( PowerSpectra ):
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
    
    numchannels = Property()
    
    cached = False
    
    #: Basename dummy
    basename = 'dummy'
    
    # internal identifier
    digest = Property( 
        depends_on = ['csm', 'sample_freq'], 
        )
    
    def _get_numchannels ( self ):
        return self.csm.shape[1]
    
    
    @cached_property
    def _get_digest( self ):
        return digest( self )
    
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
        
  