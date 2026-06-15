"""Numba-accelerated helpers for measurement-app Acoular extensions."""

# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
import numba as nb

CACHED_OPTION = True  # if True: saves the numba func as compiled func in sub directory


@nb.njit(
    [
        nb.complex128[:, :, :](nb.complex128[:, :, :], nb.complex128[:, :], nb.float64),
        nb.complex64[:, :, :](nb.complex64[:, :, :], nb.complex64[:, :], nb.float64),
    ],
    cache=CACHED_OPTION,
)
def calc_csmmav(csm, spec_all_mics, alpha):
    """Adds a given spectrum weighted to the Cross-Spectral-Matrix (CSM).

    Here only the upper triangular matrix of the CSM is calculated. After
    averaging over the various ensembles, the whole CSM is created via complex
    conjugation transposing. This happens outside
    (in :class:`PowerSpectra<acoular.spectra.PowerSpectra>`).

    Parameters
    ----------
    csm : complex128[nFreqs, nMics, nMics]
        The cross spectral matrix which gets updated with the spectrum of the ensemble.
    spec_all_mics : complex128[nFreqs, nMics]
        Spectrum of the added ensemble at all mics.
    alpha : Moving average weighting

    Returns
    -------
    None : as the input csm gets overwritten.
    """
    # ==============================================================================
    #     It showed, that parallelizing brings no benefit when calling calcCSM once per
    #     ensemble (as its done at the moment). BUT it could be whorth, taking a closer
    #     look to parallelization, when averaging over all ensembles inside this numba
    #     optimized function. See "vglOptimierungFAverage.py" for some information on
    #     the various implementations and their limitations.
    # ==============================================================================
    n_freqs = csm.shape[0]
    n_mics = csm.shape[1]
    for cnt_freq in range(n_freqs):
        for cnt_column in range(n_mics):
            temp = spec_all_mics[cnt_freq, cnt_column].conjugate()
            for cnt_row in range(cnt_column + 1):  # calculate upper triangular matrix (of every frequency-slice) only
                csm[cnt_freq, cnt_row, cnt_column] += alpha * (
                    temp * spec_all_mics[cnt_freq, cnt_row] - csm[cnt_freq, cnt_row, cnt_column]
                )
    return csm
