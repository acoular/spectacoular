#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements classes for the use in live processing applications. Some of the 
classes might move to Acoular module in the future.

.. autosummary::
    :toctree: generated/

    TimeSamplesPhantom
    TimeInOutPresenter
    CalibHelper
    FiltOctaveLive
    TimeSamplesPlayback
    SpectraInOut
"""
 
from numpy import logical_and,savetxt,mean,array,newaxis, zeros,\
 pad, ones, hanning, hamming, bartlett, blackman,fft ,arange, empty, sqrt, dot

from scipy.signal import lfilter
from datetime import datetime
from time import time,sleep
from bokeh.models.widgets import TextInput,DataTable,TableColumn,\
    NumberEditor, Select, NumericInput
from bokeh.models import ColumnDataSource
from traits.api import Property, File, CArray,Int, Delegate, Trait,\
cached_property, on_trait_change, Float,Bool, Instance, ListInt
try:
    import sounddevice as sd
    sd_enabled=True
except:
    sd_enabled = False

# acoular imports
from acoular import TimeInOut, L_p,TimeAverage,FiltFiltOctave, \
    SamplesGenerator,MaskedTimeSamples
from acoular.internal import digest
# 
from .dprocess import BasePresenter
from .bokehview import get_widgets, set_widgets
from .factory import BaseSpectacoular

invch_columns = [TableColumn(field='invalid_channels', title='invalid_channels', editor=NumberEditor()),]

class TimeSamplesPhantom(MaskedTimeSamples,BaseSpectacoular):
    """
    TimeSamples derived class for propagating signal processing blocks with
    user-defined time delay.
    
    The functionality of the class is to deliver existing blocks of data in a
    certain time interval. Can be used to simulate a measurement (but data
    is read from file).
    """

    #: Defines the delay with which the individual data blocks are propagated.
    #: Defaults to 1/sample_freq
    time_delay = Float(
        desc="Time interval between individual blocks of data")     
    
    #: Indicates if samples are collected, helper trait to break result loop
    collectsamples = Bool(True,
        desc="Indicates if result function is running")

    trait_widget_mapper = {'name': TextInput,
                        'basename': TextInput,
                        'start' : NumericInput,
                        'stop' : NumericInput,
                        'numsamples': NumericInput,
                        'sample_freq': NumericInput,
                        'invalid_channels':DataTable,
                        'numchannels' : NumericInput,
                        'time_delay': NumericInput,
                        }
    trait_widget_args = {'name': {'disabled':False},
                        'basename': {'disabled':True},
                        'start':  {'disabled':False, 'mode':'int'},
                        'stop':  {'disabled':False, 'mode':'int'},
                        'numsamples':  {'disabled':True, 'mode':'int'},
                        'sample_freq':  {'disabled':True, 'mode':'float'},
                        'invalid_channels': {'disabled':False,'editable':True, 'columns':invch_columns},
                        'numchannels': {'disabled':True,'mode':'int'},
                        'time_delay': {'disabled':False, 'mode':'float'},
                        }

    def result(self, num=128):
        """
        Python generator that yields the output block-wise.
                
        Parameters
        ----------
        num : integer, defaults to 128
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .
        
        Returns
        -------
        Samples in blocks of shape (num, numchannels). 
            The last block may be shorter than num.
        """
        
        if self.time_delay:
            slp_time = self.time_delay
        else:
            slp_time = (1/self.sample_freq)*num
        
        if self.numsamples == 0:
            raise IOError("no samples available")
        i = 0
        if self.calib:
            if self.calib.num_mics == self.numchannels:
                cal_factor = self.calib.data[newaxis]
            else:
                raise ValueError("calibration data not compatible: %i, %i" % \
                            (self.calib.num_mics, self.numchannels))
            while i < self.numsamples and self.collectsamples:
                yield self.data[i:i+num]*cal_factor
                sleep(slp_time)
                i += num
        else:
            while i < self.numsamples and self.collectsamples:
                yield self.data[i:i+num]
                sleep(slp_time)
                i += num        
                
                
                
class TimeInOutPresenter(TimeInOut,BasePresenter):
    """
    :class:`TimeInOut` derived class for building an interface from Acoular's generator 
    pipelines to Bokeh's ColumnDataSource model that serves as a source for
    plots and tables.
    
    ColumnDataSource is updated from result function. Can be used for automatic
    presenting of live data.   
    """       

    #: Bokeh's ColumnDataSource, updated from result loop
    data = ColumnDataSource(data={'data':array([])}) 

    def result(self,num):
        """
        Python generator that yields the output block-wise.
                
        Parameters
        ----------
        num : integer, defaults to 128
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .
        
        Returns
        -------
        Samples in blocks of shape (num, numchannels). 
            The last block may be shorter than num.
        """
        for temp in self.source.result(num):
            self.data.data['data'] = temp
            yield temp



columns = [TableColumn(field='calibvalue', title='calibvalue', editor=NumberEditor()),
           TableColumn(field='caliblevel', title='caliblevel', editor=NumberEditor())]

class CalibHelper(TimeInOut, BaseSpectacoular):
    """
    Class for calibration of individual source channels 
    """

    #: Data source; :class:`~acoular.sources.TimeAverage` or derived object.
    source = Instance(TimeAverage)
    
    #: Name of the file to be saved. If none is given, the name will be
    #: automatically generated from a time stamp.
    name = File(filter=['*.xml'], 
        desc="name of data file")    

    #: calibration level (e. g. dB or Pa) of calibration device 
    magnitude = Float(114,
        desc="calibration level of calibration device")
    
    #: calibration values determined during evaluation of :meth:`result`.
    #: array of floats with dimension (numchannels, 2)
    calibdata = CArray(dtype=float,
       desc="determined calibration values")

    #: calibration factor determined during evaluation of :meth:`save`.
    #: array of floats with dimension (numchannels)
    calibfactor = CArray(dtype=float,
       desc="determined calibration factor")


    #: max elements/averaged blocks to calculate calibration value. 
    buffer_size = Int(100,
       desc="number of blocks considered to determine calibration value" )

    #: channel-wise allowed standard deviation of calibration values in buffer 
    calibstd = Float(.5,
       desc="allowed standard deviation of calibration values in buffer")

    #: minimum allowed difference in magnitude between the channel to be 
    #: calibrated and remaining channels.
    delta = Float(10,
      desc="magnitude difference between calibrating channel and remaining channels")
    
    # internal identifier
    digest = Property( depends_on = ['source.digest', '__class__'])

    trait_widget_mapper = {'name': TextInput,
                           'magnitude': NumericInput,
                            'calibdata' : DataTable,
                           'buffer_size' : NumericInput,
                           'calibstd': NumericInput,
                           'delta': NumericInput,
                       }

    trait_widget_args = {'name': {'disabled':False},
                         'magnitude': {'disabled':False, 'mode': 'float'},
                           'calibdata':  {'editable':True,'columns':columns},
                         'buffer_size':  {'disabled':False,'mode': 'int'},
                         'calibstd':  {'disabled':False, 'mode': 'float'},
                         'delta': {'disabled':False, 'mode': 'float'},
                         }
    
    def to_pa(self,level):
        return (10**(level/10))*(4e-10)

    @cached_property
    def _get_digest( self ):
        return digest(self)

    @on_trait_change('source, source.numchannels')
    def adjust_calib_values(self):
        diff = self.numchannels-self.calibdata.shape[0]
        if self.calibdata.size == 0 or diff != 0:
            self.calibdata = zeros((self.numchannels,2))

    def create_filename(self):
        if self.name == '':
            stamp = datetime.fromtimestamp(time()).strftime('%H:%M:%S')
            self.name = 'calib_file_'+stamp.replace(':','')+'.xml'

    def save(self):
        self.create_filename()

        with open(self.name,'w') as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n<Calib name="{self.name}">\n')
            for i in range(self.numchannels):
                channel_string = str(i+1)
                fac = self.calibfactor[i]
                f.write(f'	<pos Name="Point {channel_string}" factor="{fac}"/>\n')
            f.write('</Calib>')
        #savetxt(self.name,self.calibdata,'%f')

    def result(self, num):
        """
        Python generator that yields the output block-wise.
                
        Parameters
        ----------
        num : integer, defaults to 128
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .
        
        Returns
        -------
        Samples in blocks of shape (num, numchannels). 
            The last block may be shorter than num.
        """
        self.adjust_calib_values()
        nc = self.numchannels
        self.calibfactor = zeros(self.numchannels)
        buffer = zeros((self.buffer_size,nc))
        for temp in self.source.result(num):
            ns = temp.shape[0]
            bufferidx = self.buffer_size-ns
            buffer[0:bufferidx] = buffer[-bufferidx:]  # copy remaining samples in front of next block
            buffer[-ns:,:] = L_p(temp)
            calibmask = logical_and(buffer > (self.magnitude-self.delta),
                                  buffer < (self.magnitude+self.delta)
                                  ).sum(0) 
            # print(calibmask)
            if (calibmask.max() == self.buffer_size) and (calibmask.sum() == self.buffer_size):
                idx = calibmask.argmax()
                # print(buffer[:,idx].std())
                if buffer[:,idx].std() < self.calibstd:
                    calibdata = self.calibdata.copy()
                    calibdata[idx,:] = [mean(buffer[:,idx]), self.magnitude]
                    # self.calibdata[idx,:] = [mean(L_p(buffer[:,idx])), self.magnitude]
                    self.calibdata = calibdata
                    print(self.calibdata[idx,:])
                        
            for i in arange(self.numchannels):
                self.calibfactor[i] = self.to_pa(self.magnitude)/self.to_pa(float(self.calibdata[i,0]))
            yield temp
            

class FiltOctaveLive( FiltFiltOctave, BaseSpectacoular ):
    """
    Octave or third-octave filter (not zero-phase).
    
    This class is similar to Acoular's :class:`~acoular.tprocess.FiltFiltOctave`.
    The only difference is that the filter coefficients can be changed while 
    the result function is executed. 
    """

    trait_widget_mapper = {'band': NumericInput,
                       }

    trait_widget_args = {'band': {'disabled':False, 'mode': 'float'},
                         }

    def result(self, num):
        """ 
        Python generator that yields the output block-wise.

        
        Parameters
        ----------
        num : integer
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (num, numchannels). 
            Delivers the bandpass filtered output of source.
            The last block may be shorter than num.
        """
        
        for block in self.source.result(num):
            b, a = self.ba(3) # filter order = 3
            zi = zeros((max(len(a), len(b))-1, self.source.numchannels))
            block, zi = lfilter(b, a, block, axis=0, zi=zi)
            yield block

if sd_enabled:                
    columns = [TableColumn(field='channels', title='channels', editor=NumberEditor()),]

    class TimeSamplesPlayback(TimeInOut,BaseSpectacoular):
        """
        Naive class implementation to allow audio playback of .h5 file contents. 
        
        The class uses the devices available to the sounddevice library for 
        audio playback. Input and output devices can be listed by
        
        >>>    import sounddevice
        >>>    sounddevice.query_devices()
        
        In the future, this class should work in buffer mode and 
        also write the current frame that is played to a class attribute.
        """
        
        # internal identifier
        digest = Property( depends_on = ['source.digest', '__class__'])
    
        #: list containing indices of the channels to be played back.
        channels = ListInt(
            desc="channel indices to be played back")
        
        #: two-element list containing indices of input and output device to 
        #: be used for audio playback. 
        device = Property()
        
        # current frame played back
        # currentframe = Int()
        
        trait_widget_mapper = {'channels': DataTable,
                           }
    
        trait_widget_args = {'channels': {'disabled':False, 'columns':columns},
                         }
    
        @cached_property
        def _get_digest( self ):
            return digest(self)
        
        def _get_device( self ):
            return list(sd.default.device)
        
        def _set_device( self, device ):
            sd.default.device = device
        
        def play( self ):
            '''
            normalized playback of source channels given by :attr:`channels` trait
            '''
            if self.channels:
                if isinstance(self.source,MaskedTimeSamples):
                    sig = self.source.data[
                        self.source.start:self.source.stop,self.channels].sum(1)
                else:
                    sig = self.source.data[:,self.channels].sum(1)
                norm = abs(sig).max()
                sd.play(sig/norm,
                        samplerate=self.sample_freq,
                        blocking=False)
            
        def stop( self ):
            ''' method stops audio playback of file content '''
            sd.stop()


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
    
    #: FFT block size, one of: 128, 256, 512, 1024, 2048 ... 65536,
    #: defaults to 1024.
    block_size = Trait(1024, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536,
        desc="number of samples per FFT block")

    #: Overlap factor for averaging: 'None'(default), '50%', '75%', '87.5%'.
    overlap = Trait('None', {'None':1, '50%':2, '75%':4, '87.5%':8}, 
        desc="overlap of FFT blocks")

    #: The floating-number-precision of entries of csm, eigenvalues and 
    #: eigenvectors, corresponding to numpy dtypes. Default is 64 bit.
    precision = Trait('complex128', 'complex64', 
                      desc="precision csm, eva, eve")
    
    # internal identifier
    digest = Property( depends_on = ['source.digest','precision','block_size',
                                    'window','overlap'])

    trait_widget_mapper = {
                        'window': Select,
                        'block_size': Select,
                        'overlap' : Select,
                       }

    trait_widget_args = {
                        'window':  {'disabled':False},
                        'block_size':  {'disabled':False},
                        'overlap':  {'disabled':False},
                         }

    get_widgets = get_widgets
    
    set_widgets = set_widgets

    @cached_property
    def _get_digest( self ):
        return digest(self)

    def fftfreq ( self ):
        """
        Return the Discrete Fourier Transform sample frequencies.
        
        Returns
        -------
        f : ndarray
            Array of length *block_size/2+1* containing the sample frequencies.
        """
        return abs(fft.fftfreq(self.block_size, 1./self.source.sample_freq)\
                    [:int(self.block_size/2+1)])

    #generator that yields the time data blocks for every channel (with optional overlap)
    def get_source_data(self):
        bs = self.block_size
        temp = empty((2*bs, self.numchannels))
        pos = bs
        posinc = bs/self.overlap_
        for data_block in self.source.result(bs):
            ns = data_block.shape[0]
            temp[bs:bs+ns] = data_block # fill from right
            while pos+bs <= bs+ns:
                yield temp[int(pos):int(pos+bs)]
                pos += posinc
            else:
                temp[0:bs] = temp[bs:] # copy to left
                pos -= bs

    #generator that yields the fft for every channel
    def result(self):
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
        wind = self.window_( self.block_size )
        weight = sqrt(self.block_size/dot(wind,wind)) # signal energy correction
        fweight = (sqrt(2)/self.block_size)
        wind = wind[:, newaxis]
        for data in self.get_source_data():
            ft = fft.rfft(data*wind*weight, None, 0).astype(self.precision)*fweight
            yield ft
