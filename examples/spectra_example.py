#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 12:56:10 2020

@author: kujawski
"""

from spectacoular import TimeSamples
from six.moves import xrange  # solves the xrange/range issue for python2/3: in py3 'xrange' is now treated as 'range' and in py2 nothing changes

from numpy import array, ones, hanning, hamming, bartlett, blackman, \
dot, newaxis, zeros,  fft, fill_diagonal, arange

from traits.api import  Int, Property, Trait, \
Range, Bool, cached_property, property_depends_on, Delegate, CArray, Float


# from acoular.internal import digest
from acoular.sources import SamplesGenerator
from acoular.tprocess import TimeInOut


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
    



ts = TimeSamples(name='example_data.h5')
sp = SpectraInOut(source=ts)

result = sp.result(num=256) # result is a generator!

res = next(result) # yields first spectra Block for all 56 channels

# get all spectra blocks  
for res in result:
    r = res
