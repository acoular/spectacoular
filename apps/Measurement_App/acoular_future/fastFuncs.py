#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------
import numba as nb

cachedOption = True  # if True: saves the numba func as compiled func in sub directory

@nb.njit([nb.complex128[:,:,:](nb.complex128[:,:,:], nb.complex128[:,:], nb.float64), 
          nb.complex64[:,:,:](nb.complex64[:,:,:], nb.complex64[:,:], nb.float64)], 
          cache=cachedOption)
def calcCSMmav(csm, SpecAllMics, alpha):
    """ Adds a given spectrum weighted to the Cross-Spectral-Matrix (CSM).
    Here only the upper triangular matrix of the CSM is calculated. After
    averaging over the various ensembles, the whole CSM is created via complex 
    conjugation transposing. This happens outside 
    (in :class:`PowerSpectra<acoular.spectra.PowerSpectra>`). 
    
    Parameters
    ----------
    csm : complex128[nFreqs, nMics, nMics] 
        The cross spectral matrix which gets updated with the spectrum of the ensemble.
    SpecAllMics : complex128[nFreqs, nMics] 
        Spectrum of the added ensemble at all Mics.
    alpha : Moving average weighting
    
    Returns
    -------
    None : as the input csm gets overwritten.
    """
#==============================================================================
#     It showed, that parallelizing brings no benefit when calling calcCSM once per 
#     ensemble (as its done at the moment). BUT it could be whorth, taking a closer 
#     look to parallelization, when averaging over all ensembles inside this numba 
#     optimized function. See "vglOptimierungFAverage.py" for some information on 
#     the various implementations and their limitations.
#==============================================================================
    nFreqs = csm.shape[0]
    nMics = csm.shape[1]
    for cntFreq in range(nFreqs):
        for cntColumn in range(nMics):
            temp = SpecAllMics[cntFreq, cntColumn].conjugate()
            for cntRow in range(cntColumn + 1):  # calculate upper triangular matrix (of every frequency-slice) only
                csm[cntFreq, cntRow, cntColumn] += alpha * (temp * SpecAllMics[cntFreq, cntRow]
                                                            - csm[cntFreq, cntRow, cntColumn])
    return csm
